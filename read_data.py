# -*- coding: utf-8 -*-
import pandas as pd
import partlib as pl

def read_data(file_name=None):
    '''Read the data from Excel and save it in a dictionary'''
    if not file_name:
        file_name = "scenario_data_test.xlsx"
    """
    #This creates two dataframes, one with data for scenario 2030 and the other from 2050
    scenario_2030 = pd.read_excel(file_name, sheet_name='2030')
    scenario_2050 = pd.read_excel(file_name, sheet_name='2050')
    description = pd.read_excel(file_name, sheet_name='description')
    costs_2030 = pd.read_excel(file_name, sheet_name='costs_2030')
    costs_2050 = pd.read_excel(file_name, sheet_name='costs_2050')
    lifespan = pd.read_excel(file_name, sheet_name='lifespan')
    """
    #inv_2030=pd.read_excel(file_name, sheet_name='inv_2030')
    #inv_2050=pd.read_excel(file_name, sheet_name='inv_2050')

    """Data for 2030"""
    input_parameters_2030= pd.read_excel(file_name, sheet_name='2030_parameters').to_dict()
    BAU_2030=pd.read_excel(file_name, sheet_name='2030_BAU').to_dict() 
    Max_RES_2030=pd.read_excel(file_name, sheet_name='2030_Max_RES').to_dict()
    Max_DH_2030=pd.read_excel(file_name, sheet_name='2030_Max_DH').to_dict()
    Max_Retrofit_2030=pd.read_excel(file_name, sheet_name='2030_Max_Retrofit').to_dict()
    Trade_off_2030=pd.read_excel(file_name, sheet_name='2030_Trade_off').to_dict()
    Trade_off_CO2_2030=pd.read_excel(file_name, sheet_name='2030_Trade_off_CO2').to_dict()
    
    """Data for 2050"""
    input_parameters_2050= pd.read_excel(file_name, sheet_name='2050_parameters').to_dict()
    BAU_2050=pd.read_excel(file_name, sheet_name='2050_BAU').to_dict()
    Max_RES_2050=pd.read_excel(file_name, sheet_name='2050_Max_RES').to_dict()
    Max_DH_2050=pd.read_excel(file_name, sheet_name='2050_Max_DH').to_dict()
    Max_Retrofit_2050=pd.read_excel(file_name, sheet_name='2050_Max_Retrofit').to_dict()
    Trade_off_2050=pd.read_excel(file_name, sheet_name='2050_Trade_off').to_dict()
    Trade_off_CO2_2050=pd.read_excel(file_name, sheet_name='2050_Trade_off_CO2').to_dict()
    
    #This puts the two dataframes into one dictionary, with "subdictionaries" for 2030 and 2050.
    #data = {'2030':scenario_2030, '2050':scenario_2050, 'description':description, 
    #'costs_2030':costs_2030, 'costs_2050':costs_2050, 'lifespan': lifespan}
    data = {'2030_input_parameters': input_parameters_2030, '2030_BAU': BAU_2030, '2030_Max_RES': Max_RES_2030,
    '2030_Max_DH': Max_DH_2030, '2030_Max_Retrofit': Max_Retrofit_2030, '2030_Trade_off': Trade_off_2030, 
    '2030_Trade_off_CO2': Trade_off_CO2_2030, 
    '2050_input_parameters': input_parameters_2050, '2050_BAU': BAU_2050, '2050_Max_RES': Max_RES_2050,
    '2050_Max_DH': Max_DH_2050, '2050_Max_Retrofit': Max_Retrofit_2050, '2050_Trade_off': Trade_off_2050, 
    '2050_Trade_off_CO2': Trade_off_CO2_2050 } #'inv_2030': inv_2030, 'inv_2050': inv_2050,  }
    
    from partlib import Resources
    resources = {
        'biomass': Resources.biomass,
        'heat': Resources.heat,
        'natural_gas': Resources.natural_gas,
        'waste': Resources.waste
    }

    for scenario_name, scenario_data in data.copy().items():
        for unit, unit_specs in scenario_data.items():
            for spec_name, spec_value in unit_specs.items():
                if spec_name == 'resource':
                    if spec_value in resources.keys() :
                        scenario_data[unit][spec_name] = resources[spec_value]
                if spec_value == 'None':
                    scenario_data[unit][spec_name] = None
        data[scenario_name] = scenario_data
    return data



if __name__ == '__main__':
    pass