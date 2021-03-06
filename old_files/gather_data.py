# This script provides data input for the resilience indicator multihazard model for Philippines. 
# Restructured from the global model and developed by Jinqiang Chen and Brian Walsh

# Magic
from IPython import get_ipython
get_ipython().magic('reset -f')
get_ipython().magic('load_ext autoreload')
get_ipython().magic('autoreload 2')

# Import packages for data analysis
from lib_country_dir import *
from lib_gather_data import *
from replace_with_warning import *
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pandas import isnull
import os, time
import warnings
import sys
warnings.filterwarnings('always',category=UserWarning)

if len(sys.argv) < 2:
    print('Need to list country. Try PH or FJ')
    assert(False)
else: myCountry = sys.argv[1]

# Set up directories/tell code where to look for inputs & where to save outputs
intermediate = set_directories(myCountry)

# Options and parameters
economy       = get_economic_unit(myCountry)

# Levels of index at which one event happens
event_level   = [economy, 'hazard', 'rp']

#Country dictionaries
#STATE/PROVINCE NAMES
# --> should be a 
df = get_places(myCountry,economy)
prov_code = get_places_dict(myCountry)

###Define parameters
df['pi']                     = reduction_vul       # how much early warning reduces vulnerability
df['rho']                    = discount_rate       # discount rate
df['shareable']              = asset_loss_covered  # target of asset losses to be covered by scale up
df['avg_prod_k']             = 0.337960802589002   # average productivity of capital, value from the global resilience model
df['T_rebuild_K']            = reconstruction_time # Reconstruction time
df['income_elast']           = inc_elast           # income elasticity
df['max_increased_spending'] = max_support         # 5% of GDP in post-disaster support maximum, if everything is ready

# Protected from events with RP < 'protection'
if myCountry == 'PH':  df['protection'] = 1
if myCountry == 'FJ':  df['protection'] = 1


# Secondary dataframe, if necessary
# For PH: this is GDP per cap info:
df2 = get_df2(myCountry)

if myCountry == 'PH': 
    df['psa_pop']      = df['population']    # Provincial population
    df.drop(['population'],axis=1,inplace=True)

    df2['gdp']         = df2['gdp_pc_pp']*df2['pop']
    #df['gdp_pc_pp']   = df2['gdp']/df['psa_pop'] #in Pesos
    df['avg_hh_size']  = df['psa_pop']/df2['pop'] # nPeople/nHH


#ft2015 = 14832.0962
#pv2015 = 21240.2924

cat_info = load_survey_data(myCountry)

print('Survey population:',cat_info.pcwgt.sum())

if myCountry == 'PH':
    get_hhid_FIES(cat_info)
    cat_info = cat_info.rename(columns={'w_prov':'province'})
    cat_info = cat_info.reset_index().set_index([cat_info.province.replace(prov_code)]) #replace district code with its name
    cat_info = cat_info.drop('province',axis=1)

    df['gdp_pc_pp_prov'] = cat_info[['pcinc_s','pcwgt']].prod(axis=1).sum(level=economy)/cat_info['pcwgt'].sum(level=economy)
    df['gdp_pc_pp_nat'] = cat_info[['pcinc_s','pcwgt']].prod(axis=1).sum()/cat_info['pcwgt'].sum()
    # ^ this is per capita income*population/number of households

if myCountry == 'FJ':
    cat_info = cat_info.rename(columns={'Poor':'poorhh'})  
    df['gdp_pc_pp_prov'] = cat_info[['New Total','Weight']].prod(axis=1).sum(level=economy)/cat_info['pcwgt'].sum(level=economy)
    df['gdp_pc_pp_nat'] = cat_info[['New Total','Weight']].prod(axis=1).sum()/cat_info['pcwgt'].sum()
    
df['pop'] = cat_info.pcwgt.sum(level=economy)

if myCountry == 'PH':
    df['pct_diff'] = 100.*(df['psa_pop']-df['pop'])/df['pop']

#Vulnerability
vul_curve = get_vul_curve(myCountry,'wall')
for thecat in vul_curve.desc.unique():
    if myCountry == 'PH': cat_info.ix[cat_info.walls.values == thecat,'v'] = vul_curve.loc[vul_curve.desc.values == thecat].v.values
    if myCountry == 'FJ': cat_info.ix[cat_info.Constructionofouterwalls.values == thecat,'v'] = vul_curve.loc[vul_curve.desc.values == thecat].v.values
    # Fiji doesn't have info on roofing, but it does have info on the condition of outer walls. Include that as a multiplier?

# Get roofing data (but Fiji doesn't have this info)
if myCountry != 'FJ':
    vul_curve = get_vul_curve(myCountry,'roof')
    for thecat in vul_curve.desc.unique():
        cat_info.ix[cat_info.roof.values == thecat,'v'] += vul_curve.loc[vul_curve.desc.values == thecat].v.values
    cat_info.v = cat_info.v/2

