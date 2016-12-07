# coding: utf-8
"""
Using Sensitivity Analysis to Interrogate Models
================================================
Will Usher, University of Oxford

Presented at UCL on:
- 10th December 2015
- 8th December 2016

Encodes a basic model of Vehicle to Grid (V2G) as developed by Kempton et al.
(2005).

Revenue = Max Power * Daily Capacity Payment * (Time Available/24)
          + Electricity Exported * Electricity Price
        = Max Power * Daily Capacity Payment * (Time Available/24)
          + Max Power * Time Available * Electricity Price

Alternatives:

Use a BEV for V2G overnight, although power is constrained by:
    1. need to charge vehicle
    2. size of battery
    3. size of connection
    4. requirements for range buffer
    5. distance driven per day

 Use a separate battery:
     1. charge during times of cheap electricity
     2. extra expense of purchasing battery
     3. size of connection is constrained

Max_Power = max(0, min(connection, available_energy / duration)

duration/24 * Max_Power * Capacity Payment
"""
import numpy as np

def max_vehicle_power(connector_power,
                      stored_energy,
                      distance_driven,
                      range_buffer,
                      dispatch_time,
                      driving_efficiency=4.025,
                      inverter_efficiency=0.93
                      ):
    """
    Compute the maximum electrical power output of a vehicle battery when
    connected to the electricity grid

    Arguments
    =========
    connector_power : float
        the power capacity of the connection to the grid
    stored_energy : float
        energy available as DC kWh to the inverter
    distance_driven : float
        distance driven (km) since energy storage full
    range_buffer : float
        minimum range required by the driver (km)
    driving_efficiency : float, default=4.025
        efficiency is measured in (km/kWh)
    inverter_efficiency : float
        electrical conversion efficiency of DC to AC inverter (93%)
    dispatch_time : float
        time over which the vehicle's stored energy is dispatched (hours)

    Returns
    =======
    float
        the maximum power in kW of a vehicle connected to the grid
    """
    maximum_vehicle_power = ((stored_energy - ((distance_driven + range_buffer)
                            / driving_efficiency)) * \
                            inverter_efficiency)  / dispatch_time

    return np.maximum(0, np.minimum(connector_power, maximum_vehicle_power))


def battery_lifetime(lifetime_cycles, total_energy_stored,
                     depth_of_discharge):
    """Compute the lifetime of a battery in energy terms

    Arguments
    =========

    lifetime_cycles
    total_energy_stored
        size of battery (kWh)
    depth_of_discharge
        the depth of discharge for which lifetime_cycles is defined
        (0 <= DoD <= 1)

    Returns
    =======
        battery_lifetime in energy terms - units: kWh"""

    lifetime = lifetime_cycles * total_energy_stored * depth_of_discharge
    return lifetime


def annualized_capital_cost(cost, discount_rate, lifetime):
    '''
    Arguments
    =========
    cost : float
        in GBP2015
    discount_rate : float
        %
    lifetime : float
        in years
    '''
    ann_cc = cost * (discount_rate / (1-(1+discount_rate)**-lifetime))
    return ann_cc


def cost_of_vehicle_to_grid(battery_capital_cost,
                            lifetime_cycles,
                            total_energy_stored,
                            depth_of_discharge,
                            purchased_energy_cost,
                            round_trip_efficiency,
                            energy_dispatched,
                            cost_of_v2g_equip,
                            discount_rate,
                            economic_lifetime):

    battery_life = battery_lifetime(lifetime_cycles,
                                    total_energy_stored,
                                    depth_of_discharge
                                    )

    degredation_cost = battery_capital_cost / battery_life

    cost_of_energy = (purchased_energy_cost / round_trip_efficiency)                         + degredation_cost

    annualised_capex = annualized_capital_cost(cost_of_v2g_equip,
                                               discount_rate,
                                               economic_lifetime)

    cost = (cost_of_energy * energy_dispatched) + annualised_capex

    return cost


def compute_profit(
        battery_size = 70, # kWh
        battery_unit_cost = 350, # £/kWh
        connector_power = 14, # kW
        lifetime_cycles = 2000,
        depth_of_discharge = 0.8,
        electricity_price = 0.1, # £/kWh - sell when its expensive
        purchased_energy_cost = 0.05, # £/kWh - buy when it's cheap
        capacity_price = 0.007, # £\kWh
        round_trip_efficiency = 0.73, # 73% efficiency grid-battery-grid
        cost_of_v2g_equip = 2000,
        discount_rate = 0.1, # 10%
        economic_lifetime = 10,
        distance_driven = 0, # km
        range_buffer = 0, # km
        ratio_dispatch_to_contract = 0.1,
        hours_connected_per_day = 18):
    """Computes the profit (revenue-cost) of using vehicle for regulation services

    Arguments
    =========

    Returns
    =======
    profit : float
        The difference between revenue and cost
    revenue
    cost

    """
    battery_capital_cost = battery_size * battery_unit_cost # 2015£

    stored_energy = battery_size * depth_of_discharge # kWh

    total_hours_connected = hours_connected_per_day * 365

    time_dispatched = total_hours_connected * ratio_dispatch_to_contract # hours

    power_available = max_vehicle_power(connector_power,
                                        stored_energy,
                                        distance_driven,
                                        range_buffer,
                                        hours_connected_per_day * \
                                        ratio_dispatch_to_contract,
                                        )

    energy_dispatched = ratio_dispatch_to_contract * \
                        power_available * time_dispatched

    revenue = capacity_price * power_available * total_hours_connected \
              + electricity_price * energy_dispatched

    cost = cost_of_vehicle_to_grid(battery_capital_cost,
                                   lifetime_cycles,
                                   battery_size,
                                   depth_of_discharge,
                                   purchased_energy_cost,
                                   round_trip_efficiency,
                                   energy_dispatched,
                                   cost_of_v2g_equip,
                                   discount_rate,
                                   economic_lifetime)

    profit = revenue - cost
    return profit, revenue, cost

if __name__ == "__main__":
    pass
