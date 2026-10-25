"""Çok taraflı mahsuplaşma (multilateral netting).

İki yöntem:

1) dongu_iptali  : Ağdaki borç döngülerini (A->B->C->A) bulur, döngünün en
   küçük kenarı kadar her kenardan düşer. Elle yapılabilecek, şeffaf yöntem.
   Sonuç her zaman döngüsüz bir ağdır ama küresel en iyi olmayabilir.

2) optimal_mahsup: Fleischman-Dini-Littera (2020) yaklaşımı. Var olan
   kenarlar üzerinde, her firmanın net pozisyonunu koruyarak toplam brüt
   borcu en aza indiren minimum maliyetli akış problemi.

Her iki yöntemin de değiştiremeyeceği tek şey NET POZİSYONDUR. Yani
mahsuplaşma net borçluyu (çoğunlukla holding) borçtan kurtarmaz; yalnızca
"kilitli" borçları siler. Modelin bütün mantığı bu kısıtın üzerine kuruludur.
"""
from __future__ import annotations

import networkx as nx

from .ag import BorcAgi, Borc

_OLCEK = 100  # kuruş hassasiyeti (min-cost flow tamsayı ister)


def _matristen_agi_kur(eski: BorcAgi, yeni_m: dict[tuple[str, str], float]) -> BorcAgi:
    """Toplu matristeki azalmayı orijinal borç kalemlerine orantılı dağıtır.
    Böylece vade ve ücret bilgisi korunur."""
    eski_m = eski.matris()
    ag = eski.kopya()
    ag.borclar = []
    for b in eski.borclar:
        anahtar = (b.borclu, b.alacakli)
        oran = yeni_m.get(anahtar, 0.0) / eski_m[anahtar] if eski_m[anahtar] else 0.0
        kalan = b.tutar * oran
        if kalan > 1e-9:
            ag.borclar.append(Borc(b.borclu, b.alacakli, kalan, b.vade, b.ucret))
    return ag


def dongu_iptali(ag: BorcAgi) -> tuple[BorcAgi, list[dict]]:
    """Döngüleri tek tek kapatır. İkinci çıktı, kapatılan döngülerin günlüğü
    (teşhis için: hangi firmalar birbirini kilitliyordu?)."""
    m = {k: v for k, v in ag.matris().items() if not _ucret_kenari(ag, k)}
    ucret_m = {k: v for k, v in ag.matris().items() if _ucret_kenari(ag, k)}
    G = nx.DiGraph()
    for (i, j), v in m.items():
        G.add_edge(i, j, w=v)
    gunluk = []
    while True:
        try:
            dongu = nx.find_cycle(G)
        except nx.NetworkXNoCycle:
            break
        en_kucuk = min(G[u][v]["w"] for u, v in dongu)
        for u, v in dongu:
            G[u][v]["w"] -= en_kucuk
            if G[u][v]["w"] <= 1e-9:
                G.remove_edge(u, v)
        gunluk.append({"dongu": [u for u, _ in dongu], "silinen": en_kucuk})
    yeni_m = {(u, v): d["w"] for u, v, d in G.edges(data=True)}
    yeni_m.update(ucret_m)
    return _matristen_agi_kur(ag, yeni_m), gunluk


def optimal_mahsup(ag: BorcAgi) -> BorcAgi:
    """Var olan ticari ilişkiler üzerinde en fazla borcu silen çözüm.
    Ücret borçları mahsuba sokulmaz (hane kimseye borç vermiyor)."""
    tum = ag.matris()
    m = {k: v for k, v in tum.items() if not _ucret_kenari(ag, k)}
    ucret_m = {k: v for k, v in tum.items() if _ucret_kenari(ag, k)}

    G = nx.DiGraph()
    talep: dict[str, int] = {}
    for (i, j), v in m.items():
        kap = int(round(v * _OLCEK))
        if kap <= 0:
            continue
        G.add_edge(i, j, capacity=kap, weight=1)
        talep[i] = talep.get(i, 0) - kap
        talep[j] = talep.get(j, 0) + kap
    for n in G.nodes:
        G.nodes[n]["demand"] = talep.get(n, 0)

    akis = nx.min_cost_flow(G) if G.number_of_edges() else {}
    yeni_m = {}
    for i, hedefler in akis.items():
        for j, x in hedefler.items():
            if x > 0:
                yeni_m[(i, j)] = x / _OLCEK
    yeni_m.update(ucret_m)
    return _matristen_agi_kur(ag, yeni_m)


def mahsup_ozeti(once: BorcAgi, sonra: BorcAgi) -> dict:
    b0, b1 = once.brut_borc(), sonra.brut_borc()
    alt_sinir = sum(v for v in once.net_pozisyon().values() if v > 0)
    return {
        "brut_once": b0,
        "brut_sonra": b1,
        "silinen": b0 - b1,
        "silinen_oran": (b0 - b1) / b0 if b0 else 0.0,
        # Merkezi takas odası olsaydı inilebilecek teorik taban:
        "teorik_taban": alt_sinir,
    }


def _ucret_kenari(ag: BorcAgi, anahtar: tuple[str, str]) -> bool:
    return ag.firmalar[anahtar[1]].katman == "hane"
