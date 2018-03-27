# -*- coding: utf-8 -*-
import pandas as pd
import friendlysam as fs
import partlib as pl
from matplotlib import pyplot as plt


def is_producer(part, resource):
    if hasattr(part, 'production'):
        return resource in part.production

def is_consumer(part, resource):
    if hasattr(part, 'consumption'):
        return resource in part.consumption

def is_accumulator(part, resource):
    if hasattr(part, 'accumulation'):
        return resource in part.accumulation


def save_results(year, scenario, results, output_data_path):
    '''Export data to excel'''
     
    try:   
        writer = pd.ExcelWriter(output_data_path+'output_%s_%s.xlsx' %(year,scenario), engine='xlsxwriter')
        for sheet_name, data in results.items():
            data.to_excel(writer, sheet_name='%s'%sheet_name)
        writer.save()

    except PermissionError:
        time=str(datetime.datetime.now().time())
        time=time.replace(":", ".")
        writer= pd.ExcelWriter(output_data_path+'output_%s_%s_%s.xlsx' %(year,scenario,time), engine='xlsxwriter')
        for sheet_name, data in results.items():
            data.to_excel(writer, sheet_name='%s'%sheet_name)
        writer.save()

    return None

def get_production(parts, resource, times):
    producers =  [p for p in parts if (is_producer(p, resource) and not isinstance(p, fs.Cluster))]
    production = dict()

    for p in producers:
        production[p.name] = fs.get_series(p.production[resource], times)
    production = pd.DataFrame.from_dict(production)
    return production

def get_consumption(parts, resource, times):
    consumers = [p for p in parts if (is_consumer(p, resource) and not isinstance(p, fs.Cluster))]
    consumption = dict()
    for p in consumers:
        consumption[p.name] = fs.get_series(p.consumption[resource], times)
    consumption = pd.DataFrame.from_dict(consumption)
    return consumption

def get_accumulation(parts, resource, times):
    accumulators = [p for p in parts if (is_accumulator(p, resource) and isinstance(p, pl.Accumulator))]
    accumulation = dict()
    for p in accumulators:
        accumulation[p.name] = fs.get_series(p.volume, times)
    accumulation = pd.DataFrame.from_dict(accumulation)
    return accumulation
    


def process_results(model, output_data_path= None):
    """ Takes a model object, extracts and returns relevant information.
    If an output_data_path is supplied, writes the data. 
    If no data path is provided it is only returned
    """
    times = model.times_between(model.time_start,model.time_end)

    heat_produced = get_production(model.descendants, pl.Resources.heat, times)
    heat_consumed = get_consumption(model.descendants, pl.Resources.heat, times)
    heat_accumulated = get_accumulation(model.descendants, pl.Resources.heat, times)

    power_produced = get_production(model.descendants, pl.Resources.power, times)   
    power_consumed = get_consumption(model.descendants, pl.Resources.power, times)
    power_accumulated = get_accumulation(model.descendants, pl.Resources.power, times)

    

    data = {'heat_producers': heat_produced,
            'power_producers': power_produced,
            'heat_consumers': heat_consumed,
            'power_consumers': power_consumed,
            'heat_accumulators': heat_accumulated,
            'power_accumulators': power_accumulated}

    if output_data_path:
        save_results(year, scenario, data, output_data_path)
    
    return data

def display_results(data, save_figures = False):
    

    if 'heat_producers' in data.keys():
        p = data['heat_producers'].plot(kind='area', legend='reverse', lw=0, figsize=(8,8))
        p.get_legend().set_bbox_to_anchor((0.5, 1))
    
    if 'heat_accumulators' in data.keys():
        s = data['heat_accumulators'].plot(kind='area', legend='reverse', lw=0, figsize=(8,8))
        s.get_legend()

    plt.show()
    return None

