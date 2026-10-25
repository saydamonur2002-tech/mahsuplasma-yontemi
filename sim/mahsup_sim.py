"""mahsup_sim: Adım1 + Adım2 mahsuplaşmanın etkisini simüle eder ve veriye kalibre eder.
Tek başına çalışır: python3 mahsup_sim.py  (EVDS için ortam değişkeni EVDS_API_KEY; değeri yazdırılmaz)
EVDS uç noktası: https://evds3.tcmb.gov.tr/igmevdsms-dis
Nedensellik iddiası yok; çıktılar mekanizma + üst sınır."""
from __future__ import annotations
import csv, json, os, urllib.request
from pathlib import Path
import numpy as np

K = Path(__file__).resolve().parent
HAM = K / "ham"
EVDS = "https://evds3.tcmb.gov.tr/igmevdsms-dis"

# Mekanizma sabitleri (repo dosyalarından)
ORTAK_STOK_A1 = 20363.4      # adim1_stok.csv TOPLAM ortak [HESAP, üst sınır]
UST_SINIR_A1 = 0.2582        # yeni_tavan
FAIZLI_STOK_A1 = 7463.7      # analiz_adim12/hassasiyet: F–PFK 7195,0 + F–ROW 268,7
SPREAD_MERKEZ = 9.89         # pp, kredi − mevduat [İKİNCİL]
SILINEN_A2 = 14602.3         # adim2_nace_ag.csv, %88,5
SILME_A2 = 0.885
KREDI_IHT_A2 = 8328.6        # brüt aşama kredi ihtiyacı λ=1
SERBEST_LIK_A2 = 208.4       # holding 0,5
BETA = 0.0439
LAMBDA = 0.8931
FIN_GIDER = {2024: 3177.7, 2025: 4280.3}   # TCMB Sektör Bilançoları [VERİ] (analiz_adim12/finansman/RAPOR.md)
GSYH_2026 = 84425.0          # gsyh_pay.csv [VARSAYIM yolu, repo]
LAMBDA_CAPA = [0.9151, 0.913, 0.9068, 0.8992, 0.8931]  # rev_adim2_sonuc.json stok_tek_tur


def evds_seri(kod, bas="01-01-2023", son="25-10-2026", agg="avg"):
    p = HAM / f"{kod}.json"
    if not p.exists():
        u = f"{EVDS}/series={kod}&startDate={bas}&endDate={son}&type=json&frequency=5&aggregationTypes={agg}"
        r = urllib.request.Request(u, headers={"key": os.environ["EVDS_API_KEY"]})
        p.write_bytes(urllib.request.urlopen(r, timeout=60).read())
    d = json.loads(p.read_text(encoding="utf-8-sig"))
    col = kod.replace(".", "_")
    out = {}
    for it in d["items"]:
        if it.get(col) not in (None, ""):
            y, m = str(it["Tarih"]).split("-")[:2]
            out[f"{y}-{int(m):02d}"] = float(it[col])
    return out


