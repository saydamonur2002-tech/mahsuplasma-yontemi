import pytest
from mahsuplasma import (BorcAgi, Firma, calistir, Parametreler, dongu_iptali,
                         optimal_mahsup, eisenberg_noe, sirali_odeme)
from mahsuplasma.senaryo import uc_firma_dongusu, turkiye_tipi


def _yakin(a, b, tol=0.05):
    return all(abs(a[k] - b[k]) < tol for k in a)


@pytest.mark.parametrize("tohum", [1, 7, 42])
def test_net_pozisyon_korunur(tohum):
    ag = turkiye_tipi(tohum=tohum)
    assert _yakin(ag.net_pozisyon(), optimal_mahsup(ag).net_pozisyon())
    assert _yakin(ag.net_pozisyon(), dongu_iptali(ag)[0].net_pozisyon())


@pytest.mark.parametrize("tohum", [1, 7, 42])
def test_optimal_dongu_iptalinden_kotu_degil(tohum):
    ag = turkiye_tipi(tohum=tohum)
    assert optimal_mahsup(ag).brut_borc() <= dongu_iptali(ag)[0].brut_borc() + 0.05
    assert optimal_mahsup(ag).brut_borc() <= ag.brut_borc()


def test_ucret_borclari_mahsuba_girmez():
    ag = turkiye_tipi()
    once = sum(b.tutar for b in ag.borclar if b.ucret)
    sonra = sum(b.tutar for b in optimal_mahsup(ag).borclar if b.ucret)
    assert abs(once - sonra) < 1e-6


def test_uc_firma_dongusu_tamamen_silinir():
    ag = uc_firma_dongusu()
    assert optimal_mahsup(ag).brut_borc() == 0
    # mahsupsuz sıralı ödemede herkes kilitli
    assert len(sirali_odeme(ag)["temerrut"]) == 3
    # ama tam koordinasyonda kimse batık değil
    assert eisenberg_noe(ag)["batik"] == []


def test_gercek_batik_tespit_edilir():
    ag = BorcAgi()
    ag.firma_ekle(Firma("A", "araci", nakit=0))
    ag.firma_ekle(Firma("B", "araci", nakit=0))
    ag.borc_ekle("A", "B", 100)          # A'nın hiç geliri yok
    s = calistir(ag)
    assert s["teshis"]["batik"] == ["A"]
    assert abs(s["teshis"]["gercek_zarar"] - 100) < 1e-6


def test_mekanizma_temerrudu_azaltir():
    s = calistir(turkiye_tipi())
    a = s["asamalar"]
    assert a["4_sart_kaldiraci"]["temerrut_sayisi"] <= a["1_brut"]["temerrut_sayisi"]
    assert a["4_sart_kaldiraci"]["kredi_ihtiyaci"] <= a["1_brut"]["kredi_ihtiyaci"]


def test_siralama_onemli():
    sonra = calistir(turkiye_tipi(), Parametreler(asgari_ucret_artisi=0.25, asgari_ucret_once_mi=False))
    once = calistir(turkiye_tipi(), Parametreler(asgari_ucret_artisi=0.25, asgari_ucret_once_mi=True))
    k = "4_sart_kaldiraci"
    assert once["asamalar"][k]["ucret_temerrut_sayisi"] >= sonra["asamalar"][k]["ucret_temerrut_sayisi"]


def test_ithal_girdi_doviz_talebi_degismez():
    d = calistir(turkiye_tipi())["doviz"]
    assert d["once"]["ithal_girdi"] == d["sonra"]["ithal_girdi"]
