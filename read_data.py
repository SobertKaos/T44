# -*- coding: utf-8 -*-
import pandas as pd

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
    inv_2030=pd.read_excel(file_name, sheet_name='inv_2030')
    inv_2050=pd.read_excel(file_name, sheet_name='inv_2050')
    
    #This puts the two dataframes into one dictionary, with "subdictionaries" for 2030 and 2050.
    #data = {'2030':scenario_2030, '2050':scenario_2050, 'description':description, 
    #'costs_2030':costs_2030, 'costs_2050':costs_2050, 'lifespan': lifespan}
    data = {'inv_2030': inv_2030, 'inv_2050': inv_2050 }
    return data



if __name__ == '__main__':
    pass