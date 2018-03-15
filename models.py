# -*- coding: utf-8 -*-

import logging
logger = logging.getLogger(__name__)

from itertools import chain, product

import friendlysam as fs
from friendlysam.compat import ignored

class DispatchModel(fs.Part):
    """docstring for MyopicDispatchModel"""
    def __init__(self, t0=None, t_end=None, step=None, name=None, require_cost=True):
        super().__init__(name=name)
        self.time_end = t_end
        self.step = step
        self.time = t0
        self.require_cost = require_cost
    
    def state_variables(self, t):
        return tuple()

    def cost(self, t):
        return 0

    def solve(self):
        
        opt_times = self.times_between(self.time, self.time_end)

        parts = self.descendants_and_self

        if self.require_cost is True:
            cost_contributors = parts
        else:
            cost_contributors = filter(self.require_cost, parts)
        system_cost = fs.Sum(p.cost(t) for p, t in product(cost_contributors, opt_times))

        problem = fs.Problem()
        problem.objective = fs.Minimize(system_cost)
        problem += (p.constraints.make(t) for p, t in product(parts, opt_times))

        solution = self.solver.solve(problem)
        
        for p, t in product(parts, self.iter_times_between(self.time, self.time_end)):
            for v in p.state_variables(t):
                v.take_value(solution)
