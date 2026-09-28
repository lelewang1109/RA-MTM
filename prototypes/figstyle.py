"""Print-size figure style for the VGTC paper: figures are drawn at their printed width (full text width 7.0 in,
column 3.4 in) so that every text element is 6.5-8 pt after placement."""
import matplotlib as mpl

TEXT_W, COL_W = 7.0, 3.4


def apply():
    mpl.rcParams.update({'font.size': 7, 'axes.titlesize': 7.5, 'axes.labelsize': 7, 'xtick.labelsize': 6.5,
                         'ytick.labelsize': 6.5, 'legend.fontsize': 6.5, 'lines.linewidth': .9, 'axes.linewidth': .6,
                         'xtick.major.width': .6, 'ytick.major.width': .6, 'xtick.major.size': 2.5, 'ytick.major.size': 2.5,
                         'pdf.fonttype': 42, 'savefig.dpi': 300})
