"""Adım 1-2 firma etkisi modeli. Çalıştır: python model.py"""
import json,os,numpy as np
D=os.path.dirname(os.path.abspath(__file__));P=json.load(open(f'{D}/params.json'))
g=lambda k:P[k]['v']
def run(mahsup,spread,kredi_faizi,silme,kobi_payi):
    n=g('borc_stoku_adim1')*mahsup*spread; f=silme/0.885
    o=dict(net_faiz=n,serbest_nakit=g('serbest_nakit_taban')*f,kopru=g('kopru_taban')*f,
      kopru_faiz=g('kopru_taban')*f*kredi_faizi,borc_stoku=g('borc_stoku_adim1')*mahsup,
      ticari_borc=g('ticari_taban_adim2')*silme)
    F,E=g('fin_gider_2025'),g('efk_2025')
    for k,s in (('G',1),('K',kobi_payi),('B',1-kobi_payi)):
        o[f'oran_once_{k}']=100*F[k]/E[k]; o[f'oran_sonra_{k}']=100*(F[k]-n*s)/E[k]
    for k in ('net_faiz','borc_stoku','ticari_borc','serbest_nakit'):
        o[k+'_KOBI']=o[k]*kobi_payi; o[k+'_buyuk']=o[k]*(1-kobi_payi)
    return o
def mc():
    m=P['mc'];r=np.random.default_rng(m['seed']);N=m['n']
    z=r.multivariate_normal([0,0],[[1,m['korelasyon_mahsup_silme']],[m['korelasyon_mahsup_silme'],1]],N)
    from scipy.stats import norm;u=norm.cdf(z)
    def tri(sp,uu):
        _,a,c,b=sp;Fc=(c-a)/(b-a)
        return np.where(uu<Fc,a+np.sqrt(uu*(b-a)*(c-a)),b-np.sqrt((1-uu)*(b-a)*(b-c)))
    x=dict(mahsup=tri(m['mahsup'],u[:,0]),silme=tri(m['silme'],u[:,1]),
      spread=tri(m['spread'],r.random(N)),kredi_faizi=tri(m['kredi_faizi'],r.random(N)),
      kobi_payi=np.clip(r.normal(*m['kobi_payi'][1:],N),0.15,0.5))
    return run(**x)
if __name__=='__main__':
    import csv,matplotlib;matplotlib.use('Agg');import matplotlib.pyplot as plt
    c=run(**P['merkez']);s=mc();fx,gd=g('usd_tl'),g('gsyh')
    with open(f'{D}/sonuc.csv','w') as fh:
        w=csv.writer(fh);w.writerow(['kalem','merkez','P10','P50','P90','P50_mlrUSD','P50_GSYH%'])
        for k in c:
            p=np.percentile(s[k]*np.ones(P['mc']['n']),[10,50,90]);pct='oran' in k
            w.writerow([k,round(c[k],1)]+[round(v,1) for v in p]+(['',''] if pct else [round(p[1]/fx,1),round(100*p[1]/gd,2)]))
    print(open(f'{D}/sonuc.csv').read())
    ks=['net_faiz','serbest_nakit','borc_stoku','ticari_borc','oran_sonra_K','oran_sonra_B']
    fig,ax=plt.subplots(2,3,figsize=(12,6))
    for a,k in zip(ax.flat,ks):
        a.hist(s[k]*np.ones(P['mc']['n']),60);a.axvline(c[k],c='k');a.set_title(k)
        for q in np.percentile(s[k]*np.ones(P['mc']['n']),[10,50,90]):a.axvline(q,c='r',ls='--')
    fig.suptitle('Adım1-2 Monte Carlo (siyah=merkez, kırmızı=P10/P50/P90) mlr TL / %');plt.tight_layout();plt.savefig(f'{D}/model_mc.png',dpi=110)