"""
    def DisplayResult(self):
        from process_results import is_producer

        t_start = self._DEFAULT_PARAMETERS['t_start']
        t_end = self._DEFAULT_PARAMETERS['t_end']
        heat_producers = [p for p in self.m.descendants
                          if is_producer(p, pl.Resources.heat) and
                          not isinstance(p, fs.Cluster)]
        
        times = self.m.times_between(t_start, t_end)
        
        heat = {p.name: fs.get_series(p.production[pl.Resources.heat], times) for p in heat_producers}
        heat = pd.DataFrame.from_dict(heat)
        other = ['Boiler A',
                 'Boiler B',
                 'Boiler C',
                 'Boiler D']
        heat['Other'] = heat[other].sum(axis=1)
        for key in other:
            del heat[key]

        order = ['Waste Incinerator',
                 'CHP A',
                 'CHP B',
                 'Other']
        heat = heat[order]
        heat *= pd.Timedelta('1h') / heat.index.freq
        print(heat)

        storage_times = self.m.times_between(t_start+pd.Timedelta('2h'), t_end)
        storage = [p for p in self.m.descendants if isinstance(p, pl.Accumulator)]
        stored_energy = {p.name: fs.get_series(p.volume, storage_times) for p in storage}
        stored_energy = pd.DataFrame.from_dict(stored_energy)

        p = heat.plot(kind='area', legend='reverse', lw=0, figsize=(8,8))
        p.get_legend().set_bbox_to_anchor((0.5, 1))
        s = stored_energy.plot(kind='area', legend='reverse', lw=0, figsize=(8,8))
        s.get_legend().set_bbox_to_anchor((0.5, 1))
        plt.show()

    def GetHeatLoad(self, p_equipment):
        heat_producers = [p for p in self.m.descendants
                          if is_producer(p, pl.Resources.heat) and not
                          isinstance(p, fs.Cluster)]

        times = self.m.times_between(t_start, t_end)

        heat = {p.name: fs.get_series(p.production[pl.Resources.heat], times)
                for p in heat_producers}
        heat = pd.DataFrame.from_dict(heat)

        heatLoadWithTimestamps = heat[p_equipment].to_dict()
        heatLoad = dict()
        for elem in heatLoadWithTimestamps:
            heatLoad[str(elem.to_pydatetime())] = heatLoadWithTimestamps[elem]

        return heatLoad

    def GetPowerLoad(self, p_equipment):
        power_producers = [p for p in self.m.descendants
                           if is_producer(p, Resources.power) and
                           not isinstance(p, fs.Cluster)]

        times = self.m.times_between(self.t0, self.t_end)

        power = {p.name: fs.get_series(p.production[Resources.power], times)
                 for p in power_producers}
        power = pd.DataFrame.from_dict(power)

        powerLoadWithTimestamps = power[p_equipment].to_dict()
        powerLoad = dict()
        for elem in powerLoadWithTimestamps:
            powerLoad[str(elem.to_pydatetime())] = powerLoadWithTimestamps[elem]

        return powerLoad

    def GetNaturalGasConsumption(self, p_equipment):
        gas_consummers = [p for p in self.m.descendants
                          if is_consumer(p, Resources.natural_gas) and
                          not isinstance(p, fs.Cluster)]

        times = self.m.times_between(self.t0, self.t_end)

        gas = {p.name: fs.get_series(p.consumption[Resources.natural_gas], times)
               for p in gas_consummers}
        gas = pd.DataFrame.from_dict(gas)

        gasLoadWithTimestamps = gas[p_equipment].to_dict()
        gasLoad = dict()
        for elem in gasLoadWithTimestamps:
            gasLoad[str(elem.to_pydatetime())] = gasLoadWithTimestamps[elem]

        return gasLoad

    def WriteLoadToCsv(self, pLoad, pPath, pFilename):
        writer = csv.DictWriter(open(pPath + '/' + pFilename, 'w'),
                                fieldnames=['Time', 'Load'])
        writer.writeheader()
        for elem in pLoad:
            writer.writerow({'Time': elem, 'Load': pLoad[elem]})

    def OutputResults(self, pPath):
        #  write time series
        self.WriteLoadToCsv(self.GetHeatLoad('Boiler A'), pPath, 'BoilerA_heat.csv')
        self.WriteLoadToCsv(self.GetHeatLoad('Boiler B'), pPath, 'BoilerB_heat.csv')
        self.WriteLoadToCsv(self.GetHeatLoad('Boiler C'), pPath, 'BoilerC_heat.csv')
        self.WriteLoadToCsv(self.GetHeatLoad('Boiler D'), pPath, 'BoilerD_heat.csv')
        self.WriteLoadToCsv(self.GetHeatLoad('CHP A'), pPath, 'CHPA_heat.csv')
        self.WriteLoadToCsv(self.GetHeatLoad('CHP B'), pPath, 'CHPB_heat.csv')
        self.WriteLoadToCsv(self.GetHeatLoad('Waste Incinerator'), pPath, 'Waste_heat.csv')
        self.WriteLoadToCsv(self.GetPowerLoad('CHP A'), pPath, 'CHPA_power.csv')
        self.WriteLoadToCsv(self.GetPowerLoad('CHP B'), pPath, 'CHPB_power.csv')
        self.WriteLoadToCsv(self.GetNaturalGasConsumption('CHP A'), pPath, 'CHPA_gas.csv')
        self.WriteLoadToCsv(self.GetNaturalGasConsumption('CHP B'), pPath, 'CHPB_gas.csv')
        self.WriteLoadToCsv(self.GetNaturalGasConsumption('Boiler A'), pPath, 'BoilerA_gas.csv')
        self.WriteLoadToCsv(self.GetNaturalGasConsumption('Boiler B'), pPath, 'BoilerB_gas.csv')
        self.WriteLoadToCsv(self.GetNaturalGasConsumption('Boiler C'), pPath, 'BoilerC_gas.csv')
        self.WriteLoadToCsv(self.GetNaturalGasConsumption('Boiler D'), pPath, 'BoilerD_gas.csv')

        #  write sums for the whole simulation
        writer = open(pPath + '/KPIs.csv', 'w')
        writer.write("DeliveredGas,ExportedHeat,ExportedPower\n")
        print(self.TotalDeliveredGas())
        print(self.TotalExportedHeat())
        print(self.TotalExportedPower())
        writer.write(str(self.TotalDeliveredGas())+","+str(self.TotalExportedHeat())+","+str(self.TotalExportedPower())+"\n")
        writer.close()

    def TotalDeliveredGas(self):
        res = 0
        for equipment in ['Boiler A', 'Boiler B', 'Boiler C',
                          'Boiler D', 'CHP A', 'CHP B']:
            res += sum(self.GetNaturalGasConsumption(equipment).values())
        return res

    def TotalExportedHeat(self):
        res = 0
        for equipment in ['Boiler A', 'Boiler B', 'Boiler C',
                          'Boiler D', 'CHP A', 'CHP B', 'Waste Incinerator']:
            res += sum(self.GetHeatLoad(equipment).values())
        return res

    def TotalExportedPower(self):
        res = 0
        for equipment in ['CHP A', 'CHP B', 'Waste Incinerator']:
            res += sum(self.GetPowerLoad(equipment).values())
        return res
    """

if __name__ == '__main__':
    pass
