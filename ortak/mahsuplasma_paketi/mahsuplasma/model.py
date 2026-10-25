"""Çoklu Mahsuplaşma Modeli — ana boru hattı.

Zincir (önceki tartışmadaki sırayla):

  1. Brüt durum      : kimse mahsuplaşmıyor, herkes sırayla ödüyor.
  2. Mahsup          : döngüler silinir, net pozisyonlar korunur.
  3. Akışla ödeme    : kalan borç, YUKARIDAN AŞAĞIYA nakit akışıyla ödenir.
  4. Şart kaldıracı  : holdingin ödemesi devlet avantajlarına bağlanır
                       (holding_odeme_orani -> 1).
  5. Teşhis          : kilitli / batık / sağlam ayrımı; gerçek zarar.
  6. Ücret kanalı    : serbest kalan likiditenin ücrete geçişi (beta) +
                       asgari ücret artışı (idari kanal).
  7. Döviz kanalı    : TL likidite açığından doğan döviz talebi azalır;
                       ithal girdi kaynaklı talep AZALMAZ.

Model bir öngörü makinesi değil, bir MEKANİZMA LABORATUVARIDIR. Sayılar
parametrelere bağlıdır; asıl çıktı, hangi halkanın hangi koşulda koptuğudur.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict

from .ag import BorcAgi
from .mahsup import dongu_iptali, optimal_mahsup, mahsup_ozeti
from .odeme import eisenberg_noe, sirali_odeme


@dataclass
class Parametreler:
    mahsup_yontemi: str = "optimal"      # "optimal" | "dongu"
    holding_odeme_orani: float = 0.5     # şart yokken holdingin tur başına ödediği pay
    sart_kaldiraci: bool = True          # devlet ödemeyi avantajlara bağlıyor mu
    ucret_gecis_beta: float = 0.3        # serbest likiditenin ücrete geçen payı (<1)
    asgari_ucret_artisi: float = 0.0     # ücret borçlarına uygulanan oran (0.25 = %25)
    asgari_ucret_once_mi: bool = False   # True: ücret artışı tahsilattan ÖNCE gelir
    dovize_kacis: float = 0.4            # TL açığının dövize yönelen payı
    doviz_tavani: float | None = None    # ikame döviz borçlanmasına tavan (firma başına)


def _asgari_ucret_uygula(ag: BorcAgi, p: Parametreler) -> BorcAgi:
    if p.asgari_ucret_artisi == 0:
        return ag
    ag = ag.kopya()
    for b in ag.borclar:
        if b.ucret:
            b.tutar *= 1 + p.asgari_ucret_artisi
            # Sıralama: artış tahsilattan önce gelirse ücret vadesi 1. tura çekilir
            # (holding ödemesi t2'de, tahsilat t3'te nakde döner)
            b.vade = 1 if p.asgari_ucret_once_mi else max(b.vade, 3)
    return ag


def teshis(ag: BorcAgi, sirali: dict, en: dict) -> dict[str, str]:
    """Firmaları sınıflar.
    batik   : tam koordinasyonda bile ödeyemiyor -> gerçek zarar
    kilitli : kapasitesi var ama sıralama/gecikme yüzünden temerrüde düşüyor
    saglam  : sorun yok
    """
    sinif = {}
    for ad, f in ag.firmalar.items():
        if f.katman == "hane":
            continue
        if ad in en["batik"]:
            sinif[ad] = "batik"
        elif ad in sirali["temerrut"]:
            sinif[ad] = "kilitli"
        else:
            sinif[ad] = "saglam"
    return sinif


def _doviz_talebi(ag: BorcAgi, kredi: dict[str, float], p: Parametreler) -> dict:
    ithal, ikame = 0.0, 0.0
    for ad, f in ag.firmalar.items():
        if f.katman == "hane":
            continue
        ithal += f.ithal_girdi_ihtiyaci
        x = p.dovize_kacis * kredi.get(ad, 0.0)
        if p.doviz_tavani is not None:
            x = min(x, p.doviz_tavani)
        ikame += x
    return {"ithal_girdi": ithal, "likidite_kaynakli": ikame, "toplam": ithal + ikame}


def _istihdam(ag: BorcAgi, sirali: dict) -> int:
    return sum(f.calisan for ad, f in ag.firmalar.items()
               if f.katman != "hane" and ad not in sirali["ucret_temerrut"])


def calistir(ag: BorcAgi, p: Parametreler | None = None) -> dict:
    p = p or Parametreler()
    ag = _asgari_ucret_uygula(ag, p)

    # 1. Brüt durum
    brut_sirali = sirali_odeme(ag, tur=_tur(ag), holding_odeme_orani=p.holding_odeme_orani)
    en = eisenberg_noe(ag)

    # 2. Mahsup
    if p.mahsup_yontemi == "dongu":
        net_ag, gunluk = dongu_iptali(ag)
    else:
        net_ag, gunluk = optimal_mahsup(ag), []
    ozet = mahsup_ozeti(ag, net_ag)

    # 3. Akışla ödeme (şartsız)
    net_sirali = sirali_odeme(net_ag, tur=_tur(ag), holding_odeme_orani=p.holding_odeme_orani)

    # 4. Şart kaldıracı
    oran = 1.0 if p.sart_kaldiraci else p.holding_odeme_orani
    sartli_sirali = sirali_odeme(net_ag, tur=_tur(ag), holding_odeme_orani=oran)

    # 5. Teşhis (brüt duruma göre)
    sinif = teshis(ag, brut_sirali, en)
    gercek_zarar = sum(v for ad, v in en["acik"].items()
                       if ag.firmalar[ad].katman != "hane")

    # 6. Ücret kanalı: aracının serbest kalan likiditesi
    serbest = 0.0
    for ad in ag.katmana_gore("araci"):
        serbest += max(0.0, sartli_sirali["son_nakit"][ad] - brut_sirali["son_nakit"][ad])
    ucret_piyasa = p.ucret_gecis_beta * serbest
    ucret_idari = sum(b.tutar for b in ag.borclar if b.ucret) * (
        p.asgari_ucret_artisi / (1 + p.asgari_ucret_artisi)) if p.asgari_ucret_artisi else 0.0

    # 7. Döviz
    dv_once = _doviz_talebi(ag, brut_sirali["kredi_ihtiyaci"], p)
    dv_sonra = _doviz_talebi(ag, sartli_sirali["kredi_ihtiyaci"], p)

    def asamalar(s):
        return {
            "temerrut_sayisi": len([a for a in s["temerrut"] if ag.firmalar[a].katman != "hane"]),
            "ucret_temerrut_sayisi": len(s["ucret_temerrut"]),
            "kredi_ihtiyaci": sum(s["kredi_ihtiyaci"].values()),
            "istihdam_korunan": _istihdam(ag, s),
            "holding_gecikmesi": s["holding_gecikmesi"],
        }

    return {
        "parametreler": asdict(p),
        "mahsup": ozet,
        "dongu_gunlugu": gunluk,
        "asamalar": {
            "1_brut": asamalar(brut_sirali),
            "3_mahsup_sonrasi_akis": asamalar(net_sirali),
            "4_sart_kaldiraci": asamalar(sartli_sirali),
        },
        "teshis": {
            "siniflar": sinif,
            "kilitli": sorted(a for a, s in sinif.items() if s == "kilitli"),
            "batik": sorted(a for a, s in sinif.items() if s == "batik"),
            "gercek_zarar": gercek_zarar,
        },
        "ucret": {
            "serbest_likidite": serbest,
            "piyasa_kanali": ucret_piyasa,
            "idari_kanal_asgari_ucret": ucret_idari,
        },
        "doviz": {"once": dv_once, "sonra": dv_sonra},
        "toplam_istihdam": sum(f.calisan for f in ag.firmalar.values()),
    }


def _tur(ag: BorcAgi) -> int:
    return max((b.vade for b in ag.borclar), default=1) + 2