if myCountry == 'PH':
    cat_info.ix[cat_info.v==0.1,'v'] *= np.random.uniform(.8,2,30187)
    cat_info.ix[cat_info.v==0.25,'v'] *= np.random.uniform(.8,1.2,5895)  
    cat_info.ix[(10*(cat_info.v-.4)).round()==0,'v'] *= np.random.uniform(.8,1.2,5130)
    cat_info.ix[cat_info.v==0.55,'v'] *= np.random.uniform(.8,1.2,153)
    cat_info.ix[cat_info.v==0.70,'v'] *= np.random.uniform(.8,1.2,179) 
    cat_info.drop(['walls','roof'],axis=1,inplace=True)

if myCountry == 'FJ':
    cat_info.ix[cat_info.v==0.1,'v'] *= np.random.uniform(.8,2,2391)
    cat_info.ix[cat_info.v==0.4,'v'] *= np.random.uniform(.8,1.2,3549)
    cat_info.ix[cat_info.v==0.7,'v'] *= np.random.uniform(.8,1.2,80) 
    cat_info.drop(['Constructionofouterwalls','Conditionofouterwalls'],axis=1,inplace=True)

# Calculate income per household
if myCountry == 'PH':
    # --> What's the difference between income & consumption/disbursements?
    # --> totdis = 'total family disbursements'
    # --> totex = 'total family expenditures'
    # --> pcinc_s seems to be what they use to calculate poverty...
    # --> can be converted to pcinc_ppp11 by dividing by (365*21.1782)
    cat_info['c'] = (cat_info['pcinc_s'])

elif myCountry == 'FJ':
    cat_info['c'] = cat_info['New Total']/cat_info['HHsize']

# --> (SL model) cat_info['c'] = cat_info[['emp','agri','other_agri','non_agri','other_inc','income_local']].sum(1)

# Cash receipts, abroad & domestic, other gifts
# --> Excluding international remittances ('cash_abroad')
# --> what about 'net_receipt'?
if myCountry == 'PH': 
                                                                               
    cat_info['social'] = (cat_info['tothrec']/cat_info['HHsize'])/cat_info['c']
    cat_info.drop(['cash_domestic','regft'],axis=1,inplace=True)
if myCountry == 'FJ':
    cat_info['social'] = (cat_info['TOTALTRANSFER']/cat_info['HHsize'])/cat_info['c']

cat_info.ix[cat_info.social>=1,'social'] = 0.99

# per cap weight = household_weight * family_size (?)
#cat_info['weight'] = cat_info[['hhwgt','fsize']].prod(axis=1)
if myCountry == 'FJ':
    cat_info['hhwgt'] = cat_info['Weight']
    cat_info.drop(['Weight'],axis=1,inplace=True)

cat_info['weight'] = cat_info['pcwgt']
# ^ don't get these twisted!

if myCountry == 'PH':    pov_line = cat_info.loc[(cat_info.poorhh == 1),'pcinc_s'].max() # <-- Individual
elif myCountry == 'FJ':
    print(cat_info)
    #cat_info['HHsize_eff'] = (0.5*cat_info['Nchildren']+cat_info['Nadult'])
    cat_info['pov_line'] = 0.
    cat_info.loc[cat_info.Sector=='Rural','pov_line'] = 49.50*52#*cat_info.loc[cat_info.Sector=='Rural','HHsize_eff']
    cat_info.loc[cat_info.Sector=='Urban','pov_line'] = 55.12*52#*cat_info.loc[cat_info.Sector=='Urban','HHsize_eff']
    cat_info.loc[(cat_info.poorhh == 1)].to_csv('~/Desktop/my_poor_FJ.csv')

print('Total population:',cat_info.weight.sum())
print('Total n households:',cat_info.hhwgt.sum())
#print('Poor in poverty:',    cat_info.loc[(cat_info.pcinc_s <= pov_line),'weight'].sum())
#print('Families in poverty:',cat_info.loc[(cat_info.pcinc_s <= pov_line), 'hhwgt'].sum())

# Change the name: district to code, and create an multi-level index 
cat_info = cat_info.rename(columns={'district':'code','HHID':'hhid'})

# Assign weighted household consumption to quintiles within each province
listofquintiles=np.arange(0.20, 1.01, 0.20) 
if myCountry == 'PH':
    cat_info = cat_info.reset_index().groupby(economy,sort=True).apply(lambda x:match_quintiles(x,perc_with_spline(reshape_data(x.pcinc_s),reshape_data(x.pcwgt),listofquintiles),'pcinc_s'))
    cat_info_c_5 = cat_info.reset_index().groupby(economy,sort=True).apply(lambda x:x.ix[x.quintile==1,'pcinc_s'].max())
