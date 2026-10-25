"""Revizyon ortak veri: TÜİK Sektör Bilançoları çok yıllı (2009–2024) NACE kısımları, TCMB/EVDS yardımcıları."""
from __future__ import annotations
import re
from functools import lru_cache
from pathlib import Path
import numpy as np, pandas as pd
KOK = Path(__file__).resolve().parent
BIL = KOK / "Ekonomik faaliyetlere ve yıllara göre firmaların  bilanço hesapları .xls"
GEL = KOK / "Ekonomik faaliyetlere ve yıllara göre firmaların  gelir tablosu .xls"
YILLAR = list(range(2009, 2025))
# blok başlığı satırına göre ofsetler (adim1_nace.BILANCO_SATIR ile aynı kalemler)
B_OFS = {"hazir": 2, "ta_kv": 14, "ta_uv": 58, "banka_kv": 127, "tb_kv": 136, "banka_uv": 177, "tb_uv": 184}
B_ETIKET = {"hazir": "A-Hazır", "ta_kv": "C-Ticari alacak", "ta_uv": "A-Ticari alacak", "banka_kv": "1-Banka kred", "tb_kv": "B-Ticari borç",
            "banka_uv": "1-Banka kred", "tb_uv": "B-Ticari borç"}
G_OFS = {"finansman_gideri": 39, "net_satis": 8}

def _bloklar(x):
    return [i for i in range(len(x)) if re.match(r"^[A-Z]\s*-", str(x.iloc[i, 0]).strip())]

@lru_cache(None)
def nace_panel() -> pd.DataFrame:
    """uzun: nace, yil, kalem (milyar TL). Etiket doğrulaması yapılır (ofset kayarsa hata)."""
    x = pd.read_excel(BIL, header=None); y = pd.read_excel(GEL, header=None)
    yil_col = {int(float(v)): c for c, v in enumerate(x.iloc[3]) if str(v).replace(".0", "").isdigit()}
    gyil_col = {int(float(v)): c for c, v in enumerate(y.iloc[3]) if str(v).replace(".0", "").isdigit()}
    rows = []
    for b in _bloklar(x):
        nace = str(x.iloc[b, 0]).strip()[0]
        for k, o in B_OFS.items():
            lab = str(x.iloc[b + o, 1]).strip()
            assert lab.replace(" ", "").startswith(B_ETIKET[k].replace(" ", "")[:8]), (nace, k, lab[:30])
            for yl, c in yil_col.items():
                v = pd.to_numeric(x.iloc[b + o, c], errors="coerce")
                rows.append({"nace": nace, "yil": yl, "kalem": k, "deger": (0.0 if pd.isna(v) else float(v)) / 1e6})
    for b in _bloklar(y):
        nace = str(y.iloc[b, 0]).strip()[0]
        for k, o in G_OFS.items():
            for yl, c in gyil_col.items():
                v = pd.to_numeric(y.iloc[b + o, c], errors="coerce")
                rows.append({"nace": nace, "yil": yl, "kalem": k, "deger": (0.0 if pd.isna(v) else float(v)) / 1e6})
    d = pd.DataFrame(rows).pivot_table(index=["nace", "yil"], columns="kalem", values="deger").reset_index()
    d["ta"] = d.ta_kv + d.ta_uv; d["tb"] = d.tb_kv + d.tb_uv; d["banka"] = d.banka_kv + d.banka_uv
    return d

def evds_pb(seri: str) -> dict:
    p = KOK / "veri_dis/para_banka_secili.csv"
    d = pd.read_csv(p)
    return {r.Donem: r.Deger for r in d[d.Seri == seri].itertuples()}
