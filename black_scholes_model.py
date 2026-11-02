"""
Black-Scholes-Merton model for European options.

Inputs used throughout:
    stock_price               current price of the underlying asset
    strike_price              exercise price of the option
    time_to_expiry_in_years   remaining life of the option, in years
    risk_free_interest_rate   continuously compounded annual risk-free rate
    volatility                annualised standard deviation of returns

Greeks are returned per unit of each input:
    delta   per 1.00 change in stock price
    gamma   per 1.00 change in stock price (change in delta)
    theta   per year (divide by 365 for a daily figure)
    vega    per 1.00 change in volatility (divide by 100 for one percentage point)
"""

import math


# ---------------------------------------------------------------------
# Normal distribution
# ---------------------------------------------------------------------

def cumulative_normal_distribution(input_value):
    return 0.5 * (1 + math.erf(input_value / math.sqrt(2)))


def normal_probability_density(input_value):
    return math.exp(-0.5 * input_value ** 2) / math.sqrt(2 * math.pi)


# ---------------------------------------------------------------------
# Pricing
# ---------------------------------------------------------------------

def calculate_d1(stock_price, strike_price, time_to_expiry_in_years,
                 risk_free_interest_rate, volatility):
    log_moneyness = math.log(stock_price / strike_price)
    drift = (risk_free_interest_rate + 0.5 * volatility ** 2) * time_to_expiry_in_years
    return (log_moneyness + drift) / (volatility * math.sqrt(time_to_expiry_in_years))


def calculate_d2(stock_price, strike_price, time_to_expiry_in_years,
                 risk_free_interest_rate, volatility):
    d1_value = calculate_d1(stock_price, strike_price, time_to_expiry_in_years,
                            risk_free_interest_rate, volatility)
    return d1_value - volatility * math.sqrt(time_to_expiry_in_years)


def calculate_call_option_price(stock_price, strike_price, time_to_expiry_in_years,
                                risk_free_interest_rate, volatility):
    d1_value = calculate_d1(stock_price, strike_price, time_to_expiry_in_years,
                            risk_free_interest_rate, volatility)
    d2_value = calculate_d2(stock_price, strike_price, time_to_expiry_in_years,
                            risk_free_interest_rate, volatility)
    present_value_of_strike = strike_price * math.exp(-risk_free_interest_rate * time_to_expiry_in_years)

    return (stock_price * cumulative_normal_distribution(d1_value)
            - present_value_of_strike * cumulative_normal_distribution(d2_value))


def calculate_put_option_price(stock_price, strike_price, time_to_expiry_in_years,
                               risk_free_interest_rate, volatility):
    d1_value = calculate_d1(stock_price, strike_price, time_to_expiry_in_years,
                            risk_free_interest_rate, volatility)
    d2_value = calculate_d2(stock_price, strike_price, time_to_expiry_in_years,
                            risk_free_interest_rate, volatility)
    present_value_of_strike = strike_price * math.exp(-risk_free_interest_rate * time_to_expiry_in_years)

    return (present_value_of_strike * cumulative_normal_distribution(-d2_value)
            - stock_price * cumulative_normal_distribution(-d1_value))


# ---------------------------------------------------------------------
# Greeks
# ---------------------------------------------------------------------

def calculate_delta(stock_price, strike_price, time_to_expiry_in_years,
                    risk_free_interest_rate, volatility, option_type):
    d1_value = calculate_d1(stock_price, strike_price, time_to_expiry_in_years,
                            risk_free_interest_rate, volatility)
    if option_type == "call":
        return cumulative_normal_distribution(d1_value)
    if option_type == "put":
        return cumulative_normal_distribution(d1_value) - 1
    raise ValueError("option_type must be 'call' or 'put'")


def calculate_gamma(stock_price, strike_price, time_to_expiry_in_years,
                    risk_free_interest_rate, volatility):
    d1_value = calculate_d1(stock_price, strike_price, time_to_expiry_in_years,
                            risk_free_interest_rate, volatility)
    return normal_probability_density(d1_value) / (
        stock_price * volatility * math.sqrt(time_to_expiry_in_years))


def calculate_theta(stock_price, strike_price, time_to_expiry_in_years,
                    risk_free_interest_rate, volatility, option_type):
    d1_value = calculate_d1(stock_price, strike_price, time_to_expiry_in_years,
                            risk_free_interest_rate, volatility)
    d2_value = calculate_d2(stock_price, strike_price, time_to_expiry_in_years,
                            risk_free_interest_rate, volatility)
    present_value_of_strike = strike_price * math.exp(-risk_free_interest_rate * time_to_expiry_in_years)

    time_decay = -(stock_price * normal_probability_density(d1_value) * volatility) / (
        2 * math.sqrt(time_to_expiry_in_years))

    if option_type == "call":
        return time_decay - risk_free_interest_rate * present_value_of_strike \
            * cumulative_normal_distribution(d2_value)
    if option_type == "put":
        return time_decay + risk_free_interest_rate * present_value_of_strike \
            * cumulative_normal_distribution(-d2_value)
    raise ValueError("option_type must be 'call' or 'put'")


def calculate_vega(stock_price, strike_price, time_to_expiry_in_years,
                   risk_free_interest_rate, volatility):
    d1_value = calculate_d1(stock_price, strike_price, time_to_expiry_in_years,
                            risk_free_interest_rate, volatility)
    return stock_price * normal_probability_density(d1_value) * math.sqrt(time_to_expiry_in_years)
