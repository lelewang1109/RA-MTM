"""Publication figures from saved evidence; PNG + vector SVG/PDF."""
from pathlib import Path
import csv,json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch,Rectangle
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'results/dual_reference';FIG=OUT/'figures'
COLORS=['#1476ad','#de7f26','#9b57a1','#29957d']
MC=['#687888','#dc852b','#6761a8','#00876c']
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.titlesize':10,
    'axes.spines.top':False,'axes.spines.right':False,'svg.fonttype':'none','pdf.fonttype':42,
    'savefig.facecolor':'white'})

def save(fig,name):
    for suffix in ['png','svg','pdf']:fig.savefig(FIG/(name+'.'+suffix),dpi=300,bbox_inches='tight')
    plt.close(fig)

def data(n):return np.load(OUT/'arrays'/(n+'.npz'))

def view(ax,d,k):
    key='Dual-'+('X' if k==0 else 'Y');x=d[key+'_x'];z=d[key+'_z'];w=d[key+'_w'];t=np.arange(len(x))
    ax.imshow(d[key+'_scalar_map'],origin='lower',aspect='auto',extent=[-.5,len(t)-.5,0,120],cmap='Greys',vmin=0,vmax=1,alpha=.35,interpolation='nearest')
    for i in range(x.shape[1]):
        ax.fill_between(t,z[:,i]-w[:,i]/2,z[:,i]+w[:,i]/2,color=COLORS[i],alpha=.15)
        ax.plot(t,x[:,i],color=COLORS[i],lw=1.4,label=chr(65+i))
        ax.plot(t,d['centers'][:,i,k],color=COLORS[i],ls='--',lw=.8)
    ax.set(xlim=(-.5,len(t)-.5),ylim=(0,120),xlabel='Time step',ylabel=('X' if k==0 else 'Y')+' reference coordinate')
    ax.set_yticks([0,30,60,90,120]);ax.grid(alpha=.12)

def field(ax,d):
    ax.imshow(d['values'][0],origin='lower',extent=[0,120,0,120],cmap='Greys',vmin=0,vmax=1,alpha=.75)
    for i in range(d['centers'].shape[1]):
        c=d['centers'][:,i];ax.plot(c[:,0],c[:,1],color=COLORS[i],lw=1.2)
        ax.scatter(*c[0],s=25,color=COLORS[i]);ax.annotate(chr(65+i),c[0],xytext=(4,5),textcoords='offset points',color=COLORS[i])
        if np.linalg.norm(c[-1]-c[0])>1:ax.annotate('',c[-1],c[0],arrowprops=dict(arrowstyle='->',color=COLORS[i],lw=1.4))
    ax.set(xlim=(0,120),ylim=(0,120),xlabel='World x',ylabel='World y');ax.set_xticks([0,60,120]);ax.set_yticks([0,60,120])

# Figure 1: forked pipeline, equal-size aligned X/Y maps.
fig=plt.figure(figsize=(14,6.5),layout='constrained')
gs=fig.add_gridspec(2,5,width_ratios=[1.05,1.25,1.25,2.1,1.3])
d=data('diagonal');ax=fig.add_subplot(gs[0,0]);field(ax,d);ax.set_title('2-D scalar field')
ax=fig.add_subplot(gs[1,0]);ax.axis('off')
coords={0:(.15,.9),1:(.5,.9),2:(.85,.9),'ab':(.325,.48),'root':(.6,.12)}
for a,b in [(0,'ab'),(1,'ab'),('ab','root'),(2,'root')]:ax.plot([coords[a][0],coords[b][0]],[coords[a][1],coords[b][1]],color='#556170')
for i in range(3):ax.scatter(*coords[i],s=45,color=COLORS[i]);ax.text(coords[i][0],1.02,chr(65+i),ha='center')
ax.set(xlim=(0,1),ylim=(0,1.2));ax.set_title('Augmented merge tree\n(schematic hierarchy)')
ax=fig.add_subplot(gs[:,1]);ax.axis('off')
ax.text(.5,.55,'Leaf supports\n\n$C_i=(C_i^x,C_i^y)$\n$A_i$\n\nShared identity\nand hierarchy',ha='center',va='center',linespacing=1.6,
 bbox=dict(boxstyle='round,pad=.5',fc='#f1f5f7',ec='#bac7ce'),fontsize=11)