elif myCountry == 'FJ':
    cat_info = cat_info.reset_index().groupby(economy,sort=True).apply(lambda x:match_quintiles(x,perc_with_spline(reshape_data(x.pcinc),reshape_data(x.pcwgt),listofquintiles),'pcinc'))
    cat_info_c_5 = cat_info.reset_index().groupby(economy,sort=True).apply(lambda x:x.ix[x.quintile==1,'pcinc'].max())

# 'c_5' is the upper consumption limit for the lowest quintile

cat_info = cat_info.reset_index().set_index([economy,'hhid']) #change the name: district to code, and create an multi-level index 
cat_info['c_5'] = broadcast_simple(cat_info_c_5,cat_info.index)
#cat_info['c_5'] = cat_info[['c_5','weight']].prod(axis=1)/cat_info['hhwgt']

cat_info.to_csv('~/Desktop/my_file.csv')

# Population of household as fraction of population of provinces
cat_info['n'] = cat_info.hhwgt/cat_info.hhwgt.sum(level=economy)

# population of household as fraction of total population
cat_info['n_national'] = cat_info.hhwgt/cat_info.hhwgt.sum() 

# These sum to 1 per province & nationally, respectively
#print('province normalization:',cat_info.n.sum(level=economy)) 
print('normalization:',cat_info.n_national.sum())

# Get the tax used for domestic social transfer
# --> tau_tax = 0.075391
df['tau_tax'] = cat_info[['social','c','hhwgt']].prod(axis=1, skipna=False).sum()/cat_info[['c','hhwgt']].prod(axis=1, skipna=False).sum()

# Get the share of Social Protection
cat_info['gamma_SP'] = cat_info[['social','c']].prod(axis=1,skipna=False)*cat_info['hhwgt'].sum()/cat_info[['social','c','hhwgt']].prod(axis=1, skipna=False).sum()
cat_info.drop('n_national',axis=1,inplace=True)

# Intl remittances: subtract from 'c'
cat_info['k'] = (1-cat_info['social'])*cat_info['c']/((1-df['tau_tax'])*df['avg_prod_k']) #calculate the capital
cat_info.ix[cat_info.k<0,'k'] = 0.0

if myCountry == 'FJ':
    #replace division codes with names
    df = df.reset_index()
    df = df.set_index([df.Division.replace(prov_code)])

    cat_info = cat_info.reset_index()
    cat_info = cat_info.set_index([cat_info.Division.replace(prov_code)]) #replace division code with its name
    cat_info.drop(['Division'],axis=1,inplace=True)

# Getting rid of Prov_code 98, 99 here
cat_info.dropna(inplace=True)

# Assign access to early warning based on 'poorhh' flag
if myCountry == 'PH':
    # --> doesn't seem to match up with the quintiles we assigned
    cat_info['shew'] = broadcast_simple(df2['shewr'],cat_info.index)
    cat_info.ix[cat_info.poorhh == 1,'shew'] = broadcast_simple(df2['shewp'],cat_info.index)
elif myCountry == 'FJ': 
    cat_info['shew'] = 0
    # can't find relevant info for Fiji

# Exposure
cat_info['fa'] = 0
cat_info.fillna(0,inplace=True)

# Cleanup dfs for writing out
cat_info = cat_info.drop([iXX for iXX in cat_info.columns.values.tolist() if iXX not in [economy,'hhid','weight','code','np','score','v','c','social','c_5','n','gamma_SP','k','shew','fa','quintile','hhwgt','cash_abroad','poorhh','Poor','totdis','pcinc_s','pcinc_ppp11','pcwgt','HHsize_eff']],axis=1)
cat_info_index = cat_info.drop([iXX for iXX in cat_info.columns.values.tolist() if iXX not in [economy,'hhid']],axis=1)

#########################
# HAZARD INFO
#
# This is the GAR
#hazard_ratios = pd.read_csv(inputs+'/PHL_frac_value_destroyed_gar_completed_edit.csv').set_index([economy, 'hazard', 'rp'])

# PHILIPPINES:
# This is the AIR dataset:
# df_haz is already in pesos
# --> Need to think about public assets
#df_haz = get_AIR_data(inputs+'/Risk_Profile_Master_With_Population.xlsx','Loss_Results','all','Agg')

df_haz = get_hazard_df(myCountry,economy)

