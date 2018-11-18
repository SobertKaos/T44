# -*- coding: utf-8 -*-
import os
import pdb
import xlsxwriter
import pandas as pd

PEF_waste = 0
PEF_natural_gas = 1
All_PEF_power = {
    2030: {
        "Italy pessimistic": 2.05,
        "Italy medium": 1.64,
        "ENPAC": 0
        },
    2050: {
        "Italy pessimistic": 2.17,
        "Italy medium": 1.72,
        "ENPAC": 0
    } 
}

scenario_keys = {
    "2030_BAU_Italy medium_CO2_cost": "2030 BAU Italy medium CO2 cost",
    "2030_BAU_Italy medium_No_CO2_cost": "2030 BAU Italy medium NO CO2 cost",
    "2030_BAU_Italy pessimistic_CO2_cost": "2030 BAU Italy pessimistic CO2 cost",
    "2030_BAU_Italy pessimistic_No_CO2_cost": "2030 BAU  Italy pessimistic NO CO2 cost",
    "2030_BAU_NP_CO2_cost": "2030 BAU NP CO2 cost",
    "2030_BAU_NP_No_CO2_cost": "2030 BAU NP NO CO2 cost",
    "2030_BAU_SD_CO2_cost": "2030 BAU SD CO2 cost",
    "2030_BAU_SD_No_CO2_cost": "2030 BAU SD NO CO2 cost",
    "2030_Max_DH_Italy medium_CO2_cost": "2030 Max DH Italy medium CO2 cost",
    "2030_Max_DH_Italy medium_No_CO2_cost": "2030 Max DH Italy medium NO CO2 cost",
    "2030_Max_DH_Italy pessimistic_CO2_cost": "2030 Max DH  Italy pessimistic CO2 cost",
    "2030_Max_DH_Italy pessimistic_No_CO2_cost": "2030 Max DH  Italy pessimistic NO CO2 cost",
    "2030_Max_DH_NP_CO2_cost": "2030 Max DH NP CO2 cost",
    "2030_Max_DH_NP_No_CO2_cost": "2030 Max DH NP NO CO2 cost",
    "2030_Max_DH_SD_CO2_cost": "2030 Max DH SD CO2 cost",
    "2030_Max_DH_SD_No_CO2_cost": "2030 Max DH SD NO CO2 cost",
    "2030_Max_RES_Italy medium_CO2_cost": "2030 Max RES Italy medium CO2 cost",
    "2030_Max_RES_Italy medium_No_CO2_cost": "2030 Max RES Italy medium NO CO2 cost",
    "2030_Max_RES_Italy pessimistic_CO2_cost": "2030 Max RES  Italy pessimistic CO2 cost",
    "2030_Max_RES_Italy pessimistic_No_CO2_cost": "2030 Max RES  Italy pessimistic NO CO2 cost",
    "2030_Max_RES_NP_CO2_cost": "2030 Max RES NP CO2 cost",
    "2030_Max_RES_NP_No_CO2_cost": "2030 Max RES NP NO CO2 cost",
    "2030_Max_RES_SD_CO2_cost": "2030 Max RES SD CO2 cost",
    "2030_Max_RES_SD_No_CO2_cost": "2030 Max RES SD NO CO2 cost",
    "2030_Max_Retrofit_Italy medium_CO2_cost": "2030 Max Retrofit Italy medium CO2 cost",
    "2030_Max_Retrofit_Italy medium_No_CO2_cost": "2030 Max Retrofit Italy medium NO CO2 cost",
    "2030_Max_Retrofit_Italy pessimistic_CO2_cost": "2030 Max Retrofit Italy pessimistic CO2 cost",
    "2030_Max_Retrofit_Italy pessimistic_No_CO2_cost": "2030 Max Retrofit Italy pessimistic NO CO2 cost",
    "2030_Max_Retrofit_NP_CO2_cost": "2030 Max Retrofit NP CO2 cost",
    "2030_Max_Retrofit_NP_No_CO2_cost": "2030 Max Retrofit NP NO CO2 cost",
    "2030_Max_Retrofit_SD_CO2_cost": "2030 Max Retrofit SD CO2 cost",
    "2030_Max_Retrofit_SD_No_CO2_cost": "2030 Max Retrofit SD NO CO2 cost",
    "2030_Trade_off_Italy medium_CO2_cost": "2030 Trade off Italy medium CO2 cost",
    "2030_Trade_off_Italy medium_No_CO2_cost": "2030 Trade off Italy medium NO CO2 cost",
    "2030_Trade_off_Italy pessimistic_CO2_cost": "2030 Trade off Italy pessimistic CO2 cost",
    "2030_Trade_off_Italy pessimistic_No_CO2_cost": "2030 Trade off Italy pessimistic NO CO2 cost",
    "2030_Trade_off_NP_CO2_cost": "2030 Trade off NP CO2 cost",
    "2030_Trade_off_NP_No_CO2_cost": "2030 Trade off NP NO CO2 cost",
    "2030_Trade_off_SD_CO2_cost": "2030 Trade off SD CO2 cost",
    "2030_Trade_off_SD_No_CO2_cost": "2030 Trade off SD NO CO2 cost",
    "2050_BAU_Italy medium_CO2_cost": "2050 BAU Italy medium CO2 cost",
    "2050_BAU_Italy medium_No_CO2_cost": "2050 BAU Italy medium NO CO2 cost",
    "2050_BAU_Italy pessimistic_CO2_cost": "2050 BAU Italy pessimistic CO2 cost",
    "2050_BAU_Italy pessimistic_No_CO2_cost": "2050 BAU  Italy pessimistic NO CO2 cost",
    "2050_BAU_NP_CO2_cost": "2050 BAU NP CO2 cost",
    "2050_BAU_NP_No_CO2_cost": "2050 BAU NP NO CO2 cost",
    "2050_BAU_SD_CO2_cost": "2050 BAU SD CO2 cost",
    "2050_BAU_SD_No_CO2_cost": "2050 BAU SD NO CO2 cost",
    "2050_Max_DH_Italy medium_CO2_cost": "2050 Max DH Italy medium CO2 cost",
    "2050_Max_DH_Italy medium_No_CO2_cost": "2050 Max DH Italy medium NO CO2 cost",
    "2050_Max_DH_Italy pessimistic_CO2_cost": "2050 Max DH  Italy pessimistic CO2 cost",
    "2050_Max_DH_Italy pessimistic_No_CO2_cost": "2050 Max DH  Italy pessimistic NO CO2 cost",
    "2050_Max_DH_NP_CO2_cost": "2050 Max DH NP CO2 cost",
    "2050_Max_DH_NP_No_CO2_cost": "2050 Max DH NP NO CO2 cost",
    "2050_Max_DH_SD_CO2_cost": "2050 Max DH SD CO2 cost",
    "2050_Max_DH_SD_No_CO2_cost": "2050 Max DH SD NO CO2 cost",
    "2050_Max_RES_Italy medium_CO2_cost": "2050 Max RES Italy medium CO2 cost",
    "2050_Max_RES_Italy medium_No_CO2_cost": "2050 Max RES Italy medium NO CO2 cost",
    "2050_Max_RES_Italy pessimistic_CO2_cost": "2050 Max RES  Italy pessimistic CO2 cost",
    "2050_Max_RES_Italy pessimistic_No_CO2_cost": "2050 Max RES  Italy pessimistic NO CO2 cost",
    "2050_Max_RES_NP_CO2_cost": "2050 Max RES NP CO2 cost",
    "2050_Max_RES_NP_No_CO2_cost": "2050 Max RES NP NO CO2 cost",
    "2050_Max_RES_SD_CO2_cost": "2050 Max RES SD CO2 cost",
    "2050_Max_RES_SD_No_CO2_cost": "2050 Max RES SD NO CO2 cost",
    "2050_Max_Retrofit_Italy medium_CO2_cost": "2050 Max Retrofit Italy medium CO2 cost",
    "2050_Max_Retrofit_Italy medium_No_CO2_cost": "2050 Max Retrofit Italy medium NO CO2 cost",
    "2050_Max_Retrofit_Italy pessimistic_CO2_cost": "2050 Max Retrofit Italy pessimistic CO2 cost",
    "2050_Max_Retrofit_Italy pessimistic_No_CO2_cost": "2050 Max Retrofit Italy pessimistic NO CO2 cost",
    "2050_Max_Retrofit_NP_CO2_cost": "2050 Max Retrofit NP CO2 cost",
    "2050_Max_Retrofit_NP_No_CO2_cost": "2050 Max Retrofit NP NO CO2 cost",
    "2050_Max_Retrofit_SD_CO2_cost": "2050 Max Retrofit SD CO2 cost",
    "2050_Max_Retrofit_SD_No_CO2_cost": "2050 Max Retrofit SD NO CO2 cost",
    "2050_Trade_off_Italy medium_CO2_cost": "2050 Trade off Italy medium CO2 cost",
    "2050_Trade_off_Italy medium_No_CO2_cost": "2050 Trade off Italy medium NO CO2 cost",
    "2050_Trade_off_Italy pessimistic_CO2_cost": "2050 Trade off Italy pessimistic CO2 cost",
    "2050_Trade_off_Italy pessimistic_No_CO2_cost": "2050 Trade off Italy pessimistic NO CO2 cost",
    "2050_Trade_off_NP_CO2_cost": "2050 Trade off NP CO2 cost",
    "2050_Trade_off_NP_No_CO2_cost": "2050 Trade off NP NO CO2 cost",
    "2050_Trade_off_SD_CO2_cost": "2050 Trade off SD CO2 cost",
    "2050_Trade_off_SD_No_CO2_cost": "2050 Trade off SD NO CO2 cost"
    }


