#This script processes data outputs for the resilience indicator multihazard model for the Philippines. Developed by Brian Walsh.
#import IPython
from IPython import get_ipython, display
get_ipython().magic('reset -f')
get_ipython().magic('load_ext autoreload')
get_ipython().magic('autoreload 2')

#Import packages for data analysis
from lib_compute_resilience_and_risk import *
from replace_with_warning import *
from lib_country_dir import *
from lib_gather_data import *
from maps_lib import *

from scipy.stats import norm
#import matplotlib 
#matplotlib.rc('xtick', labelsize=10) 
#matplotlib.rc('ytick', labelsize=10) 

from pandas import isnull
import pandas as pd
import numpy as np
import os, time
import sys

#Aesthetics
import seaborn as sns
import brewer2mpl as brew
from matplotlib import colors
sns.set_style('darkgrid')
brew_pal = brew.get_map('Set1', 'qualitative', 8).mpl_colors
sns_pal = sns.color_palette('Set1', n_colors=8, desat=.5)

params = {'savefig.bbox': 'tight', #or 'standard'
          #'savefig.pad_inches': 0.1 
          'xtick.labelsize': 8,
          'ytick.labelsize': 8,
          'legend.fontsize': 9,
          'legend.facecolor': 'white',
          #'legend.linewidth': 2, 
          'legend.fancybox': True,
          'savefig.facecolor': 'white',   # figure facecolor when saving
          #'savefig.edgecolor': 'white'    # figure edgecolor when saving
          }
plt.rcParams.update(params)

font = {'family' : 'sans serif',
    'size'   : 10}
plt.rc('font', **font)

import warnings
warnings.filterwarnings('always',category=UserWarning)

if len(sys.argv) < 2:
    print('Need to list country.')
    assert(False)
else: myCountry = sys.argv[1]

model  = os.getcwd() #get current directory
output = model+'/../output_country/'+myCountry+'/'

economy = get_economic_unit(myCountry)
event_level = [economy, 'hazard', 'rp']
dem = get_demonym(myCountry)

svg_file = '../map_files/'+myCountry+'/BlankSimpleMap.svg'
if myCountry == 'PH' and economy == 'region':
    svg_file = '../map_files/'+myCountry+'/BlankSimpleMapRegional.svg'

#
drm_pov_sign = -1 # toggle subtraction or addition of dK to affected people's incomes

pov_line = get_poverty_line(myCountry,'Rural')
sub_line = get_subsistence_line(myCountry)

# Load output files
pol_str = ''#'_v95'#could be {'_v95'}

base_str = 'no'
pds_str = 'unif_poor'
if myCountry == 'FJ': pds_str = 'fiji_SPP'#'no'

#res_base = pd.read_csv(output+'results_tax_no_.csv', index_col=[economy,'hazard','rp'])
df = pd.read_csv(output+'results_tax_'+base_str+'_'+pol_str+'.csv', index_col=[economy,'hazard','rp'])
iah = pd.read_csv(output+'iah_tax_'+base_str+'_'+pol_str+'.csv', index_col=[economy,'hazard','rp'])
macro = pd.read_csv(output+'macro_tax_'+base_str+'_'+pol_str+'.csv', index_col=[economy,'hazard','rp'])

## get frac below natl avg
#print(iah.columns)
#prov_mean = iah.dw.mean(level=economy)
#prov_mean.columns = ['provincial_mean']
#prov_mean['natl_mean'] = iah.dw.mean()
#natl_mean = iah.dw.mean()
#prov_mean.columns = ['dw']

#(iah.loc[iah.dw > natl_mean,'weight'].sum(level=economy)/iah.weight.sum(level=economy)).to_csv('~/Desktop/my_dw.csv')

#print(prov_mean)
#prov_mean.to_csv('~/Desktop/my_dw.csv')

# These are equivalent
#df_prov = sum_with_rp(myCountry,macro[['dk_event']],['dk_event'],sum_provinces=False,national=False)
df_prov = df[['dKtot','dWtot_currency']]
df_prov['gdp'] = df[['pop','gdp_pc_prov']].prod(axis=1)
df_prov['gdp_hh'] = float(macro['avg_prod_k'].mean())*iah[['k','pcwgt']].prod(axis=1).sum(level=event_level)

# HACK
#df_prov.ix['Rotuma'].dWtot_currency = df_prov.ix['Rotuma'].dWtot_currency.clip(upper=df_prov.ix['Rotuma'].gdp.mean())

results_df = macro.reset_index().set_index([economy,'hazard'])
results_df = results_df.loc[results_df.rp==100,'dk_event'].sum(level='hazard')
results_df = results_df.rename(columns={'dk_event':'dk_event_100'})
results_df = pd.concat([results_df,df_prov.reset_index().set_index([economy,'hazard']).sum(level='hazard')['dKtot']],axis=1,join='inner')
results_df.columns = ['dk_event_100','AAL']
results_df.to_csv(output+'results_table_old.csv')

#print(iah.columns)
#print(iah[['dc_npv_post','hhwgt','hhsize_ae']].prod(axis=1).sum(level=['hazard','rp'])/iah[['hhwgt','hhsize_ae']].prod(axis=1).sum(level=['hazard','rp']))

df_prov['R_asst'] = round(100.*df_prov['dKtot']/df_prov['gdp'],2)
df_prov['R_welf'] = round(100.*df_prov['dWtot_currency']/df_prov['gdp'],2)
df_prov = df_prov.sum(level=economy)
df_prov['gdp'] = df[['pop','gdp_pc_prov']].prod(axis=1).mean(level=economy).copy()

print(df_prov)
print(df_prov[['dKtot','dWtot_currency','gdp','gdp_hh']].sum())
print('R_asset:',100.*df_prov['dKtot'].sum()/df_prov['gdp'].sum())
print('R_welf:',100.*df_prov['dWtot_currency'].sum()/df_prov['gdp'].sum())

print('R_asset per hazard: ',df['dKtot'].sum(level='hazard')/df[['pop','gdp_pc_prov']].prod(axis=1).mean(level=[economy,'hazard']).sum(level='hazard'))

# Map asset losses as fraction of natl GDP
print('\n',df_prov.dKtot/df_prov.gdp.sum())
print((df_prov.dKtot/df_prov.gdp.sum()).sum(),'\n')

print(svg_file)
make_map_from_svg(
    df_prov.dKtot/df_prov.gdp.sum(), 
    svg_file,
    outname=myCountry+'_asset_risk_over_natl_gdp',
    color_maper=plt.cm.get_cmap('Blues'),
    #svg_handle = 'reg',
    label='Annual asset risk [% of national GDP]',
    new_title='Annual asset risk [% of national GDP]',
    do_qualitative=False,
    res=2000)

res_pds = pd.read_csv(output+'results_tax_'+pds_str+'_'+pol_str+'.csv', index_col=[economy,'hazard','rp'])
iah_pds = pd.read_csv(output+'iah_tax_'+pds_str+'_'+pol_str+'.csv', index_col=[economy,'hazard','rp','hhid','helped_cat','affected_cat'])
iah = iah.reset_index().set_index([economy,'hazard','rp','hhid','helped_cat','affected_cat'])
print(output+'results_tax_'+pds_str+'_'+pol_str+'.csv')
print(output+'iah_tax_'+pds_str+'_'+pol_str+'.csv')

def format_delta_p(delta_p):
    delta_p_int = int(delta_p)
    delta_p = int(delta_p)

    if delta_p_int >= 1E6:
        delta_p = str(delta_p)[:-6]+','+str(delta_p)[-6:]
    if delta_p_int >= 1E3:         
        delta_p = str(delta_p)[:-3]+','+str(delta_p)[-3:]
    return(str(delta_p))
        
#cats = pd.read_csv(output+'cats_tax_no_.csv', index_col=[economy,'hazard','rp'])

# Transform dw:
wprime = df.wprime.mean()
print('\n\n Wprime = ',wprime,'\n\n')

iah['dw'] = iah['dw']/wprime
try: 
    iah['pds_dw'] = iah_pds['dw']/wprime
    iah['pds_nrh'] = iah_pds['help_fee']-iah_pds['help_received'] # Net received help
    iah['pds_help_fee'] = iah_pds['help_fee']
    iah['pds_help_received'] = iah_pds['help_received']