def odemeyen():
    p = HAM / "odemeyen_payi_aylik.csv"
    if not p.exists():  # zarar-teorisi/odemeyen_gosterge.py ile aynı tanım: BDDK tablo 6 (EVDS), bin TL -> milyar TL
        kr = evds_seri("TP.HPBITABLO6.19", "01-06-2024", agg="last"); tk = evds_seri("TP.HPBITABLO6.55", "01-06-2024", agg="last")
        with p.open("w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f); w.writerow(["Donem", "ticari_ve_diger_kredi", "takip_ticari_diger", "firma_G1_%"])
            for a in sorted(set(kr) & set(tk)):
                k, t = kr[a] / 1e6, tk[a] / 1e6
                w.writerow([a, round(k, 3), round(t, 3), round(100 * t / (k + t), 3)])
    return {r["Donem"]: r for r in csv.DictReader((HAM / "odemeyen_payi_aylik.csv").open(encoding="utf-8-sig"))}


def kalibre():
    faiz = evds_seri("TP.KTF17")
    od = odemeyen()
    son_ay = max(faiz)
    r_son = faiz[son_ay]
    # θ: finansman gideri = θ × ort(ticari kredi stoku) × ort(faiz); 2024'te kur, 2025'te test
    def yil(y):
        ay = [a for a in od if a.startswith(str(y)) and a in faiz]
        st = np.mean([float(od[a]["ticari_ve_diger_kredi"]) for a in ay])
        fz = np.mean([faiz[a] for a in ay]) / 100
        return st, fz, len(ay)
    s24, f24, n24 = yil(2024); s25, f25, n25 = yil(2025)
    theta = FIN_GIDER[2024] / (s24 * f24)
    tahmin25 = theta * s25 * f25
    # G1 ~ faiz(t-6) ilişkisi (ilişki, nedensellik değil)
    aylar = sorted(a for a in od)
    xs, ys = [], []
    for a in aylar:
        y, m = map(int, a.split("-")); m -= 6
        while m <= 0: m += 12; y -= 1
        g = f"{y}-{m:02d}"
        if g in faiz:
            xs.append(faiz[g]); ys.append(float(od[a]["firma_G1_%"]))
    e, c = np.polyfit(xs, ys, 1)
    r2 = float(np.corrcoef(xs, ys)[0, 1] ** 2)
    son_od = aylar[-1]
    return {
        "faiz_son": {"ay": son_ay, "deger": r_son, "seri": "TP.KTF17", "etiket": "VERİ"},
        "faiz_hedef": {"model": 53.19, "evds": r_son, "fark_pp": round(53.19 - r_son, 2), "tol": 1.0, "tuttu": bool(abs(53.19 - r_son) <= 1.0)},
        "theta": {"deger": round(theta, 4), "n_ay_2024": n24, "etiket": "HESAP (2024'e kalibre)"},
        "geri_test_2025": {"gercek": FIN_GIDER[2025], "model": round(tahmin25, 1), "hata_yuzde": round(100 * (tahmin25 / FIN_GIDER[2025] - 1), 1),
                           "tol_yuzde": 15, "tuttu": bool(abs(tahmin25 / FIN_GIDER[2025] - 1) <= 0.15), "n_ay": n25},
        "lambda_capa": {"degerler": LAMBDA_CAPA, "aralik": [min(LAMBDA_CAPA), max(LAMBDA_CAPA)], "tol": 0.02,
                        "tuttu": bool(max(abs(x - LAMBDA) for x in LAMBDA_CAPA) <= 0.02)},
        "g1_iliski": {"egim_pp_per_faiz_pp": round(float(e), 4), "r2": round(r2, 3), "n": len(xs), "etiket": "TAHMİN (ilişki)", "kullanildi": bool(e > 0)},
        "g1_son": {"ay": son_od, "deger": float(od[son_od]["firma_G1_%"])},
        "ticari_kredi_son": {"ay": son_od, "milyar": float(od[son_od]["ticari_ve_diger_kredi"])},
    }


def rampa(ay, yari=6.0, egim=1.5):
    return 1 / (1 + np.exp(-(ay - yari) / egim))


def senaryo(k, adim2, kal, m=1.0, spread=SPREAD_MERKEZ, silme=SILME_A2, gecis=0.3, r=None):
    r = kal["faiz_son"]["deger"] if r is None else r
    kredi = kal["ticari_kredi_son"]["milyar"]
    ay = np.arange(1, 25)
    kt = k * rampa(ay)
    a1_stok = kt * m * FAIZLI_STOK_A1
    a1_faiz_ay = a1_stok * spread / 100 / 12
    olc = silme / SILME_A2
    a2_stok = kt * olc * SILINEN_A2 if adim2 else 0 * kt
    a2_kopru = kt * olc * KREDI_IHT_A2 if adim2 else 0 * kt
    a2_faiz_ay = a2_kopru * r / 100 / 12 if adim2 else 0 * kt
    y1, y2 = slice(0, 12), slice(12, 24)
    faiz_y = [float(a1_faiz_ay[y1].sum()), float(a1_faiz_ay[y2].sum())]
    kacinilan_y = [float(a2_faiz_ay[y1].sum()), float(a2_faiz_ay[y2].sum())]
    tam = faiz_y[1] * 12 / 12  # 2. yıl ≈ tam katılım
    efektif_pp = 100 * (faiz_y[1] + kacinilan_y[1]) / kredi
    e = kal["g1_iliski"]["egim_pp_per_faiz_pp"]
    dG1 = e * (-efektif_pp) if e > 0 else None  # işaret ters/anlamsızsa kanal kullanılmaz
    return {
        "k": k, "adim": "1+2" if adim2 else "1",
        "silinen_stok_A1": round(float(a1_stok[-1]), 1),
        "silinen_stok_A2": round(float(a2_stok[-1]), 1),
        "faiz_dusus_y1": round(faiz_y[0], 1), "faiz_dusus_y2": round(faiz_y[1], 1),
        "faiz_dusus_pct_2025": round(100 * faiz_y[1] / FIN_GIDER[2025], 1),
        "kacinilan_kopru_faizi_y2": round(kacinilan_y[1], 1),
        "likidite_ihtiyaci_kacinilan": round(float(a2_kopru[-1]), 1),
        "kredi_talebi_pct": round(-100 * float(a2_kopru[-1]) / kredi, 1),
        "ucret_kanali": round(float(kt[-1]) * olc * SERBEST_LIK_A2 * BETA if adim2 else 0.0, 1),
        "efektif_faiz_pp": round(efektif_pp, 2), "G1_degisim_pp": None if dG1 is None else round(dG1, 3),
        "tufe_ust_sinir_pp": round(100 * gecis * faiz_y[1] / GSYH_2026, 3),
    }


def monte_carlo(kal, k, adim2, n=5000, seed=1):
    g = np.random.default_rng(seed)
    m = g.triangular(0.25, 0.6, 1.0, n); sp = g.triangular(5, 9.89, 15, n)
    sl = g.triangular(0.40, 0.65, 0.885, n); gc = g.triangular(0, 0.3, 0.6, n)
    out = {"faiz_dusus_y2": [], "kacinilan_kopru_faizi_y2": [], "kredi_talebi_pct": [], "tufe_ust_sinir_pp": []}
    for i in range(n):
        s = senaryo(k, adim2, kal, m[i], sp[i], sl[i], gc[i])
        for key in out: out[key].append(s[key])
    return {key: [round(float(np.percentile(v, q)), 3) for q in (5, 50, 95)] for key, v in out.items()}


def grafik(kal):
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    ay = np.arange(1, 25); fig, ax = plt.subplots(1, 2, figsize=(11, 4))
    for k in (0.25, 0.5, 1.0):
        ax[0].plot(ay, k * rampa(ay) * FAIZLI_STOK_A1 * SPREAD_MERKEZ / 100, label=f"Adım1 k={k:.0%}")
    ax[0].set_title("Adım1 yıllıklandırılmış faiz düşüşü (mlr TL) [HESAP]"); ax[0].set_xlabel("ay"); ax[0].legend()
    labs, med, lo, hi = [], [], [], []
    for adim2 in (False, True):
        for k in (0.25, 0.5, 1.0):
            mc = monte_carlo(kal, k, adim2, n=1000)["faiz_dusus_y2"]
            labs.append(f"{'1+2' if adim2 else '1'}\n{k:.0%}"); lo.append(mc[1] - mc[0]); med.append(mc[1]); hi.append(mc[2] - mc[1])
    ax[1].bar(labs, med, yerr=[lo, hi], capsize=4); ax[1].set_title("2. yıl faiz düşüşü, MC P5–P50–P95 (mlr TL)")
    fig.tight_layout(); fig.savefig(K / "etki.png", dpi=120)


def main():
    HAM.mkdir(exist_ok=True)
    kal = kalibre()
    tab = [senaryo(k, a2, kal) for a2 in (False, True) for k in (0.25, 0.5, 1.0)]
    mc = {f"{s['adim']}_{s['k']}": monte_carlo(kal, s["k"], s["adim"] == "1+2") for s in tab}
    merkez_test = senaryo(1.0, False, kal)["faiz_dusus_y2"]
    sonuc = {"kalibrasyon": kal, "senaryolar": tab, "monte_carlo_P5_P50_P95": mc,
             "merkez_A1_tam_yillik": round(FAIZLI_STOK_A1 * SPREAD_MERKEZ / 100, 1), "y2_A1_k1": merkez_test}
    (K / "sim_sonuc.json").write_text(json.dumps(sonuc, ensure_ascii=False, indent=1), encoding="utf-8")
    with (K / "senaryolar.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(tab[0])); w.writeheader(); w.writerows(tab)
    grafik(kal)
    print(json.dumps(sonuc, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
