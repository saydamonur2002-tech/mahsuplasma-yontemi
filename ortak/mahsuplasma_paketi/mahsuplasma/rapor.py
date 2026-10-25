"""Sonuçları okunabilir Türkçe rapora çevirir."""
from __future__ import annotations


def _tl(x: float) -> str:
    return f"{x:,.1f}".replace(",", "X").replace(".", ",").replace("X", ".")


def rapor_yaz(s: dict) -> str:
    m, a, t = s["mahsup"], s["asamalar"], s["teshis"]
    satir = []
    satir.append("=== ÇOKLU MAHSUPLAŞMA MODELİ ===")
    satir.append(f"Brüt borç           : {_tl(m['brut_once'])} -> {_tl(m['brut_sonra'])}"
                 f"  (silinen %{100*m['silinen_oran']:.1f})")
    satir.append(f"Teorik taban        : {_tl(m['teorik_taban'])}  (net borçluların toplamı;"
                 " mahsup buranın altına inemez)")
    satir.append("")
    satir.append(f"{'Aşama':<26}{'Temerrüt':>9}{'Ücret tem.':>11}{'Kredi ihtiyacı':>16}{'İstihdam':>10}")
    for ad, k in [("1. Brüt (mahsupsuz)", "1_brut"),
                  ("3. Mahsup + akış", "3_mahsup_sonrasi_akis"),
                  ("4. + Şart kaldıracı", "4_sart_kaldiraci")]:
        x = a[k]
        satir.append(f"{ad:<26}{x['temerrut_sayisi']:>9}{x['ucret_temerrut_sayisi']:>11}"
                     f"{_tl(x['kredi_ihtiyaci']):>16}{x['istihdam_korunan']:>10}")
    satir.append(f"(toplam istihdam: {s['toplam_istihdam']})")
    satir.append("")
    satir.append("TEŞHİS")
    satir.append(f"  Kilitli firmalar  : {len(t['kilitli'])}  (ödeme gücü var, sıra/gecikme yüzünden batıyor)")
    satir.append(f"  Batık firmalar    : {len(t['batik'])}  {', '.join(t['batik']) or '-'}")
    satir.append(f"  Gerçek zarar      : {_tl(t['gercek_zarar'])}")
    u = s["ucret"]
    satir.append("")
    satir.append("ÜCRET KANALI")
    satir.append(f"  Aracıda serbest kalan likidite : {_tl(u['serbest_likidite'])}")
    satir.append(f"  Piyasa kanalı (beta ile)       : {_tl(u['piyasa_kanali'])}")
    satir.append(f"  İdari kanal (asgari ücret)     : {_tl(u['idari_kanal_asgari_ucret'])}")
    d = s["doviz"]
    satir.append("")
    satir.append("DÖVİZ TALEBİ")
    satir.append(f"  Likidite kaynaklı : {_tl(d['once']['likidite_kaynakli'])} -> {_tl(d['sonra']['likidite_kaynakli'])}")
    satir.append(f"  İthal girdi       : {_tl(d['once']['ithal_girdi'])} -> {_tl(d['sonra']['ithal_girdi'])}  (mahsup buna dokunmaz)")
    return "\n".join(satir)
