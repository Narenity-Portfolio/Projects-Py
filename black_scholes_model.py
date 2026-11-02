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


# ---------------------------------------------------------------------
# Tests
# Each Greek is validated against a central finite difference, i.e. the
# observed change in price when the input is shifted slightly up and down.
# ---------------------------------------------------------------------

number_of_tests_passed = 0
number_of_tests_failed = 0


def check_values_match(test_name, model_value, benchmark_value, tolerance):
    global number_of_tests_passed, number_of_tests_failed
    if abs(model_value - benchmark_value) <= tolerance:
        number_of_tests_passed += 1
        result = "PASS"
    else:
        number_of_tests_failed += 1
        result = "FAIL"
    print("  %s  %-48s model = %10.6f   benchmark = %10.6f"
          % (result, test_name, model_value, benchmark_value))


def check_condition(test_name, condition):
    global number_of_tests_passed, number_of_tests_failed
    if condition:
        number_of_tests_passed += 1
        result = "PASS"
    else:
        number_of_tests_failed += 1
        result = "FAIL"
    print("  %s  %s" % (result, test_name))


def run_all_tests():
    stock_price = 100
    strike_price = 105
    time_to_expiry_in_years = 0.5
    risk_free_interest_rate = 0.05
    volatility = 0.25
    shift = 0.0001

    print("MODEL VALIDATION")
    print("-" * 100)
    print("Inputs: stock price %.2f, strike price %.2f, expiry %.2f years, "
          "risk-free rate %.2f%%, volatility %.2f%%\n"
          % (stock_price, strike_price, time_to_expiry_in_years,
             risk_free_interest_rate * 100, volatility * 100))

    # Pricing checks
    check_values_match("Call price against published example (10.4506)",
                       calculate_call_option_price(100, 100, 1, 0.05, 0.20), 10.4506, 0.001)

    call_price = calculate_call_option_price(stock_price, strike_price, time_to_expiry_in_years,
                                             risk_free_interest_rate, volatility)
    put_price = calculate_put_option_price(stock_price, strike_price, time_to_expiry_in_years,
                                           risk_free_interest_rate, volatility)
    check_values_match("Put-call parity: C - P = S - K*exp(-rT)",
                       call_price - put_price,
                       stock_price - strike_price * math.exp(-risk_free_interest_rate * time_to_expiry_in_years),
                       0.000001)

    # Delta
    for option_type, price_function in [("call", calculate_call_option_price),
                                        ("put", calculate_put_option_price)]:
        price_up = price_function(stock_price + shift, strike_price, time_to_expiry_in_years,
                                  risk_free_interest_rate, volatility)
        price_down = price_function(stock_price - shift, strike_price, time_to_expiry_in_years,
                                    risk_free_interest_rate, volatility)
        check_values_match("Delta (%s) against finite difference" % option_type,
                           calculate_delta(stock_price, strike_price, time_to_expiry_in_years,
                                           risk_free_interest_rate, volatility, option_type),
                           (price_up - price_down) / (2 * shift), 0.00001)

    call_delta = calculate_delta(stock_price, strike_price, time_to_expiry_in_years,
                                 risk_free_interest_rate, volatility, "call")
    put_delta = calculate_delta(stock_price, strike_price, time_to_expiry_in_years,
                                risk_free_interest_rate, volatility, "put")
    check_values_match("Call delta - put delta = 1", call_delta - put_delta, 1.0, 0.000001)

    # Gamma
    model_gamma = calculate_gamma(stock_price, strike_price, time_to_expiry_in_years,
                                  risk_free_interest_rate, volatility)
    delta_up = calculate_delta(stock_price + shift, strike_price, time_to_expiry_in_years,
                               risk_free_interest_rate, volatility, "call")
    delta_down = calculate_delta(stock_price - shift, strike_price, time_to_expiry_in_years,
                                 risk_free_interest_rate, volatility, "call")
    check_values_match("Gamma against change in delta", model_gamma,
                       (delta_up - delta_down) / (2 * shift), 0.00001)

    wide_shift = 0.01
    price_up = calculate_call_option_price(stock_price + wide_shift, strike_price, time_to_expiry_in_years,
                                           risk_free_interest_rate, volatility)
    price_middle = call_price
    price_down = calculate_call_option_price(stock_price - wide_shift, strike_price, time_to_expiry_in_years,
                                             risk_free_interest_rate, volatility)
    check_values_match("Gamma against second derivative of price", model_gamma,
                       (price_up - 2 * price_middle + price_down) / wide_shift ** 2, 0.0001)

    # Theta (time to expiry falls as time passes, so theta = -dPrice/dT)
    for option_type, price_function in [("call", calculate_call_option_price),
                                        ("put", calculate_put_option_price)]:
        price_longer = price_function(stock_price, strike_price, time_to_expiry_in_years + shift,
                                      risk_free_interest_rate, volatility)
        price_shorter = price_function(stock_price, strike_price, time_to_expiry_in_years - shift,
                                       risk_free_interest_rate, volatility)
        check_values_match("Theta (%s) against finite difference" % option_type,
                           calculate_theta(stock_price, strike_price, time_to_expiry_in_years,
                                           risk_free_interest_rate, volatility, option_type),
                           -(price_longer - price_shorter) / (2 * shift), 0.0001)

    # Vega
    model_vega = calculate_vega(stock_price, strike_price, time_to_expiry_in_years,
                                risk_free_interest_rate, volatility)
    for option_type, price_function in [("call", calculate_call_option_price),
                                        ("put", calculate_put_option_price)]:
        price_higher = price_function(stock_price, strike_price, time_to_expiry_in_years,
                                      risk_free_interest_rate, volatility + shift)
        price_lower = price_function(stock_price, strike_price, time_to_expiry_in_years,
                                     risk_free_interest_rate, volatility - shift)
        check_values_match("Vega (%s) against finite difference" % option_type,
                           model_vega, (price_higher - price_lower) / (2 * shift), 0.0001)

    # Sign and range checks
    call_theta = calculate_theta(stock_price, strike_price, time_to_expiry_in_years,
                                 risk_free_interest_rate, volatility, "call")
    check_condition("Call delta lies between 0 and 1", 0 < call_delta < 1)
    check_condition("Put delta lies between -1 and 0", -1 < put_delta < 0)
    check_condition("Gamma is positive", model_gamma > 0)
    check_condition("Vega is positive", model_vega > 0)
    check_condition("Call theta is negative", call_theta < 0)

    print("\nResult: %d passed, %d failed\n" % (number_of_tests_passed, number_of_tests_failed))