# Edit & Shuffle provinces
if myCountry == 'PH':
    AIR_prov_rename = {'Shariff Kabunsuan':'Maguindanao',
                       'Davao Oriental':'Davao',
                       'Davao del Norte':'Davao',
                       'Metropolitan Manila':'Manila',
                       'Dinagat Islands':'Surigao del Norte'}
    df_haz['province'].replace(AIR_prov_rename,inplace=True) 

    # Add NCR 2-4 to AIR dataset
    df_NCR = pd.DataFrame(df_haz.loc[(df_haz.province == 'Manila')])
    df_NCR['province'] = 'NCR-2nd Dist.'
    df_haz = df_haz.append(df_NCR)

    df_NCR['province'] = 'NCR-3rd Dist.'
    df_haz = df_haz.append(df_NCR)
    
    df_NCR['province'] = 'NCR-4th Dist.'
    df_haz = df_haz.append(df_NCR)

    # In AIR, we only have 'Metropolitan Manila'
    # Distribute losses among Manila & NCR 2-4 according to assets
    cat_info = cat_info.reset_index()
    k_NCR = cat_info.loc[((cat_info.province == 'Manila') | (cat_info.province == 'NCR-2nd Dist.') 
                          | (cat_info.province == 'NCR-3rd Dist.') | (cat_info.province == 'NCR-4th Dist.')), ['k','hhwgt']].prod(axis=1).sum()

    df_haz.loc[df_haz.province ==        'Manila','value_destroyed'] *= cat_info.loc[cat_info.province ==        'Manila', ['k','hhwgt']].prod(axis=1).sum()/k_NCR
    df_haz.loc[df_haz.province == 'NCR-2nd Dist.','value_destroyed'] *= cat_info.loc[cat_info.province == 'NCR-2nd Dist.', ['k','hhwgt']].prod(axis=1).sum()/k_NCR
    df_haz.loc[df_haz.province == 'NCR-3rd Dist.','value_destroyed'] *= cat_info.loc[cat_info.province == 'NCR-3rd Dist.', ['k','hhwgt']].prod(axis=1).sum()/k_NCR
    df_haz.loc[df_haz.province == 'NCR-4th Dist.','value_destroyed'] *= cat_info.loc[cat_info.province == 'NCR-4th Dist.', ['k','hhwgt']].prod(axis=1).sum()/k_NCR

    # Sum over the provinces that we're merging
    # Losses are absolute value, so they are additive
    df_haz = df_haz.reset_index().set_index([economy,'hazard','rp']).sum(level=[economy,'hazard','rp']).drop(['index'],axis=1)
    
elif myCountry == 'FJ':
    pass

# Turn losses into fraction
cat_info = cat_info.reset_index().set_index([economy])

hazard_ratios = cat_info[['k','hhwgt']].prod(axis=1).sum(level=economy).to_frame(name='provincial_capital')
hazard_ratios = hazard_ratios.join(df_haz,how='outer')

if myCountry == 'PH':
    hazard_ratios['frac_destroyed'] = hazard_ratios['value_destroyed']/hazard_ratios['provincial_capital']
    hazard_ratios = hazard_ratios.drop(['provincial_capital','value_destroyed'],axis=1)
elif myCountry == 'FJ':
    hazard_ratios = hazard_ratios.drop([economy],axis=1)
    hazard_ratios['frac_destroyed'] = hazard_ratios['value_destroyed']/hazard_ratios['total_value']
    hazard_ratios['hazard'] = 'AAL'
    hazard_ratios['rp'] = '1'
    hazard_ratios = hazard_ratios.drop(['provincial_capital','value_destroyed','total_value'],axis=1)

# Have frac destroyed, need fa...
# Frac value destroyed = SUM_i(k*v*fa)

hazard_ratios = pd.merge(hazard_ratios.reset_index(),cat_info.reset_index(),on=economy,how='outer').set_index(event_level+['hhid'])[['frac_destroyed','v']]

# Transfer fa in excess of 95% to vulnerability
fa_threshold = 0.95
hazard_ratios['fa'] = (hazard_ratios['frac_destroyed']/hazard_ratios['v']).fillna(1E-8)

hazard_ratios.loc[hazard_ratios.fa>fa_threshold,'v'] = hazard_ratios.loc[hazard_ratios.fa>fa_threshold,['v','fa']].prod(axis=1)/fa_threshold
hazard_ratios['fa'] = hazard_ratios['fa'].clip(lower=0.0000001,upper=fa_threshold)

cat_info = cat_info.reset_index().set_index([economy,'hhid'])
cat_info['v'] = hazard_ratios.reset_index().set_index([economy,'hhid'])['v'].mean(level=[economy,'hhid']).clip(upper=0.99)

df.to_csv(intermediate+'/macro.csv',encoding='utf-8', header=True,index=True)

if 'index' in cat_info.columns: cat_info = cat_info.drop(['index'],axis=1)
cat_info.to_csv(intermediate+'/cat_info.csv',encoding='utf-8', header=True,index=True)

hazard_ratios= hazard_ratios.drop(['frac_destroyed','v'],axis=1)
hazard_ratios.to_csv(intermediate+'/hazard_ratios.csv',encoding='utf-8', header=True)
