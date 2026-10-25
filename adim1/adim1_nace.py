"""Faz 1 — Adım 1 için silinen miktarın hesaplanabilir sınırı: F sektörü içi (firma→firma) ticari kredi.

Adım 1 (`adim1_stok.csv`) hazneler arası (H, F, B′, K′, D) çiftlerde üst sınır verir; `silinen` boş kalır, çünkü kimden-kime
xls depoda yok. Bu dosya o sütunu DOLDURMAZ. Başka bir nesneyi ölçer: firma sektörü İÇİNDEKİ karşılıklı ticari borç,
üç katmanda:

  (a) ölçüm        : F konsolide olmayan − konsolide (EVDS 2026-Q1). Fark = firmaların birbirine olan alacak/borcu.
                     ZP22 (VF.8 diğer alacaklar) ve ZP44 (F.8 diğer borçlar) ticari kredi vekili; ZP45 (F.0) toplam.
  (b) ust_sinir    : NACE kısmı (17 düğüm + dış düğüm) çok taraflı netleştirme tabanı. Sektör Bilançoları 2024
                     (TÜİK–TCMB) ticari alacak (dönen+duran) ve ticari borç (KV+UV). silinen_max = brüt − Σmax(net_i,0).
                     Kısım içi (aynı NACE) borçlar düğümde yok olur → gerçek silinenden büyük; o yüzden üst sınır.
  (c) varsayim     : kenarları çekim kuralıyla dağıt (kenar_ij ∝ TB_i · TA_j), `optimal_mahsup` çalıştır. Dağılım ölçüm
                     değil; tam grafta sonuç (b) tabanına iner. Faz 2 bu kenar matrisini girdi alır (etiketiyle).

Birim: xls bin TL → milyar TL (÷1e6). EVDS bin TL → milyar TL (÷1e6).
Çıktı: adim1_nace.csv (kısım satırları + özet), adim1_nace_kenar.csv (çekim kenarları), adim1_yuzde20.csv ((e) koşusu), adim1_nace_sonuc.json, ADIM1_NACE.md.
`adim1_stok.csv` ve `tek_sistem_esleme.csv` yazılmaz.
"""

from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

import pandas as pd

KOK = Path(__file__).resolve().parent
sys.path.insert(0, str(KOK / "mahsup"))
from mahsuplasma.ag import BorcAgi, Firma  # noqa: E402
from mahsuplasma.mahsup import mahsup_ozeti, optimal_mahsup  # noqa: E402

BILANCO_XLS = KOK / "Ekonomik faaliyetlere göre firmaların referans yıl bilanço hesapları .xls"
GELIR_XLS = KOK / "Ekonomik faaliyetlere göre firmaların referans yıl gelir tablosu .xls"
YSHI_XLS = KOK / "Ekonomik faaliyetlere göre temel göstergeler, 2024.xls"
REFERANS_YIL = 2024
DONEM_EVDS = "2026-Q1"
DIS = "DIS"  # dış düğüm: hane, kamu, banka, yurt dışı, kapsam dışı firma
SENARYO_SILINEN_ORAN = 0.20  # (e) 'yaklaşık yüzde 20' koşusu; varsayım, ölçüm değil

# Sektör Bilançoları t2 satır indeksleri (0 tabanlı; doğrulandı)
SATIR = {"hazir_degerler": 7, "ticari_alacak_kv": 19, "ticari_alacak_uv": 63, "aktif": 128,
         "banka_kredisi_kv": 132, "banka_kredisi_uv": 182, "ticari_borc_kv": 141, "ticari_borc_uv": 189, "oz_kaynak": 215}
GELIR_SATIR = {"net_satis": 13, "faaliyet_kari": 24, "finansman_gideri": 44, "donem_kari": 55}


def _sayi(x) -> float | None:
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return None
    s = str(x).strip().replace(".", "").replace(",", ".")
    if s in {"", "c", "x", "-", "nan"}:
        return None
    try:
        return float(s)
    except ValueError:
        return None


def _nace_kodu(baslik) -> str | None:
    m = re.match(r"^\s*([A-Z])\s*[- ]", str(baslik))
    return m.group(1) if m else None