# ---------------------------------------------------------------------
# Demonstrations
# ---------------------------------------------------------------------

def demonstrate_delta():
    strike_price = 100
    time_to_expiry_in_years = 0.5
    risk_free_interest_rate = 0.05
    volatility = 0.20

    print("DELTA: sensitivity to the stock price")
    print("-" * 60)
    print("Strike price 100, expiry 0.5 years, risk-free rate 5%, volatility 20%\n")
    print("Stock price | Call price | Call delta | Put delta")
    for stock_price in [70, 80, 90, 100, 110, 120, 130]:
        call_price = calculate_call_option_price(stock_price, strike_price, time_to_expiry_in_years,
                                                 risk_free_interest_rate, volatility)
        call_delta = calculate_delta(stock_price, strike_price, time_to_expiry_in_years,
                                     risk_free_interest_rate, volatility, "call")
        put_delta = calculate_delta(stock_price, strike_price, time_to_expiry_in_years,
                                    risk_free_interest_rate, volatility, "put")
        print("%11d | %10.4f | %10.4f | %9.4f" % (stock_price, call_price, call_delta, put_delta))

    original_price = calculate_call_option_price(100, strike_price, time_to_expiry_in_years,
                                                 risk_free_interest_rate, volatility)
    delta_at_100 = calculate_delta(100, strike_price, time_to_expiry_in_years,
                                   risk_free_interest_rate, volatility, "call")
    actual_price = calculate_call_option_price(101, strike_price, time_to_expiry_in_years,
                                               risk_free_interest_rate, volatility)
    print("\nCall delta rises from 0 (out of the money) to 1 (in the money).")
    print("A one-point rise in the stock price from 100: delta estimates a call price of %.4f, "
          "the model price is %.4f." % (original_price + delta_at_100, actual_price))
    print("The gap arises because delta itself changes with the stock price (gamma).\n")


def demonstrate_gamma():
    strike_price = 100
    risk_free_interest_rate = 0.05
    volatility = 0.20

    print("GAMMA: rate of change of delta")
    print("-" * 60)
    print("Strike price 100, risk-free rate 5%, volatility 20%\n")
    print("Stock price | Gamma (0.50 years) | Gamma (0.05 years)")
    for stock_price in [80, 85, 90, 95, 100, 105, 110, 115, 120]:
        gamma_long_expiry = calculate_gamma(stock_price, strike_price, 0.5,
                                            risk_free_interest_rate, volatility)
        gamma_short_expiry = calculate_gamma(stock_price, strike_price, 0.05,
                                             risk_free_interest_rate, volatility)
        print("%11d | %18.5f | %18.5f" % (stock_price, gamma_long_expiry, gamma_short_expiry))

    print("\nGamma is highest when the option is at the money, and the peak becomes")
    print("taller and narrower as expiry approaches.\n")


