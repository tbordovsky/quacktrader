from datetime import date, timedelta
from typing import Callable, Dict, List, Tuple
from pandas import DataFrame
import pandas

from quacktrader.portfolio.account import Account
from quacktrader.portfolio.revenue import Payment, SimpleDividends, FixedExpense, FixedIncome, CompoundInterest, is_new_year

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

    def with_expected_return(self, return_model: CompoundInterest):
        self.return_model = return_model

    def with_dividends(self, dividends_model: SimpleDividends):
        self.dividends_model = dividends_model

    def assess(self, current_date: date) -> Tuple[date, float, float]:
        balance = self.initial_deposit_amount
        # todo: if date is less than initial deposit date yield 0

        while True:
            dividends = self.dividends_model.assess_revenue(balance, current_date)
            capital_gains = self.return_model.assess_revenue(balance, current_date)
            payments = sum([revenue.assess_revenue(current_date) for revenue in self.income_models])      
            balance += capital_gains + dividends + payments

            yield current_date, balance, dividends, capital_gains
            current_date += timedelta(days = 1)

    def get_balance_sheet(self, start_date: date, n_days: int) -> DataFrame:
        balance_sheet = DataFrame(
            data=self.take(start_date, n_days),
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
        self.distribution_models: List[Payment] = []
        self.return_model: CompoundInterest = None
        self.dividends_model: SimpleDividends = SimpleDividends()

    def with_transfer(self, transfer: Payment):
        self.income_models.append(transfer) if isinstance(transfer, FixedIncome) else self.distribution_models.append(transfer)

    def with_required_min_distributions(self, transfer: FixedExpense):
        self.distribution_models.append(transfer)

    # todo: contributions are made from post-tax income, so they have to be deducted later
    def assess(self, current_date: date) -> Tuple[date, ...]:
        balance = self.initial_deposit_amount
        # todo: if date is less than initial deposit date yield 0
        while True:
            dividends = self.dividends_model.assess_revenue(balance, current_date)
            capital_gains = self.return_model.assess_revenue(balance, current_date)
            ira_contributions = sum([revenue.assess_revenue(current_date) for revenue in self.income_models])
            ira_distributions = sum([revenue.assess_revenue(current_date) for revenue in self.distribution_models])
            balance += capital_gains + dividends + ira_contributions + ira_distributions
            yield current_date, balance, ira_contributions, -ira_distributions
            current_date += timedelta(days = 1)
    
    def get_balance_sheet(self, start_date: date, n_days: int) -> DataFrame:
        balance_sheet = DataFrame(
            data=self.take(start_date, n_days),
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