def bilanco() -> pd.DataFrame:
    df = pd.read_excel(BILANCO_XLS, sheet_name="t2", header=None)
    kolon = {c: _nace_kodu(df.iloc[4, c]) for c in range(1, df.shape[1])}
    kolon = {c: k for c, k in kolon.items() if k}
    kayit = {}
    for c, k in kolon.items():
        kayit[k] = {ad: (_sayi(df.iloc[r, c]) or 0.0) / 1e6 for ad, r in SATIR.items()}
    g = pd.read_excel(GELIR_XLS, sheet_name="t3", header=None)
    gkolon = {c: _nace_kodu(g.iloc[4, c]) for c in range(1, g.shape[1])}
    for c, k in gkolon.items():
        if k in kayit:
            for ad, r in GELIR_SATIR.items():
                kayit[k][ad] = (_sayi(g.iloc[r, c]) or 0.0) / 1e6
    out = pd.DataFrame(kayit).T
    out.index.name = "nace"
    out["ticari_alacak"] = out["ticari_alacak_kv"] + out["ticari_alacak_uv"]
    out["ticari_borc"] = out["ticari_borc_kv"] + out["ticari_borc_uv"]
    out["banka_kredisi"] = out["banka_kredisi_kv"] + out["banka_kredisi_uv"]
    return out


def _yshi_sutun(sutun: int, bolen: float) -> dict[str, float]:
    df = pd.read_excel(YSHI_XLS, sheet_name="t2", header=None)
    out = {}
    for r in range(4, df.shape[0]):
        k = _nace_kodu(df.iloc[r, 0])
        if k and "Toplam" in str(df.iloc[r, 1]):
            v = _sayi(df.iloc[r, sutun])
            if v is not None:
                out[k] = v / bolen
    return out


def personel_maliyeti() -> dict[str, float]:
    """YSHİ 2024 personel maliyeti (TL → milyar TL), NACE kısım toplamı."""
    return _yshi_sutun(5, 1e9)


def calisan_sayisi() -> dict[str, float]:
    """YSHİ 2024 çalışanlar sayısı (kişi), NACE kısım toplamı."""
    return _yshi_sutun(3, 1.0)


def evds_fark() -> dict:
    """F konsolide olmayan (stok_silim_tavan_ham) − konsolide (finansal_hesaplar_uzun), 2026-Q1, milyar TL."""
    ko = {}
    for r in csv.DictReader((KOK / "stok_silim_tavan_ham.csv").open(encoding="utf-8-sig")):
        if r["hazne"] == "F" and r["donem"] == DONEM_EVDS:
            ko[r["seri"].split(".")[-1]] = float(r["deger"]) / 1e6
    k = {}
    for r in csv.DictReader((KOK / "finansal_hesaplar_uzun.csv").open(encoding="utf-8-sig")):
        if r["Hazne"] == "F" and r["Donem"] == DONEM_EVDS:
            k[r["Seri"].split(".")[-1]] = float(r["Deger"]) / 1e6
    def satir(kod, ad):
        return {"kod": kod, "ad": ad, "konsolide_olmayan": round(ko[kod], 1), "konsolide": round(k[kod], 1),
                "sektor_ici": round(ko[kod] - k[kod], 1), "durum": "olcum"}
    return {"ZP22": satir("ZP22", "VF.8 diğer alacaklar (ticari kredi vekili)"),
            "ZP44": satir("ZP44", "F.8 diğer borçlar (ticari kredi vekili)"),
            "ZP45": satir("ZP45", "F.0 toplam yükümlülük")}


def netlestirme_tabani(b: pd.DataFrame) -> dict:
    net = (b["ticari_alacak"] - b["ticari_borc"]).to_dict()
    net[DIS] = -sum(net.values())
    brut = float(b["ticari_borc"].sum())  # firmaların tüm ticari borcu; hepsi firma-içi sayılır → brüt üst sınır
    taban = sum(v for v in net.values() if v > 0)
    return {"brut_milyar": round(brut, 1), "taban_milyar": round(taban, 1), "silinen_max_milyar": round(brut - taban, 1),
            "silinen_max_oran": round((brut - taban) / brut, 4) if brut else None, "net": {k: round(v, 1) for k, v in net.items()},
            "dugum": len(net), "durum": "ust_sinir_nace",
            "not": "Kısım içi (aynı NACE) borç düğümde görünmez; dış düğüm artığı taşır. Üst sınır, ölçüm değil."}