for k in range(2):
 ax=fig.add_subplot(gs[k,2]);ax.axis('off');symbol='xy'[k]
 ax.text(.5,.76,'Fixed '+symbol.upper()+' projection\n$q_i^'+symbol+'=a_'+symbol+'^T C_i$',ha='center',va='center',linespacing=1.6,fontsize=11)
 ax.annotate('',(.5,.54),(.5,.64),arrowprops=dict(arrowstyle='->',color='#536777',lw=1.5))
 ax.text(.5,.30,'Hierarchy-constrained RA\n$w_i=cA_i$\n$|x_i-q_i|\\leq\\tau^*+\\Delta$\n2-D geometry +\nmotion residual',ha='center',va='center',linespacing=1.5,
  bbox=dict(boxstyle='round,pad=.4',fc='#f1f5f7',ec='#bac7ce'),fontsize=9)
 ax=fig.add_subplot(gs[k,3]);view(ax,d,k);ax.set_title(('X' if k==0 else 'Y')+'-reference RA-MTM')
ax=fig.add_subplot(gs[0,4]);c=d['centers'];p=d['dual_positions']
for i in range(c.shape[1]):
 ax.plot(c[:,i,0],c[:,i,1],'--',color=COLORS[i]);ax.plot(p[:,i,0],p[:,i,1],color=COLORS[i]);ax.scatter(*p[-1,i],color=COLORS[i],s=20)
ax.set(xlim=(0,120),ylim=(0,120),xlabel='Reconstructed x',ylabel='Reconstructed y',title='Feature-level 2-D position');ax.set_aspect('equal')
ax=fig.add_subplot(gs[1,4]);ax.axis('off');ax.text(.5,.5,'$\\hat C_i=(x_i^X,x_i^Y)$\n\nMatched identity\nacross both views\n\n2-D motion from\nposition differences\n\nNo full scalar-field inverse',ha='center',va='center',linespacing=1.5)
fig.suptitle('Dual-Reference RA-MTM: two complementary views, one feature identity',fontsize=15)
save(fig,'figure1_method')

# Figure 2: exact mathematical counterexample, no sampling ambiguity.
c=np.array([[25.,25.],[55.,40.],[75.,75.]]);v=np.array([15.,20.]);dist=np.linalg.norm(c[:,None]-c[None,:],axis=-1)
fig,axs=plt.subplots(1,3,figsize=(11.5,3.7),layout='constrained')
ax=axs[0]
for i in range(3):
    ax.scatter(*c[i],facecolor='white',edgecolor=COLORS[i],s=50);ax.scatter(*(c[i]+v),color=COLORS[i],s=50)
    ax.annotate('',c[i]+v,c[i],arrowprops=dict(arrowstyle='->',color=COLORS[i]));ax.text(*(c[i]+[-4,-7]),chr(65+i),color=COLORS[i])
ax.set(xlim=(0,110),ylim=(0,110),xlabel='World x',ylabel='World y',title='(a) Common translation $v=(15,20)$');ax.set_aspect('equal')
ax=axs[1];im=ax.imshow(dist,cmap='Blues',vmin=0,vmax=80)
for i in range(3):
 for j in range(3):ax.text(j,i,f'{dist[i,j]:.1f}',ha='center',va='center',color='white' if dist[i,j]>50 else '#24384b')
ax.set(xticks=range(3),yticks=range(3),xticklabels=list('ABC'),yticklabels=list('ABC'),title='(b) ST-MTM distance input unchanged')
ax.set_xlabel('$D(C+v)=D(C)$\nDistances alone cannot identify translation')
ax=axs[2]
for i in range(3):
 ax.plot([0,1],[c[i,0],c[i,0]+v[0]],color=COLORS[i],label=chr(65+i)+' / X')
 ax.plot([0,1],[c[i,1],c[i,1]+v[1]],color=COLORS[i],ls='--')
ax.set(xticks=[0,1],xticklabels=['Before','After'],ylim=(0,110),ylabel='Fixed reference coordinate',title='(c) Dual reference changes on both axes')
ax.text(.05,.94,'Solid: $q_x$ (+15)\nDashed: $q_y$ (+20)',transform=ax.transAxes,va='top',fontsize=9)
fig.suptitle('Relative distances are translation-invariant; fixed references retain the missing signal',fontsize=13)
save(fig,'figure2_translation_invariance')

