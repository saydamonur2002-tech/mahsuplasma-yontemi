from model import run,P
def test_merkez():
    c=run(**P['merkez'])
    assert round(c['net_faiz'],1)==738.2
    assert round(c['oran_sonra_G'],1)==64.3 and round(c['oran_sonra_K'],1)==55.3 and round(c['oran_sonra_B'],1)==69.9
    assert round(c['ticari_borc'],0)==14602 and round(c['serbest_nakit'],1)==208.4
if __name__=='__main__':test_merkez();print('TEST OK')
