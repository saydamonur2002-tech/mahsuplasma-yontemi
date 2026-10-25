"""Faz 2 — Adım 2'yi sentetik 150 firma ağından çıkarıp ölçülmüş düğümlere bağlama.

`adim2.csv` (sentetik ağ, temerrüt 0, `modellendi`) yazılmaz; H-A2 kilidi durur. Bu dosya aynı mahsup paketini
(`mahsup/mahsuplasma`) ölçülmüş düğümlerle çalıştırır ve sonucu ayrı dosyaya yazar.

Düğümler (17 NACE kısmı, katman `araci`; Sektör Bilançoları 2024, milyar TL):
  nakit            = hazır değerler (ölçüm) × λ (λ=1 ölçüm; λ* kalibrasyon varsayımı)
  calisan          = YSHİ 2024 çalışanlar sayısı (ölçüm)
  ücret borcu      = personel maliyeti / 12 → HANE_i (ölçüm; aylık dilim varsayımı), ucret=True
Kenarlar (firma→firma, firma→DIS, DIS→firma): Faz 1 çekim/RAS dağılımı (`varsayim_dagitim`); satır toplamı = ticari borç,
sütun toplamı = ticari alacak. DIS (hane, kamu, yurt dışı, kapsam dışı) katmanı `holding`: vadeyi uzatan taraf;
brüt borcu EVDS payından (konsolide ZP22 / konsolide olmayan ZP22, 2026-Q1; `varsayim_oran_tasima`).

Çapa: G1 firma takip oranı 2026-09 (odemeyen_payi_aylik.csv firma_G1_%). Brüt aşamada ödenmemiş/brüt payı buna
oturtan λ* bulunur (kalibrasyon varsayımı); λ=1 ayrı satır.
β tavanı: personel_aylık / (ticari borç + personel_aylık). Serbest likiditenin ücrete gidebilecek payının üst sınırı;
0,3 (sentetik) bununla karşılaştırılır.

Çıktı: adim2_nace_ag.csv (senaryo satırları), adim2_nace_dugum.csv, adim2_nace_ag_sonuc.json, ADIM2_NACE_AG.md.
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

KOK = Path(__file__).resolve().parent
sys.path.insert(0, str(KOK / "mahsup"))
from mahsuplasma.ag import BorcAgi, Firma  # noqa: E402
from mahsuplasma.model import Parametreler, calistir  # noqa: E402
from mahsuplasma.odeme import sirali_odeme  # noqa: E402

import adim1_nace as a1  # noqa: E402

DIS = a1.DIS
CAPA_DONEM = "2026-09"
BETA_SENTETIK = 0.3
HOLDING_SENTETIK = 0.5


def evds_dis_payi() -> dict:
    """Firmaların alacağında başka sektörlerin payı: konsolide ZP22 / konsolide olmayan ZP22 (2026-Q1)."""
    f = a1.evds_fark()
    pay_alacak = f["ZP22"]["konsolide"] / f["ZP22"]["konsolide_olmayan"]
    pay_borc = f["ZP44"]["konsolide"] / f["ZP44"]["konsolide_olmayan"]
    return {"alacak_dis_payi": round(pay_alacak, 4), "borc_dis_payi": round(pay_borc, 4), "donem": a1.DONEM_EVDS,
            "durum": "varsayim_oran_tasima", "not": "EVDS 2026-Q1 payı Sektör Bilançoları 2024 stokuna taşındı."}


def capa() -> dict:
    r = next(x for x in csv.DictReader((KOK / "odemeyen_payi_aylik.csv").open(encoding="utf-8-sig")) if x["Donem"] == CAPA_DONEM)
    return {"firma_G1_yuzde": float(r["firma_G1_%"]), "donem": CAPA_DONEM, "kaynak": "odemeyen_payi_aylik.csv (BDDK/EVDS)", "durum": "olcum"}


def ag_kur(b, kenarlar: list[dict], personel: dict, calisan: dict, lam: float, dis_nakit: float) -> BorcAgi:
    ag = BorcAgi()
    for k, r in b.iterrows():
        ag.firma_ekle(Firma(k, "araci", nakit=float(r["hazir_degerler"]) * lam, calisan=int(calisan.get(k, 0))))
        ag.firma_ekle(Firma(f"HANE_{k}", "hane"))
    ag.firma_ekle(Firma(DIS, "holding", nakit=dis_nakit))
    for e in kenarlar:
        ag.borc_ekle(e["borclu"], e["alacakli"], float(e["milyar_tl"]), vade=1)
    for k in b.index:
        if personel.get(k):
            ag.borc_ekle(k, f"HANE_{k}", personel[k] / 12, vade=1, ucret=True)
    return ag


def odenmemis_payi(ag: BorcAgi, h: float) -> float:
    s = sirali_odeme(ag, tur=3, holding_odeme_orani=h)
    firma = [a for a in ag.firmalar if ag.firmalar[a].katman == "araci"]
    borc = sum(bb.tutar for bb in ag.borclar if bb.borclu in firma)
    return sum(s["odenmemis"][a] for a in firma) / borc if borc else 0.0


def kalibre_lambda(kur, hedef: float, h: float) -> dict:
    """Brüt aşamada firma ödenmemiş/brüt payını G1'e oturtan nakit çarpanı; ikiye bölme."""
    alt, ust = 0.05, 20.0
    p_alt, p_ust = odenmemis_payi(kur(alt), h), odenmemis_payi(kur(ust), h)
    if not (p_ust <= hedef <= p_alt):
        return {"lambda": None, "pay_alt": p_alt, "pay_ust": p_ust, "durum": "bulunamadi"}
    for _ in range(60):
        orta = (alt + ust) / 2
        if odenmemis_payi(kur(orta), h) > hedef:
            alt = orta
        else:
            ust = orta
    return {"lambda": round((alt + ust) / 2, 4), "pay": round(odenmemis_payi(kur((alt + ust) / 2), h), 4), "durum": "kalibrasyon_varsayim"}


