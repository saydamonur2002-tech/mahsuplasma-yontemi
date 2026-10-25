"""Mahsuplaşmanın sektörel (TCMB hazne) etkisi — yalnızca EVDS girdisi.

Kenar: finansal hesaplardan türetilmiş aylık TL servis akışı (kredi + diğer),
kalibre_matris / odeme_gercek ile aynı L^m paylaşım kuralı. Bilateral ölçüm yok.

Çalıştırma: python3 mahsup_sektor_evds.py
Çıktı: mahsup_evds_ham.csv, mahsup_sektor_donem.csv, mahsup_sektor_ozet.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

KOK = Path(__file__).resolve().parent
MAHSUP_KOK = KOK / "mahsup"
if str(MAHSUP_KOK) not in sys.path:
    sys.path.insert(0, str(MAHSUP_KOK))

from evds_cek import fetch_group  # noqa: E402
from akis_model import IDX, INSTR, Lm, SEC, panel  # noqa: E402
from odeme_gercek import DIGER_AY, KISA_AY, UZUN_AY, kisa_pay  # noqa: E402
from mahsuplasma.ag import BorcAgi, Firma  # noqa: E402
from mahsuplasma.mahsup import mahsup_ozeti, optimal_mahsup  # noqa: E402

EVDS_GRUPLAR = (
    "bie_finhestnks71011",
    "bie_finhestnks71012",
    "bie_finhestnks71013",
    "bie_finhestnks71014",
    "bie_finhestnks71015",
    "bie_finhestnks7102",
    "bie_finhestnks710121",
    "bie_finhestnks61011",
    "bie_finhestnks61012",
    "bie_finhestnks61013",
    "bie_finhestnks61014",
    "bie_finhestnks61015",
    "bie_finhestnks6102",
    "bie_finhestnks610121",
)

SMAP = {
    "bie_finhestnks71011": "F",
    "bie_finhestnks71012": "B",
    "bie_finhestnks71013": "K",
    "bie_finhestnks71014": "H",
    "bie_finhestnks71015": "H",
    "bie_finhestnks7102": "D",
}
DONEMLER = ("2025-Q4", "2026-Q1", "2026-Q2")
HAM = KOK / "mahsup_evds_ham.csv"
OUT = KOK / "mahsup_sektor_donem.csv"
OZET = KOK / "mahsup_sektor_ozet.json"

SEKTOR_AD = {
    "H": "Hane (+NPISH)",
    "F": "Finansal olmayan kuruluşlar",
    "B": "Bankalar (TCMB ayrılmış)",
    "K": "Bankacılık dışı finansal",
    "D": "Devlet / yerleşik olmayan",
}


def evds_indir() -> pd.DataFrame:
    if HAM.exists() and __import__("os").environ.get("MAHSUP_EVDS_YENILE") != "1":
        print(f"Mevcut ham kullanılıyor: {HAM.name} (yenilemek için MAHSUP_EVDS_YENILE=1)", flush=True)
        return pd.read_csv(HAM, encoding="utf-8-sig")
    rows = []
    for g in EVDS_GRUPLAR:
        try:
            part, n = fetch_group(g, start="01-01-2015", end="07-10-2026", freq="5")
            print(g, n, "seri,", len(part), "gözlem", flush=True)
            rows.extend(part)
        except Exception as exc:  # noqa: BLE001
            print(g, "HATA", exc, flush=True)
    df = pd.DataFrame(rows, columns=["Grup", "Donem", "Seri", "Ad", "Agg", "Deger"])
    df.to_csv(HAM, index=False, encoding="utf-8-sig")
    return df


def _zp(seri: str) -> int:
    return int(seri.rsplit(".", 1)[-1].replace("ZP", ""))


def tablolardan_yukle(df: pd.DataFrame) -> tuple[dict, dict]:
    """akis_model.panel ile uyumlu stok + TCMB stok sözlükleri (H+NPISH toplanır)."""
    stab: dict = {}
    tcs_st: dict = {}
    for _, r in df.iterrows():
        g, p, z, v = r["Grup"], r["Donem"], int(_zp(r["Seri"])), float(r["Deger"])
        if g in SMAP:
            key = (SMAP[g], p, z)
            stab[key] = stab.get(key, 0.0) + v
        elif g == "bie_finhestnks710121":
            tcs_st[(p, z)] = v
    return stab, tcs_st


def kenar_servis(stab, tcs, donem: str) -> dict[tuple[int, int], float]:
    """borçlu j -> alacaklı i, trilyon TL / ay."""
    A, Y = panel(stab, tcs, donem)
    ad = list(INSTR)
    ik, idg = ad.index("kredi"), ad.index("diger")
    mat = Lm(A, Y)
    pay = kisa_pay(stab, tcs)
    aylik = np.zeros((2, 5))
    aylik[0] = Y[ik] * (pay / KISA_AY + (1.0 - pay) / UZUN_AY)
    aylik[1] = Y[idg] / DIGER_AY
    kenar: dict[tuple[int, int], float] = {}
    for blok, M in ((0, mat["kredi"]), (1, mat["diger"])):
        for j in range(5):
            for i in range(5):
                if i == j:
                    continue
                w = float(aylik[blok, j] * M[j, i] / 1e9)
                if w > 1e-12:
                    kenar[(j, i)] = kenar.get((j, i), 0.0) + w
    return kenar


def ag_kur(stab, tcs, donem: str) -> BorcAgi:
    A, Y = panel(stab, tcs, donem)
    im = list(INSTR).index("para_mevduat")
    lik = A[im] / 1e9
    kenar = kenar_servis(stab, tcs, donem)
    ag = BorcAgi()
    for s in SEC:
        ag.firma_ekle(Firma(s, "holding", nakit=float(lik[IDX[s]])))
    for (j, i), w in kenar.items():
        ag.borc_ekle(SEC[j], SEC[i], w, vade=1)
    return ag


def sektor_kirilim(once: BorcAgi, sonra: BorcAgi) -> list[dict]:
    m0, m1 = once.matris(), sonra.matris()
    net0 = once.net_pozisyon()
    net1 = sonra.net_pozisyon()
    satir = []
    for s in SEC:
        cik0 = sum(v for (a, _), v in m0.items() if a == s)
        cik1 = sum(v for (a, _), v in m1.items() if a == s)
        gir0 = sum(v for (_, b), v in m0.items() if b == s)
        gir1 = sum(v for (_, b), v in m1.items() if b == s)
        satir.append(
            {
                "sektor": s,
                "sektor_ad": SEKTOR_AD[s],
                "brut_cikis_once": cik0,
                "brut_cikis_sonra": cik1,
                "brut_giris_once": gir0,
                "brut_giris_sonra": gir1,
                "silinen_cikis": cik0 - cik1,
                "silinen_cikis_oran": (cik0 - cik1) / cik0 if cik0 > 1e-12 else 0.0,
                "net_once": net0[s],
                "net_sonra": net1[s],
                "net_fark": net1[s] - net0[s],
            }
        )
    return satir


def main() -> None:
    print("EVDS indiriliyor…", flush=True)
    ham = evds_indir()
    stab, tcs_st = tablolardan_yukle(ham)
    mevcut = sorted({k[1] for k in stab if k[0] == "F"})
    donemler = [p for p in DONEMLER if p in mevcut]
    if not donemler:
        donemler = mevcut[-3:]
    print("Dönemler:", donemler, flush=True)

    tum = []
    ozet_donem = []
    for p in donemler:
        once = ag_kur(stab, tcs_st, p)
        sonra = optimal_mahsup(once)
        oz = mahsup_ozeti(once, sonra)
        for row in sektor_kirilim(once, sonra):
            row["donem"] = p
            row["ag_brut_once"] = oz["brut_once"]
            row["ag_brut_sonra"] = oz["brut_sonra"]
            row["ag_silinen_oran"] = oz["silinen_oran"]
            tum.append(row)
        ozet_donem.append(
            {
                "donem": p,
                "brut_once_trilyon_ay": oz["brut_once"],
                "brut_sonra_trilyon_ay": oz["brut_sonra"],
                "silinen_oran": oz["silinen_oran"],
                "en_cok_silinen_sektor": max(
                    sektor_kirilim(once, sonra), key=lambda r: r["silinen_cikis"]
                )["sektor"],
            }
        )

    df = pd.DataFrame(tum)
    df.to_csv(OUT, index=False, encoding="utf-8-sig")

    son = df[df.donem == donemler[-1]].sort_values("silinen_cikis", ascending=False)
    out = {
        "kaynak": "EVDS finansal hesaplar (bie_finhestnks710* stok, 610* akım, 710121/610121 TCMB)",
        "ham_dosya": str(HAM.name),
        "kenar_kurali": "Aylık kredi+diger servis × L^m; trilyon TL/ay; bilateral ölçüm değil",
        "mahsup": "optimal_mahsup (net pozisyon sabit)",
        "donemler": donemler,
        "donem_ozet": ozet_donem,
        "son_donem_siralama": son[["sektor", "sektor_ad", "silinen_cikis", "silinen_cikis_oran"]].to_dict(
            orient="records"
        ),
    }
    OZET.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print("\n=== Mahsup sektörel (EVDS) ===")
    for o in ozet_donem:
        print(
            f"{o['donem']}: brüt {o['brut_once_trilyon_ay']:.3f} → {o['brut_sonra_trilyon_ay']:.3f} "
            f"TL/ay (−%{100 * o['silinen_oran']:.1f}); en çok silinen hazne {o['en_cok_silinen_sektor']}"
        )
    print(f"\nDosyalar: {HAM.name}, {OUT.name}, {OZET.name}")


if __name__ == "__main__":
    main()
