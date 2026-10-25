import csv,matplotlib;matplotlib.use('Agg');import matplotlib.pyplot as plt
S=7463.7;T=14602.3/.885;F=dict(G=(4280.27,5508.99),K=(1397.07,2092.42),B=(2836.4,3345.98))
def run(m=1,s=.885,k=1397.07/4280.27,sp=.0989):
  n=S*m*sp;c=T*s
  r=lambda g,d:round(100*(F[g][0]-d)/F[g][1],1)
  return dict(net_faiz=round(n,1),serbest_nakit=round(208.4*s/.885,1),borc_stoku=round(S*m,1),ticari_borc=round(c,1),kopru=round(8328.6*s/.885,1),fin_efk_genel=r('G',n),fin_efk_KOBI=r('K',n*k),fin_efk_buyuk=r('B',n*(1-k)))
P={'mahsup':(.25,.5,1),'silme':(.40,.65,.885),'KOBI_payi':(.25,1397.07/4280.27,.40),'spread':(.05,.0989,.15)}
pm={'mahsup':'m','silme':'s','KOBI_payi':'k','spread':'sp'}
rows=[];base=run()
w=csv.writer(open('hassasiyet.csv','w'));w.writerow(['varsayim','seviye','deger']+list(base))
for p,v in P.items():
  for l,x in zip(['dusuk','orta','yuksek'],v):
    o=run(**{pm[p]:x});w.writerow([p,l,round(x,4)]+list(o.values()));rows.append((p,l,o))
print(base);[print(r) for r in rows]
# tornado on net faiz & KOBI oran
fig,ax=plt.subplots(1,2,figsize=(11,4))
for a,key in zip(ax,['net_faiz','fin_efk_KOBI']):
  sw=[(p,[o[key] for q,l,o in rows if q==p]) for p in P];sw.sort(key=lambda t:abs(t[1][2]-t[1][0]))
  for i,(p,v) in enumerate(sw):a.barh(i,max(v[0],v[2])-min(v[0],v[2]),left=min(v[0],v[2]))
  a.set_yticks(range(4));a.set_yticklabels([p for p,_ in sw]);a.axvline(base[key],c='k');a.set_title(key+' (merkez %s)'%base[key])
plt.tight_layout();plt.savefig('tornado.png',dpi=120)
