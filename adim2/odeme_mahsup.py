"""Ödeme zinciri ağını çoklu mahsuplaşma laboratuvarına bağlar.

TCMB 2026-Q1 stokları ve ag_kur_v2 kenar kuralı (Tur 7–8 ile aynı).
Makro düğümler (H,B,K,D) holding; 150 firma aracı katmanı.

Tekrar: python3 odeme_mahsup.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

KOK = Path(__file__).resolve().parent
MAHSUP_KOK = KOK / "mahsup"
if str(MAHSUP_KOK) not in sys.path:
    sys.path.insert(0, str(MAHSUP_KOK))

import numpy as np

from mahsuplasma import BorcAgi, Firma, Parametreler, calistir, rapor_yaz  # noqa: E402
from mahsuplasma.mahsup import dongu_iptali, mahsup_ozeti, optimal_mahsup  # noqa: E402
from mahsuplasma.model import teshis  # noqa: E402
from mahsuplasma.odeme import eisenberg_noe, sirali_odeme  # noqa: E402

from odeme_dagilim import F0, N_FIRMA, stok_yukle  # noqa: E402
from odeme_kons7 import ag_kur_v2  # noqa: E402

MACRO = ("H", "B", "K", "D")


def _ad(idx: int) -> str:
    if idx < F0:
        return MACRO[idx]
    return f"F{idx - F0}"


def _name_to_idx(nd: int) -> dict[str, int]:
    m = {MACRO[i]: i for i in range(F0)}
    for f in range(F0, nd):
        m[f"F{f - F0}"] = f
    return m


def ag_kenarlari_pakete(pak: dict, ag: BorcAgi) -> dict:
    """Kenar listesini günceller; lik/kucuk/fx aynı kalır."""
    import copy

    out = copy.deepcopy(pak)
    net = out["net"]
    nd = int(out["lik"].size)
    idx = _name_to_idx(nd)
    borclu, alacakli, w0 = [], [], []
    for b in ag.borclar:
        if b.tutar < 1e-12:
            continue
        borclu.append(idx[b.borclu])
        alacakli.append(idx[b.alacakli])
        w0.append(float(b.tutar))
    borclu_a = np.asarray(borclu, dtype=np.int32)
    alacakli_a = np.asarray(alacakli, dtype=np.int32)
    w0_a = np.asarray(w0, dtype=np.float64)
    net["borclu"] = borclu_a
    net["alacakli"] = alacakli_a
    net["w0"] = w0_a
    net["borc"] = np.bincount(borclu_a, weights=w0_a, minlength=nd).astype(np.float64)
    net["alacak"] = np.bincount(alacakli_a, weights=w0_a, minlength=nd).astype(np.float64)
    net["dis_akis"] = net["borc"] - net["alacak"]
    kucuk, buyuk = net["kucuk"], net["buyuk"]
    net["idx_ku_al"] = np.flatnonzero(kucuk[alacakli_a])
    net["idx_bu_al"] = np.flatnonzero(buyuk[alacakli_a])
    net["idx_bu_borc"] = np.flatnonzero(buyuk[borclu_a])
    net["idx_b2k"] = np.flatnonzero(buyuk[borclu_a] & kucuk[alacakli_a])
    return out


def mahsup_paket(pak: dict, yontem: str = "optimal") -> tuple[dict, dict, BorcAgi, BorcAgi]:
    ag = paket_to_ag(pak)
    if yontem == "dongu":
        ag2, _ = dongu_iptali(ag)
    else:
        ag2 = optimal_mahsup(ag)
    oz = mahsup_ozeti(ag, ag2)
    return ag_kenarlari_pakete(pak, ag2), oz, ag, ag2


def statik_teshis(ag: BorcAgi, holding_odeme_orani: float = 0.5) -> dict:
    tur = max((b.vade for b in ag.borclar), default=1) + 2
    sir = sirali_odeme(ag, tur=tur, holding_odeme_orani=holding_odeme_orani)
    en = eisenberg_noe(ag)
    sinif = teshis(ag, sir, en)
    firma = [ad for ad, f in ag.firmalar.items() if f.katman != "hane"]
    tem = len([ad for ad in sir["temerrut"] if ad in firma])
    return {
        "temerrut": tem,
        "kilitli": len([ad for ad in firma if sinif.get(ad) == "kilitli"]),
        "batik": len([ad for ad in firma if sinif.get(ad) == "batik"]),
    }


def paket_to_ag(pak: dict) -> BorcAgi:
    net = pak["net"]
    lik = pak["lik"]
    nd = int(lik.size)
    ag = BorcAgi()
    for i in range(F0):
        ag.firma_ekle(Firma(MACRO[i], "holding", nakit=float(lik[i])))
    for f in range(F0, nd):
        ag.firma_ekle(Firma(_ad(f), "araci", nakit=float(lik[f])))
    for j, i, w in zip(net["borclu"], net["alacakli"], net["w0"]):
        wt = float(w)
        if wt < 1e-9:
            continue
        ucret = i == 0 and j >= F0
        ag.borc_ekle(_ad(int(j)), _ad(int(i)), wt, vade=1, ucret=ucret)
    return ag


def ozet_sayisal(ag: BorcAgi, p: Parametreler | None = None) -> dict:
    p = p or Parametreler()
    s = calistir(ag, p)
    m = s["mahsup"]
    b, a3, a4 = s["asamalar"]["1_brut"], s["asamalar"]["3_mahsup_sonrasi_akis"], s["asamalar"]["4_sart_kaldiraci"]
    return {
        "brut_borc": ag.brut_borc(),
        "brut_sonra_mahsup": m["brut_sonra"],
        "brut_azalma_oran": m["silinen_oran"],
        "temerrut_brut": b["temerrut_sayisi"],
        "temerrut_mahsup_akis": a3["temerrut_sayisi"],
        "temerrut_sart": a4["temerrut_sayisi"],
        "kredi_ihtiyaci_brut": b["kredi_ihtiyaci"],
        "kredi_ihtiyaci_sart": a4["kredi_ihtiyaci"],
        "kilitli_sayisi": len(s["teshis"]["kilitli"]),
        "batik_sayisi": len(s["teshis"]["batik"]),
        "gercek_zarar": s["teshis"]["gercek_zarar"],
        "araci_sayisi": len(ag.katmana_gore("araci")),
    }


def main() -> None:
    stok = stok_yukle()
    n = N_FIRMA
    mev = srv = alac = __import__("numpy").full(n, 1.0 / n)
    pak = ag_kur_v2(stok, mev, srv, alac)
    ag = paket_to_ag(pak)

    p = Parametreler(holding_odeme_orani=0.5, sart_kaldiraci=True)
    sonuc = calistir(ag, p)
    say = ozet_sayisal(ag, p)

    en = eisenberg_noe(ag)
    tur = max((b.vade for b in ag.borclar), default=1) + 2
    sir = sirali_odeme(ag, tur=tur, holding_odeme_orani=0.5)
    say["eisenberg_batik"] = len([a for a in en["batik"] if ag.firmalar[a].katman != "hane"])

    out = {
        "senaryo": "esit_pay_150_firma_tcmb_2026q1",
        "kenar_sayisi": len(ag.borclar),
        "parametreler": sonuc["parametreler"],
        "ozet": say,
        "teshis": {
            "kilitli_ornek": sonuc["teshis"]["kilitli"][:12],
            "batik_ornek": sonuc["teshis"]["batik"][:12],
        },
    }
    (KOK / "odeme_mahsup_sonuc.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print("=== Ödeme zinciri → mahsup (eşit pay, 150 firma) ===")
    print(f"Brüt borç: {say['brut_borc']:.1f} | Mahsup sonrası: {say['brut_sonra_mahsup']:.1f} "
          f"(−%{100 * say['brut_azalma_oran']:.1f})")
    print(
        f"Temerrüt: brüt {say['temerrut_brut']} → mahsup+akış {say['temerrut_mahsup_akis']} "
        f"→ şart kaldıracı {say['temerrut_sart']}"
    )
    print(
        f"Kilitli {say['kilitli_sayisi']} | Batık {say['batik_sayisi']} | "
        f"Eisenberg batık {say['eisenberg_batik']} | Gerçek zarar {say['gercek_zarar']:.1f}"
    )
    print(f"Kredi ihtiyacı: brüt {say['kredi_ihtiyaci_brut']:.1f} → şart {say['kredi_ihtiyaci_sart']:.1f}")
    print()
    print(rapor_yaz(sonuc))


if __name__ == "__main__":
    main()