for names,number,title in [(['pure_x','pure_y','diagonal'],3,'Translation components in complementary time maps'),(['same_x','same_y'],4,'Projection crowding reveals complementarity and unavoidable interval conflict')]:
 fig,axs=plt.subplots(3,len(names),figsize=(4*len(names),8.1),layout='constrained',gridspec_kw={'height_ratios':[1.1,1,1]})
 for j,name in enumerate(names):
    d=data(name);field(axs[0,j],d);axs[0,j].set_title(name.replace('_',' ').title())
    view(axs[1,j],d,0);view(axs[2,j],d,1)
    axs[1,j].legend(ncol=d['centers'].shape[1],fontsize=7,loc='upper left')
 fig.suptitle(title+'\nSolid: displayed anchor; dashed: centroid projection; tint: absolute-width interval',fontsize=12)
 save(fig,f'figure{number}_'+('translations' if number==3 else 'crowding'))

# Figure 5: actual extracted hierarchy, independent LP minima, visible budgets.
d=data('hierarchy_conflict');fig,axs=plt.subplots(1,3,figsize=(12,4),layout='constrained');field(axs[0],d)
h=json.loads((OUT/'records/hierarchy_conflict_input.json').read_text())['hierarchies'][0]
def hl(h):return chr(65+h) if isinstance(h,int) else '('+','.join(hl(x) for x in h)+')'
axs[0].set_title('(a) Extracted hierarchy '+hl(h))
for k,ax in enumerate(axs[1:]):
 key='Dual-'+('X' if k==0 else 'Y');q=d['centers'][0,:,k];x=d[key+'_x'][0];z=d[key+'_z'][0];w=d[key+'_w'][0]
 tau=d[key+'_tau'][0];budget=d[key+'_budget'][0]
 for i in range(len(q)):
    ax.plot([q[i]-budget,q[i]+budget],[i,i],color=COLORS[i],lw=7,alpha=.13)
    ax.add_patch(Rectangle((z[i]-w[i]/2,i-.15),w[i],.3,fc=COLORS[i],alpha=.35))
    ax.plot([q[i],x[i]],[i,i],color=COLORS[i],lw=1)
    ax.scatter(q[i],i,marker='x',color=COLORS[i],s=45);ax.scatter(x[i],i,marker='|',color=COLORS[i],s=100)
 ax.set(yticks=range(len(q)),yticklabels=list('ABCD'),xlim=(0,120),ylim=(-.6,len(q)-.4),xlabel='Fixed reference coordinate',title=f'({chr(98+k)}) {"XY"[k]}: $\\tau^*$={tau:.2f}, budget={budget:.2f}')
 ax.grid(axis='x',alpha=.15)
fig.suptitle('Hierarchy versus reference: crosses = target q; ticks = optimized anchor; pale bands = allowed budget',fontsize=12)
save(fig,'figure5_hierarchy_conflict')

rows=list(csv.DictReader((OUT/'tables/metrics.csv').open()));names=list(dict.fromkeys(r['scene'] for r in rows))
methods=['TMTM','ST-MTM','X-only RA-MTM','Dual-Reference RA-MTM']
for full in [False,True]:
 chosen=names if full else names[:14]
 fig,axs=plt.subplots(1,4,figsize=(13,10 if full else 6.8),sharey=True,layout='constrained')
 keys=['position_2d_nrmse','trajectory_2d_nmae','distance_x_nrmse','distance_y_nrmse']
 for ax,key,label in zip(axs,keys,['2-D position NRMSE','2-D trajectory NMAE','X-view distance NRMSE','Y-view distance NRMSE']):
    for j,m in enumerate(methods):
        rr=[next(r for r in rows if r['scene']==n and r['method']==m and r['readout']!='first_frame_2d_affine') for n in chosen]
        xx=[float(r[key]) if r[key] else np.nan for r in rr]
        ax.scatter(xx,np.arange(len(chosen))+(j-1.5)*.13,color=MC[j],s=16,label=m,marker=['o','s','^','D'][j])
    ax.set(xlabel=label,yticks=range(len(chosen)),yticklabels=[n.replace('_',' ') for n in chosen]);ax.grid(axis='x',alpha=.2)
 axs[0].invert_yaxis();axs[0].legend(loc='lower left',bbox_to_anchor=(0,1.01),fontsize=8)
 fig.suptitle('Formal comparison: all declared cases retained; lower is better\nSingle-view 2-D readout gets true initial Y held fixed; geometry columns evaluate original 2-D distances',fontsize=12)
 save(fig,'supplementary_all_sequences' if full else 'figure6_comparison')
print('Wrote six main figures and full-sequence supplement')
