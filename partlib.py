# -*- coding: utf-8 -*-
import logging
import numbers
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
    heating_oil = 4
    bio_oil = 5
    wood_chips = 6
    wood_pellets = 7
    waste = 8


class Boiler(fs.Node):
    """docstring for Boiler"""

    def __init__(self, fuel=None, taxation=None, Fmax=None, eta=None, running_cost=None, max_capacity=None, **kwargs):
        super().__init__(**kwargs)

        with fs.namespace(self):
            F = fs.VariableCollection(lb=0, ub=Fmax, name='F')
            cap = fs.Variable(lb=0, ub=max_capacity, name='cap')
        self.cap = cap
        
        self.consumption[fuel] = F
        self.production[Resources.heat] = lambda t: eta * F(t)
        self.constraints += self.max_production

        self.cost = lambda t: self.consumption[fuel](t) * running_cost
        self.invest =  cap * 1

        self.static_variables = {cap}
        self.state_variables = lambda t: {F(t)}

    def max_production(self, t):
        return fs.LessEqual(self.production[Resources.heat](t), self.cap)

class Accumulator(fs.Node):
    def __init__(self, resource, max_flow, max_energy,
                 loss_factor, name=None, **kwargs):
        super().__init__(**kwargs)
        with fs.namespace(self):
            self.volume = fs.VariableCollection(lb=0,
                                                ub=max_energy,
                                                name='Storage')

        self.resource = resource
        self.consumption[self.resource] = lambda t: loss_factor * self.volume(t)
        self.max_flow = max_flow
        self.cost = lambda t: 0
        self.state_variables = lambda t: {self.volume(t)}

        self.accumulation[self.resource] = self.compute_accumulation
        self.constraints += self.max_change_constraints

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

    def __init__(self, fuel=None, alpha=None, eta=None, Fmax=None, taxation=None, running_cost=None, max_capacity=None, annuity=None, **kwargs):        
        super().__init__(**kwargs)

        with fs.namespace(self):
            F = fs.VariableCollection(lb=0, ub=Fmax, name='F')
            cap = fs.Variable(lb=0, ub=max_capacity, name='cap')
        self.cap = cap
        
        self.consumption[fuel] = F
        self.production[Resources.heat] = lambda t: F(t) * eta / (alpha + 1)
        self.production[Resources.power] = lambda t: alpha * F(t) * eta / (alpha + 1)
        self.constraints += self.max_production

        self.cost = lambda t: F(t) * running_cost  #_CHP_cost_func(self, taxation, fuel)
        self.invest = cap * 10
        
        self.static_variables =  {cap}
        self.state_variables = lambda t: {F(t)}
    
    def max_production(self, t):
        return fs.LessEqual(self.production[Resources.heat](t), self.cap)


class LinearSlowCHP(fs.Node):
    """docstring for LinearSlowCHP"""

    def __init__(self, start_steps=None, fuel=None, alpha=None, eta=None,
                 Fmin=None, Fmax=None, taxation=None, **kwargs):
        super().__init__(**kwargs)

        mode_names = ('off', 'starting', 'on')
        with fs.namespace(self):
            modes = OrderedDict(
                (n, VariableCollection(name=n, domain=fs.Domain.binary)) for n in mode_names)
            F_on = VariableCollection(lb=0, name='F_on')  # Fuel use if on

        self.consumption[fuel] = lambda t: F_on(t) + modes['starting'](t) * Fmin
        self.production[Resources.heat] = lambda t: F_on(t) * eta / (alpha + 1)
        self.production[Resources.power] = lambda t: alpha * self.production[Resources.heat](t)

        self.cost = _CHP_cost_func(self, taxation, fuel)

        on_or_starting = lambda t: modes['on'](t) + modes['starting'](t)
        def mode_constraints(t):
            yield Constraint(
                fs.Eq(fs.Sum(m(t) for m in modes.values()), 1), desc='Exactly one mode at a time')

            if start_steps > 0:
                recent_sum = fs.Sum(on_or_starting(tau) for tau in self.iter_times(t, -(start_steps+1), 0))
                yield Constraint(
                    modes['on'](t) <= recent_sum / start_steps,
                    desc="'on' mode is only allowed after start_steps in 'on' and 'starting'")

            yield Constraint(
                self.consumption[fuel](t) <= Fmax * modes['on'](t) + Fmin * modes['starting'](t),
                desc='Max fuel use')

        self.constraints += mode_constraints

        self.state_variables = lambda t: {F_on(t)} | {var(t) for var in modes.values()}


class HeatPump(fs.Node):
    """docstring for HeatPump"""

    def __init__(self, COP=None, max_capacity=None, Qmax=None, taxation=None, **kwargs):
        super().__init__(**kwargs)

        with fs.namespace(self):
            Q = fs.VariableCollection(lb=0, ub=Qmax, name='Q')
            cap = fs.Variable(lb=0, ub=max_capacity, name='cap')
        self.cap = cap   

        self.production[Resources.heat] = Q
        self.consumption[Resources.power] = lambda t: Q(t) / COP
        self.constraints += self.max_production
        #power_cons_tax = taxation('consumption', Resources.power)
        #Instead of using power_cons_tax in the lambda function I added 10 as a fixed cost
        self.cost = lambda t: self.consumption[Resources.power](t) * 10
        self.invest = cap * 10

        self.static_variables =  {cap}
        self.state_variables = lambda t: {Q(t)}

    def max_production(self, t):
        return fs.LessEqual(self.production[Resources.heat](t), self.cap)

class SolarPV(fs.Node):
    def __init__(self, G=None, T=None, max_capacity = None, capacity = None, eta=None, taxation=None, running_cost=0, annuity=None,  **kwargs):        
        super().__init__(**kwargs)
          
        if max_capacity:  
            with fs.namespace(self):              
                PV_cap = fs.Variable(lb=0, ub=max_capacity, name='PV_cap')
                self.static_variables =  {PV_cap}
        else:
            with fs.namespace(self): 
                PV_cap = capacity

        self.PV_cap=PV_cap

        #self.PV_cap = PV_cap   

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
                prod = PV_cap* (G[t]*(1 + c1*math.log10(G[t]) + c2*(math.log10(G[t]))**2 + c3*T[t] + c4*T[t]*math.log10(G[t]) + c5*T[t]*(math.log10(G[t]))**2 + c6*(T[t])**2))
            return prod
        
        self.production[Resources.power] =lambda t: prod(t)
        self.state_variables = lambda t: {}
        
        #self.constraints += self.max_production

        self.cost = lambda t: 0
        self.invest = 0

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

    def __init__(self, resource=None, capacity=None, price=None, **kwargs):
        super().__init__(**kwargs)

        with fs.namespace(self):
            quantity = VariableCollection(lb=0, ub=capacity, name='import')

        self.production[resource] = quantity

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
        