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
    


class Boiler(fs.Node):
    """docstring for Boiler"""

    def __init__(self, fuel=None, taxation=None, Fmax=None, eta=None, 
                investment_cost = None, running_cost=1, max_capacity=None, **kwargs):
        super().__init__(**kwargs)

        with fs.namespace(self):
            F = fs.VariableCollection(lb=0, ub=Fmax, name='F')
            cap = fs.Variable(lb=0, ub=max_capacity, name='cap')
        
        self.test = {'Fmax':Fmax, 'eta': eta,
                    'running_cost' : running_cost, 'max_capacity': max_capacity}

        self.consumption[fuel] = F
        self.production[Resources.heat] = lambda t: eta * F(t)
        
        self.cost = lambda t: self.consumption[fuel](t) * running_cost

        self.state_variables = lambda t: {F(t)}

        self.cap = cap
        

        if max_capacity:
            self.constraints += self.max_production
            self.investment_cost = cap * investment_cost
            self.static_variables = {cap}
        else: 
            #self.investment_cost =  investment_cost
            self.static_variables = {}

    def max_production(self, t):
        return fs.LessEqual(self.production[Resources.heat](t), self.cap)

class Accumulator(fs.Node):
    def __init__(self, resource=None, max_flow=0, max_energy=0,
                 loss_factor=0, max_capacity=None, investment_cost=None,  **kwargs):
        super().__init__(**kwargs)
        with fs.namespace(self):
            self.volume = fs.VariableCollection(lb=0,
                                                ub=max_energy,
                                                name='Storage')
            #cap = fs.Variable(lb=0, ub=max_capacity, name='cap')
            
            inv = fs.Variable(domain=fs.Domain.binary)
        if max_capacity == 'None':
            max_capacity = None
        self.test={'resource':resource, 'max_flow':max_flow, 'max_energy': max_energy, 'loss_factor':loss_factor,
                    'max_capacity':max_capacity, 'investment_cost':investment_cost}
        
        self.resource = resource
        self.consumption[self.resource] = lambda t: loss_factor * self.volume(t)
        self.max_flow = max_flow
        self.cost = lambda t: 0
        self.state_variables = lambda t: {self.volume(t)}

        self.accumulation[self.resource] = self.compute_accumulation
        self.constraints += self.max_change_constraints

        self.max_capacity = max_capacity
        self.inv = inv
        

        if max_capacity:
            self.investment_cost = self.inv * self.max_capacity * investment_cost
            self.constraints += self.max_volume
            self.static_variables = {inv}
        else:
            #self.investment_cost = investment_cost
            self.static_variables = {}

        self.constraints += self.start_end_volume

    def start_end_volume(self, t):
        import pandas as pd
        return fs.Eq(self.volume(pd.Timestamp('2015-01-01 00:00')),
                     self.volume(pd.Timestamp('2015-01-02 00:00'))
                    )    

    def max_volume(self, t):
        return fs.LessEqual(self.volume(t), self.inv*self.max_capacity)

    def compute_accumulation(self, index):
        return self.volume(index) - self.volume(self.step_time(index, -1))

    def max_change_constraints(self, index):
        acc = self.accumulation[self.resource](index)
        max_flow = self.max_flow
        if max_flow is None:
            return ()
        return (
            fs.LessEqual(acc, max_flow),
            fs.LessEqual(-max_flow, acc))

def _CHP_cost_func(node, taxation, fuel):
    fuel_cons_tax = taxation('consumption', fuel, chp=True)
    power_prod_tax = taxation('production', Resources.power, fuel=fuel)
    return lambda t: (
        node.consumption[fuel](t) * fuel_cons_tax +
        node.production[Resources.power](t) * power_prod_tax)


