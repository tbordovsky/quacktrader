from dataclasses import astuple
from datetime import date, timedelta
from typing import Callable, Dict, List, Tuple
from pandas import DataFrame
import pandas

from quacktrader.portfolio.account import Account
from quacktrader.portfolio.assessment import Assessment
from quacktrader.portfolio.revenue import CapitalGains, Payment, SimpleDividends, FixedExpense, FixedIncome, CompoundInterest, is_new_year

# todo: rename to TaxableAccount
class InvestmentAccount(Account):
    def __init__(self, name: str, initial_deposit_date: date, initial_deposit_amount: float, composition: Dict[str, float]):
        self.name = name
        self.initial_deposit_date = initial_deposit_date
        self.initial_deposit_amount = initial_deposit_amount
        self.composition = composition
        self.income_models: List[Payment] = []
        self.expense_models: List[Payment] = []
        self.return_model: CompoundInterest = None
        self.dividends_model: SimpleDividends = SimpleDividends()

    def with_income(self, income: FixedIncome):
        self.income_models.append(income)

    def with_expense(self, expense: FixedExpense):
        self.expense_models.append(expense)

    def with_transfer(self, transfer: Payment):
        self.income_models.append(transfer)

    def with_expected_return(self, return_model: CapitalGains):
        self.return_model = return_model

    def with_dividends(self, dividends_model: SimpleDividends):
        self.dividends_model = dividends_model

    def simulate(self, date: date) -> Tuple[date, ...]:
        balance = self.initial_deposit_amount
        while True:
            assessment = self.assess(date, balance)
            balance = assessment.balance
            yield astuple(assessment)
            date += timedelta(days=1)

    def assess(self, date: date, balance: float) -> Assessment:
            income = sum([revenue.assess_revenue(date) for revenue in self.income_models])
            expenses = sum([expense_model.assess_revenue(date) for expense_model in self.expense_models])
            dividends = self.dividends_model.assess_revenue(date, balance)
            capital_gains = self.return_model.assess_revenue(date, balance)
            balance += income + expenses + dividends + capital_gains
            return Assessment(date=date, balance=balance, income=income, expenses=expenses, dividends=dividends, capital_gains=capital_gains)

    def get_balance_sheet(self, simulation: List[Tuple]) -> DataFrame:
        balance_sheet = DataFrame(
            data=simulation,
            columns=['date', 'balance', 'dividends', 'capital_gains'])
        balance_sheet.set_index('date', inplace=True)
        balance_sheet.index = pandas.to_datetime(balance_sheet.index)
        balance_sheet['short_term_capital_gains'] = balance_sheet['capital_gains'].rolling('365D').sum()
        balance_sheet['long_term_capital_gains'] = balance_sheet['capital_gains'].cumsum() - balance_sheet['short_term_capital_gains']
        return balance_sheet


class TraditionalIRA(InvestmentAccount):
    def __init__(self, name: str, initial_deposit_date: date, initial_deposit_amount: float, composition: Dict[str, float]):
        self.name = name
        self.initial_deposit_date = initial_deposit_date
        self.initial_deposit_amount = initial_deposit_amount
        self.composition = composition
        self.income_models: List[Payment] = []
        self.expense_models: List[Payment] = []
        self.return_model: CompoundInterest = None
        self.dividends_model: SimpleDividends = SimpleDividends()

    def simulate(self, date: date) -> Tuple[date, ...]:
        balance = self.initial_deposit_amount
        while True:
            assessment = self.assess(date, balance)
            balance = assessment.balance
            yield astuple(assessment)
            date += timedelta(days=1)

    # todo: contributions are made from post-tax income, so they have to be deducted later
    def assess(self, date: date, balance: float) -> Assessment:
        income = sum([revenue.assess_revenue(date) for revenue in self.income_models])
        expenses = sum([expense_model.assess_revenue(date) for expense_model in self.expense_models])
        dividends = self.dividends_model.assess_revenue(date, balance)
        capital_gains = self.return_model.assess_revenue(date, balance)
        balance += income + expenses + dividends + capital_gains
        return Assessment(date=date, balance=balance, income=income, expenses=expenses, dividends=dividends, capital_gains=capital_gains)
    
    def get_balance_sheet(self, simulation: List[Tuple]) -> DataFrame:
        raise NotImplementedError("Fix the column names first")
        balance_sheet = DataFrame(
            data=simulation,
            columns=['date', 'balance', 'ira_contributions', 'ira_distributions'])
        balance_sheet.set_index('date', inplace=True)
        balance_sheet.index = pandas.to_datetime(balance_sheet.index)
        return balance_sheet


class HealthSavingsAccount(TraditionalIRA):
    pass

class Traditional401K(TraditionalIRA):
    pass

class RothIRA(TraditionalIRA):
    pass