except: iah['pds_dw'] = None

iah = iah.reset_index()
iah['ratio'] = iah['dw']/iah['dc0']

for irp in get_all_rps(myCountry,iah)[2::4]:
    print('Running',irp)
    _iah = iah.loc[(iah.affected_cat=='a')&(iah.helped_cat=='helped')&(iah.hazard=='EQ')&(iah.rp==irp)].copy()

    #
    bin0 = float(_iah.loc[(_iah.dw<200000),['dw','pcwgt']].prod(axis=1).sum())/1.E6
    bin1 = float(_iah.loc[(_iah.dw>=200000)&(_iah.dw<400000),['dw','pcwgt']].prod(axis=1).sum())/1.E6
    bin2 = float(_iah.loc[(_iah.dw>=400000)&(_iah.dw<600000),['dw','pcwgt']].prod(axis=1).sum())/1.E6
    bin3 = float(_iah.loc[(_iah.dw>=600000)&(_iah.dw<800000),['dw','pcwgt']].prod(axis=1).sum())/1.E6
    bin4 = float(_iah.loc[(_iah.dw>=1000000),['dw','pcwgt']].prod(axis=1).sum())/1.E6
    tot_float = round((bin0 + bin1 + bin2 + bin3 + bin4),2)

    ax = _iah.plot.scatter('k','dw',c='welf_class',loglog=True)
    ax.annotate(str(round(100*bin0/tot_float,1))+'%',xy=(0.4E7,190000),xycoords='data',ha='left',va='top',fontsize=9,annotation_clip=False,weight='bold')
    ax.annotate(str(round(100*bin1/tot_float,1))+'%',xy=(0.4E7,390000),xycoords='data',ha='left',va='top',fontsize=9,annotation_clip=False,weight='bold')
    ax.annotate(str(round(100*bin2/tot_float,1))+'%',xy=(0.4E7,590000),xycoords='data',ha='left',va='top',fontsize=9,annotation_clip=False,weight='bold')
    ax.annotate(str(round(100*bin3/tot_float,1))+'%',xy=(0.4E7,790000),xycoords='data',ha='left',va='top',fontsize=9,annotation_clip=False,weight='bold')
    ax.annotate(str(round(100*bin4/tot_float,1))+'%',xy=(0.4E7,990000),xycoords='data',ha='left',va='top',fontsize=9,annotation_clip=False,weight='bold')
    ax.annotate(r'$\Delta W_{tot}$ = '+str(tot_float)+'M',xy=(0.4E7,1090000),xycoords='data',ha='left',va='top',fontsize=9,annotation_clip=False,weight='bold')
    ax.plot()
    fig = plt.gcf()
    
    fig.savefig('/Users/brian/Desktop/BANK/hh_resilience_model/check_plots/dw_eq_'+str(irp)+'.pdf',format='pdf')
    plt.clf()

    fig = plt.figure(figsize=(15,6))

    cmap = colors.ListedColormap(sns.color_palette('Greens').as_hex())
    ax = _iah.loc[(_iah.welf_class==1)].plot.hexbin('dk0','ratio',cmap=cmap,alpha=0.4,mincnt=1,yscale='log')
    
    cmap = colors.ListedColormap(sns.color_palette('Blues').as_hex())
    ax = _iah.loc[(_iah.welf_class==2)].plot.hexbin('dk0','ratio',ax=ax,cmap=cmap,alpha=0.4,mincnt=1,yscale='log')
    
    cmap = colors.ListedColormap(sns.color_palette('Reds').as_hex())
    ax = _iah.loc[(_iah.welf_class==3)].plot.hexbin('dk0','ratio',ax=ax,cmap=cmap,alpha=0.4,mincnt=1,yscale='log')

    fig = plt.gcf()
    im=fig.get_axes()        #this is a list of all images that have been plotted
    for iax in range(len(im))[1:]: im[iax].remove()
    
    plt.axes(ax)
    
    fig = plt.gcf()
    fig.set_size_inches(15, 6)
    
    plt.xlim(0,1E5)
    plt.subplots_adjust(right=0.90)
    
    plt.ticklabel_format(style='sci',axis='x', scilimits=(0,0))
    plt.tight_layout()
    plt.draw()
    fig.savefig('/Users/brian/Desktop/BANK/hh_resilience_model/check_plots/resil_all_'+str(irp)+'.pdf',format='pdf',bbox_inches='tight')
    plt.clf()

    ax = plt.gca()
    fig = ax.get_figure()
    fig.set_size_inches(6.5,5.5)
    _iah['t_reco'] = (np.log(1/0.05)/_iah['hh_reco_rate']).fillna(25).clip(upper=25)

    # define binning using entire dataset
    _h,_b = np.histogram(_iah.t_reco,bins=   50,weights=_iah.pcwgt/1.E6)

    heights2, bins2  = np.histogram(_iah.loc[(_iah.welf_class==2)&(_iah.c>pov_line)].t_reco,bins=_b,weights=_iah.loc[(_iah.welf_class==2)&(_iah.c>pov_line)].pcwgt/1.E6)
    heights1, bins1  = np.histogram(_iah.loc[(_iah.welf_class==1)].t_reco,bins=_b,weights=_iah.loc[(_iah.welf_class==1)].pcwgt/1.E6)
    heights3, bins3  = np.histogram(_iah.loc[(_iah.welf_class==3)&(_iah.c>sub_line)].t_reco,bins=_b,weights=_iah.loc[(_iah.welf_class==3)&(_iah.c>sub_line)].pcwgt/1.E6)
    heights2_pov, bins2_pov = np.histogram(_iah.loc[(_iah.welf_class==2)&(_iah.c<=pov_line)].t_reco,bins=_b,weights=_iah.loc[(_iah.welf_class==2)&(_iah.c<=pov_line)].pcwgt/1.E6)
    heights3_sub, bins3_sub = np.histogram(_iah.loc[(_iah.welf_class==3)&(_iah.c<=sub_line)].t_reco,bins=_b,weights=_iah.loc[(_iah.welf_class==3)&(_iah.c<=sub_line)].pcwgt/1.E6)
    #heights0, bins0 = np.histogram(_iah.loc[(_iah.welf_class==0)].t_reco,bins=_b,weights=_iah.loc[(_iah.welf_class==0)].pcwgt/1.E6)
    # ^ empty dataframe

    ax.bar(bins2[:-1],heights1,      width=(bins2[1]-bins2[0]), facecolor=q_colors[1],alpha=0.8,label='Above poverty (Case 1)')
    ax.bar(bins2[:-1],heights2_pov,  width=(bins2[1]-bins2[0]), facecolor=q_colors[0],alpha=0.8,bottom=heights1,label='Pushed into poverty (Case 2)')
    ax.bar(bins2[:-1],heights2,      width=(bins2[1]-bins2[0]), facecolor=q_colors[2],alpha=0.8,bottom=(heights1+heights2_pov),label='Already in poverty (Case 2)')
    ax.bar(bins2[:-1],heights3,      width=(bins2[1]-bins2[0]), facecolor=q_colors[3],alpha=0.8,bottom=(heights1+heights2_pov+heights2),label='Pushed into subsistence (Case 3)')
    ax.bar(bins2[:-1],heights3_sub, width=(bins2[1]-bins2[0]), facecolor=q_colors[4],alpha=0.8,bottom=(heights1+heights2_pov+heights2+heights3),label='Already in subsistence (Case 3)')
    
    plt.xlabel(r'Household reconstruction time ($\tau_h$)')
    plt.ylabel(r'Households ($\times 10^6$)')
    plt.ylim(0,1.0E1)
    leg = ax.legend(loc='best',labelspacing=0.75,ncol=1,fontsize=9,borderpad=0.75,fancybox=True,frameon=True,framealpha=0.9,title='Household status post-disaster')

    fig.savefig('/Users/brian/Desktop/Dropbox/Bank/unbreakable_writeup/Figures/reco_periods_'+str(irp)+'.pdf',format='pdf',bbox_inches='tight')
    plt.clf()

    fig, axes = plt.subplots(nrows=3, ncols=2,figsize=(8,12))

    _iah.loc[(_iah.welf_class==1)&(_iah.dk0<150000)&(_iah.ratio<250)].plot.hexbin('dk0','ratio',ax=axes[0,0])
    _iah.loc[(_iah.welf_class==2)&(_iah.dk0<150000)&(_iah.ratio<250)].plot.hexbin('dk0','ratio',ax=axes[1,0])
    _iah.loc[(_iah.welf_class==3)&(_iah.dk0<150000)&(_iah.ratio<250)].plot.hexbin('dk0','ratio',ax=axes[2,0])
    
    plt.tight_layout()
    fig.savefig('/Users/brian/Desktop/BANK/hh_resilience_model/check_plots/resil_'+str(irp)+'.pdf',format='pdf')
    plt.close('all')

