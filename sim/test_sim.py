import json, math
from pathlib import Path
import mahsup_sim as ms
K = Path(__file__).resolve().parent
kal = ms.kalibre()

def test_merkez_738():
    assert abs(ms.FAIZLI_STOK_A1 * ms.SPREAD_MERKEZ / 100 - 738.2) < 0.5
    assert abs(ms.senaryo(1.0, False, kal)["faiz_dusus_y2"] / 738.2 - 1) < 0.01  # 2. yıl rampa ≈ tam

def test_mc_kapsar():
    for a2 in (False, True):
        for k in (0.25, 0.5, 1.0):
            mc = ms.monte_carlo(kal, k, a2, n=500)
            for v in mc.values():
                assert v[0] <= v[1] <= v[2] and all(math.isfinite(x) for x in v)

def test_sonlu_ve_monoton():
    t = [ms.senaryo(k, True, kal) for k in (0.25, 0.5, 1.0)]
    assert t[0]["faiz_dusus_y2"] < t[1]["faiz_dusus_y2"] < t[2]["faiz_dusus_y2"]
    assert abs(t[2]["silinen_stok_A2"] - 14602.3) < 1

def test_geri_test_dolu():
    for k in ("faiz_hedef", "geri_test_2025", "lambda_capa", "g1_iliski"):
        assert "tuttu" in kal[k] or "kullanildi" in kal[k]