def cekim_kenarlari(b: pd.DataFrame, dis_brut_borc: float | None = None) -> tuple[list[dict], dict]:
    """kenar_ij ∝ TB_i · TA_j, RAS ile satır/sütun toplamlarına oturtulur; dış düğüm artığı taşır. Varsayım.

    dis_brut_borc verilirse dış düğümün firmalara brüt borcu o olur (alacağı = brüt borç + artık); verilmezse yalnız net artık
    tek yönde durur (Faz 1 üst sınır kurgusu)."""
    ta, tb = b["ticari_alacak"].to_dict(), b["ticari_borc"].to_dict()
    sum_ta, sum_tb = sum(ta.values()), sum(tb.values())
    artik = sum_tb - sum_ta  # >0: firmalar dışa net borçlu
    if dis_brut_borc is None:
        dis_alacak, dis_borc = max(0.0, artik), max(0.0, -artik)
    else:
        dis_borc = dis_brut_borc
        dis_alacak = dis_brut_borc + artik
        if dis_alacak < 0:
            raise ValueError("dış düğüm alacağı negatif; dis_brut_borc artığı karşılamıyor")
    ta_d, tb_d = dict(ta), dict(tb)
    ta_d[DIS], tb_d[DIS] = dis_alacak, dis_borc
    dugumler = list(b.index) + [DIS]
    # RAS: satır toplamı = TB_i, sütun toplamı = TA_j, köşegen sıfır (kendine borç yok)
    m = {(i, j): tb_d[i] * ta_d[j] for i in dugumler for j in dugumler if i != j}
    for _ in range(200):
        for i in dugumler:
            s = sum(v for (a, _), v in m.items() if a == i)
            if s > 0:
                for j in dugumler:
                    if i != j:
                        m[(i, j)] *= tb_d[i] / s
        for j in dugumler:
            s = sum(v for (_, c), v in m.items() if c == j)
            if s > 0:
                for i in dugumler:
                    if i != j:
                        m[(i, j)] *= ta_d[j] / s
    kenarlar = []
    ag = BorcAgi()
    for ad in dugumler:
        ag.firma_ekle(Firma(ad, "araci" if ad != DIS else "holding"))
    for (i, j), tutar in m.items():
        if tutar > 1e-6:
            kenarlar.append({"borclu": i, "alacakli": j, "milyar_tl": round(tutar, 3), "kural": "cekim_ras", "durum": "varsayim_dagitim"})
            ag.borc_ekle(i, j, tutar)
    sonra = optimal_mahsup(ag)
    oz = mahsup_ozeti(ag, sonra)
    kalan = sonra.matris()
    return kenarlar, {"brut_milyar": round(oz["brut_once"], 1), "silinen_milyar": round(oz["silinen"], 1),
                      "silinen_oran": round(oz["silinen_oran"], 4), "teorik_taban_milyar": round(oz["teorik_taban"], 1),
                      "kalan_kenar": len(kalan), "durum": "varsayim_dagitim",
                      "not": "Çekim dağılımı ölçüm değil. Tam grafta optimal mahsup (b) tabanına iner; gerçek (seyrek) ağda silinen daha az."}


def senaryo_yuzde(fark: dict, taban: dict, cekim: dict) -> dict:
    """(e) Silinen oranı SENARYO_SILINEN_ORAN (yüzde 20) VARSAYILIRSA ne çıkar: üç tabanda, üst sınırla karşılaştırmalı.

    Oran ölçüm değil; 'yaklaşık yüzde 20' cümlesi için koşu. adim1_stok.csv silinen sütunu dolmaz."""
    a1 = {r["cift"]: r for r in csv.DictReader((KOK / "adim1_stok.csv").open(encoding="utf-8-sig"))}
    top = a1.get("TOPLAM", {})
    brut_hazne = float(top["brut"]) if top.get("brut") else None
    yeni_tavan = float(top["yeni_tavan"]) if top.get("yeni_tavan") else None
    o = SENARYO_SILINEN_ORAN
    tabanlar = [
        {"taban": "NACE Σ ticari borç (Sektör Bilançoları 2024)", "brut_milyar": taban["brut_milyar"], "ust_sinir_oran": taban["silinen_max_oran"],
         "ust_sinir_kaynak": "b_nace_taban"},
        {"taban": "EVDS F içi diğer borç ZP44 (2026-Q1)", "brut_milyar": fark["ZP44"]["sektor_ici"], "ust_sinir_oran": taban["silinen_max_oran"],
         "ust_sinir_kaynak": "b_nace_taban oranı taşındı (varsayım)"},
        {"taban": "Hazneler arası brüt (adim1_stok.csv TOPLAM)", "brut_milyar": brut_hazne, "ust_sinir_oran": yeni_tavan,
         "ust_sinir_kaynak": "adim1_stok yeni_tavan (ust_sinir)"},
    ]
    satirlar = []
    for t in tabanlar:
        if t["brut_milyar"] is None:
            continue
        silinen = o * t["brut_milyar"]
        ust = None if t["ust_sinir_oran"] is None else t["ust_sinir_oran"] * t["brut_milyar"]
        satirlar.append({**t, "oran": o, "silinen_milyar": round(silinen, 1), "ust_sinir_milyar": None if ust is None else round(ust, 1),
                         "ust_sinir_icinde": None if ust is None else bool(silinen <= ust + 1e-9),
                         "ust_sinira_oran": None if not ust else round(silinen / ust, 3), "durum": "varsayim_yuzde20"})
    return {"oran": o, "satirlar": satirlar, "cekim_sonucu_oran": cekim["silinen_oran"], "durum": "varsayim_yuzde20",
            "not": "Oran varsayım; üç tabanda sayı. Üst sınır içinde kalması olabilirliği gösterir, gerçekleştiğini değil. adim1_stok.csv silinen boş."}


