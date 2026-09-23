"""RA-MTM ERA5 plate: saved six-hour layouts, linked geographic snapshots.
The pressure offset is a fixed datum, not a climatological anomaly.
"""
from pathlib import Path
from datetime import datetime
import hashlib,json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.colors import Normalize, LinearSegmentedColormap
from scipy.interpolate import RegularGridInterpolator
from matplotlib.patches import FancyBboxPatch
from run_experiment import ROOT, extract, signature, b2

RAW=ROOT/'results/supplementary/era5/six_hour'
OUT=ROOT/'results/main/figures'
NAME='era5_ramtm_paper'
DATUM=1013.25

def main():
    sc=extract(step=6)
    record=json.loads((RAW/'RA-MTM_records.json').read_text())['details']
    length=record['raster_attempts'][-1]['length']
    maps=[]
    for t,(fr,d) in enumerate(zip(sc['frames'],record['discrete'])):
        sk=b2.DiscreteSkeleton(tuple(d['ordering']),np.asarray(d['anchors']),np.asarray(d['starts']),np.asarray(d['ends']))
        values=b2.fill_frame(fr,sk,length)
        assert signature(values)==signature(sc['trees'][t])
        maps.append(values)
    values=np.column_stack(maps)
    dates=[datetime.fromisoformat(t) for t in sc['dates']];time=mdates.date2num(dates)
    requested=['1999-12-03 18:00:00','1999-12-17 18:00:00','1999-12-26 12:00:00','1999-12-27 12:00:00']
    picks=[sc['dates'].index(d) for d in requested]
    conflict=int(np.argmax([r['tau'] for r in record['frames']]))
    picks=sorted(set(picks+[conflict]));assert len(picks)==5
    coast=json.loads((Path(__file__).parent/'assets/europe_coastline.json').read_text())
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'svg.fonttype':'none','pdf.fonttype':42,'axes.linewidth':.9})
    fig=plt.figure(figsize=(18,9),facecolor='white')
    ax=fig.add_axes([.065,.375,.92,.565])
    # Requested paper-style fixed range. Out-of-range values use endpoint
    # colors; the colorbar extensions and provenance disclose saturation.
    bound=35.
    norm=Normalize(-bound,bound)
    ramp=np.linspace(0,1,1024);colors=plt.get_cmap('RdBu_r')(.08+.84*ramp)
    white=.22*(1-abs(2*ramp-1))**.7
    colors[:,:3]=colors[:,:3]*(1-white[:,None])+white[:,None]
    cmap=LinearSegmentedColormap.from_list('pressure_soft',colors)
    dt=(time[1]-time[0])/2
    # Display interpolation only; original six-hour layouts and widths remain
    # untouched. Interpolated colors are not additional observations or metrics.
    ax.imshow(values-DATUM,origin='lower',aspect='auto',cmap=cmap,norm=norm,interpolation='bilinear',interpolation_stage='data',
              extent=[time[0]-dt,time[-1]+dt,0,120],rasterized=True)
    ax.set_ylim(0,120);ax.set_xlim(time[0]-dt,time[-1]+dt)
    for spine in ax.spines.values():spine.set_visible(True)
    ax.set_yticks([0,30,60,90,120]);ax.tick_params(axis='y',length=3,pad=4,labelsize=10)
    ax.set_ylabel(r'Fixed reference coordinate $\xi$',fontsize=13,labelpad=9)
    ax.xaxis.set_major_locator(mdates.WeekdayLocator(byweekday=mdates.MO,interval=2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d %b'))
    ax.xaxis.set_minor_locator(mdates.DayLocator(interval=2));ax.tick_params(axis='x',which='major',length=5,labelsize=10,pad=5)
    ax.tick_params(axis='x',which='minor',length=3)
    # Arrowed axes, preserving the explicit numeric reference scale.
    ax.annotate('',xy=(1,-.08),xytext=(0,-.08),xycoords='axes fraction',arrowprops=dict(arrowstyle='-|>',lw=.8,color='black'))
    ax.text(1,-.115,'Time (UTC)',transform=ax.transAxes,ha='right',va='top',fontsize=11)
    fig.text(.065,.973,'RA-MTM',fontsize=17,fontweight='bold',va='center')
    fig.text(.166,.973,'ERA5 mean sea level pressure  ·  17 Nov 1999 – 14 Jan 2000  ·  6-hour samples',fontsize=12,va='center',color='#333333')
    # Inset legend follows the supplied publication example.
    panel=FancyBboxPatch((.02,.775),.235,.195,transform=ax.transAxes,boxstyle='round,pad=.01,rounding_size=.016',
        facecolor='white',edgecolor='black',lw=.7,alpha=.93,zorder=7)
    ax.add_patch(panel)
    ax.text(.033,.928,r'MSLP $-$ 1013.25 hPa',transform=ax.transAxes,fontsize=12,va='center',zorder=9)
    ca=ax.inset_axes([.034,.838,.208,.031],zorder=9)
    cb=fig.colorbar(plt.cm.ScalarMappable(norm=norm,cmap=cmap),cax=ca,orientation='horizontal',extend='both')
    cb.set_ticks([-bound,0,bound]);cb.ax.tick_params(labelsize=10,length=3,pad=2)
    cb.outline.set_linewidth(.55)
    panels=[];selected=[]
    lon=np.linspace(-30,40,sc['protocol']['grid']+1)
    lat=np.rad2deg(np.arcsin(np.linspace(np.sin(np.deg2rad(30)),np.sin(np.deg2rad(75)),sc['protocol']['grid']+1)))
    for k,t in enumerate(picks):
        letter=chr(65+k)
        ax.axvline(time[t],color='#575757',lw=.8,ls=(0,(2,3)),alpha=.8,zorder=5)
        # A-D: lowest-pressure leaf; E: the leaf with largest reference residual.
        ids=sc['ids'][t];j=int(np.argmin(sc['frames'][t].values[ids]));leaf=ids[j]
        if t==conflict:
            j=int(np.argmax(abs(np.asarray(record['frames'][t]['x'])-np.asarray(record['frames'][t].get('reference',sc['centers'][t][:,0])))))
            leaf=ids[j]
        anchor=float(record['frames'][t]['x'][j]);yi,xi=divmod(leaf,sc['protocol']['grid'])
        longitude=float((lon[xi]+lon[xi+1])/2)
        latitude=float(np.rad2deg(np.arcsin((np.sin(np.deg2rad(lat[yi]))+np.sin(np.deg2rad(lat[yi+1])))/2)))
        a=fig.add_axes([.075+k*.184,.084,.165,.207]);panels.append(a)
        # Interpolate in the original equal-area grid, then display in lon/lat.
        # Clamp half-cell borders to avoid extrapolating new extrema.
        lonc=(lon[:-1]+lon[1:])/2
        sinc=(np.sin(np.deg2rad(lat[:-1]))+np.sin(np.deg2rad(lat[1:])))/2
        display_lon=np.linspace(-30,40,601);display_lat=np.linspace(30,75,401)
        xx,yy=np.meshgrid(display_lon,display_lat)
        points=np.c_[np.clip(np.sin(np.deg2rad(yy.ravel())),sinc[0],sinc[-1]),np.clip(xx.ravel(),lonc[0],lonc[-1])]
        raster=RegularGridInterpolator((sinc,lonc),sc['fields'][t]-DATUM)(points).reshape(401,601)
        a.imshow(raster,origin='lower',extent=[-30,40,30,75],aspect='auto',cmap=cmap,norm=norm,interpolation='bilinear',rasterized=True)
        for line in coast['lines']:
            pts=np.asarray(line);a.plot(pts[:,0],pts[:,1],color='#202020',lw=.42,alpha=.9,clip_on=True)
        a.set(xlim=(-30,40),ylim=(30,75),xticks=[],yticks=[])
        for spine in a.spines.values():spine.set_visible(True)
        a.text(.035,.945,letter,transform=a.transAxes,ha='left',va='top',fontsize=12,fontweight='bold',
            bbox=dict(boxstyle='circle,pad=.17',fc='white',ec='black',lw=.7,alpha=.94))
        a.set_xlabel(dates[t].strftime('%Y-%m-%d %H:%M'),fontsize=10.5,labelpad=7)
        # Orthogonal connectors keep adjacent late-December samples distinct.
        start=fig.transFigure.inverted().transform(ax.transData.transform((time[t],0)))
        end=(a.get_position().x0+a.get_position().width/2,a.get_position().y1)
        elbow=.316+k*.004
        fig.lines.append(plt.Line2D([start[0],start[0],end[0],end[0]],[start[1],elbow,elbow,end[1]],
            transform=fig.transFigure,color='#888888',lw=.65,zorder=0))
        selected.append(dict(panel=letter,t=t,date=sc['dates'][t],feature_index=j,leaf=leaf,anchor=anchor,leaf_longitude=longitude,leaf_latitude=latitude,tau=record['frames'][t]['tau']))
    def callout(text,target,xytext):
        ax.annotate(text,xy=target,xytext=xytext,textcoords='axes fraction',fontsize=11,ha='center',va='center',
            bbox=dict(boxstyle='round,pad=.38',fc='white',ec='black',lw=.7,alpha=.95),
            arrowprops=dict(arrowstyle='-|>',lw=.8,color='black',shrinkA=4,shrinkB=3),zorder=10)
    # Link panel letters to times, without emphasizing individual minima.
    for selected_frame in selected:
        ax.text(time[selected_frame['t']],5,selected_frame['panel'],ha='center',va='center',fontsize=10,
            bbox=dict(boxstyle='round,pad=.18',fc='white',ec='.45',lw=.5,alpha=.9),zorder=8)
    # Conflict is a frame-wise LP bound, not an identification of a cyclone.
    rr=record['frames'][conflict];j=int(np.argmax(abs(np.asarray(rr['x'])-np.asarray(rr.get('reference',sc['centers'][conflict][:,0])))))
    callout(r'E  Largest reference conflict'+'\n'+r'$\tau^* = '+f"{rr['tau']:.2f}"+'$',
        (time[conflict],rr['x'][j]),(.83,.84))
    fig.text(.065,.018,'Bilinear display interpolation; original 6-hour layouts and widths unchanged. Fixed pressure datum, not a climatological anomaly.',fontsize=9.5,color='#444444')
    OUT.mkdir(parents=True,exist_ok=True)
    for ext in ['png','svg']:fig.savefig(OUT/(NAME+'.'+ext),dpi=300,facecolor='white')
    plt.close(fig)
    provenance=dict(source_run='six_hour',frames=len(dates),raster_length=length,pressure_datum_hPa=DATUM,color_range_hPa=[-bound,bound],
        display_interpolation='bilinear scalar display interpolation only; not additional observations or certified intermediate layouts',
        colormap='RdBu_r sampled from 0.08 to 0.92, with a continuous 22-percent maximum white blend near the center',selected_panels=selected,
        minimum_markers=False,clipped_map_fraction=float(np.mean(abs(values-DATUM)>bound)),clipped_source_fraction=float(np.mean(abs(sc['fields']-DATUM)>bound)),
        selection='Four dates resembling the reference figure, plus the full-sequence maximum tau; all times are actual six-hour samples.',
        storm_identification='No named cyclone identities are asserted.',
        map_sha256=hashlib.sha256(values.tobytes()).hexdigest(),
        coastline_source=coast['source'],coastline_source_sha256=coast['source_sha256'],
        topology_checks=len(maps),script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    (ROOT/'results/supplementary/era5/paper_figure.json').write_text(json.dumps(provenance,indent=2))
    print('WROTE',OUT/(NAME+'.png'),flush=True)
if __name__=='__main__':main()