class LinearCHP(fs.Node):
    """docstring for LinearCHP"""

    def __init__(self, fuel=None, alpha=None, eta=None, Fmax=None, taxation=None, 
                investment_cost=None, running_cost=0, max_capacity=None, **kwargs):        
        super().__init__(**kwargs)

        with fs.namespace(self):
            F = fs.VariableCollection(lb=0, ub=Fmax, name='F')
            cap = fs.Variable(lb=0, ub=max_capacity, name='cap')
        
        self.consumption[fuel] = F
        self.production[Resources.heat] = lambda t: F(t) * eta / (alpha + 1)
        self.production[Resources.power] = lambda t: alpha * F(t) * eta / (alpha + 1)

        self.cost = lambda t: F(t) * running_cost  #_CHP_cost_func(self, taxation, fuel)

        self.state_variables = lambda t: {F(t)}

        self.cap = cap
        

        if max_capacity:
            self.constraints += self.max_production
            self.investment_cost = cap * investment_cost
            self.static_variables =  {cap}
        else:
            self.static_variables = {}
    
    def max_production(self, t):
        return fs.LessEqual(self.production[Resources.heat](t), self.cap)


class LinearSlowCHP(fs.Node):
    """docstring for LinearSlowCHP"""

    def __init__(self, start_steps=None, fuel=None, alpha=None, eta=None, capacity=None,
                 Fmin=None, Fmax=None, max_capacity=None, taxation=None, investment_cost=None,**kwargs):
        super().__init__(**kwargs)

        mode_names = ('off', 'starting', 'on')
        with fs.namespace(self):
            modes = OrderedDict(
                (n, fs.VariableCollection(name=n, domain=fs.Domain.binary)) for n in mode_names)
            F_on = fs.VariableCollection(lb=0, name='F_on')  # Fuel use if on
            #cap = fs.Variable(lb=0, ub=max_capacity, name='cap')

            inv = fs.Variable(domain=fs.Domain.binary)

        self.test={'start_steps': start_steps, 'fuel':fuel, 'alpha':alpha, 'eta':eta, 'capacity':capacity, 
                    'Fmin':Fmin, 'Fmax':Fmax, 'max_capacity':max_capacity, 'taxation':taxation, 
                    'investment_cost':investment_cost}

        self.max_capacity= max_capacity
        self.inv = inv
        self.modes=modes

        if max_capacity:
            Fmin=0.2*max_capacity*(1 + alpha) / eta
            Fmax=max_capacity*(1 + alpha) / eta
            self.investment_cost =  inv * max_capacity * investment_cost
            self.constraints += self.max_production
            self.static_variables =  {inv}
        elif capacity:
            Fmin=0.2*capacity*(1 + alpha) / eta
            Fmax=capacity*(1 + alpha) / eta
            #self.investment_cost = investment_cost
            self.static_variables =  {}
        else:
            #self.investment_cost = investment_cost
            self.static_variables =  {}

        self.consumption[fuel] = lambda t: F_on(t) + modes['starting'](t) * Fmin
        self.production[Resources.heat] = lambda t: F_on(t) * eta / (alpha + 1)
        self.production[Resources.power] = lambda t: alpha * self.production[Resources.heat](t)

        self.cost = lambda t : self.consumption[fuel](t) * 1 #_CHP_cost_func(self, taxation, fuel)
    
        on_or_starting = lambda t: modes['on'](t) + modes['starting'](t)
        def mode_constraints(t):
            yield Constraint(
                fs.Eq(fs.Sum(m(t) for m in modes.values()), 1), desc='Exactly one mode at a time')

            if start_steps:
                recent_sum = fs.Sum(on_or_starting(tau) for tau in self.iter_times(t, -(start_steps+1), 0))
                yield Constraint(
                    modes['on'](t) <= recent_sum / start_steps,
                    desc="'on' mode is only allowed after start_steps in 'on' and 'starting'")

            yield Constraint(
                self.consumption[fuel](t) <= Fmax * modes['on'](t) + Fmin  * modes['starting'](t),
                desc='Max fuel use when on or starting')
            
            yield Constraint(
                self.consumption[fuel](t) >= Fmin * modes['on'](t),
                desc= 'Min fuel use when on') 
        
        self.constraints += mode_constraints

        
        self.state_variables = lambda t: {F_on(t)} | {var(t) for var in modes.values()}

    def max_production(self, t):
        return fs.LessEqual(self.production[Resources.heat](t), self.inv*self.max_capacity)