def _md_table(baslik: list[str], satirlar: list[list]) -> str:
    s = ["| " + " | ".join(baslik) + " |", "| " + " | ".join("---" for _ in baslik) + " |"]
    for r in satirlar:
        s.append("| " + " | ".join("" if x is None else str(x) for x in r) + " |")
    return "\n".join(s)



def _rev_bant_md():
    import json as _j
    p = KOK / "rev_adim1_sonuc.json"
    if not p.exists():
        return ["- rev_adim1_sonuc.json yok; önce `python rev_adim1.py`."]
    r = _j.loads(p.read_text(encoding="utf-8")); z = r["zaman_istikrari"]; t = r["tasima_2026Q1_milyar"]
    sat = [f"- Tam graf oranı 2009–2024: [{z['tam_graf_oran_min']:.3f}, {z['tam_graf_oran_max']:.3f}], 2024: {z['tam_graf_oran_2024']:.3f} (`ust_sinir_nace`).",
           "- Seyrek ağ 2024 (çekim+RAS, rastgele kenar alt kümesi, LP en iyi mahsup; `varsayim_yogunluk`):"]
    for d, v in r["seyrek_ag_2024"].items():
        sat.append(f"  - yoğunluk {d}: min {v['min']:.3f} / medyan {v['median']:.3f} / max {v['max']:.3f}")
    sat.append(f"- 2026Ç1 taşıma (`varsayim_oran_tasima`): tam graf {t['tam_graf_bandi'][0]:,.1f}–{t['tam_graf_bandi'][1]:,.1f} milyar; seyrek alt uç {t['seyrek_alt_uc']:,.1f} milyar.")
    return sat