def _md_table(baslik, satirlar):
    s = ["| " + " | ".join(baslik) + " |", "| " + " | ".join("---" for _ in baslik) + " |"]
    for r in satirlar:
        s.append("| " + " | ".join("" if x is None else str(x) for x in r) + " |")
    return "\n".join(s)


def main() -> dict:
    b = a1.bilanco()
    personel, calisan = a1.personel_maliyeti(), a1.calisan_sayisi()
    dp = evds_dis_payi()
    dis_brut_borc = float(b["ticari_alacak"].sum()) * dp["alacak_dis_payi"]
    kenarlar, cekim = a1.cekim_kenarlari(b, dis_brut_borc=dis_brut_borc)
    g1 = capa()
    hedef = g1["firma_G1_yuzde"] / 100
    personel_aylik = {k: v / 12 for k, v in personel.items() if k in b.index}
    beta_tavan = sum(personel_aylik.values()) / (float(b["ticari_borc"].sum()) + sum(personel_aylik.values()))
    beta_kisim = {k: round(personel_aylik.get(k, 0) / (float(b.loc[k, "ticari_borc"]) + personel_aylik.get(k, 0)), 4) for k in b.index}

    kur = lambda lam: ag_kur(b, kenarlar, personel, calisan, lam, dis_nakit=dis_brut_borc)
    kal = kalibre_lambda(kur, hedef, HOLDING_SENTETIK)
    lambdalar = [("olcum", 1.0)] + ([("kalibrasyon_varsayim", kal["lambda"])] if kal.get("lambda") else [])

    satirlar, sonuclar = [], {}
    for lam_etiket, lam in lambdalar:
        for h in (HOLDING_SENTETIK, 1.0):
            for beta_etiket, beta in (("sentetik", BETA_SENTETIK), ("tavan", round(beta_tavan, 4))):
                ag = kur(lam)
                r = calistir(ag, Parametreler(holding_odeme_orani=h, sart_kaldiraci=True, ucret_gecis_beta=beta))
                a = r["asamalar"]
                sat = {"adim": 2, "ag": f"NACE {len(b)} kısım + DIS + {len(b)} hane; {len(ag.borclar)} kenar", "lambda": lam, "lambda_etiket": lam_etiket,
                       "holding_odeme_orani": h, "ucret_gecis_beta": beta, "beta_etiket": beta_etiket,
                       "temerrut_brut": a["1_brut"]["temerrut_sayisi"], "temerrut_mahsup": a["3_mahsup_sonrasi_akis"]["temerrut_sayisi"],
                       "temerrut_sart": a["4_sart_kaldiraci"]["temerrut_sayisi"],
                       "ucret_temerrut_brut": a["1_brut"]["ucret_temerrut_sayisi"], "ucret_temerrut_sart": a["4_sart_kaldiraci"]["ucret_temerrut_sayisi"],
                       "kredi_ihtiyaci_brut": round(a["1_brut"]["kredi_ihtiyaci"], 1), "kredi_ihtiyaci_sart": round(a["4_sart_kaldiraci"]["kredi_ihtiyaci"], 1),
                       "istihdam_korunan_brut": a["1_brut"]["istihdam_korunan"], "istihdam_korunan_sart": a["4_sart_kaldiraci"]["istihdam_korunan"],
                       "silinen_milyar": round(r["mahsup"]["silinen"], 1), "silinen_oran": round(r["mahsup"]["silinen_oran"], 4),
                       "serbest_likidite": round(r["ucret"]["serbest_likidite"], 1), "ucret_piyasa_kanali": round(r["ucret"]["piyasa_kanali"], 1),
                       "kilitli": "+".join(r["teshis"]["kilitli"]), "batik": "+".join(r["teshis"]["batik"]),
                       "birim": "milyar TL; adet", "durum": "modellendi_olculmus_dugum",
                       "not": "Düğüm/nakit/ücret ölçüm (2024); kenar dağılımı varsayım; sentetik ağ değil."}
                satirlar.append(sat)
                sonuclar[f"lam{lam}_h{h}_b{beta}"] = sat
    alan = list(satirlar[0].keys())
    with (KOK / "adim2_nace_ag.csv").open("w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=alan); w.writeheader(); w.writerows(satirlar)

    dugum_alan = ["dugum", "katman", "nakit_milyar", "ticari_borc", "ticari_alacak", "ucret_aylik", "calisan", "beta_tavan", "durum"]
    dugum = [{"dugum": k, "katman": "araci", "nakit_milyar": round(float(r["hazir_degerler"]), 1), "ticari_borc": round(float(r["ticari_borc"]), 1),
              "ticari_alacak": round(float(r["ticari_alacak"]), 1), "ucret_aylik": round(personel_aylik.get(k, 0), 1),
              "calisan": int(calisan.get(k, 0)), "beta_tavan": beta_kisim[k], "durum": "olcum"} for k, r in b.iterrows()]
    dugum.append({"dugum": DIS, "katman": "holding", "nakit_milyar": round(dis_brut_borc, 1), "ticari_borc": round(dis_brut_borc, 1),
                  "ticari_alacak": round(dis_brut_borc + float(b["ticari_borc"].sum() - b["ticari_alacak"].sum()), 1),
                  "ucret_aylik": None, "calisan": None, "beta_tavan": None, "durum": "varsayim_oran_tasima"})
    with (KOK / "adim2_nace_dugum.csv").open("w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=dugum_alan); w.writeheader()
        for s in dugum:
            w.writerow({a: ("" if s.get(a) is None else s.get(a)) for a in dugum_alan})

    om = json.load((KOK / "odeme_mahsup_sonuc.json").open(encoding="utf-8"))
    sonuc = {"faz": 2, "adim": 2, "adim2_csv": "yazilmadi (sentetik satır ve H-A2 kilidi durur)",
             "dugum": {"nace": len(b), "hane": len(b), "dis": 1}, "kenar": cekim, "dis_payi": dp, "capa": g1,
             "kalibrasyon": kal, "beta_tavan": round(beta_tavan, 4), "beta_kisim": beta_kisim,
             "sentetik_karsilastirma": {"araci_sayisi": om["ozet"]["araci_sayisi"], "temerrut_sart": om["ozet"]["temerrut_sart"],
                                        "silinen_oran": om.get("mahsup", {}).get("silinen_oran")},
             "senaryolar": sonuclar}
    (KOK / "adim2_nace_ag_sonuc.json").write_text(json.dumps(sonuc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    f = lambda x, n=1: "" if x is None else f"{x:,.{n}f}"
    md = ["# Faz 2 — Adım 2: ölçülmüş düğümlü ağ (sentetik 150 firma yerine)", "",
          "Çalıştır: `python3 adim2_nace_ag.py`. Çıktı: `adim2_nace_ag.csv`, `adim2_nace_dugum.csv`, `adim2_nace_ag_sonuc.json`.", "",
          "`adim2.csv` yazılmaz; sentetik satır (150 firma, temerrüt 0, `modellendi`) ve H-A2 kilidi durur. Aynı mahsup paketi, "
          "başka düğümler: 17 NACE kısmı (Sektör Bilançoları 2024), 17 hane düğümü (ücret), bir dış düğüm.", "",
          "## Ne ölçüm, ne varsayım", "",
          "- Ölçüm: düğüm nakdi (hazır değerler), ticari borç/alacak toplamları, ücret (personel maliyeti/12), çalışan sayısı; "
          f"çapa G1 firma takip oranı {g1['firma_G1_yuzde']}% ({g1['donem']}).",
          f"- Varsayım: kenar dağılımı (çekim/RAS, Faz 1); dış düğüm brüt borcu (EVDS payı {dp['alacak_dis_payi']:.3f} → {f(dis_brut_borc)} milyar); "
          "vade hepsi 1 tur; ücret aylık dilim; λ* kalibrasyonu.",
          "- Eksik: A (tarım) YSHİ kapsamı dışı → ücret ve çalışan 0; o kısımda ücret temerrüdü ölçülemez.",
          f"- λ*: brüt aşamada firma ödenmemiş/brüt payını G1'e oturtan nakit çarpanı: **{kal.get('lambda')}** (`{kal['durum']}`). "
          "λ=1 ölçülen nakitle koşu ayrı satır.",
          f"- β tavanı: Σücret_aylık / (Σticari borç + Σücret_aylık) = **{beta_tavan:.4f}**; sentetik 0,3 bunun "
          f"{'altında' if BETA_SENTETIK < beta_tavan else 'ÜSTÜNDE'}. Orantılı dağılım varsayımı: serbest kalan likidite vadesi gelen "
          "yükümlülüklere payıyla gider; ücret payı bu kadar. Kısım bazında `adim2_nace_dugum.csv`. Üst sınır, ölçüm değil.",
          f"- Brüt aşama kredi ihtiyacı ({f(satirlar[0]['kredi_ihtiyaci_brut'])} milyar, λ=1) stok ölçekli köprü ihtiyacıdır; "
          "tüm ticari borç tek turda istenirse. F F.4 stoku ile karşılaştırılır, eşitlenmez.", "",
          "## Senaryo satırları (milyar TL; adet)", "",
          _md_table(["λ", "etiket", "holding", "β", "temerrüt brüt→mahsup→şart", "ücret temerrüt brüt→şart", "kredi ihtiyacı brüt→şart",
                     "istihdam korunan brüt→şart", "silinen (oran)", "serbest likidite", "ücret piyasa kanalı", "kilitli", "batık"],
                    [[s["lambda"], s["lambda_etiket"], s["holding_odeme_orani"], s["ucret_gecis_beta"],
                      f"{s['temerrut_brut']}→{s['temerrut_mahsup']}→{s['temerrut_sart']}", f"{s['ucret_temerrut_brut']}→{s['ucret_temerrut_sart']}",
                      f"{f(s['kredi_ihtiyaci_brut'])}→{f(s['kredi_ihtiyaci_sart'])}", f"{s['istihdam_korunan_brut']:,}→{s['istihdam_korunan_sart']:,}",
                      f"{f(s['silinen_milyar'])} ({s['silinen_oran']:.1%})", f(s["serbest_likidite"]), f(s["ucret_piyasa_kanali"]),
                      s["kilitli"] or "—", s["batik"] or "—"] for s in satirlar]), "",
          "## Sentetik ile fark", "",
          f"- Sentetik: {om['ozet']['araci_sayisi']} aracı, şart sonrası temerrüt {om['ozet']['temerrut_sart']}. Burada düğüm 17 kısım; temerrüt sayısı "
          "düğüm sayısına bağlıdır, firma sayısına çevrilmez. Temerrüt eden kısım = o kısmın toplulaştırılmış nakdi borcunu karşılamıyor; "
          "kısım içi dağılım görünmez.",
          "- Silinen oranı tam grafta tabana iner (Faz 1 (b)); gerçek seyrek ağda daha düşük. Üst sınır.", "",
          "## Ne denmez", "",
          "- 'Adım 2 ölçüldü' denmez; düğümler ölçüm, kenarlar varsayım: `modellendi_olculmus_dugum`.",
          "- Bu satırlar `adim2.csv`'ye ve `uc_kural_senaryo.csv`'ye taşınmaz.", ""]
    (KOK / "ADIM2_NACE_AG.md").write_text("\n".join(md), encoding="utf-8")
    for s in satirlar:
        print(f"λ {s['lambda']:<7} h {s['holding_odeme_orani']} β {s['ucret_gecis_beta']:<6} temerrüt {s['temerrut_brut']}→{s['temerrut_mahsup']}→{s['temerrut_sart']} "
              f"ücret {s['ucret_temerrut_brut']}→{s['ucret_temerrut_sart']} kredi {s['kredi_ihtiyaci_brut']:,.1f}→{s['kredi_ihtiyaci_sart']:,.1f} "
              f"silinen {s['silinen_oran']:.1%} serbest {s['serbest_likidite']:,.1f}")
    print(f"λ* {kal} | β tavanı {beta_tavan:.4f}")
    return sonuc


if __name__ == "__main__":
    main()
