from datetime import date, datetime, timedelta
from quacktrader.portfolio.deposit_account import DepositAccount
from quacktrader.portfolio.investment_account import InvestmentAccount
from quacktrader.portfolio.portfolio import Portfolio, Transfer
from quacktrader.portfolio.revenue import FixedExpense, FixedIncome, Salary, CompoundInterest, SimpleReturns, is_first_of_the_month, is_friday_biweekly, is_monday_biweekly, is_monthly_on_the_25th, is_trading_day_2023
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

taxable_tda = InvestmentAccount(
    name = "taxable_tda",
    initial_deposit_date = start_date,
    initial_deposit_amount = 13018.40,
    composition = {"^SPX": 100})
taxable_tda.with_expected_return(SimpleReturns(annualized_return=.10, credit_period=is_trading_day_2023))

portfolio = Portfolio()
[portfolio.with_account(account) for account in [
    checking,
    taxable_tda]]
portfolio.set_primary_account(checking.name)

portfolio.with_transfer(Transfer(payment=1000, transfer_period=is_monthly_on_the_25th,
                                 source=checking,
                                 destination=taxable_tda)
                                 .until(retirement_date))

simulation = portfolio.take(start_date=start_date, n_days=365*50)
balance_sheet = portfolio.get_balance_sheet(simulation)
figure = balance_sheet.plot()
pyplot.show()
pandas.set_option('display.max_rows', 500)
# print(balance_sheet[330:366])
balance_sheet = balance_sheet.resample('1Y').first()
print(balance_sheet.head(50))

# # balance_sheet = hsa_fidelity.get_balance_sheet(start_date, n_days=365*50)
# # balance_sheet.plot()
# # pyplot.show()
# # pandas.set_option('display.max_rows', 500)
# # print(balance_sheet.head(500))