def demonstrate_theta():
    stock_price = 100
    strike_price = 100
    risk_free_interest_rate = 0.05
    volatility = 0.20

    print("THETA: time decay")
    print("-" * 60)
    print("At-the-money call, stock price 100, strike price 100, volatility 20%\n")
    print("Days to expiry | Call price | Theta per day")
    for days_to_expiry in [180, 120, 90, 60, 30, 14, 7, 3, 1]:
        time_to_expiry_in_years = days_to_expiry / 365
        call_price = calculate_call_option_price(stock_price, strike_price, time_to_expiry_in_years,
                                                 risk_free_interest_rate, volatility)
        theta_per_day = calculate_theta(stock_price, strike_price, time_to_expiry_in_years,
                                        risk_free_interest_rate, volatility, "call") / 365
        print("%14d | %10.4f | %13.4f" % (days_to_expiry, call_price, theta_per_day))

    print("\nThe option loses value each day, and the decay accelerates near expiry.\n")


def demonstrate_vega():
    stock_price = 100
    strike_price = 100
    time_to_expiry_in_years = 0.5
    risk_free_interest_rate = 0.05

    print("VEGA: sensitivity to volatility")
    print("-" * 60)
    print("At-the-money option, expiry 0.5 years\n")
    print("Volatility | Call price | Put price | Vega per 1 point")
    for volatility in [0.10, 0.20, 0.30, 0.40, 0.50]:
        call_price = calculate_call_option_price(stock_price, strike_price, time_to_expiry_in_years,
                                                 risk_free_interest_rate, volatility)
        put_price = calculate_put_option_price(stock_price, strike_price, time_to_expiry_in_years,
                                               risk_free_interest_rate, volatility)
        vega_per_point = calculate_vega(stock_price, strike_price, time_to_expiry_in_years,
                                        risk_free_interest_rate, volatility) / 100
        print("%9d%% | %10.4f | %9.4f | %16.4f" % (volatility * 100, call_price, put_price, vega_per_point))

    print("\nHigher volatility increases both call and put prices.\n")


def demonstrate_price_attribution():
    stock_price = 100
    strike_price = 100
    time_to_expiry_in_years = 0.5
    risk_free_interest_rate = 0.05
    volatility = 0.20

    change_in_stock_price = 2.0
    change_in_time = 1 / 365
    change_in_volatility = 0.01

    original_price = calculate_call_option_price(stock_price, strike_price, time_to_expiry_in_years,
                                                 risk_free_interest_rate, volatility)

    delta_effect = change_in_stock_price * calculate_delta(
        stock_price, strike_price, time_to_expiry_in_years, risk_free_interest_rate, volatility, "call")
    gamma_effect = 0.5 * change_in_stock_price ** 2 * calculate_gamma(
        stock_price, strike_price, time_to_expiry_in_years, risk_free_interest_rate, volatility)
    theta_effect = change_in_time * calculate_theta(
        stock_price, strike_price, time_to_expiry_in_years, risk_free_interest_rate, volatility, "call")
    vega_effect = change_in_volatility * calculate_vega(
        stock_price, strike_price, time_to_expiry_in_years, risk_free_interest_rate, volatility)

    estimated_price = original_price + delta_effect + gamma_effect + theta_effect + vega_effect
    actual_price = calculate_call_option_price(stock_price + change_in_stock_price, strike_price,
                                               time_to_expiry_in_years - change_in_time,
                                               risk_free_interest_rate, volatility + change_in_volatility)

    print("PRICE ATTRIBUTION: combining the Greeks")
    print("-" * 60)
    print("Scenario: stock price +2, one day elapses, volatility +1 percentage point\n")
    print("Original call price:  %8.4f" % original_price)
    print("  Delta effect:       %+8.4f" % delta_effect)
    print("  Gamma effect:       %+8.4f" % gamma_effect)
    print("  Theta effect:       %+8.4f" % theta_effect)
    print("  Vega effect:        %+8.4f" % vega_effect)
    print("Estimated new price:  %8.4f" % estimated_price)
    print("Model new price:      %8.4f" % actual_price)
    print("Approximation error:  %8.4f" % abs(estimated_price - actual_price))
    print("\nThe residual error reflects the higher-order terms the Greeks omit.\n")


if __name__ == "__main__":
    print("=" * 60)
    print("BLACK-SCHOLES-MERTON MODEL: OPTION PRICES AND GREEKS")
    print("=" * 60 + "\n")
    run_all_tests()
    demonstrate_delta()
    demonstrate_gamma()
    demonstrate_theta()
    demonstrate_vega()
    demonstrate_price_attribution()