iah['hhwgt'] = iah['hhwgt'].fillna(0)
iah['pcwgt'] = iah['pcwgt'].fillna(0)

# Convert all these hh variables to per cap
#iah['c']   = iah[['c','hhwgt']].prod(axis=1)/iah['weight']
#iah['k']   = iah[['k','hhwgt']].prod(axis=1)/iah['weight']
#iah['dk0'] = iah[['dk0','hhwgt']].prod(axis=1)/iah['weight']
#iah['dc']  = iah[['dc','hhwgt']].prod(axis=1)/iah['weight']
#iah['dc_npv_pre'] = iah[['dc_npv_pre','hhwgt']].prod(axis=1)/iah['weight']

#iah['dw'] = iah[['dw','hhwgt']].prod(axis=1)/iah['weight']
#iah['pds_dw'] = iah[['pds_dw','hhwgt']].prod(axis=1)/iah['weight']

#iah['pds_nrh'] = iah[['pds_nrh','hhwgt']].prod(axis=1)/iah['weight']
#iah['pds_help_fee'] = iah[['pds_help_fee','hhwgt']].prod(axis=1)/iah['weight']
#iah['pds_help_received'] = iah[['pds_help_received','hhwgt']].prod(axis=1)/iah['weight']

#cf_ppp = 17.889

q_labels = ['Poorest quintile','Q2','Q3','Q4','Wealthiest quintile']
q_colors = [sns_pal[0],sns_pal[1],sns_pal[2],sns_pal[3],sns_pal[5]]

# Look at single event:
if myCountry == 'PH':
    myHaz = [['NCR'],['EQ','TC'],[1,10,25,30,50,100,200,250,500,1000]]
elif myCountry == 'FJ':
    myHaz = [['Ba'],['TC'],[1,5,10,20,22,50,72,75,100,200,224,250,475,500,975,1000,2475]]
    #myHaz = [['Lau'],['earthquake','tsunami','typhoon'],[1,10,20,50,100,250,500,1000]]

iah = iah.reset_index()

# PH and SL hazards
allDis = ['EQ','TC']
upper_clip = 100000

if myCountry == 'FJ': 
    allDis = myHaz[1]
    upper_clip = 20000

