from datetime import date, datetime, timedelta
from quacktrader.portfolio.account import Account, transfer
from quacktrader.portfolio.deposit_account import DepositAccount
from quacktrader.portfolio.investment_account import HealthSavingsAccount, InvestmentAccount, Traditional401K, TraditionalIRA
from quacktrader.portfolio.portfolio import Portfolio
from quacktrader.portfolio.revenue import FixedExpense, FixedIncome, Salary, CompoundInterest, SimpleDividends, SimpleReturns, is_annual, is_annual_in_may, is_first_of_the_month, is_friday_biweekly, is_monday_biweekly, is_monthly_on_the_25th, is_monthly_on_the_8th, is_quarterly, is_semiannual, is_trading_day_2023
from matplotlib import pyplot
import pandas


start_date = datetime.now().date()
retirement_date = start_date + timedelta(days=365*36) # at age 65
rmd_start_date = date(1993, 4, 1) + timedelta(days=365*73) # April 1st of the year following the calendar year in which you reach age 72

checking = DepositAccount(
    name = "checking",
    initial_deposit_date = start_date,
    initial_deposit_amount = 30000)
checking.with_salary(Salary(payment=3777.33, credit_period=is_friday_biweekly, annual_gross=185000, w2_withholdings=35415.5).until(retirement_date))
checking.with_expense(FixedExpense(payment=150, debit_period=is_monday_biweekly))        # groceries
checking.with_expense(FixedExpense(payment=2662.50, debit_period=is_first_of_the_month)) # rent
checking.with_interest(CompoundInterest(interest_rate=.0001, compounding_period=is_first_of_the_month))
# todo: check if salary is being taxed correctly
# todo: is annual_gross necessary or proper?

hsa_fidelity = HealthSavingsAccount(
    name = "hsa_fidelity",
    initial_deposit_date = start_date,
    initial_deposit_amount = 1814.11,
    composition = {"^SPX": 100})
hsa_fidelity.with_expected_return(SimpleReturns(annualized_return=.10, credit_period=is_trading_day_2023))

hsa_homedepot = HealthSavingsAccount(
    name = "hsa_homedepot",
    initial_deposit_date = start_date,
    initial_deposit_amount = 15000,
    composition = {"^SPX": 100})
hsa_homedepot.with_income(FixedIncome(payment=140.38, credit_period=is_friday_biweekly).until(retirement_date))
hsa_homedepot.with_expected_return(SimpleReturns(annualized_return=.10, credit_period=is_trading_day_2023))
# todo: account for company match
# todo: account for qualified healthcare expenditures

retirement_401k = Traditional401K(
    name = "retirement_401k",
    initial_deposit_date = start_date,
    initial_deposit_amount = 75000,
    composition = {"^SPX": 100})
retirement_401k.with_income(FixedIncome(payment=788.46, credit_period=is_friday_biweekly).until(retirement_date))
retirement_401k.with_expected_return(SimpleReturns(annualized_return=.10, credit_period=is_trading_day_2023))
# todo: account for company match

rsu_holdings = InvestmentAccount(
    name = "rsu_holdings",
    initial_deposit_date = start_date,
    initial_deposit_amount = 46995,
    composition = {"HD": 100})
rsu_holdings.with_income(FixedIncome(payment=15000, credit_period=is_annual_in_may).until(retirement_date))
rsu_holdings.with_expected_return(SimpleReturns(annualized_return=.10, credit_period=is_trading_day_2023))
rsu_holdings.with_dividends(SimpleDividends(payout_ratio=.0025, credit_period=is_quarterly))
# todo: count income towards wages?

espp_homedepot = InvestmentAccount(
    name = "espp_homedepot",
    initial_deposit_date = start_date,
    initial_deposit_amount = 0,
    composition = {"HD": 100})
espp_homedepot.with_expected_return(CompoundInterest(interest_rate=.10, compounding_period=is_trading_day_2023))
espp_homedepot.with_dividends(SimpleDividends(payout_ratio=.0025, credit_period=is_quarterly))
transfer(amount=826.92, transfer_period=is_friday_biweekly, source=checking, destination=espp_homedepot, end_date=retirement_date)
# todo: transfer everything out semiannually, may require balance aware transfers
# todo: apply discount to semiannual rolling sum of contributions

roth_ira = InvestmentAccount(
    name = "roth_ira",
    initial_deposit_date = start_date,
    initial_deposit_amount = 28000,
    composition = {"^SPX": 100})
roth_ira.with_expected_return(SimpleReturns(annualized_return=.10, credit_period=is_trading_day_2023))

traditional_ira = TraditionalIRA(
    name = "traditional_ira",
    initial_deposit_date = start_date,
    initial_deposit_amount = 4000,
    composition = {"^SPX": 100})
traditional_ira.with_expected_return(SimpleReturns(annualized_return=.10, credit_period=is_trading_day_2023))
transfer(amount=500, transfer_period=is_monthly_on_the_8th, source=checking, destination=traditional_ira, end_date=retirement_date) 
transfer(amount=180000, transfer_period=is_annual, source=traditional_ira, destination=checking, start_date=retirement_date) # todo: this amount depends on the accumulated balance
# todo: count this against wages?

taxable_fidelity = InvestmentAccount(
    name = "taxable_fidelity",
    initial_deposit_date = start_date,
    initial_deposit_amount = 110080.47,
    composition = {"^SPX": 100})
taxable_fidelity.with_expected_return(SimpleReturns(annualized_return=.10, credit_period=is_trading_day_2023))

taxable_tda = InvestmentAccount(
    name = "taxable_tda",
    initial_deposit_date = start_date,
    initial_deposit_amount = 13018.40,
    composition = {"^SPX": 100})
taxable_tda.with_expected_return(SimpleReturns(annualized_return=.10, credit_period=is_trading_day_2023))
transfer(amount=1000, transfer_period=is_monthly_on_the_25th, source=checking, destination=taxable_tda, end_date=retirement_date)

trust_fund = InvestmentAccount(
    name = "trust_fund",
    initial_deposit_amount=1000000,
    initial_deposit_date = start_date,
    composition = {"^SPX": 100})
trust_fund.with_expected_return(SimpleReturns(annualized_return=.10, credit_period=is_trading_day_2023))

portfolio = Portfolio()
[portfolio.with_account(account) for account in [
    checking,
    hsa_fidelity,
    hsa_homedepot,
    retirement_401k,
    rsu_holdings,
    roth_ira,
    traditional_ira,
    taxable_fidelity,
    taxable_tda,
    # trust_fund
    ]]

balance_sheet = portfolio.simulate_and_plot(start_date=start_date, simulation_period=365*50)
# figure = balance_sheet.plot()
# pyplot.show()
pandas.set_option('display.max_rows', 500)
# print(balance_sheet[330:366])
balance_sheet = balance_sheet.resample('1Y').last()
print(balance_sheet.tail(20))

# balance_sheet = hsa_fidelity.get_balance_sheet(start_date, n_days=365*50)
# balance_sheet.plot()
# pyplot.show()
# pandas.set_option('display.max_rows', 500)
# print(balance_sheet.head(500))