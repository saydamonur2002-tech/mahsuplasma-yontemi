"""Sentetik borç ağı üretici.

UYARI: Bu veriler gerçek değildir. Gerçek uygulamada ağ e-fatura (GİB)
verisinden kurulmalıdır. Buradaki amaç mekanizmanın davranışını görmek.

Yapı (önceki tartışmadaki tipoloji):
  - Holdingler aracılardan alım yapar ve vadeyi uzatır (vade = 2).
  - Aracılar birbirine ve holdinglere borçludur (vade = 1) -> döngüler.
  - Aracılar işçilerine ücret borçludur (varsayılan vade = 3: ay sonu).
  Zaman çizelgesi: t1 aracı borçları, t2 holding ödemesi, t3 ücret.
  Tahsilat bir tur gecikmeli nakde döner; yani t2'de holdingden gelen
  para ancak t3'teki ücrete yetişir.
  - Holdinglerin nakdi bol, aracılarınki kıt.
"""
from __future__ import annotations

import random

from .ag import BorcAgi, Firma


def uc_firma_dongusu() -> BorcAgi:
    """Ders kitabı örneği: A->B->C->A, her biri 100. Kimse net borçlu değil,
    kimsenin nakdi yok. Mahsupsuz herkes batar; mahsupla kimse batmaz."""
    ag = BorcAgi()
    for ad in "ABC":
        ag.firma_ekle(Firma(ad, "araci", nakit=0.0, calisan=10))
    ag.borc_ekle("A", "B", 100)
    ag.borc_ekle("B", "C", 100)
    ag.borc_ekle("C", "A", 100)
    return ag


def turkiye_tipi(n_holding: int = 3, n_araci: int = 40, tohum: int = 42,
                 ucret_vadesi: int = 3) -> BorcAgi:
    r = random.Random(tohum)
    ag = BorcAgi()
    H = [f"H{i+1}" for i in range(n_holding)]
    A = [f"A{i+1:02d}" for i in range(n_araci)]

    for h in H:
        ag.firma_ekle(Firma(h, "holding", nakit=r.uniform(800, 1500),
                            doviz_borcu=r.uniform(300, 600),
                            ithal_girdi_ihtiyaci=r.uniform(100, 200),
                            calisan=r.randint(400, 900)))
    for a in A:
        ag.firma_ekle(Firma(a, "araci", nakit=r.uniform(20, 70),
                            doviz_borcu=r.uniform(0, 40),
                            ithal_girdi_ihtiyaci=r.uniform(0, 15),
                            calisan=r.randint(5, 60)))
        ag.firma_ekle(Firma(f"hane_{a}", "hane"))

    # Holding -> aracı (geç ödenen alımlar)
    for h in H:
        for a in r.sample(A, k=n_araci // 2):
            ag.borc_ekle(h, a, r.uniform(20, 80), vade=2)
    # Aracı -> aracı (yatay ticaret, döngü kaynağı)
    for a in A:
        for b in r.sample([x for x in A if x != a], k=3):
            ag.borc_ekle(a, b, r.uniform(5, 40), vade=1)
    # Aracı -> holding (holdingden hammadde/ürün alımı)
    for a in A:
        ag.borc_ekle(a, r.choice(H), r.uniform(5, 30), vade=1)
    # Aracı -> hane (ücret)
    for a in A:
        f = ag.firmalar[a]
        ag.borc_ekle(a, f"hane_{a}", f.calisan * r.uniform(0.6, 1.0),
                     vade=ucret_vadesi, ucret=True)
    return ag