for myDis in allDis:

    cut_rps = iah.loc[(iah.hazard == myDis)].set_index([economy,'hazard','rp']).fillna(0)
    if (cut_rps['pcwgt'].sum() == 0 or cut_rps.shape[0] == 0): continue

    cut_rps['c_initial'] = 0.    
    cut_rps['delta_c']   = 0.
    cut_rps.loc[cut_rps.pcwgt_ae != 0.,'c_initial'] = cut_rps.loc[cut_rps.pcwgt_ae != 0.,['c','hhsize']].prod(axis=1)/cut_rps.loc[(cut_rps.pcwgt_ae != 0.), 'hhsize_ae']

    # If our calculation of consumption has changed, we need to shift the poverty line by the same amount
    #print(cut_rps['pov_line'].mean())
    #if myCountry == 'FJ':
    #    cut_rps['pov_line'] *= cut_rps['c_initial']/cut_rps['pcinc_ae']
    #print(cut_rps['pov_line'].mean())
    #assert(False)

    cut_rps.loc[cut_rps.pcwgt_ae != 0.,'delta_c']   = (cut_rps.loc[(cut_rps.pcwgt_ae != 0.), ['dk0','pcwgt']].prod(axis=1)/cut_rps.loc[(cut_rps.pcwgt_ae != 0.),'pcwgt_ae'])*(df['avg_prod_k'].mean()+1/df['T_rebuild_K'].mean())

    cut_rps['c_final']   = (cut_rps['c_initial'] + drm_pov_sign*cut_rps['delta_c'])
    cut_rps['c_final_pds']   = (cut_rps['c_initial'] - cut_rps['delta_c'] - cut_rps['pds_nrh'])

    cut_rps['c_initial'] = cut_rps['c_initial']

    cut_rps['pre_dis_n_pov'] = 0
    cut_rps['pre_dis_n_sub'] = 0
    cut_rps.loc[(cut_rps.c_initial <= cut_rps.pov_line), 'pre_dis_n_pov'] = cut_rps.loc[(cut_rps.c_initial <= cut_rps.pov_line), 'pcwgt']
    if sub_line:
        cut_rps.loc[(cut_rps.c_initial <= sub_line), 'pre_dis_n_sub'] = cut_rps.loc[(cut_rps.c_initial <= sub_line), 'pcwgt']
    print('\n\nTotal pop:',cut_rps['pcwgt'].sum(level='rp').mean())
    print('Pop below pov line before disaster:',cut_rps['pre_dis_n_pov'].sum(level=['hazard','rp']).mean())
    print('Pop below sub line before disaster:',cut_rps['pre_dis_n_sub'].sum(level=['hazard','rp']).mean(),'\n')

    print('--> poor, below pov',cut_rps.loc[(cut_rps.ispoor == 1) & (cut_rps.c_initial <= cut_rps.pov_line), 'pcwgt'].sum(level=['hazard','rp']).mean())
    print('--> poor, above pov',cut_rps.loc[(cut_rps.ispoor == 1) & (cut_rps.c_initial > cut_rps.pov_line), 'pcwgt'].sum(level=['hazard','rp']).mean())
    print('--> rich, below pov',cut_rps.loc[(cut_rps.ispoor == 0) & (cut_rps.c_initial <= cut_rps.pov_line), 'pcwgt'].sum(level=['hazard','rp']).mean())
    print('--> rich, above pov',cut_rps.loc[(cut_rps.ispoor == 0) & (cut_rps.c_initial > cut_rps.pov_line), 'pcwgt'].sum(level=['hazard','rp']).mean())
        
    if sub_line:
        print('poor, below sub',cut_rps.loc[(cut_rps.ispoor == 1) & (cut_rps.c_initial <= sub_line), 'pcwgt'].sum(level=['hazard','rp']).mean())
        print('poor, above sub',cut_rps.loc[(cut_rps.ispoor == 1) & (cut_rps.c_initial > sub_line), 'pcwgt'].sum(level=['hazard','rp']).mean())
        print('rich, below sub',cut_rps.loc[(cut_rps.ispoor == 0) & (cut_rps.c_initial <= sub_line), 'pcwgt'].sum(level=['hazard','rp']).mean())
        print('rich, above sub',cut_rps.loc[(cut_rps.ispoor == 0) & (cut_rps.c_initial > sub_line), 'pcwgt'].sum(level=['hazard','rp']).mean())

    cut_rps['disaster_n_pov'] = 0
    cut_rps['disaster_pds_n_pov'] = 0
    cut_rps['disaster_n_sub'] = 0

    cut_rps.loc[(cut_rps.c_final <= cut_rps.pov_line) & (cut_rps.c_initial > cut_rps.pov_line), 'disaster_n_pov'] = cut_rps.loc[(cut_rps.c_final <= cut_rps.pov_line) & (cut_rps.c_initial > cut_rps.pov_line), 'pcwgt']
    cut_rps.loc[(cut_rps.c_final_pds <= cut_rps.pov_line) & (cut_rps.c_initial > cut_rps.pov_line), 'disaster_pds_n_pov'] = cut_rps.loc[(cut_rps.c_final_pds <= cut_rps.pov_line) & (cut_rps.c_initial > cut_rps.pov_line), 'pcwgt']

    print('Pop pushed below pov line by disaster:',cut_rps['disaster_n_pov'].sum(level=['hazard','rp']).mean())
    print('Pop pushed below pov line by disaster & after PDS:',cut_rps['disaster_pds_n_pov'].sum(level=['hazard','rp']).mean(),'\n')
    
    if sub_line:
        cut_rps.loc[(cut_rps.c_final <= sub_line) & (cut_rps.c_initial > sub_line), 'disaster_n_sub'] = cut_rps.loc[(cut_rps.c_final <= sub_line) & (cut_rps.c_initial > sub_line), 'pcwgt']

    n_pov = pd.DataFrame(cut_rps[['disaster_n_pov','disaster_n_sub']].sum(level=[economy,'rp']).reset_index(),
                         columns=[economy,'rp','disaster_n_pov','disaster_n_sub']).set_index([economy,'rp'])
    n_pov['disaster_n_pov_pct'] = (n_pov['disaster_n_pov']/cut_rps.pcwgt.sum(level=[economy,'rp']).reset_index().set_index([economy,'rp']).T).T
    n_pov['disaster_n_sub_pct'] = (n_pov['disaster_n_sub']/cut_rps.pcwgt.sum(level=[economy,'rp']).reset_index().set_index([economy,'rp']).T).T
    
    n_pov.disaster_n_pov/=100.
    n_pov.disaster_n_sub/=100.
    n_pov = n_pov.reset_index().set_index([economy,'rp'])

    n_pov = sum_with_rp(myCountry,n_pov[['disaster_n_pov','disaster_n_pov_pct','disaster_n_sub','disaster_n_sub_pct']],
                        ['disaster_n_pov','disaster_n_pov_pct','disaster_n_sub','disaster_n_sub_pct'],sum_provinces=False,economy=economy)
    my_n_pov = n_pov.copy()

    if myCountry == 'PH': my_n_pov = n_pov.copy()#.drop(['Batanes'],axis=0)

    make_map_from_svg(
        my_n_pov.disaster_n_pov, 
        svg_file,
        outname=myCountry+'_new_poverty_incidence_'+myDis+'_allRPs',
        color_maper=plt.cm.get_cmap('RdYlGn_r'), 
        label='Number of '+dem+' pushed into poverty each year by '+myDis+'s',
        new_title='Number of '+dem+' pushed into poverty each year by '+myDis+'s',
        do_qualitative=False,
        res=2000)
    
    make_map_from_svg(
        my_n_pov.disaster_n_pov_pct, 
        svg_file,
        outname=myCountry+'_new_poverty_incidence_pct_'+myDis+'_allRPs',
        color_maper=plt.cm.get_cmap('RdYlGn_r'), 
        label=dem+' pushed into poverty each year by '+myDis+'s [%]',
        new_title= dem+' pushed into poverty by '+myDis+'s [%]',
        do_qualitative=False,
        res=2000)
    
    if sub_line:
        make_map_from_svg(
            my_n_pov.disaster_n_sub, 
            svg_file,
            outname=myCountry+'_new_subsistence_incidence_'+myDis+'_allRPs',
            color_maper=plt.cm.get_cmap('RdYlGn_r'), 
            label='Number of '+dem+' pushed into subsistence each year by '+myDis+'s',
            new_title='Number of '+dem+' pushed into subsistence each year by '+myDis+'s',
            do_qualitative=False,
            res=800)
    
        make_map_from_svg(
            my_n_pov.disaster_n_sub_pct, 
            svg_file,
            outname=myCountry+'_new_subsistence_incidence_pct_'+myDis+'_allRPs',
            color_maper=plt.cm.get_cmap('RdYlGn_r'), 
            label= dem+' pushed into subsistence each year by '+myDis+'s [%]',
            new_title= dem+' pushed into subsistence by '+myDis+'s [%]',
            do_qualitative=False,
            res=800)
    
    myC_ylim = None
    for myRP in myHaz[2]:
        
        cutA = iah.loc[(iah.hazard == myDis) & (iah.rp == myRP)].set_index([economy,'hazard','rp']).fillna(0)
        #cutA = iah.loc[(iah.hazard == myDis) & (iah.rp == myRP) & (iah.helped_cat == 'helped')].set_index([economy,'hazard','rp']).fillna(0)
        if (cutA['pcwgt'].sum() == 0 or cutA.shape[0] == 0): continue

        # look at instantaneous dk
        ax=plt.gca()

        cutA['c_initial'] = 0.
        cutA['delta_c']   = 0.
        cutA.loc[cutA.pcwgt_ae != 0,'c_initial'] = cutA.loc[cutA.pcwgt_ae != 0,['c','pcwgt']].prod(axis=1)/cutA.loc[cutA.pcwgt_ae != 0.,'pcwgt_ae']

        # If our calculation of consumption has changed, we need to shift the poverty line by the same amount
        #cutA['pov_line'] *= cutA['c_initial']/cutA['pcinc_ae']

        cutA.loc[cutA.pcwgt_ae != 0,'delta_c']   = (cutA.loc[cutA.pcwgt_ae != 0,['dk0','pcwgt']].prod(axis=1)/cutA.loc[cutA.pcwgt_ae != 0.,'pcwgt_ae'])*(df['avg_prod_k'].mean()+1/df['T_rebuild_K'].mean())
        cutA['c_final']   = (cutA['c_initial'] + drm_pov_sign*cutA['delta_c'])
        cutA['c_initial'] = cutA['c_initial']

        cutA['disaster_n_pov'] = 0
        cutA['disaster_n_sub'] = 0
        cutA.loc[(cutA.c_final <= cutA.pov_line) & (cutA.c_initial > cutA.pov_line), 'disaster_n_pov'] = cutA.loc[(cutA.c_final <= cutA.pov_line) & (cutA.c_initial > cutA.pov_line), 'pcwgt']
        if sub_line:
            cutA.loc[(cutA.c_final <= sub_line) & (cutA.c_initial > sub_line), 'disaster_n_sub'] = cutA.loc[(cutA.c_final <= sub_line) & (cutA.c_initial > sub_line), 'pcwgt']

        disaster_n_pov = pd.DataFrame(cutA[['disaster_n_pov','disaster_n_sub']].sum(level=event_level).reset_index(),columns=[economy,'disaster_n_pov','disaster_n_sub']).set_index(economy)
        disaster_n_pov['disaster_n_pov_pct'] = (disaster_n_pov['disaster_n_pov']/cutA.pcwgt.sum(level=economy).reset_index().set_index(economy).T).T
        disaster_n_pov['disaster_n_sub_pct'] = (disaster_n_pov['disaster_n_sub']/cutA.pcwgt.sum(level=economy).reset_index().set_index(economy).T).T

        disaster_n_pov.disaster_n_pov/=100.
        disaster_n_pov.disaster_n_sub/=100.
        disaster_n_pov = disaster_n_pov.reset_index().set_index(economy)

        sf = 1.
        if myCountry == 'FJ': sf = 2.321208
        ci_heights, ci_bins = np.histogram((cutA['c_initial']/sf).clip(upper=upper_clip), bins=50, weights=cutA['pcwgt'])
        cf_heights, cf_bins = np.histogram((cutA['c_final']/sf).clip(upper=upper_clip), bins=ci_bins, weights=cutA['pcwgt'])

        ci_heights /= get_pop_scale_fac(myCountry)[0]
        cf_heights /= get_pop_scale_fac(myCountry)[0]

        if myDis == 'TC' and str(myRP) == '100':
            np.savetxt('/Users/brian/Desktop/to_send/income_dist_pre_'+myDis+'_'+str(myRP)+'.csv',[ci_heights],delimiter=',')
            np.savetxt('/Users/brian/Desktop/to_send/income_dist_post_'+myDis+'_'+str(myRP)+'.csv',[cf_heights],delimiter=',')
            np.savetxt('/Users/brian/Desktop/to_send/income_dist_bins_'+myDis+'_'+str(myRP)+'.csv',[cf_bins],delimiter=',')

        ax.bar(ci_bins[:-1], ci_heights, width=(ci_bins[1]-ci_bins[0]), label='Initial', facecolor=q_colors[1],alpha=0.4)
        ax.bar(cf_bins[:-1], cf_heights, width=(ci_bins[1]-ci_bins[0]), label='Post-disaster', facecolor=q_colors[0],alpha=0.4)

        # Change in poverty incidence
        delta_p = cutA.loc[(cutA.c_initial > cutA.pov_line) & (cutA.c_final <= cutA.pov_line),'pcwgt'].sum()
        p_str = format_delta_p(delta_p)
        p_pct = ' ('+str(round((delta_p/cutA['pcwgt'].sum())*100.,2))+'% of population)'

        plt.plot([pov_line,pov_line],[0,1.25*cf_heights[:-2].max()],'k-',lw=1.5,color='black',zorder=100,alpha=0.85)
        ax.annotate('Poverty line',xy=(1.1*pov_line,1.25*cf_heights[:-2].max()),xycoords='data',ha='left',va='top',fontsize=9,annotation_clip=False,weight='bold')
        ax.annotate(r'$\Delta$N$_p$ = +'+p_str+p_pct,xy=(1.1*pov_line,1.15*cf_heights[:-2].max()),xycoords='data',ha='left',va='top',fontsize=9,annotation_clip=False)

        # Change in subsistence incidence
        if sub_line:
            delta_s = cutA.loc[(cutA.c_initial > sub_line) & (cutA.c_final <= sub_line),'pcwgt'].sum()
            s_str = format_delta_p(delta_s)
            s_pct = ' ('+str(round((delta_s/cutA['pcwgt'].sum())*100.,2))+'% of population)'

            plt.plot([sub_line,sub_line],[0,1.6*cf_heights[:-2].max()],'k-',lw=1.5,color='black',zorder=100,alpha=0.85)
            ax.annotate('Subsistence line',xy=(1.1*sub_line,1.60*cf_heights[:-2].max()),xycoords='data',ha='left',va='top',fontsize=9,annotation_clip=False,weight='bold')
            ax.annotate(r'$\Delta$N$_s$ = +'+s_str+s_pct,xy=(sub_line*1.1,1.5*cf_heights[:-2].max()),xycoords='data',ha='left',va='top',fontsize=9,annotation_clip=False)
        
        fig = ax.get_figure()
        plt.title(str(myRP)+'-Year '+myDis[:1].upper()+myDis[1:]+' Event')

        if myC_ylim == None: myC_ylim = ax.get_ylim()
        plt.ylim(myC_ylim[0],myC_ylim[1])

        plt.xlabel(r'Income ('+get_currency(myCountry)[0]+' yr$^{-1}$)')
        plt.ylabel('Population'+get_pop_scale_fac(myCountry)[1])
        plt.legend(loc='best')
        print('poverty_k_'+myDis+'_'+str(myRP)+'.pdf')
        fig.savefig('../output_plots/'+myCountry+'/poverty_k_'+myDis+'_'+str(myRP)+'.pdf',format='pdf')#+'.pdf',format='pdf')
        fig.savefig('../output_plots/'+myCountry+'/png/poverty_k_'+myDis+'_'+str(myRP)+'.png',format='png')#+'.pdf',format='pdf')
        plt.cla()    
        
        ##

        # Same as above, for affected people
        ax=plt.gca()

        ci_heights, ci_bins = np.histogram(cutA.loc[(cutA.affected_cat =='a'),'c_initial'],       bins=50, weights=cutA.loc[(cutA.affected_cat =='a'),'pcwgt'])
        cf_heights, cf_bins = np.histogram(cutA.loc[(cutA.affected_cat =='a'),'c_final'],    bins=ci_bins, weights=cutA.loc[(cutA.affected_cat =='a'),'pcwgt'])

        ax.bar(ci_bins[:-1], ci_heights, width=(ci_bins[1]-ci_bins[0]), label='Initial', facecolor=q_colors[0],alpha=0.4)
        ax.bar(cf_bins[:-1], cf_heights, width=(ci_bins[1]-ci_bins[0]), label='Post-disaster', facecolor=q_colors[1],alpha=0.4)

        print('All people: ',cutA['pcwgt'].sum())
        print('Affected people: ',cutA.loc[(cutA.affected_cat =='a'),'pcwgt'].sum())

        delta_p = cutA.loc[(cutA.affected_cat =='a') & (cutA.c_final <= cutA.pov_line),'pcwgt'].sum() 
        delta_p -= cutA.loc[(cutA.affected_cat =='a') & (cutA.c_initial <= cutA.pov_line),'pcwgt'].sum()
        p_str = format_delta_p(delta_p)
        p_pct = ' ('+str(round((delta_p/cutA['pcwgt'].sum())*100.,2))+'% of population)'

        plt.plot([pov_line,pov_line],[0,1.2*cf_heights[:-2].max()],'k-',lw=1.5,color='black',zorder=100,alpha=0.85)
        ax.annotate('Poverty line',xy=(1.1*pov_line,1.20*cf_heights[:-2].max()),xycoords='data',ha='left',va='top',fontsize=8,annotation_clip=False)
        ax.annotate(r'$\Delta$N$_p$ = +'+p_str+p_pct,xy=(1.1*pov_line,1.12*cf_heights[:-2].max()),xycoords='data',ha='left',va='top',fontsize=8,annotation_clip=False)

        fig = ax.get_figure()
        plt.xlabel(r'Income ['+get_currency(myCountry)[0]+' yr$^{-1}$]')
        plt.ylabel('Population')
        #plt.ylim(0,400000)
        plt.legend(loc='best')
        print('poverty_k_aff_'+myDis+'_'+str(myRP)+'.pdf\n')
        fig.savefig('../output_plots/'+myCountry+'/poverty_k_aff_'+myDis+'_'+str(myRP)+'.pdf',format='pdf')#+'.pdf',format='pdf')
        fig.savefig('../output_plots/'+myCountry+'/png/poverty_k_aff_'+myDis+'_'+str(myRP)+'.png',format='png')#+'.pdf',format='pdf')
        plt.cla()

        if myCountry != 'FJ':
            make_map_from_svg(
                disaster_n_pov.disaster_n_pov, 
                svg_file,
                outname='new_poverty_incidence_'+myDis+'_'+str(myRP),
                color_maper=plt.cm.get_cmap('RdYlGn_r'), 
                label='Number of '+dem+' pushed into poverty by '+myDis+' (RP = '+str(myRP)+')',
                new_title='Number of '+dem+' pushed into poverty by '+myDis+' (RP = '+str(myRP)+')',
                do_qualitative=False,
                res=800)
            
            make_map_from_svg(
                disaster_n_pov.disaster_n_pov_pct, 
                svg_file,
                outname='new_poverty_incidence_pct_'+myDis+'_'+str(myRP),
                color_maper=plt.cm.get_cmap('RdYlGn_r'), 
                label=dem+' pushed into poverty by '+myDis+' (RP = '+str(myRP)+') [%]',
                new_title=dem+' pushed into poverty by '+myDis+' (RP = '+str(myRP)+') [%]',
                do_qualitative=False,
                res=800)

