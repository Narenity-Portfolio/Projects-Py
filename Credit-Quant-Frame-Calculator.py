import math

borrower_names = []
loan_exposures = []
default_probabilities = []
recovery_rates = []
years_to_maturity = []


def get_number(prompt_text, bottom_limit, top_limit, fallback_value=None):
    while True:
        typed_text = input(prompt_text).strip()
        if typed_text == "" and fallback_value is not None:
            return fallback_value
        typed_text = typed_text.replace(",", "").replace("%", "").replace("$", "").replace(" ", "")
        try:
            parsed_number = float(typed_text)
        except ValueError:
            print("  Invalid input: please enter a number.")
            continue
        if not math.isfinite(parsed_number):
            print("  Invalid input: please enter a finite number.")
            continue
        if parsed_number < bottom_limit or parsed_number > top_limit:
            print("  Value must be between", bottom_limit, "and", top_limit, "- please try again.")
            continue
        return parsed_number


def get_whole_number(prompt_text, bottom_limit, top_limit, fallback_value=None):
    while True:
        parsed_number = get_number(prompt_text, bottom_limit, top_limit, fallback_value)
        if parsed_number != int(parsed_number):
            print("  Please enter a whole number.")
            continue
        return int(parsed_number)


def portfolio_loaded():
    lists_match = len(loan_exposures) == len(borrower_names) == len(default_probabilities) == len(recovery_rates) == len(years_to_maturity)
    if len(loan_exposures) == 0 or not lists_match:
        print("No portfolio loaded. Please select option 1 first.")
        return False
    return True


def normal_prob_below(z_score):
    return 0.5 * (1 + math.erf(z_score / math.sqrt(2)))


def bond_value(coupon_pct, maturity_years, riskless_rate, credit_spread_bp):
    running_price = 0
    coupon_count = int(round(maturity_years * 2))
    discount_rate = riskless_rate + credit_spread_bp / 10000
    for coupon_num in range(1, coupon_count + 1):
        payment_time = coupon_num / 2
        running_price = running_price + (coupon_pct * 100 / 2) * math.exp(-discount_rate * payment_time)
    running_price = running_price + 100 * math.exp(-discount_rate * maturity_years)
    return running_price


def equity_from_firm_value(firm_value, debt_owed, riskless_rate, firm_vol, maturity_years):
    dee_one = (math.log(firm_value / debt_owed) + (riskless_rate + 0.5 * firm_vol ** 2) * maturity_years) / (firm_vol * math.sqrt(maturity_years))
    dee_two = dee_one - firm_vol * math.sqrt(maturity_years)
    return firm_value * normal_prob_below(dee_one) - debt_owed * math.exp(-riskless_rate * maturity_years) * normal_prob_below(dee_two)


print("=== CREDIT RISK ANALYTICS TOOLKIT ===")
print("(Press Enter at any prompt to accept the default value shown in brackets.)")