final_results = {
    "total CO2 kg": dict(),
    "primary energy MWh": dict(),
    "running costs EUR": dict(),
    "investment costs EUR": dict(),
    "investments": dict(),
    "total costs EUR": dict(),
    'CO2 emissions relative to base': dict(),
    'investment cost efficiency': dict()
}

def annuity(interest_rate, lifespan, investment_cost):
    k = interest_rate/(1-(1+interest_rate)**(-lifespan))
    r = investment_cost*k
    return r

def get_year_and_scenario(case_name):
    year = 2030 if "2030" in case_name else 2050
    if 'Italy pessimistic' in case_name:
        scenario = 'Italy pessimistic'
    elif 'Italy medium' in case_name:
        scenario = 'Italy medium'
    else:
        scenario = 'ENPAC'
    return year, scenario

def get_co2_cost_efficiency(base_case_total_costs, base_case_total_CO2, total_costs, total_CO2):
    delta_co2 = total_CO2 - base_case_total_CO2
    delta_cost = total_costs - base_case_total_costs
    try:
        cost_efficiency = delta_co2/delta_cost
    except ZeroDivisionError:
        cost_efficiency = 7777
    return cost_efficiency

def final_processor(total_results, output_path = None, base_case = None):
    if not base_case:
        base_case = '2030_BAU_Italy medium_No_CO2_cost'
    base_CO2 = total_results[base_case]['total cost and emissions']['total emissions [kg/year]']
    base_total_costs= total_results[base_case]['total cost and emissions']['running cost [EUR/year]']

    for case, result in total_results.items():
        case_name = scenario_keys[case]
        year, scenario = get_year_and_scenario(case_name)
        PEF_power = All_PEF_power[year][scenario]          

        total_CO2 = result['total cost and emissions']['total emissions [kg/year]']
        running_costs = result['total cost and emissions']['running cost [EUR/year]']

        total_PE = PEF_waste * result['import resources']['waste import']\
                 + PEF_power * (result['import resources']['power import'] - result['power_consumers']['power export'].sum())\
                 + PEF_natural_gas * result['import resources']['natural gas import']
        
        """ Get investment cost """
        if 'trade off' in case_name.lower():
            investment_costs = result['total cost and emissions']['investment cost [EUR/year]']
        else:
            investment_costs = 0
            for technology in result['input for scenario'].keys():
                if 'existing' in technology.lower():
                    pass
                else:
                    interest_rate = result['interest rate']
                    lifespan = result['input for scenario'][technology]['lifespan']
                    total_technology_investment_cost = result['input for scenario'][technology]['investment_cost']
                    if 'renovation' in technology.lower() :
                        "Deep renovation in non-trade off cases"
                        if "2030" in case_name:
                            total_technology_investment_cost = 76050075.6071256
                        else:
                             total_technology_investment_cost = 167708546.405733

                    technology_investment_cost= annuity(interest_rate, lifespan, total_technology_investment_cost)
                    investment_costs += technology_investment_cost
        if 'max dh' in case_name.lower():
            yearly_dh_grid_extension_cost = {2030: 0, 2050: 0}
            investment_costs += yearly_dh_grid_extension_cost[year]
        total_costs = investment_costs + running_costs
        cost_efficiency = get_co2_cost_efficiency(base_total_costs, base_CO2, total_costs, total_CO2)

        """ Collect results """
        final_results["total CO2 kg"][case_name] = total_CO2
        final_results["primary energy MWh"][case_name] = total_PE
        final_results["running costs EUR"][case_name] = running_costs
        final_results["investment costs EUR"][case_name] = investment_costs
        final_results["total costs EUR"][case_name] = total_costs
        final_results['CO2 emissions relative to base'][case_name] = total_CO2 / base_CO2
        final_results['investment cost efficiency'][case_name] = cost_efficiency
        
        if 'trade off' in case_name.lower():
            investments = result['invest or not']
            final_results['investments'][case_name] = investments        

    maximum_CO2_reduction = {'relative' : 1, "case": " "}
    if base_CO2:
        for case in final_results["total CO2 kg"].keys():
            if case in final_results['investments'].keys():
                continue
            relative_CO2 = final_results["total CO2 kg"][case] / base_CO2
            final_results['CO2 emissions relative to base'][case] = relative_CO2

            if relative_CO2 < maximum_CO2_reduction['relative']:
                maximum_CO2_reduction['case'] = case
                maximum_CO2_reduction['relative'] = relative_CO2
                    
    if output_path:
        "Write total results to excel"
        save_results_excel(final_results, output_path)
        pass

    return final_results

def save_results_excel(results, output_path):
    """Write the results to on excelfile for each year and scenario"""
    timestamp_now = pd.Timestamp.now()
    writer = pd.ExcelWriter(output_path+"Combined results {} {}-{}.xlsx".format(timestamp_now.date(), timestamp_now.hour, timestamp_now.minute), engine='xlsxwriter')
    for item in results.items():
        key=item[0]
        data=item[1]
        if isinstance(data, dict):
            output = pd.Series(data)
            output.to_excel(writer, sheet_name=key)
        else:
            output = pd.DataFrame(data)
            output.to_excel(writer, sheet_name=key)
    writer.save()
    writer.close()

    



if __name__ == '__main__':
    pass