df_out_sum = pd.DataFrame()
df_out = pd.DataFrame()

rp_all = []
dk_all = []
dw_all = []

dk_q1 = []
dw_q1 = []

for myRP in myHaz[2]:

    # Don't care about province or hazard, but I DO still need to separate out by RP
    # try means for all of the Philippines
    all_q1 = iah.loc[(iah.helped_cat == 'helped') & (iah.quintile == 1) & (iah.rp == myRP)]
    all_q2 = iah.loc[(iah.helped_cat == 'helped') & (iah.quintile == 2) & (iah.rp == myRP)]
    all_q3 = iah.loc[(iah.helped_cat == 'helped') & (iah.quintile == 3) & (iah.rp == myRP)]
    all_q4 = iah.loc[(iah.helped_cat == 'helped') & (iah.quintile == 4) & (iah.rp == myRP)]
    all_q5 = iah.loc[(iah.helped_cat == 'helped') & (iah.quintile == 5) & (iah.rp == myRP)]
    #all_q2 = iah.loc[(((iah.affected_cat == 'a') & (iah.helped_cat == 'helped')) | ((iah.affected_cat == 'na') & (iah.helped_cat == 'not_helped'))) 
    #                 & (iah.quintile == 2) & (iah.rp == myRP)]
    #all_q2 = iah.loc[(((iah.affected_cat == 'a') & (iah.helped_cat == 'helped')) | ((iah.affected_cat == 'na') & (iah.helped_cat == 'not_helped'))) 
    #                 & (iah.quintile == 2) & (iah.rp == myRP)]
    #all_q3 = iah.loc[(((iah.affected_cat == 'a') & (iah.helped_cat == 'helped')) | ((iah.affected_cat == 'na') & (iah.helped_cat == 'not_helped'))) 
    #                 & (iah.quintile == 3) & (iah.rp == myRP)]
    #all_q4 = iah.loc[(((iah.affected_cat == 'a') & (iah.helped_cat == 'helped')) | ((iah.affected_cat == 'na') & (iah.helped_cat == 'not_helped'))) 
    #                 & (iah.quintile == 4) & (iah.rp == myRP)]
    #all_q5 = iah.loc[(((iah.affected_cat == 'a') & (iah.helped_cat == 'helped')) | ((iah.affected_cat == 'na') & (iah.helped_cat == 'not_helped'))) 
    #                 & (iah.quintile == 5) & (iah.rp == myRP)]


    print('RP = ',myRP,'dk =',iah.loc[(iah.helped_cat == 'helped') & (iah.rp == myRP),['dk0','pcwgt']].prod(axis=1).sum())
    print('RP = ',myRP,'dw =',iah.loc[(iah.helped_cat == 'helped') & (iah.rp == myRP),['dw','pcwgt']].prod(axis=1).sum())
     

    print('RP = ',myRP,'dk (Q1&2) = ',iah.loc[(iah.helped_cat == 'helped') & (iah.rp == myRP) & (iah.quintile <= 2),['dk0','pcwgt']].prod(axis=1).sum())
    print('RP = ',myRP,'dw (Q1&2) = ',iah.loc[(iah.helped_cat == 'helped') & (iah.rp == myRP) & (iah.quintile <= 2),['dw','pcwgt']].prod(axis=1).sum())        

    print('RP = ',myRP,'dk (Q1) = ',iah.loc[(iah.helped_cat == 'helped') & (iah.rp == myRP) & (iah.quintile == 1),['dk0','pcwgt']].prod(axis=1).sum())
    print('RP = ',myRP,'dw (Q1) = ',iah.loc[(iah.helped_cat == 'helped') & (iah.rp == myRP) & (iah.quintile == 1),['dw','pcwgt']].prod(axis=1).sum())       

    #print('RP = ',myRP,'dk =',iah.loc[(((iah.affected_cat == 'a') & (iah.helped_cat == 'helped')) | ((iah.affected_cat == 'na') & (iah.helped_cat == 'not_helped'))) 
    #              & (iah.rp == myRP),['dk0','pcwgt']].prod(axis=1).sum())
    #print('RP = ',myRP,'dw =',iah.loc[(((iah.affected_cat == 'a') & (iah.helped_cat == 'helped')) | ((iah.affected_cat == 'na') & (iah.helped_cat == 'not_helped'))) 
    #              & (iah.rp == myRP),['dw','pcwgt']].prod(axis=1).sum())          

    #print('RP = ',myRP,'dk (Q1&2) = ',iah.loc[(((iah.affected_cat == 'a') & (iah.helped_cat == 'helped')) | ((iah.affected_cat == 'na') & (iah.helped_cat == 'not_helped'))) 
    #              & (iah.rp == myRP) & (iah.quintile <= 2),['dk0','pcwgt']].prod(axis=1).sum())
    #print('RP = ',myRP,'dw (Q1&2) = ',iah.loc[(((iah.affected_cat == 'a') & (iah.helped_cat == 'helped')) | ((iah.affected_cat == 'na') & (iah.helped_cat == 'not_helped'))) 
    #              & (iah.rp == myRP) & (iah.quintile <= 2),['dw','pcwgt']].prod(axis=1).sum())        

    #print('RP = ',myRP,'dk (Q1) = ',iah.loc[(((iah.affected_cat == 'a') & (iah.helped_cat == 'helped')) | ((iah.affected_cat == 'na') & (iah.helped_cat == 'not_helped'))) 
    #              & (iah.rp == myRP) & (iah.quintile == 1),['dk0','pcwgt']].prod(axis=1).sum())
    #print('RP = ',myRP,'dw (Q1) = ',iah.loc[(((iah.affected_cat == 'a') & (iah.helped_cat == 'helped')) | ((iah.affected_cat == 'na') & (iah.helped_cat == 'not_helped'))) 
    #              & (iah.rp == myRP) & (iah.quintile == 1),['dw','pcwgt']].prod(axis=1).sum())        

    rp_all.append(myRP)
    dk_all.append(iah.loc[(iah.helped_cat == 'helped') & (iah.rp == myRP),['dk0','pcwgt']].prod(axis=1).sum())
    dw_all.append(iah.loc[(iah.helped_cat == 'helped') & (iah.rp == myRP),['dw','pcwgt']].prod(axis=1).sum())

    dk_q1.append(iah.loc[(iah.helped_cat == 'helped') & (iah.rp == myRP) & (iah.quintile == 1),['dk0','pcwgt']].prod(axis=1).sum())
    dw_q1.append(iah.loc[(iah.helped_cat == 'helped') & (iah.rp == myRP) & (iah.quintile == 1),['dw','pcwgt']].prod(axis=1).sum())

    k_mean = get_weighted_mean(all_q1,all_q2,all_q3,all_q4,all_q5,'k')
    dk_mean = get_weighted_mean(all_q1,all_q2,all_q3,all_q4,all_q5,'dk0')
    dc_mean = get_weighted_mean(all_q1,all_q2,all_q3,all_q4,all_q5,'dc0')
    dw_mean = get_weighted_mean(all_q1,all_q2,all_q3,all_q4,all_q5,'dw')
    nrh_mean = get_weighted_mean(all_q1.loc[all_q1.help_received != 0.],all_q2.loc[all_q2.help_received != 0.],all_q3.loc[all_q3.help_received != 0.],all_q4.loc[all_q4.help_received != 0.],all_q5.loc[all_q5.help_received != 0.],'pds_nrh')
    dw_pds_mean = get_weighted_mean(all_q1.loc[all_q1.help_received != 0.],all_q2.loc[all_q2.help_received != 0.],all_q3.loc[all_q3.help_received != 0.],all_q4.loc[all_q4.help_received != 0.],all_q5.loc[all_q5.help_received != 0.],'pds_dw')
    pds_help_fee_mean = get_weighted_mean(all_q1.loc[all_q1.help_received != 0.],all_q2.loc[all_q2.help_received != 0.],all_q3.loc[all_q3.help_received != 0.],all_q4.loc[all_q4.help_received != 0.],all_q5.loc[all_q5.help_received != 0.],'pds_help_fee')
    pds_help_rec_mean = get_weighted_mean(all_q1.loc[all_q1.help_received != 0.],all_q2.loc[all_q2.help_received != 0.],all_q3.loc[all_q3.help_received != 0.],all_q4.loc[all_q4.help_received != 0.],all_q5.loc[all_q5.help_received != 0.],'pds_help_received')
    
    df_this_sum = pd.DataFrame({     'k_q1':     k_mean[0],     'k_q2':     k_mean[1],     'k_q3':     k_mean[2],     'k_q4':     k_mean[3],     'k_q5':     k_mean[4],
                                     'dk_q1':    dk_mean[0],    'dk_q2':    dk_mean[1],    'dk_q3':    dk_mean[2],    'dk_q4':    dk_mean[3],    'dk_q5':    dk_mean[4], 
                                     'dc_q1':    dc_mean[0],    'dc_q2':    dc_mean[1],    'dc_q3':    dc_mean[2],    'dc_q4':    dc_mean[3],    'dc_q5':    dc_mean[4],
                                     'dw_q1':    dw_mean[0],    'dw_q2':    dw_mean[1],    'dw_q3':    dw_mean[2],    'dw_q4':    dw_mean[3],    'dw_q5':    dw_mean[4],
                                     'nrh_q1':   nrh_mean[0],   'nrh_q2':   nrh_mean[1],   'nrh_q3':   nrh_mean[2],   'nrh_q4':   nrh_mean[3],   'nrh_q5':   nrh_mean[4],
                                     'dw_pds_q1':dw_pds_mean[0],'dw_pds_q2':dw_pds_mean[1],'dw_pds_q3':dw_pds_mean[2],'dw_pds_q4':dw_pds_mean[3],'dw_pds_q5':dw_pds_mean[4]},
                               columns=[     'k_q1',     'k_q2',     'k_q3',     'k_q4',     'k_q5',
                                             'dk_q1',    'dk_q2',    'dk_q3',    'dk_q4',    'dk_q5',
                                             'dc_q1',    'dc_q2',    'dc_q3',    'dc_q4',    'dc_q5',
                                             'dw_q1',    'dw_q2',    'dw_q3',    'dw_q4',    'dw_q5',
                                             'nrh_q1',   'nrh_q2',   'nrh_q3',   'nrh_q4',   'nrh_q5',
                                             'dw_pds_q1','dw_pds_q2','dw_pds_q3','dw_pds_q4','dw_pds_q5'],
                               index=[myRP])

    if df_out_sum.empty: df_out_sum = df_this_sum
    else: df_out_sum = df_out_sum.append(df_this_sum)

    print('--> WHOLE COUNTRY (rp =',myRP,')')
    print('k/100 (avg) = ',0.01*np.array(k_mean))
    print('dk (avg) = ',dk_mean)
    print('dc (avg) = ',dc_mean)
    print('dw (pc avg) = ',dw_mean)
    print('pds_help_fee_mean (avg) = ',pds_help_fee_mean)
    print('pds_help_rec_mean (avg) = ',pds_help_rec_mean)
    print('\n')

    for myProv in myHaz[0]:
        for myDis in myHaz[1]:

            cut = None
            if myCountry == 'PH':
                cut = iah.loc[(((iah.affected_cat == 'a')&(iah.helped_cat == 'helped'))|((iah.affected_cat == 'na')&(iah.helped_cat == 'not_helped')))&(iah[economy] == myProv) & (iah.hazard == myDis) & (iah.rp == myRP)].set_index([economy,'hazard','rp'])
            elif myCountry == 'FJ':
                cut = iah.loc[(iah.helped_cat == 'helped') & (iah.Division == myProv) & (iah.hazard == myDis) & (iah.rp == myRP)].set_index([economy,'hazard','rp'])

            if cut.shape[0] == 0: 
                print('Nothing here!')
                continue
        
            # look at quintiles
            q1 = cut.loc[(cut.quintile == 1)].reset_index()
            q2 = cut.loc[(cut.quintile == 2)].reset_index()
            q3 = cut.loc[(cut.quintile == 3)].reset_index()
            q4 = cut.loc[(cut.quintile == 4)].reset_index()
            q5 = cut.loc[(cut.quintile == 5)].reset_index()
            
            k_mean = get_weighted_mean(q1,q2,q3,q4,q5,'k')
            dk_mean = get_weighted_mean(q1,q2,q3,q4,q5,'dk0')
            dc_mean = get_weighted_mean(q1,q2,q3,q4,q5,'dc0')
            dw_mean = get_weighted_mean(q1,q2,q3,q4,q5,'dw')
            nrh_mean = get_weighted_mean(q1.loc[q1.help_received != 0],q2.loc[q2.help_received != 0],q3.loc[q3.help_received != 0],
                                         q4.loc[q4.help_received != 0],q5.loc[q5.help_received != 0],'pds_nrh')
            dw_pds_mean = get_weighted_mean(q1.loc[q1.help_received != 0],q2.loc[q2.help_received != 0],q3.loc[q3.help_received != 0],
                                            q4.loc[q4.help_received != 0],q5.loc[q5.help_received != 0],'pds_dw')
            pds_help_fee_mean = get_weighted_mean(q1.loc[q1.help_received != 0],q2.loc[q2.help_received != 0],q3.loc[q3.help_received != 0],
                                                  q4.loc[q4.help_received != 0],q5.loc[q5.help_received != 0],'pds_help_fee')
            pds_help_rec_mean = get_weighted_mean(q1.loc[q1.help_received != 0],q2.loc[q2.help_received != 0],q3.loc[q3.help_received != 0],
                                                  q4.loc[q4.help_received != 0],q5.loc[q5.help_received != 0],'pds_help_received')

            df_this = pd.DataFrame({     'k_q1':     k_mean[0],     'k_q2':     k_mean[1],     'k_q3':     k_mean[2],     'k_q4':     k_mean[3],     'k_q5':     k_mean[4],
                                        'dk_q1':    dk_mean[0],    'dk_q2':    dk_mean[1],    'dk_q3':    dk_mean[2],    'dk_q4':    dk_mean[3],    'dk_q5':    dk_mean[4], 
                                        'dc_q1':    dc_mean[0],    'dc_q2':    dc_mean[1],    'dc_q3':    dc_mean[2],    'dc_q4':    dc_mean[3],    'dc_q5':    dc_mean[4],
                                        'dw_q1':    dw_mean[0],    'dw_q2':    dw_mean[1],    'dw_q3':    dw_mean[2],    'dw_q4':    dw_mean[3],    'dw_q5':    dw_mean[4],
                                       'nrh_q1':   nrh_mean[0],   'nrh_q2':   nrh_mean[1],   'nrh_q3':   nrh_mean[2],   'nrh_q4':   nrh_mean[3],   'nrh_q5':   nrh_mean[4],
                                    'dw_pds_q1':dw_pds_mean[0],'dw_pds_q2':dw_pds_mean[1],'dw_pds_q3':dw_pds_mean[2],'dw_pds_q4':dw_pds_mean[3],'dw_pds_q5':dw_pds_mean[4]},
                                      columns=[     'k_q1',     'k_q2',     'k_q3',     'k_q4',     'k_q5',
                                                   'dk_q1',    'dk_q2',    'dk_q3',    'dk_q4',    'dk_q5',
                                                   'dc_q1',    'dc_q2',    'dc_q3',    'dc_q4',    'dc_q5',
                                                   'dw_q1',    'dw_q2',    'dw_q3',    'dw_q4',    'dw_q5',
                                                  'nrh_q1',   'nrh_q2',   'nrh_q3',   'nrh_q4',   'nrh_q5',
                                               'dw_pds_q1','dw_pds_q2','dw_pds_q3','dw_pds_q4','dw_pds_q5'],
                                      index=[[myProv],[myDis],[myRP]])

            if df_out.empty: df_out = df_this
            else: df_out = df_out.append(df_this)

            # histograms
            df_wgt = pd.DataFrame({'q1_w': q1.loc[(q1.affected_cat=='a') & (q1.c <= 100000),'pcwgt'],
                                   'q2_w': q2.loc[(q2.affected_cat=='a') & (q2.c <= 100000),'pcwgt'],
                                   'q3_w': q3.loc[(q3.affected_cat=='a') & (q3.c <= 100000),'pcwgt'],
                                   'q4_w': q4.loc[(q4.affected_cat=='a') & (q4.c <= 100000),'pcwgt'],
                                   'q5_w': q5.loc[(q5.affected_cat=='a') & (q5.c <= 100000),'pcwgt']}, 
                                  columns=['q1_w', 'q2_w', 'q3_w', 'q4_w', 'q5_w']).fillna(0)

            #df_wgt.to_csv('~/Desktop/weights.csv')

            for istr in ['dk0','dc0','dw']:
                continue
                
                upper_clip = 75000
                if istr == 'dw': upper_clip =  200000

                df_tmp = pd.DataFrame({'q1': q1.loc[(q1.affected_cat=='a') & (q1.c <= 100000),istr],
                                       'q2': q2.loc[(q2.affected_cat=='a') & (q2.c <= 100000),istr],
                                       'q3': q3.loc[(q3.affected_cat=='a') & (q3.c <= 100000),istr],
                                       'q4': q4.loc[(q4.affected_cat=='a') & (q4.c <= 100000),istr],
                                       'q5': q5.loc[(q5.affected_cat=='a') & (q5.c <= 100000),istr]},columns=['q1', 'q2', 'q3', 'q4', 'q5']).fillna(0)

                q1_heights, q1_bins = np.histogram(df_tmp['q1'].clip(upper=upper_clip),weights=df_wgt['q1_w'],bins=15)                
                #q2_heights, q2_bins = np.histogram(df_tmp['q2'].clip(upper=upper_clip),weights=df_wgt['q2_w'],bins=q1_bins)
                q3_heights, q3_bins = np.histogram(df_tmp['q3'].clip(upper=upper_clip),weights=df_wgt['q3_w'],bins=q1_bins)
                #q4_heights, q4_bins = np.histogram(df_tmp['q4'].clip(upper=upper_clip),weights=df_wgt['q4_w'],bins=q1_bins)
                q5_heights, q5_bins = np.histogram(df_tmp['q5'].clip(upper=upper_clip),weights=df_wgt['q5_w'],bins=q1_bins)

                width = (q1_bins[1] - q1_bins[0])*2/7
            
                ax = plt.gca()
                ax.bar(q1_bins[:-1],         q1_heights, width=width, label='q1', facecolor=q_colors[0],alpha=0.3)
                #ax.bar(q2_bins[:-1], q2_heights, width=width, label='q2', facecolor=q_colors[1],alpha=0.3)
                ax.bar(q3_bins[:-1]+1*width, q3_heights, width=width, label='q3', facecolor=q_colors[2],alpha=0.3)
                #ax.bar(q4_bins[:-1], q4_heights, width=width, label='q4', facecolor=q_colors[3],alpha=0.3)
                ax.bar(q5_bins[:-1]+2*width, q5_heights, width=width, label='q5', facecolor=q_colors[4],alpha=0.3)

                mu = np.average(df_tmp['q1'], weights=df_wgt['q1_w'])
                sigma = np.sqrt(np.average((df_tmp['q1']-mu)**2, weights=df_wgt['q1_w']))
                #y = df_wgt['q1_w'].sum()*mlab.normpdf(q1_bins, mu, sigma)
                #l = plt.plot(q1_bins, df_wgt['q1_w'].sum()*y, 'r--', linewidth=2,color=q_colors[0]) 

                mu = np.average(df_tmp['q3'], weights=df_wgt['q3_w'])
                sigma = np.sqrt(np.average((df_tmp['q3']-mu)**2, weights=df_wgt['q3_w']))      
                #y = df_wgt['q3_w'].sum()*mlab.normpdf(q3_bins, mu, sigma)
                #l = plt.plot(q3_bins, df_wgt['q3_w'].sum()*y, 'r--', linewidth=2,color=q_colors[2]) 

                mu = np.average(df_tmp['q5'], weights=df_wgt['q5_w'])
                sigma = np.sqrt(np.average((df_tmp['q5']-mu)**2, weights=df_wgt['q5_w']))     
                #y = df_wgt['q5_w'].sum()*mlab.normpdf(q5_bins, mu, sigma)
                #l = plt.plot(q5_bins, df_wgt['q5_w'].sum()*y, 'r--', linewidth=2,color=q_colors[4]) 

                plt.title(myDis+' in '+myProv+' (rp = '+str(myRP)+') - '+istr)
                plt.xlabel(istr,fontsize=12)
                plt.legend(loc='best')
                
                fig = ax.get_figure()
                print('Saving: hists/'+istr+'_'+myProv+'_'+myDis+'_'+str(myRP)+'.pdf')
                fig.savefig('../output_plots/'+myCountry+'/'+istr+'_'+myProv.replace(' ','_')+'_'+myDis+'_'+str(myRP)+'.pdf',format='pdf')#+'.pdf',format='pdf')
                fig.savefig('../output_plots/'+myCountry+'/png/'+istr+'_'+myProv.replace(' ','_')+'_'+myDis+'_'+str(myRP)+'.png',format='png')#+'.pdf',format='pdf')
                plt.cla()

            # Means
            ax1 = plt.subplot(111)
            for ij in range(0,5):
                #ax1.bar([6*ii+ij for ii in range(1,3)],[dk_mean[ij],dw_mean[ij]],color=q_colors[ij],alpha=0.7,label=q_labels[ij])
                #ax1.bar([6*ii+ij for ii in range(1,5)],[0.01*np.array(k_mean[ij]),dk_mean[ij],dc_mean[ij],dw_mean[ij]],color=q_colors[ij],alpha=0.7,label=q_labels[ij])
                ax1.bar([6*ii+ij for ii in range(1,7)],[0.01*np.array(k_mean[ij]),dk_mean[ij],dc_mean[ij],dw_mean[ij],nrh_mean[ij],dw_pds_mean[ij]],color=q_colors[ij],alpha=0.7,label=q_labels[ij])
                        
            label_y_val = 0.5*np.array(nrh_mean).min()

            ax1.xaxis.set_ticks([])
            plt.title(str(myRP)+'-Year '+myDis[:1].upper()+myDis[1:]+' Event in '+myProv)
            plt.ylabel('Disaster losses ('+get_currency(myCountry)[0]+' per capita)')
            ax1.annotate('1% of assets',                 xy=( 6,label_y_val),xycoords='data',ha='left',va='top',weight='bold',fontsize=8,annotation_clip=False)
            ax1.annotate('Asset loss',                   xy=(12,label_y_val),xycoords='data',ha='left',va='top',weight='bold',fontsize=8,annotation_clip=False)
            ax1.annotate('Consumption\nloss',            xy=(18,label_y_val),xycoords='data',ha='left',va='top',weight='bold',fontsize=8,annotation_clip=False)
            ax1.annotate('Well-being loss',              xy=(24,label_y_val),xycoords='data',ha='left',va='top',weight='bold',fontsize=8,annotation_clip=False)
            ax1.annotate('Net cost \nof help',           xy=(30,1.5*np.array(nrh_mean).min()),xycoords='data',ha='left',va='top',weight='bold',fontsize=8,annotation_clip=False)
            ax1.annotate('Well-being loss\npost-support',xy=(36,label_y_val),xycoords='data',ha='left',va='top',weight='bold',fontsize=8,annotation_clip=False)
            ax1.legend(loc='best')

            plt.xlim(5.5,41.5)
            #plt.ylim(-50,250)

            print('Saving: histo_'+myProv+'_'+myDis+'_'+str(myRP)+'.pdf\n')
            plt.savefig('../output_plots/'+myCountry+'/means_'+myProv.replace(' ','_')+'_'+myDis+'_'+str(myRP)+'.pdf',bbox_inches='tight',format='pdf')
            plt.savefig('../output_plots/'+myCountry+'/png/means_'+myProv.replace(' ','_')+'_'+myDis+'_'+str(myRP)+'.png',format='png')#+'.pdf',bbox_inches='tight',format='pdf')
            plt.cla()