def main() -> dict:
    b = bilanco()
    pm = personel_maliyeti()
    b["personel_maliyeti"] = pd.Series(pm)
    fark = evds_fark()
    taban = netlestirme_tabani(b)
    kenarlar, cekim = cekim_kenarlari(b)
    f = lambda x, n=1: "" if x is None else f"{x:,.{n}f}"

    # NACE oranını EVDS F-içi stokuna uygulama: ayrı etiket, ayrı satır; toplanmaz
    birlesik = {"evds_sektor_ici_zp44_milyar": fark["ZP44"]["sektor_ici"], "nace_silinen_max_oran": taban["silinen_max_oran"],
                "silinen_ust_milyar": round(fark["ZP44"]["sektor_ici"] * taban["silinen_max_oran"], 1), "durum": "varsayim_oran_tasima",
                "not": "2024 NACE oranı 2026-Q1 EVDS stokuna taşındı; iki kaynak, iki dönem. Varsayım."}
    yuzde = senaryo_yuzde(fark, taban, cekim)

    alan = ["nace", "ticari_alacak", "ticari_borc", "net", "hazir_degerler", "banka_kredisi_kv", "banka_kredisi_uv", "finansman_gideri",
            "net_satis", "personel_maliyeti", "aktif", "birim", "kaynak", "donem", "durum"]
    satirlar = []
    for k, r in b.iterrows():
        satirlar.append({"nace": k, "ticari_alacak": round(r["ticari_alacak"], 1), "ticari_borc": round(r["ticari_borc"], 1),
                         "net": round(r["ticari_alacak"] - r["ticari_borc"], 1), "hazir_degerler": round(r["hazir_degerler"], 1),
                         "banka_kredisi_kv": round(r["banka_kredisi_kv"], 1), "banka_kredisi_uv": round(r["banka_kredisi_uv"], 1),
                         "finansman_gideri": round(r["finansman_gideri"], 1), "net_satis": round(r["net_satis"], 1),
                         "personel_maliyeti": None if pd.isna(r["personel_maliyeti"]) else round(r["personel_maliyeti"], 1),
                         "aktif": round(r["aktif"], 1), "birim": "milyar TL", "kaynak": "Sektör Bilançoları 2024 (TÜİK–TCMB); YSHİ 2024",
                         "donem": REFERANS_YIL, "durum": "olcum"})
    satirlar.append({"nace": DIS, "ticari_alacak": None, "ticari_borc": None, "net": taban["net"][DIS], "birim": "milyar TL",
                     "kaynak": "artık", "donem": REFERANS_YIL, "durum": "ust_sinir_nace"})
    satirlar.append({"nace": "TOPLAM", "ticari_alacak": round(b["ticari_alacak"].sum(), 1), "ticari_borc": round(b["ticari_borc"].sum(), 1),
                     "net": round((b["ticari_alacak"] - b["ticari_borc"]).sum(), 1), "hazir_degerler": round(b["hazir_degerler"].sum(), 1),
                     "banka_kredisi_kv": round(b["banka_kredisi_kv"].sum(), 1), "banka_kredisi_uv": round(b["banka_kredisi_uv"].sum(), 1),
                     "finansman_gideri": round(b["finansman_gideri"].sum(), 1), "net_satis": round(b["net_satis"].sum(), 1),
                     "personel_maliyeti": round(b["personel_maliyeti"].sum(), 1), "aktif": round(b["aktif"].sum(), 1),
                     "birim": "milyar TL", "kaynak": "toplam", "donem": REFERANS_YIL, "durum": "olcum"})
    with (KOK / "adim1_nace.csv").open("w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=alan); w.writeheader()
        for s in satirlar:
            w.writerow({a: ("" if s.get(a) is None else s.get(a)) for a in alan})
    y_alan = ["taban", "brut_milyar", "oran", "silinen_milyar", "ust_sinir_oran", "ust_sinir_milyar", "ust_sinir_icinde", "ust_sinira_oran", "ust_sinir_kaynak", "durum"]
    with (KOK / "adim1_yuzde20.csv").open("w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=y_alan); w.writeheader()
        for t in yuzde["satirlar"]:
            w.writerow({a: ("" if t.get(a) is None else t.get(a)) for a in y_alan})
    with (KOK / "adim1_nace_kenar.csv").open("w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=["borclu", "alacakli", "milyar_tl", "kural", "durum"]); w.writeheader(); w.writerows(kenarlar)

    sonuc = {"faz": 1, "adim": 1, "nesne": "F sektörü içi ticari kredi; adim1_stok.csv silinen sütunu DOLDURULMAZ",
             "a_evds_fark": fark, "b_nace_taban": taban, "c_cekim_mahsup": cekim, "d_oran_tasima": birlesik, "e_senaryo_yuzde20": yuzde,
             "nace_kisim": len(b), "kaynak": {"bilanco": BILANCO_XLS.name, "gelir": GELIR_XLS.name, "yshi": YSHI_XLS.name,
                                               "evds": ["stok_silim_tavan_ham.csv", "finansal_hesaplar_uzun.csv"]},
             "adim1_stok_silinen": "bos (dokunulmadi)", "etiketler": ["olcum", "ust_sinir_nace", "varsayim_dagitim", "varsayim_oran_tasima", "varsayim_yuzde20"]}
    (KOK / "adim1_nace_sonuc.json").write_text(json.dumps(sonuc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    md = ["# Faz 1 — Adım 1: silinen miktarın hesaplanabilir sınırı (F sektörü içi)", "",
          "Çalıştır: `python3 adim1_nace.py`. Çıktı: `adim1_nace.csv`, `adim1_nace_kenar.csv`, `adim1_yuzde20.csv`, `adim1_nace_sonuc.json`.", "",
          "`adim1_stok.csv` hazneler arası (H, F, B′, K′, D) üst sınırdır; `silinen` sütunu boş kalır ve bu dosya onu doldurmaz. "
          "Burada başka bir nesne ölçülür: firma sektörü içindeki karşılıklı ticari borç. İki sayı toplanmaz.", "",
          "## (a) Ölçüm: F konsolide olmayan − konsolide, EVDS 2026-Q1 (milyar TL)", "",
          _md_table(["kod", "kalem", "konsolide olmayan", "konsolide", "sektör içi", "etiket"],
                    [[v["kod"], v["ad"], f(v["konsolide_olmayan"]), f(v["konsolide"]), f(v["sektor_ici"]), v["durum"]] for v in fark.values()]), "",
          "Sektör içi fark, firmaların birbirine olan alacak/borcudur; ZP22 ile ZP44 farkının eşit çıkması tutarlılık kontrolüdür. "
          "Bu sayı brüt stoktur; kaçının netleşebileceğini söylemez. Sektör Bilançoları Σ ticari alacak "
          f"({f(float(b['ticari_alacak'].sum()))}, {REFERANS_YIL}) bu stokun altındadır: kapsam (bilanço veren firmalar) ve kalem "
          "(VF.8 ticari krediden geniştir) farklı; dönem farklı. İkisi eşitlenmez.", "",
          f"## (b) Üst sınır: NACE {len(b)} kısım + dış düğüm, çok taraflı netleştirme tabanı (Sektör Bilançoları {REFERANS_YIL})", "",
          f"- Brüt (Σ ticari borç) {f(taban['brut_milyar'])} milyar; taban Σmax(net,0) {f(taban['taban_milyar'])}; "
          f"silinen_max {f(taban['silinen_max_milyar'])} = **{taban['silinen_max_oran']:.1%}** (`{taban['durum']}`).",
          f"- {taban['not']}",
          f"- Dış düğüm net {f(taban['net'][DIS])}: firmaların ticari alacağı ile borcu arasındaki fark (hane, kamu, yurt dışı, kapsam dışı).", "",
          _md_table(["NACE", "ticari alacak", "ticari borç", "net", "hazır değerler", "banka kredisi KV", "finansman gideri", "personel"],
                    [[s["nace"], f(s.get("ticari_alacak")), f(s.get("ticari_borc")), f(s.get("net")), f(s.get("hazir_degerler")),
                      f(s.get("banka_kredisi_kv")), f(s.get("finansman_gideri")), f(s.get("personel_maliyeti"))] for s in satirlar]), "",
          "## (c) Varsayım: çekim dağılımı + optimal mahsup", "",
          f"- kenar_ij ∝ TB_i · TA_j; {len(kenarlar)} kenar; brüt {f(cekim['brut_milyar'])}; silinen {f(cekim['silinen_milyar'])} "
          f"({cekim['silinen_oran']:.1%}); teorik taban {f(cekim['teorik_taban_milyar'])}; kalan kenar {cekim['kalan_kenar']}.",
          f"- {cekim['not']} Kenar matrisi Faz 2'ye `varsayim_dagitim` etiketiyle girdi olur.", "",
          "## (d) Varsayım: oranı EVDS stokuna taşıma", "",
          f"- {f(birlesik['evds_sektor_ici_zp44_milyar'])} × {birlesik['nace_silinen_max_oran']:.4f} = **{f(birlesik['silinen_ust_milyar'])} milyar** üst sınır "
          f"(`{birlesik['durum']}`). {birlesik['not']}", "",
          "## (e) Ölçülen bant (rev C; eski 'yüzde 20' koşusu kaldırıldı)", "",
          *_rev_bant_md(), "",
          "## Ne denmez", "",
          "- 'Stok yüzde X silindi' denmez; (b) ve (c) üst sınır, (d) varsayım, (e) bant (yoğunluk varsayımlı). Gerçek silinen için firma düzeyi kimden-kime gerekir (depoda yok).",
          "- Hazneler arası `yeni_tavan` 0,2582 ile bu oran toplanmaz; biri hazneler arası, biri F içi.", ""]
    (KOK / "ADIM1_NACE.md").write_text("\n".join(md), encoding="utf-8")
    print(f"(a) F içi ZP44 {fark['ZP44']['sektor_ici']:,.1f} | (b) silinen_max {taban['silinen_max_oran']:.1%} "
          f"({taban['silinen_max_milyar']:,.1f}/{taban['brut_milyar']:,.1f}) | (c) çekim {cekim['silinen_oran']:.1%} | (d) {birlesik['silinen_ust_milyar']:,.1f}")
    for t in yuzde["satirlar"]:
        print(f"(e) %20 | {t['taban'][:44]:<44} brüt {t['brut_milyar']:>9,.1f} silinen {t['silinen_milyar']:>8,.1f} üst {t['ust_sinir_milyar']!s:>9} içinde {t['ust_sinir_icinde']}")
    return sonuc


if __name__ == "__main__":
    main()