while True:
    print("\n-------- MAIN MENU --------")
    print("1 - Enter loan portfolio (or load example data)")
    print("2 - Expected loss and credit spread table")
    print("3 - CDS curve: implied default probabilities")
    print("4 - Risky bond pricing (credit spread, CS01)")
    print("5 - Merton structural model (equity to default probability)")
    print("0 - Exit")
    try:
        menu_pick = input("Select an option: ").strip()
    except (EOFError, KeyboardInterrupt):
        print("\nGoodbye.")
        break

    try:
        if menu_pick == "1":
            example_or_own = input("Type 'e' to load the example portfolio, or anything else to enter your own loans: ").strip().lower()
            if example_or_own == "e":
                borrower_names = ["Utility A", "Pharma B", "Retailer C", "Telecom D", "Airline E", "Energy F", "Media G", "Distressed H"]
                loan_exposures = [40e6, 35e6, 30e6, 45e6, 20e6, 15e6, 10e6, 5e6]
                default_probabilities = [0.0006, 0.0006, 0.0018, 0.0018, 0.009, 0.035, 0.035, 0.25]
                recovery_rates = [0.65, 0.60, 0.55, 0.55, 0.45, 0.40, 0.35, 0.30]
                years_to_maturity = [7, 5, 5, 7, 4, 5, 5, 3]
                print("Example portfolio loaded (8 loans).")
            else:
                loan_count = get_whole_number("Number of loans (1-50): ", 1, 50)
                typed_names = []
                typed_cash = []
                typed_odds = []
                typed_recovery = []
                typed_years = []
                for loan_num in range(loan_count):
                    print("Loan", loan_num + 1)
                    entered_name = input("  Borrower name (Enter for Loan " + str(loan_num + 1) + "): ").strip()
                    if entered_name == "":
                        entered_name = "Loan " + str(loan_num + 1)
                    typed_names.append(entered_name)
                    typed_cash.append(get_number("  Loan amount ($): ", 1, 1e13))
                    typed_odds.append(get_number("  Annual default probability (%, 0 to 99.9): ", 0, 99.9) / 100)
                    typed_recovery.append(get_number("  Recovery rate (%, 0 to 100): ", 0, 100) / 100)
                    typed_years.append(get_number("  Years to maturity (0.1 to 100): ", 0.1, 100))
                borrower_names = typed_names
                loan_exposures = typed_cash
                default_probabilities = typed_odds
                recovery_rates = typed_recovery
                years_to_maturity = typed_years
                print("Saved", loan_count, "loans.")

        elif menu_pick == "2":
            if not portfolio_loaded():
                continue
            riskless_rate = get_number("Risk-free rate % (Enter = 4): ", -5, 50, 4) / 100
            print()
            print("Amounts in $; spreads in basis points; hazard rate is annualised.\n\nBorrower         Exposure   Cum. PD  Exp. Loss  EL (%)   Spread   Hazard")
            portfolio_cash = 0
            portfolio_expected_loss = 0
            spread_weighted_sum = 0
            for loan_num in range(len(loan_exposures)):
                hazard_rate = -math.log(1 - default_probabilities[loan_num]) + 0.0
                survival_probability = math.exp(-hazard_rate * years_to_maturity[loan_num])
                cumulative_default_probability = 1 - survival_probability
                loss_share = 1 - recovery_rates[loan_num]
                loan_expected_loss = cumulative_default_probability * loss_share * loan_exposures[loan_num]
                credit_spread_bp = hazard_rate * loss_share * 10000
                print(borrower_names[loan_num][:12].ljust(14), str(round(loan_exposures[loan_num])).rjust(10), str(round(cumulative_default_probability * 100, 2)).rjust(8) + "%",
                      str(round(loan_expected_loss)).rjust(10), str(round(loan_expected_loss / loan_exposures[loan_num] * 100, 2)).rjust(6) + "%",
                      str(round(credit_spread_bp, 1)).rjust(8), str(round(hazard_rate, 4)).rjust(8))
                portfolio_cash = portfolio_cash + loan_exposures[loan_num]
                portfolio_expected_loss = portfolio_expected_loss + loan_expected_loss
                spread_weighted_sum = spread_weighted_sum + credit_spread_bp * loan_exposures[loan_num]
            print("Total exposure:", round(portfolio_cash), " Expected loss:", round(portfolio_expected_loss), "(", round(portfolio_expected_loss / portfolio_cash * 100, 2), "% of exposure )")
            print("Exposure-weighted average spread:", round(spread_weighted_sum / portfolio_cash, 1), "bp")
            pv_of_losses = 0
            for loan_num in range(len(loan_exposures)):
                hazard_rate = -math.log(1 - default_probabilities[loan_num]) + 0.0
                discount_rate = hazard_rate + riskless_rate
                if abs(discount_rate) < 0.000000001:
                    pv_factor = hazard_rate * years_to_maturity[loan_num]
                else:
                    pv_factor = hazard_rate / discount_rate * (1 - math.exp(-discount_rate * years_to_maturity[loan_num]))
                pv_of_losses = pv_of_losses + loan_exposures[loan_num] * (1 - recovery_rates[loan_num]) * pv_factor
            print("Present value of expected loss (discounted):", round(pv_of_losses))

        elif menu_pick == "3":
            print("Enter market CDS par spreads (in basis points) for each tenor.")
            cds_recovery = get_number("Recovery rate % (Enter = 40): ", 0, 95, 40) / 100
            tenor_list = [1, 3, 5, 7, 10]
            cds_quotes_bp = []
            for tenor in tenor_list:
                cds_quotes_bp.append(get_number("  " + str(tenor) + "y CDS spread (bp, 0 to 20000): ", 0, 20000))
            print()
            print("Spreads in basis points; hazard rates are annualised.\n\nYrs   Spread Avg Hazard   Survival  Cum. PD   Fwd Hazard")
            previous_total_bust = 0
            previous_tenor = 0
            for quote_num in range(len(tenor_list)):
                tenor = tenor_list[quote_num]
                avg_failure_rate = cds_quotes_bp[quote_num] / 10000 / (1 - cds_recovery)
                cumulative_bust = avg_failure_rate * tenor
                survival_probability = math.exp(-cumulative_bust)
                default_prob_by_then = 1 - survival_probability
                bust_speed_in_gap = (cumulative_bust - previous_total_bust) / (tenor - previous_tenor)
                curve_warning = ""
                if bust_speed_in_gap < 0:
                    curve_warning = "  <- negative forward hazard: curve is not arbitrage-free"
                print(str(tenor).rjust(3), str(cds_quotes_bp[quote_num]).rjust(8), str(round(avg_failure_rate, 4)).rjust(10), str(round(survival_probability, 4)).rjust(10),
                      str(round(default_prob_by_then * 100, 2)).rjust(7) + "%", str(round(bust_speed_in_gap, 4)).rjust(12), curve_warning)
                previous_total_bust = cumulative_bust
                previous_tenor = tenor
            print("\nNote: these are risk-neutral default probabilities (they include a risk premium),")
            print("so they are typically higher than real-world (historical) default rates.")
            historical_pd = get_number("Historical annual default rate % for comparison (press Enter to skip): ", 0.0001, 100, -1)
            if historical_pd != -1:
                historical_pd = historical_pd / 100
                market_one_year_pd = 1 - math.exp(-(cds_quotes_bp[2] / 10000 / (1 - cds_recovery)))
                print("Market-implied 1y PD (from 5y spread):", round(market_one_year_pd * 100, 3), "%")
                print("Historical default rate:", round(historical_pd * 100, 3), "%")
                print("Ratio (risk premium multiple):", round(market_one_year_pd / historical_pd, 2))

        elif menu_pick == "4":
            coupon_pct = get_number("Coupon rate % (0 to 100): ", 0, 100) / 100
            maturity_years = get_number("Years to maturity (0.5 to 50): ", 0.5, 50)
            maturity_years = round(maturity_years * 2) / 2
            riskless_rate = get_number("Risk-free rate % (Enter = 4): ", -5, 50, 4) / 100
            credit_spread_bp = get_number("Credit spread (bp, 0 to 20000): ", 0, 20000)
            bond_recovery = get_number("Recovery rate % (Enter = 40): ", 0, 95, 40) / 100
            print("(Using", maturity_years, "years to maturity, rounded to the nearest half-year)")

            riskless_price = bond_value(coupon_pct, maturity_years, riskless_rate, 0)
            defaultable_price = bond_value(coupon_pct, maturity_years, riskless_rate, credit_spread_bp)
            print("\nRisk-free price:", round(riskless_price, 3))
            print("Risky bond price (spread method):", round(defaultable_price, 3))

            hazard_rate = credit_spread_bp / 10000 / (1 - bond_recovery)
            hazard_method_price = 0
            for coupon_num in range(1, int(round(maturity_years * 2)) + 1):
                payment_time = coupon_num / 2
                still_alive_end = math.exp(-hazard_rate * payment_time)
                still_alive_start = math.exp(-hazard_rate * (payment_time - 0.5))
                hazard_method_price = hazard_method_price + (coupon_pct * 100 / 2) * math.exp(-riskless_rate * payment_time) * still_alive_end
                hazard_method_price = hazard_method_price + bond_recovery * 100 * math.exp(-riskless_rate * payment_time) * (still_alive_start - still_alive_end)
            hazard_method_price = hazard_method_price + 100 * math.exp(-riskless_rate * maturity_years) * math.exp(-hazard_rate * maturity_years)
            print("Risky bond price (hazard rate and recovery method):", round(hazard_method_price, 3))
            print("Difference between methods:", round(defaultable_price - hazard_method_price, 3), "(arises from differing modelling assumptions)")
            print("\nPrice reduction due to credit risk:", round(riskless_price - defaultable_price, 3), "per 100 face value")
            print("Probability of default before maturity:", round((1 - math.exp(-hazard_rate * maturity_years)) * 100, 2), "%")

            price_spread_plus_one = bond_value(coupon_pct, maturity_years, riskless_rate, credit_spread_bp + 1)
            cs01_value = price_spread_plus_one - defaultable_price
            print("\nCS01 (price change for a +1bp spread move):", round(cs01_value, 4), "per 100 face value")
            if defaultable_price > 0:
                print("Approximate spread duration:", round(-cs01_value / defaultable_price * 10000, 2), "years")
            print("\nSpread sensitivity:")
            for spread_jump in [-100, -50, 50, 100, 200, 500]:
                shocked_spread = credit_spread_bp + spread_jump
                if shocked_spread < 0:
                    continue
                shocked_price = bond_value(coupon_pct, maturity_years, riskless_rate, shocked_spread)
                if defaultable_price > 0:
                    print("  Spread shock", str(spread_jump).rjust(4), "bp -> price", round(shocked_price, 3), "  change", round((shocked_price / defaultable_price - 1) * 100, 2), "%")

        elif menu_pick == "5":
            print("Merton structural model: equity is treated as a call option on the firm's assets.")
            market_cap = get_number("Market capitalisation (equity value): ", 0.000001, 1e15)
            equity_vol = get_number("Equity volatility % (e.g. 40): ", 1, 500) / 100
            debt_owed = get_number("Face value of debt (same units as market cap): ", 0.000001, 1e15)
            riskless_rate = get_number("Risk-free rate % (Enter = 4): ", -5, 50, 4) / 100
            maturity_years = get_number("Debt maturity in years (0.1 to 50): ", 0.1, 50)
            firm_expected_growth = get_number("Expected asset return % (real-world, Enter = 8): ", -50, 100, 8) / 100

            firm_vol = equity_vol * market_cap / (market_cap + debt_owed)
            firm_value = market_cap + debt_owed
            solver_converged = False
            solver_failed = False
            for solver_pass in range(500):
                lower_bound = market_cap
                upper_bound = market_cap + debt_owed * 2
                for squeeze_round in range(200):
                    midpoint = (lower_bound + upper_bound) / 2
                    if equity_from_firm_value(midpoint, debt_owed, riskless_rate, firm_vol, maturity_years) > market_cap:
                        upper_bound = midpoint
                    else:
                        lower_bound = midpoint
                firm_value = (lower_bound + upper_bound) / 2
                dee_one = (math.log(firm_value / debt_owed) + (riskless_rate + 0.5 * firm_vol ** 2) * maturity_years) / (firm_vol * math.sqrt(maturity_years))
                equity_slice = firm_value * max(normal_prob_below(dee_one), 0.000000000001)
                next_firm_vol = equity_vol * market_cap / equity_slice
                if (not math.isfinite(next_firm_vol)) or next_firm_vol < 0.000001 or next_firm_vol > 50:
                    solver_failed = True
                    break
                if abs(next_firm_vol - firm_vol) < 0.0000001:
                    firm_vol = next_firm_vol
                    solver_converged = True
                    break
                firm_vol = next_firm_vol

            debt_market_value = firm_value - market_cap
            if solver_failed or debt_market_value <= 0:
                print("\nThe model could not be solved with these inputs (they may be too extreme,")
                print("e.g. debt very small relative to equity, or vice versa). Please try less extreme values.")
                continue
            if not solver_converged:
                print("\n(Warning: the iterative solver did not fully converge; interpret results with caution.)")

            dee_one = (math.log(firm_value / debt_owed) + (riskless_rate + 0.5 * firm_vol ** 2) * maturity_years) / (firm_vol * math.sqrt(maturity_years))
            dee_two = dee_one - firm_vol * math.sqrt(maturity_years)
            risk_neutral_pd = normal_prob_below(-dee_two)
            distance_to_default = (math.log(firm_value / debt_owed) + (firm_expected_growth - 0.5 * firm_vol ** 2) * maturity_years) / (firm_vol * math.sqrt(maturity_years))
            real_world_pd = normal_prob_below(-distance_to_default)
            debt_yield = -math.log(debt_market_value / debt_owed) / maturity_years
            merton_credit_spread_bp = max((debt_yield - riskless_rate) * 10000, 0.0)
            recovery_denominator = debt_owed * normal_prob_below(-dee_two)
            if recovery_denominator < 0.000000000001:
                model_recovery = None
            else:
                model_recovery = firm_value * math.exp(riskless_rate * maturity_years) * normal_prob_below(-dee_one) / recovery_denominator

            print("\nImplied asset value:", round(firm_value, 2))
            print("Implied asset volatility:", round(firm_vol * 100, 2), "%")
            print("Leverage (debt / assets):", round(debt_owed / firm_value * 100, 1), "%")
            print("Distance to default:", round(distance_to_default, 3), "standard deviations")
            print("Real-world PD:", round(real_world_pd * 100, 3), "%")
            print("Risk-neutral PD:", round(risk_neutral_pd * 100, 3), "%")
            print("Market value of debt:", round(debt_market_value, 2))
            print("Merton credit spread:", round(merton_credit_spread_bp, 1), "bp")
            if model_recovery is None:
                print("Model-implied recovery rate: n/a (default is effectively impossible)")
            else:
                print("Model-implied recovery rate:", round(model_recovery * 100, 1), "%")

            print("\nSensitivity to asset volatility (asset value and debt held constant):")
            for test_vol in [0.10, 0.15, 0.20, 0.25, 0.30, 0.40]:
                test_dee_two = (math.log(firm_value / debt_owed) + (riskless_rate - 0.5 * test_vol ** 2) * maturity_years) / (test_vol * math.sqrt(maturity_years))
                test_dee_one = test_dee_two + test_vol * math.sqrt(maturity_years)
                test_equity_value = firm_value * normal_prob_below(test_dee_one) - debt_owed * math.exp(-riskless_rate * maturity_years) * normal_prob_below(test_dee_two)
                test_debt_value = firm_value - test_equity_value
                if test_debt_value <= 0:
                    print("  Vol", str(round(test_vol * 100)).rjust(3) + "%", " n/a (inputs too extreme)")
                    continue
                test_spread_bp = max((-math.log(test_debt_value / debt_owed) / maturity_years - riskless_rate) * 10000, 0.0)
                print("  Vol", str(round(test_vol * 100)).rjust(3) + "%", " PD", str(round(normal_prob_below(-test_dee_two) * 100, 2)).rjust(6) + "%", "  Spread", str(round(test_spread_bp, 1)).rjust(8), "bp")

        elif menu_pick == "0":
            print("Goodbye.")
            break

        else:
            print("Invalid selection. Please enter a number from 0 to 5.")

    except EOFError:
        print("\nInput ended. Goodbye.")
        break
    except KeyboardInterrupt:
        print("\nOperation interrupted. Returning to the main menu.")
    except Exception as error_message:
        print("An unexpected error occurred:", error_message, "- returning to the main menu.")