df_out.to_csv('~/Desktop/my_plots/my_means_'+myCountry+pol_str+'.csv')
df_out_sum.to_csv('~/Desktop/my_plots/my_means_ntl_'+myCountry+pol_str+'.csv')

print('rp:',rp_all,'\ndk:',dk_all,'\ndw:',dw_all,'\ndk_q1:',dk_q1,'\ndw_q1:',dw_q1)

#natl_df = pd.DataFrame([np.array(rp_all).T,dk_all.T,dw_all.T,dk_q1.T,dw_q1.T],columns=['rp_all','dk_all','dw_all','dk_q1','dw_q1'])
natl_df = pd.DataFrame(np.array(dk_all).T,index=rp_all,columns=['dk_all'])
natl_df.index.name = 'rp'
natl_df['dw_all'] = np.array(dw_all).T
natl_df['dk_q1'] = np.array(dk_q1).T
natl_df['dw_q1'] = np.array(dw_q1).T

summed = sum_with_rp('FJ',natl_df,['dk_all','dw_all','dk_q1','dw_q1'],sum_provinces=True,economy=economy,national=True)

df = df.reset_index()
#print('Prov pop = ',df.loc[(df.rp==1)&(df.hazard=='typhoon'),'pop'])
#print('Prov GDP pc = ',df.loc[(df.rp==1)&(df.hazard=='typhoon'),'gdp_pc_prov'])
#print('Prov GDP = ',df.loc[(df.rp==1)&(df.hazard=='typhoon'),['gdp_pc_prov','pop']].prod(axis=1))
natl_gdp = df.loc[(df.rp==1)&(df.hazard==myHaz[1][0]),['gdp_pc_prov','pop']].prod(axis=1).sum()

print(summed)
print(natl_gdp)
print('Asset Risk:',round(100.*summed['dk_all']/natl_gdp,2),'% of natl GDP per year')
print('Well-being Risk:',round(100.*summed['dw_all']/natl_gdp,2),'% of natl GDP per year')