class HeatPump(fs.Node):
    """docstring for HeatPump"""

    def __init__(self, COP=None, max_capacity=None, Qmax=None, taxation=None, **kwargs):
        super().__init__(**kwargs)

        with fs.namespace(self):
            Q = fs.VariableCollection(lb=0, ub=Qmax, name='Q')
            cap = fs.Variable(lb=0, ub=max_capacity, name='cap')   

        self.production[Resources.heat] = Q
        self.consumption[Resources.power] = lambda t: Q(t) / COP
        #power_cons_tax = taxation('consumption', Resources.power)
        #Instead of using power_cons_tax in the lambda function I added 10 as a fixed cost
        self.cost = lambda t: self.consumption[Resources.power](t) * 10
        self.state_variables = lambda t: {Q(t)}

        self.cap = cap

        if max_capacity:
            self.constraints += self.max_production
            self.investment_cost = cap * 1
            self.static_variables =  {cap}
        else:
            self.static_variables =  {}

    def max_production(self, t):
        return fs.LessEqual(self.production[Resources.heat](t), self.cap)

class SolarPV(fs.Node):
    def __init__(self, G=None, T=None, max_capacity=None, capacity=None, taxation=None, 
                running_cost=0, investment_cost=None,  **kwargs):        
        super().__init__(**kwargs)

        self.test = {'max_capacity':max_capacity, 'capacity':capacity, 'taxation':taxation, 
                    'investment_cost':investment_cost}

        Gstc=1
        Tstc=25
        coef_temp_PV = 0.035
        G_irr = abs(G)/Gstc
        T_temp = (T + coef_temp_PV*G) - Tstc
        
        with fs.namespace(self):
            if max_capacity:              
                PV_cap = fs.Variable(lb=0, ub=max_capacity, name='PV_cap')
                self.static_variables =  {PV_cap}

                self.PV_cap = PV_cap
                self.investment_cost = PV_cap * investment_cost
                self.constraints += self.max_production
            else:
                with fs.namespace(self): 
                    PV_cap = capacity
                self.static_variables = {}

        c1 = -0.0177162
        c2 = -0.040289
        c3 = -0.004681
        c4 = 0.000148
        c5 = 0.000169
        c6 = 0.000005

        def prod(t):
            if G[t] == 0:
                prod = PV_cap * 0  
            else: 
                prod = prod = PV_cap* (G[t]*(1 + c1*math.log10(G[t]) + c2*(math.log10(G[t]))**2 + c3*T[t] + c4*T[t]*math.log10(G[t]) + c5*T[t]*(math.log10(G[t]))**2 + c6*(T[t])**2))
            return prod

        self.cost = lambda t: 0
        self.production[Resources.power] =lambda t: prod(t)
        self.state_variables = lambda t: {}

    def max_production(self, t):
        return fs.LessEqual(self.production[Resources.power](t), self.PV_cap)

class PipeLoss(fs.Node):
    """ docstring for PipeLoss """
    def __init__(self, loss_factor=0.11, **kwargs):
        self.resource = Resources.heat
        self.loss_factor = loss_factor
        self.consumption[self.resource] = self.compute_losses
        self.cost = lambda t: 0
        self.state_variables = lambda t: {}

    def compute_losses(self, index):
        inflow = fs.Sum(flow(index) for flow in self.inflows[self.resource])
        heat_loss = self.loss_factor * inflow
        return heat_loss


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

    def __init__(self, resource=None, capacity=None, price=None, **kwargs):
        super().__init__(**kwargs)

        with fs.namespace(self):
            quantity = VariableCollection(lb=0, ub=capacity, name='export of {}'.format(resource))

        self.consumption[resource] = quantity

        if isinstance(price, numbers.Real):
            self.cost = lambda t: -price * quantity(t)
        else:
            self.cost = lambda t: -price[t] * quantity(t)

        self.state_variables = lambda t: {quantity(t)}
