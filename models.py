# -*- coding: utf-8 -*-

import logging
logger = logging.getLogger(__name__)

from itertools import chain, product

import friendlysam as fs
from friendlysam.compat import ignored

class DispatchModel(fs.Part):
    """docstring for MyopicDispatchModel"""
    def __init__(self, t_start=None, t_end=None, time_unit=None, name=None, require_cost=True):
        super().__init__(name=name)
        self.time_end = t_end
        self.step = time_unit
        self.time = t_start
        self.require_cost = require_cost
    
    def state_variables(self, t):
        return tuple()

    def cost(self, t):
        return 0

    def solve(self):
        
        opt_times = self.times_between(self.time, self.time_end)

        parts = self.descendants

        if self.require_cost is True:
            cost_contributors = parts
        else:
            cost_contributors = filter(self.require_cost, parts)
        running_cost = fs.Sum(p.cost(t) for p, t in product(cost_contributors, opt_times))

        investment_cost = fs.Sum(p.investment_cost for p in parts if ('investment_cost' in dir(p)))    

        system_cost = fs.Add(running_cost, investment_cost)

        problem = fs.Problem()
        problem.objective = fs.Minimize(system_cost)
        problem += (p.constraints.make(t) for p, t in product(parts, opt_times))

        solver = fs.get_solver()
        solution = solver.solve(problem)
        for p, t in product(parts, self.iter_times_between(self.time, self.time_end)):
            for v in p.state_variables(t):
                v.take_value(solution)

        for p in parts:
            if 'static_variables' in dir(p):
                for v in p.static_variables:
                    v.take_value(solution)              