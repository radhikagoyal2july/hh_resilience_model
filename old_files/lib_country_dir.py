import os
import pandas as pd
from lib_gather_data import *

global model
model = os.getcwd()

# People/hh will be affected or not_affected, and helped or not_helped
affected_cats = pd.Index(['a', 'na'], name='affected_cat')	     # categories for social protection
helped_cats   = pd.Index(['helped','not_helped'], name='helped_cat')

# These parameters could vary by country
reconstruction_time = 3.00 #time needed for reconstruction
reduction_vul       = 0.20 # how much early warning reduces vulnerability
inc_elast           = 1.50 # income elasticity
discount_rate       = 0.06 # discount rate
asset_loss_covered  = 0.80 # becomes 'shareable' 
max_support         = 0.05 # fraction of GDP

# Define directories
def set_directories(myCountry):  # get current directory
    global inputs, intermediate
    inputs        = model+'/../inputs/'+myCountry+'/'       # get inputs data directory
    intermediate  = model+'/../intermediate/'+myCountry+'/' # get outputs data directory

    # If the depository directories don't exist, create one:
    if not os.path.exists(inputs): 
        print('You need to put the country survey files in a directory titled ','/inputs/'+myCountry+'/')
        assert(False)
    if not os.path.exists(intermediate):
        os.makedirs(intermediate)

    return intermediate

def get_economic_unit(myC):
    
    if myC == 'PH': return 'province'
    elif myC == 'FJ': return 'Division'#'tikina'
    
    else: return None

def get_currency(myC):
    
    if myC == 'PH': return 'PhP'
    if myC == 'FJ': return 'FJD'
    else: return 'XXX'

def get_places(myC,economy):
    # This df should have just province code/name and population

    if myC == 'PH': 
        df = pd.read_excel(inputs+'population_2015.xlsx',sheetname='population').set_index(economy)
        return df

    if myC == 'FJ':
        df = pd.read_excel(inputs+'HIES 2013-14 Housing Data.xlsx',sheetname='Sheet1').set_index('Division').dropna(how='all')[['HHsize','Weight']].prod(axis=1).sum(level='Division').to_frame()
        df.columns = ['population']
        return df

    else: return None

def get_places_dict(myC):

    if myC == 'PH': 
        return pd.read_excel(inputs+'FIES_provinces.xlsx')[['province_code','province_AIR']].set_index('province_code').squeeze() 

    if myC == 'FJ':
        return pd.read_excel(inputs+'Fiji_provinces.xlsx')[['code','name']].set_index('code').squeeze() 

    else: return None

def load_survey_data(myC):

    if myC == 'PH':
        df = pd.read_csv(inputs+'fies2015.csv',usecols=['w_regn','w_prov','w_mun','w_bgy','w_ea','w_shsn','w_hcn','walls','roof','totex','cash_abroad','cash_domestic','regft','hhwgt','fsize','poorhh','totdis','tothrec','pcinc_s','pcinc_ppp11','pcwgt'])
        df['HHsize'] = df['pcwgt']/df['hhwgt']
        df['HHsize_eff'] = df['HHsize']
        return df

    elif myC == 'FJ':
        df = pd.read_excel(inputs+'HIES 2013-14 Income Data.xlsx',usecols=['HHID','Division','Nchildren','Nadult','HHsize','Sector','Weight','TOTALTRANSFER','TotalIncome','New Total']).set_index('HHID')
        df['HHsize_eff'] = (0.5*df['Nchildren']+df['Nadult'])
        df['pcwgt'] = df[['Weight','HHsize_eff']].prod(axis=1)
        df['pcinc'] = df['New Total']/df['HHsize_eff']

        df_housing = pd.read_excel(inputs+'HIES 2013-14 Housing Data.xlsx',sheetname='Sheet1').set_index('HHID').dropna(how='all')[['Constructionofouterwalls','Conditionofouterwalls']]
        
        df_poor = pd.read_excel(inputs+'HIES 2013-14 Demographic Data.xlsx',sheetname='Sheet1').set_index('HHID').dropna(how='all')['Poor']
        df_poor = df_poor[~df_poor.index.duplicated(keep='first')]

        df = pd.concat([df,df_housing,df_poor],axis=1).reset_index().set_index('Division')
        return df

    else: return None


def get_df2(myC):

    if myC == 'PH':
        return pd.read_excel(inputs+'PSA_compiled.xlsx',skiprows=1)[['province','gdp_pc_pp','pop','shewp','shewr']].set_index('province')

    else: return None

def get_vul_curve(myC,struct):

    if myC == 'PH':
        return pd.read_excel(inputs+'vulnerability_curves_FIES.xlsx',sheetname=struct)[['desc','v']]

    if myC == 'FJ':
        df = pd.read_excel(inputs+'vulnerability_curves_Fiji.xlsx',sheetname=struct)[['desc','v']]
        return df

    else: return None

def get_hazard_df(myC,economy):

    if myC == 'PH': 
        df = get_AIR_data(inputs+'/Risk_Profile_Master_With_Population.xlsx','Loss_Results','Private','Agg').reset_index()
        df.columns = [economy,'hazard','rp','value_destroyed']
        return df
    
    if myC == 'FJ':
        df = pd.read_csv(inputs+'fj_tikina_aal.csv')[['TIKINA','PROVINCE','TID','Total_AAL','Total_Valu']].set_index(['TIKINA','PROVINCE','TID']).sum(level='PROVINCE').reset_index()
        df.columns = [economy,'value_destroyed','total_value']
        df = df.set_index([df.Division.replace({'Nadroga':'Nadroga-Navosa'})])        
        return df

    else: return None

def get_poverty_line(myC):
    
    if myC == 'PH':
        return 22302.6775#21240.2924

    if myC == 'FJ':
        # 55.12 per week for an urban adult
        # 49.50 per week for a rural adult
        # children under age 14 are counted as half an adult
        return 55.12*52. #this is for an urban adult
    

def get_subsistence_line(myC):
    
    if myC == 'PH':
        return 14832.0962*(22302.6775/21240.2924)
    
    else: return None

def get_to_USD(myC):

    if myC == 'PH': return 50.0
    elif myC == 'FJ': return 0.48
    else: return 0.

def get_scale_fac(myC):
    
    if myC == 'PH': return [1.E6,' [Millions]']
    elif myC == 'FJ': return [1.E3,' [Thousands]']
    else: return [1,'']

