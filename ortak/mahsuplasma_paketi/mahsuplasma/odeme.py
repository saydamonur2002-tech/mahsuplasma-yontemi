"""Ödeme akışı.

İki farklı soru, iki farklı algoritma:

eisenberg_noe   -> "Herkes aynı anda, tam koordinasyonla ödese kim batar?"
                   Bu, ağın ÖDEME KAPASİTESİDİR. Döngüler burada sorun
                   yaratmaz; çünkü eşzamanlı takas döngüyü kendiliğinden çözer.
                   Burada batan firma gerçekten batıktır.

sirali_odeme    -> "Herkes elindeki nakitle, vadesi gelince, 'önce alacağımı
                   tahsil edeyim' diye beklerse ne olur?" Gerçek hayat budur.
                   Burada batan ama yukarıda batmayan firma KİLİTLİDİR:
                   sorun ödeme gücü değil, koordinasyon ve sıralamadır.

İkisinin farkı, mahsuplaşmanın ve "akışla ödeme"nin çözebileceği alanı verir.
"""
from __future__ import annotations

from .ag import BorcAgi


def eisenberg_noe(ag: BorcAgi, tol: float = 1e-9, maks_iter: int = 10_000) -> dict:
    """Eisenberg & Noe (2001) takas vektörü (en büyük sabit nokta).
    p_i = min( L_i , e_i + sum_j Pi_ji * p_j )"""
    L = ag.toplam_yukumluluk()
    m = ag.matris()
    e = {ad: f.nakit for ad, f in ag.firmalar.items()}
    p = dict(L)
    for _ in range(maks_iter):
        gelen = {ad: 0.0 for ad in ag.firmalar}
        for (i, j), lij in m.items():
            if L[i] > 0:
                gelen[j] += lij / L[i] * p[i]
        yeni = {ad: min(L[ad], e[ad] + gelen[ad]) for ad in ag.firmalar}
        fark = max(abs(yeni[k] - p[k]) for k in p) if p else 0.0
        p = yeni
        if fark < tol:
            break
    acik = {ad: L[ad] - p[ad] for ad in ag.firmalar}
    return {
        "odeme": p,
        "acik": acik,
        "batik": sorted(ad for ad, v in acik.items() if v > 1e-6),
    }


def sirali_odeme(ag: BorcAgi, tur: int | None = None,
                 holding_odeme_orani: float = 1.0) -> dict:
    """Tur tur ödeme simülasyonu.

    - Her tur başında firma elindeki nakitle, vadesi gelmiş ve ödenmemiş
      borçlarını orantılı öder.
    - Bu turda gelen para ancak bir sonraki tura yetişir (tahsilat gecikmesi).
    - Holdingler, nakitleri yetse bile vadesi gelen borcun yalnızca
      `holding_odeme_orani` kadarını öder (vade uzatma davranışı).
      Devletin "şarta bağlama" kaldıracı bu oranı 1'e çeker.
    - Vadesinde tam ödenemeyen borç = temerrüt. Ücret borcunda temerrüt
      ayrıca işaretlenir: aracının asıl batma anı budur.
    """
    if tur is None:
        tur = max((b.vade for b in ag.borclar), default=1)
    nakit = {ad: f.nakit for ad, f in ag.firmalar.items()}
    kalan = [b.tutar for b in ag.borclar]
    temerrut: dict[str, int] = {}
    ucret_temerrut: dict[str, int] = {}
    kredi_ihtiyaci = {ad: 0.0 for ad in ag.firmalar}

    for t in range(1, tur + 1):
        gelen = {ad: 0.0 for ad in ag.firmalar}
        # firma bazında vadesi gelmiş borçlar
        vadeli: dict[str, list[int]] = {}
        for k, b in enumerate(ag.borclar):
            if b.vade <= t and kalan[k] > 1e-12:
                vadeli.setdefault(b.borclu, []).append(k)
        for ad, idx in vadeli.items():
            istenen = sum(kalan[k] for k in idx)
            oran_ust = holding_odeme_orani if ag.firmalar[ad].katman == "holding" else 1.0
            odenebilir = min(nakit[ad], istenen * oran_ust)
            pay = odenebilir / istenen if istenen else 0.0
            for k in idx:
                o = kalan[k] * pay
                kalan[k] -= o
                gelen[ag.borclar[k].alacakli] += o
            nakit[ad] -= odenebilir
            acik = istenen - odenebilir
            # gecikme davranışı (holding) temerrüt değil, tercih: ayrı tutulur
            gercek_acik = istenen * oran_ust - odenebilir
            if gercek_acik > 1e-6:
                temerrut.setdefault(ad, t)
                kredi_ihtiyaci[ad] = max(kredi_ihtiyaci[ad], gercek_acik)
                if any(ag.borclar[k].ucret and kalan[k] > 1e-6 for k in idx):
                    ucret_temerrut.setdefault(ad, t)
            elif acik > 1e-6 and ag.firmalar[ad].katman != "holding":
                temerrut.setdefault(ad, t)
        for ad, v in gelen.items():
            nakit[ad] += v

    odenmemis = {ad: 0.0 for ad in ag.firmalar}
    for k, b in enumerate(ag.borclar):
        odenmemis[b.borclu] += kalan[k]
    return {
        "son_nakit": nakit,
        "odenmemis": odenmemis,
        "temerrut": temerrut,               # firma -> ilk temerrüt turu
        "ucret_temerrut": ucret_temerrut,   # işçisini ödeyemeyenler
        "kredi_ihtiyaci": kredi_ihtiyaci,   # temerrüdü önlemek için gereken köprü kredi
        "holding_gecikmesi": sum(odenmemis[a] for a in ag.katmana_gore("holding")),
    }
