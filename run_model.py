# -*- coding: utf-8 -*-

def annuity(interest_rate, lifespan, investment_cost):
    '''Calculate the annual cost of the investment'''

    k = interest_rate/(1-(1+interest_rate)**(-lifespan))
    r = investment_cost*k
    
    return r

def run_model(model, start_time, end_time):
    pass