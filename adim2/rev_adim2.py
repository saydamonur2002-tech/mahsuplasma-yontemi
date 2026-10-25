"""Revizyon D — Adım 2: β tavanı ve bandı, çeyreklik akım kredi ihtiyacı, çok çapalı λ*.
- β ∈ {0, β_tavan/2, β_tavan}; β=0,3 (sentetik) ana tablodan çıkarıldı (tavanın üstünde → tutarsız).
- Akım: borçlunun ticari borcu × φ_i, φ_i = min(1, 91,25 / DPO_i), DPO_i = KV ticari borç / net satış × 365 (Sektör Bilançoları 2024;
  net satış maliyet yerine → DPO alt tahmin, φ üst tahmin: kredi ihtiyacı temkinli üst). Ücret: çeyreklik (yıllık/4). VARSAYIM: çeyrekte bir tur.
- λ*: çapa G1 ∈ {2024-06, 2025-03, 2025-09, 2026-03, 2026-09} (odemeyen_payi_aylik.csv), hem 'stok tek tur' hem 'çeyreklik akım' ağında.
Çıktı: rev_adim2.csv, rev_adim2_sonuc.json
"""
import csv, json
from pathlib import Path
import pandas as pd
import adim1_nace as a1, adim2_nace_ag as a2, rev_veri as rv
from mahsuplasma.ag import BorcAgi, Firma
from mahsuplasma.model import Parametreler, calistir
KOK = Path(__file__).resolve().parent
CAPALAR = ("2024-06", "2025-03", "2025-09", "2026-03", "2026-09")

def ag(b, kenar, personel, calisan, lam, dis, phi, ucret_bolen):
    g = BorcAgi()
    for k, r in b.iterrows():
        g.firma_ekle(Firma(k, "araci", nakit=float(r["hazir_degerler"]) * lam, calisan=int(calisan.get(k, 0)))); g.firma_ekle(Firma(f"HANE_{k}", "hane"))
    g.firma_ekle(Firma(a2.DIS, "holding", nakit=dis))
    for e in kenar:
        g.borc_ekle(e["borclu"], e["alacakli"], float(e["milyar_tl"]) * phi.get(e["borclu"], 1.0), vade=1)
    for k in b.index:
        if personel.get(k): g.borc_ekle(k, f"HANE_{k}", personel[k] / ucret_bolen, vade=1, ucret=True)
    return g

def main():
    b = a1.bilanco(); personel, calisan = a1.personel_maliyeti(), a1.calisan_sayisi()
    dp = a2.evds_dis_payi(); dis = float(b["ticari_alacak"].sum()) * dp["alacak_dis_payi"]
    kenar, _ = a1.cekim_kenarlari(b, dis_brut_borc=dis)
    p = rv.nace_panel(); p24 = p[p.yil == 2024].set_index("kod") if "kod" in p.columns else p[p.yil == 2024].set_index(p.columns[0])
    dpo = (p24.tb_kv / p24.net_satis * 365).to_dict()
    phi = {k: min(1.0, 91.25 / v) if v and v > 0 else 1.0 for k, v in dpo.items()}
    pa = {k: v / 12 for k, v in personel.items() if k in b.index}
    beta_t = sum(pa.values()) / (float(b["ticari_borc"].sum()) + sum(pa.values()))
    rejim = {"stok_tek_tur": ({}, 12), "ceyreklik_akim": (phi, 4)}
    g1 = {r["Donem"]: float(r["firma_G1_%"]) / 100 for r in csv.DictReader(open(KOK / "odemeyen_payi_aylik.csv", encoding="utf-8-sig"))}
    lam_tab, satir = [], []
    for rj, (ph, ub) in rejim.items():
        kur = lambda lam, ph=ph, ub=ub: ag(b, kenar, personel, calisan, lam, dis, ph, ub)
        for c in CAPALAR:
            k = a2.kalibre_lambda(kur, g1[c], a2.HOLDING_SENTETIK); lam_tab.append({"rejim": rj, "capa": c, "G1": g1[c], "lambda": k["lambda"], "durum": k["durum"]})
        lams = sorted({x["lambda"] for x in lam_tab if x["rejim"] == rj and x["lambda"]})
        for lam_et, lam in [("olcum", 1.0)] + ([("lambda*_min", lams[0]), ("lambda*_max", lams[-1])] if lams else []):
            for h in (a2.HOLDING_SENTETIK, 1.0):
                for bet, beta in (("sifir", 0.0), ("tavan/2", round(beta_t / 2, 4)), ("tavan", round(beta_t, 4))):
                    r = calistir(kur(lam), Parametreler(holding_odeme_orani=h, sart_kaldiraci=True, ucret_gecis_beta=beta)); a = r["asamalar"]
                    satir.append({"rejim": rj, "lambda_etiket": lam_et, "lambda": lam, "holding": h, "beta_etiket": bet, "beta": beta,
                                  "temerrut_brut": a["1_brut"]["temerrut_sayisi"], "temerrut_sart": a["4_sart_kaldiraci"]["temerrut_sayisi"],
                                  "ucret_temerrut_sart": a["4_sart_kaldiraci"]["ucret_temerrut_sayisi"],
                                  "kredi_brut": round(a["1_brut"]["kredi_ihtiyaci"], 1), "kredi_sart": round(a["4_sart_kaldiraci"]["kredi_ihtiyaci"], 1),
                                  "silinen_oran": round(r["mahsup"]["silinen_oran"], 4)})
    pd.DataFrame(satir).to_csv(KOK / "rev_adim2.csv", index=False)
    s = {"faz": "rev D", "beta_tavan": round(beta_t, 4), "beta_bandi": [0.0, round(beta_t, 4)], "beta_0_3": "ana tablodan çıkarıldı (tavan üstü)",
         "phi": {k: round(v, 3) for k, v in phi.items()}, "dpo_gun": {k: round(v, 1) for k, v in dpo.items()},
         "lambda_yildiz": lam_tab, "etiketler": {"phi": "olcum_turevi (DPO, net satış ile)", "ceyrekte_bir_tur": "varsayim", "beta": "tavan olcum_turevi, bant varsayim", "lambda*": "kalibrasyon_varsayim"}}
    (KOK / "rev_adim2_sonuc.json").write_text(json.dumps(s, ensure_ascii=False, indent=1), encoding="utf-8")
    print(pd.DataFrame(lam_tab).to_string(index=False)); print(pd.DataFrame(satir).to_string(index=False))

if __name__ == "__main__":
    main()
