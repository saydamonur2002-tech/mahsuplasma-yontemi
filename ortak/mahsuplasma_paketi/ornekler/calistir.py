"""Örnek çalıştırma: python ornekler/calistir.py"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from mahsuplasma import calistir, Parametreler, rapor_yaz
from mahsuplasma.senaryo import uc_firma_dongusu, turkiye_tipi

print(">>> Senaryo 0: Üç firma döngüsü (A->B->C->A)\n")
print(rapor_yaz(calistir(uc_firma_dongusu(), Parametreler(sart_kaldiraci=False))))

print("\n\n>>> Senaryo 1: Türkiye tipi ağ, temel parametreler\n")
print(rapor_yaz(calistir(turkiye_tipi())))

print("\n\n>>> Senaryo 2: Sıralama testi — %25 asgari ücret artışı")
for once in (False, True):
    s = calistir(turkiye_tipi(), Parametreler(asgari_ucret_artisi=0.25, asgari_ucret_once_mi=once))
    x = s["asamalar"]["4_sart_kaldiraci"]
    etiket = "ÖNCE ücret, sonra tahsilat" if once else "ÖNCE tahsilat, sonra ücret"
    print(f"  {etiket:<28}: ücretini ödeyemeyen aracı = {x['ucret_temerrut_sayisi']}, "
          f"korunan istihdam = {x['istihdam_korunan']}")

print("\n>>> Senaryo 3: Şart kaldıracının tek başına etkisi (holding ödeme oranı taraması)")
for theta in (0.2, 0.5, 0.8, 1.0):
    s = calistir(turkiye_tipi(), Parametreler(holding_odeme_orani=theta, sart_kaldiraci=False))
    x = s["asamalar"]["3_mahsup_sonrasi_akis"]
    print(f"  holding_odeme_orani={theta:.1f}: temerrüt={x['temerrut_sayisi']:>3}, "
          f"kredi ihtiyacı={x['kredi_ihtiyaci']:>8.1f}")
