# -*- coding: utf-8 -*-
import logging
import numbers
import math
import friendlysam as fs
from itertools import chain, product
from collections import OrderedDict
from enum import Enum, unique
from friendlysam import Constraint, VariableCollection 
logger = logging.getLogger(__name__)


@unique
class Resources(Enum):
    natural_gas = 1
    power = 2
    heat = 3
    waste = 4
    biomass = 5
    CO2 = 6
    pvpower = 7
    


class Boiler(fs.Node):
    """docstring for Boiler"""

    def __init__(self, fuel=None, taxation=None, Fmax=None, eta=None, running_cost=0, hour = 1, **kwargs):
        super().__init__(**kwargs)

        with fs.namespace(self):
            F = fs.VariableCollection(lb=0, ub=Fmax, name='F')
        
        self.test = {'Fmax':Fmax, 'eta': eta,
                    'running_cost' : running_cost}

        self.consumption[fuel] = lambda t: F(t) / hour
        self.production[Resources.heat] = lambda t: eta * F(t) / hour
        self.cost = lambda t: self.consumption[fuel](t) * running_cost

        self.state_variables = lambda t: {F(t)}
        self.static_variables = {}
        

class Accumulator(fs.Node):
    def __init__(self, resource=None, max_flow=0, loss_factor=0, t_start = '2016-01-01', t_end='2016-01-02',
                 specific_investment_cost=0, running_cost=0, capacity_lb=0, capacity_ub = None, hour = 1, **kwargs):
        super().__init__(**kwargs)
        with fs.namespace(self):
            volume = fs.VariableCollection(lb=0, ub=None, name='Accumulator energy volume')
            capacity = fs.Variable(lb = capacity_lb, ub = capacity_ub, name = 'Capacity of accumulator')

        self.test={'resource':resource, 'max_flow':max_flow, 'loss_factor':loss_factor,
                    'max_capacity':capacity_ub, 'investment_cost':specific_investment_cost}
        
        self.t_start=t_start
        self.t_end=t_end
        self.resource = resource
        self.max_flow = max_flow / hour
        self.volume = volume
        self.cost = lambda t: 0
        self.investment_cost = capacity * specific_investment_cost

        self.state_variables = lambda t: {volume(t)}
        self.static_variables = {capacity}

        self.consumption[self.resource] = lambda t: loss_factor * volume(t)
        self.accumulation[self.resource] = self.compute_accumulation
        self.constraints += self.max_change_constraints
              
        self.constraints += lambda t: fs.LessEqual(volume(t), capacity) 
        self.constraints += lambda t: fs.Eq(volume(self.t_start), volume(self.t_end))
        self.constraints += lambda t: fs.Eq(self.accumulation[self.resource](self.t_start), 0)

    def compute_accumulation(self, index):
        return self.volume(index) - self.volume(self.step_time(index, -1))

    def max_change_constraints(self, index):
        acc = self.accumulation[self.resource](index)
        if self.max_flow is None:
            return ()
        return (
            fs.LessEqual(acc, self.max_flow),
            fs.LessEqual(-self.max_flow, acc))


class LinearCHP(fs.Node):
    """docstring for LinearCHP"""

    def __init__(self, fuel=None, alpha=None, eta=None, taxation=None, 
                specific_investment_cost=0, running_cost=0, capacity_lb=0, capacity_ub = None, hour= 1, **kwargs):        
        super().__init__(**kwargs)
        
        with fs.namespace(self):
            F = fs.VariableCollection(lb=0, ub=None, name='Fuel usage')
            capacity = fs.Variable(lb = capacity_lb, ub = capacity_ub,  name='CHP capacity')

        self.test={ 'fuel':fuel, 'alpha':alpha, 'eta':eta, 'taxation':taxation, 
                    'investment_cost':specific_investment_cost}

        self.consumption[fuel] = lambda t:  F(t)/hour
        self.production[Resources.heat] = lambda t: (F(t) * eta / (alpha + 1)) /hour
        self.production[Resources.power] = lambda t: (alpha * F(t) * eta / (alpha + 1)) /hour
        self.cost = lambda t: self.production[Resources.power](t) * running_cost
        self.investment_cost = capacity * specific_investment_cost

        self.state_variables = lambda t: {F(t)}
        self.static_variables = {capacity}
        self.constraints += lambda t: fs.LessEqual(F(t), capacity)


