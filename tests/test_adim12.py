"""Adım 1 ve 2 sonuç dosyalarının tutarlılık testleri (kaynak: zarar-teorisi/test_rev.py, uyarlanmış)."""
import json
from pathlib import Path
K = Path(__file__).resolve().parents[1]
j = lambda a: json.loads((K / a).read_text(encoding="utf-8"))

def test_adim1_bant():
    z = j("adim1/rev_adim1_sonuc.json")["zaman_istikrari"]
    assert 0 < z["tam_graf_oran_min"] <= z["tam_graf_oran_2024"] <= z["tam_graf_oran_max"] < 1
    assert "yüzde 20" not in (K / "adim1/ADIM1_NACE.md").read_text(encoding="utf-8").split("## (e)")[1].split("kaldırıldı")[1]

def test_adim2_beta_tavan():
    r = j("adim2/rev_adim2_sonuc.json")
    assert abs(r["beta_tavan"] - 0.0439) < 1e-3 and r["beta_bandi"][1] < 0.3

def test_adim2_lambda():
    assert j("adim2/adim2_nace_ag_sonuc.json")
