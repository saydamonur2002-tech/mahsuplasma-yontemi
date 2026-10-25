"""Revizyon C — Adım 1: silinebilir pay bandı.
(1) Zaman istikrarı: 2009–2024 Sektör Bilançoları, 17 NACE + DIŞ düğüm, tam graf tavanı r_y = 1 − Σmax(net,0)/Σbrüt.
(2) Seyrek ağ: 2024, çekim+RAS kenarları, yoğunluk d ∈ {0.25, 0.5, 0.75, 1.0} (rastgele kenar alt kümesi, 30 tohum);
    mevcut kenarlarla en iyi mahsup = min Σf s.t. düğüm net korunur, 0 ≤ f ≤ w (LP). Yoğunluk VARSAYIM (sektör düzeyi; firma ağı gözlenmedi).
(3) 2026Ç1 taşıma: EVDS F içi diğer borç 39.928,6 × oran bandı. 'Yüzde 20' kaldırıldı; yerine ölçülen/hesaplanan bant.
Çıktı: rev_adim1_sonuc.json, rev_adim1_zaman.csv, rev_adim1_seyrek.csv
"""
import json
import numpy as np, pandas as pd
from scipy.optimize import linprog
import rev_veri as rv
KOK = rv.KOK
F_ICI_2026Q1 = 39928.6  # adim1_nace_sonuc.json a_evds_fark ZP44 (milyar TL)
YOGUNLUK = (0.25, 0.5, 0.75, 1.0); TOHUM = 30

def tam_graf(b):
    net = b.ta - b.tb; dis = b.tb.sum() - b.ta.sum()
    taban = net.clip(lower=0).sum() + max(dis, 0.0)
    return float(b.tb.sum()), float(taban), float(1 - taban / b.tb.sum())

def ras(W, r, c, it=500):
    W = W.copy()
    for _ in range(it):
        rs = W.sum(1); W *= np.divide(r, rs, out=np.zeros_like(r), where=rs > 0)[:, None]
        cs = W.sum(0); W *= np.divide(c, cs, out=np.zeros_like(c), where=cs > 0)[None, :]
    return W

def min_brut(W):
    n = len(W); E = [(i, j) for i in range(n) for j in range(n) if W[i, j] > 1e-9]
    net = W.sum(1) - W.sum(0)  # borç çıkışı − alacak (borçlu pozitif)
    Aeq = np.zeros((n, len(E)))
    for k, (i, j) in enumerate(E): Aeq[i, k] += 1; Aeq[j, k] -= 1
    res = linprog(np.ones(len(E)), A_eq=Aeq, b_eq=net, bounds=[(0, W[i, j]) for i, j in E], method="highs")
    return float(res.fun) if res.success else None

def seyrek(b):
    # satır i borçlu (ticari borç), sütun j alacaklı (ticari alacak); DIŞ düğüm farkı kapatır
    tb = np.append(b.tb.to_numpy(), max(b.ta.sum() - b.tb.sum(), 0)); ta = np.append(b.ta.to_numpy(), max(b.tb.sum() - b.ta.sum(), 0))
    n = len(tb); G = np.outer(tb, ta); np.fill_diagonal(G, 0)
    out = []
    for d in YOGUNLUK:
        for s in range(TOHUM if d < 1 else 1):
            rng = np.random.default_rng(s); M = (rng.random((n, n)) < d) if d < 1 else np.ones((n, n), bool)
            np.fill_diagonal(M, False); M[:, -1] |= True; M[-1, :] |= True  # DIŞ her düğüme bağlı (fizibilite)
            W = ras(G * M, tb, ta)
            if abs(W.sum() - tb.sum()) / tb.sum() > 1e-3: continue
            mb = min_brut(W)
            if mb is None: continue
            out.append({"yogunluk": d, "tohum": s, "brut": round(W.sum(), 1), "kalan": round(mb, 1), "silinen_oran": round(1 - mb / W.sum(), 4)})
    return pd.DataFrame(out)

def main():
    p = rv.nace_panel()
    z = []
    for y in rv.YILLAR:
        brut, taban, r = tam_graf(p[p.yil == y]); z.append({"yil": y, "brut_milyar": round(brut, 1), "taban_milyar": round(taban, 1), "tam_graf_oran": round(r, 4)})
    z = pd.DataFrame(z); z.to_csv(KOK / "rev_adim1_zaman.csv", index=False)
    sy = seyrek(p[p.yil == 2024]); sy.to_csv(KOK / "rev_adim1_seyrek.csv", index=False)
    band = sy.groupby("yogunluk").silinen_oran.agg(["min", "median", "max"]).round(4)
    r_min, r_max = float(z.tam_graf_oran.min()), float(z.tam_graf_oran.max())
    s_min = float(sy.silinen_oran.min())
    sonuc = {"faz": "rev C", "adim": 1,
             "zaman_istikrari": {"yillar": [2009, 2024], "tam_graf_oran_min": r_min, "tam_graf_oran_max": r_max,
                                  "tam_graf_oran_2024": float(z[z.yil == 2024].tam_graf_oran.iloc[0]), "etiket": "ust_sinir_nace (ölçüm türevi)"},
             "seyrek_ag_2024": {str(k): v for k, v in band.to_dict("index").items()},
             "seyrek_etiket": "varsayim_yogunluk (sektör düzeyi; firma ağı gözlenmedi)",
             "tasima_2026Q1_milyar": {"taban_stok": F_ICI_2026Q1,
                                       "tam_graf_bandi": [round(F_ICI_2026Q1 * r_min, 1), round(F_ICI_2026Q1 * r_max, 1)],
                                       "seyrek_alt_uc": round(F_ICI_2026Q1 * s_min, 1),
                                       "etiket": "varsayim_oran_tasima (iki kaynak, iki dönem)"},
             "yuzde20": "kaldırıldı; ölçülen bant: tam graf [%.3f, %.3f] (2009–2024), seyrek ağ alt ucu %.3f" % (r_min, r_max, s_min)}
    (KOK / "rev_adim1_sonuc.json").write_text(json.dumps(sonuc, ensure_ascii=False, indent=1), encoding="utf-8")
    print(z.to_string(index=False)); print(band); print(json.dumps(sonuc["tasima_2026Q1_milyar"], ensure_ascii=False))
    return sonuc

if __name__ == "__main__":
    main()