class SolarPV(fs.Node):
    def __init__(self, G=None, T=None, taxation=None, specific_investment_cost=0, running_cost=0,
                 capacity_lb=0, capacity_ub = None, hour= 1,  **kwargs):        
        super().__init__(**kwargs)

        self.G = G
        self.T = T

        self.test = {'max_capacity':capacity_ub, 'capacity':capacity_ub, 'taxation':taxation, 
                    'investment_cost':specific_investment_cost}

        with fs.namespace(self):
            capacity = fs.Variable(lb = capacity_lb, ub = capacity_ub, name='PV capacity')
            pv_power_capacity = fs.VariableCollection(lb = 0, ub = capacity_ub, name='PV production of export power')
            power_capacity = fs.VariableCollection(lb = 0, ub = capacity_ub, name = 'PV production of consumption power')

        
        self.cost = lambda t: running_cost * self.production[Resources.power](t)            
        self.investment_cost = capacity * specific_investment_cost
                
        self.state_variables = lambda t: {pv_power_capacity(t), power_capacity(t)} 
        self.static_variables =  {capacity}
        
        self.production[Resources.power] =lambda t: prod(t) * power_capacity(t) / hour
        self.production[Resources.pvpower] = lambda t: prod(t) * pv_power_capacity(t) / hour
        self.constraints += lambda t: fs.Eq(pv_power_capacity(t) + power_capacity(t), capacity)
        
        def prod(t):
            c1 = -0.0177162
            c2 = -0.040289
            c3 = -0.004681
            c4 = 0.000148
            c5 = 0.000169
            c6 = 0.000005

            Gstc=1000 #W/m2
            Tstc=25 #degrees C
            coef_temp_PV = 0.035

            if self.G[t] == 0:
                production_factor = 0  
            else: 
                G_c = abs(self.G[t]/(Gstc))
                T_c = (self.T[t] + coef_temp_PV * self.G[t]) -Tstc
                # Factor is W/installed W_peak, from: Norwood, Z., Nyholm, E., Otanicar, T. and Johnsson, F., 2014 . 
                # A geospatial comparison of distributed solar heat and power in Europe and the US . PloS one, 9(12), p.e112442
                factor = (G_c*(1 + c1*math.log10(G_c) + c2*(math.log10(G_c))**2 + c3*T_c + c4*T_c*math.log10(G_c) + c5*T_c*(math.log10(G_c))**2 + c6*(T_c)**2))
                production_factor = factor    
            return production_factor


class Import(fs.Node):
    """docstring for Import"""

    def __init__(self, resource=None, capacity=None, price=None, CO2_factor=None, **kwargs):
        super().__init__(**kwargs)

        with fs.namespace(self):
            quantity = VariableCollection(lb=0, ub=capacity, name='import')

        self.production[resource] = lambda t:  quantity(t)
        self.production[Resources.CO2] = lambda t: quantity(t) * CO2_factor

        if isinstance(price, numbers.Real):
            self.cost = lambda t: price * quantity(t)
        else:
            self.cost = lambda t: price[t] * quantity(t)

        self.state_variables = lambda t: {quantity(t)}


class Export(fs.Node):
    """ docstring for Export """

    def __init__(self, resource=None, capacity=None, price=0, **kwargs):
        super().__init__(**kwargs)

        with fs.namespace(self):
            quantity = VariableCollection(lb=0, ub=capacity, name='export of {}'.format(resource))

        self.consumption[resource] = quantity

        if isinstance(price, numbers.Real):
            self.cost = lambda t: -price * quantity(t)
        else:
            self.cost = lambda t: -price[t] * quantity(t)

        self.state_variables = lambda t: {quantity(t)}
