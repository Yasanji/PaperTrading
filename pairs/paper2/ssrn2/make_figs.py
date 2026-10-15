import pandas as pd, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
plt.rcParams.update({'font.family':'serif','font.size':9})
r=pd.read_csv('../fig2_rolling.csv',parse_dates=['end'])
f,a=plt.subplots(figsize=(6.2,2.9))
a.fill_between(r.end,r.lo,r.hi,color='#2a6fdb',alpha=.15,lw=0); a.plot(r.end,r.coef,color='#2a6fdb',lw=1.6,marker='o',ms=2.5)
a.axhline(0,color='#888',lw=.8); a.axhline(-0.321,color='#555',lw=.8,ls='--'); a.text(r.end.iloc[0],-0.50,'Registered window estimate, −0.32',fontsize=7.5,color='#444')
a.axvline(pd.Timestamp('2023-03-17'),color='#555',lw=.8,ls=':'); a.text(pd.Timestamp('2023-01-01'),0.55,'End of HMM sample',ha='right',fontsize=7.5,color='#444')
a.set_ylabel('Threshold coefficient'); a.spines[['top','right']].set_visible(False); f.tight_layout(); f.savefig('fig1.png',dpi=300)
l=pd.read_csv('../fig1_lp.csv'); f,a=plt.subplots(figsize=(6.2,2.9))
for s,c,n in (('thr','#2a6fdb','Threshold'),('calw4','#888888','Calendar × last week')):
    d=l[l.signal==s]; h=[0]+list(d.h); m=[0]+list(d.coef)
    a.fill_between(d.h,d.lo,d.hi,color=c,alpha=.15,lw=0); a.plot(h,m,color=c,lw=1.6,marker='o',ms=3,label=n)
a.axhline(0,color='#888',lw=.8); a.set_xlabel('Trading days after the signal'); a.set_ylabel('Cumulative coefficient'); a.legend(frameon=False,fontsize=8,loc='lower left'); a.set_xticks(range(11))
a.spines[['top','right']].set_visible(False); f.tight_layout(); f.savefig('fig2.png',dpi=300)
