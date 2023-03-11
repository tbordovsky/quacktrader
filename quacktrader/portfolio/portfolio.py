from collections import deque
from datetime import date, timedelta
import math
import pprint
from typing import Callable, Deque, Dict, Generator, List, Set, Tuple
from pandas import pandas, DataFrame, Series
from matplotlib import pyplot

from quacktrader.portfolio.account import Account
from quacktrader.portfolio.assessment import Assessment
from quacktrader.portfolio.revenue import FixedIncome, calculate_required_minimum_distribution, count_annual_occurrences, is_first_of_the_year
from quacktrader.portfolio.tax_worksheet import TaxWorksheet, calculate_tax

class Transfer(FixedIncome):
    def __init__(self, payment: float, transfer_period: Callable[[date], bool], source: Account, destination: Account):
        self.payment = payment
        self.credit_period = transfer_period
        self.source = source
        self.destination = destination

class IraDistribution(Transfer):
    def __init__(self, payment: float, transfer_period: Callable[[date], bool], source: Account, destination: Account):
        self.payment = payment
        self.credit_period = transfer_period
        self.source = source
        self.destination = destination

    def assess(self, current_date: date, current_balance: float) -> float:
        return self.payment if self.credit_period(current_date) else 0

class RequiredMininumDistribution(IraDistribution):
    def __init__(self, birthday: date, transfer_period: Callable[[date], bool], source: Account, destination: Account):
        self.birthday = birthday
        self.credit_period = transfer_period
        self.source = source
        self.destination = destination
        self.annual_withdrawal_occurrences = count_annual_occurrences(transfer_period)
        self.starting(self.birthday + timedelta(days=72*365))

    def assess(self, current_date: date, current_balance: float) -> float:
        age = current_date.year - self.birthday.year
        return calculate_required_minimum_distribution(age, current_balance, self.annual_withdrawal_occurrences) if self.credit_period(current_date) else 0
        

class Portfolio:
    def __init__(self):
        self._accounts: Set[Account] = set()
        self._transfer_models: List[Transfer] = []
        self._ira_distribution_models: List[IraDistribution] = []

    def with_account(self, account: Account):
        self._accounts.add(account)

    def set_primary_account(self, account_name: str):
        self._primary_account = self.find_account_by_name(account_name)

    def find_account_by_name(self, account_name: str) -> Account:
        try:
            return next(account for account in self._accounts if account.name == account_name)
        except StopIteration:
            message = f"{account_name} was not found in the list of accounts."
            raise Exception(message)


    def with_transfer(self, transfer: Transfer):
        """Register a new transfer model"""
        self._transfer_models.append(transfer)

    def with_ira_distribution(self, transfer: Transfer):
        """Register a new IRA distribution model"""
        self._ira_distribution_models.append(transfer)

    class AccountContainer:
        def __init__(self, account: Account):
            self.name: str = account.name
            self.balance: float = account.initial_deposit_amount
            self.assess = account.assess
            self.capital_gains_queue: Deque[float] = deque(maxlen=365)
            self.short_term_capital_gains: float = 0
            self.long_term_capital_gains: float = 0
        
        def accumulate_capital_gains(self, capital_gains: float):
            """Assuming capital gains for an account is assessed every day"""
            if (len(self.capital_gains_queue) == self.capital_gains_queue.maxlen):
                capital_gains_matured = self.capital_gains_queue.pop()
                self.long_term_capital_gains += capital_gains_matured
                self.short_term_capital_gains = max(self.short_term_capital_gains - capital_gains_matured, 0)
            self.capital_gains_queue.append(capital_gains)
            self.short_term_capital_gains += capital_gains

        def realize_capital_gains(self, sale_amount: float) -> float:
            if (sale_amount > 0):
                overdraw = min(self.long_term_capital_gains + self.short_term_capital_gains - sale_amount, 0)
                self.long_term_capital_gains -= sale_amount
                if (self.long_term_capital_gains < 0):
                    self.short_term_capital_gains += self.long_term_capital_gains
                    self.long_term_capital_gains = 0
                    self.short_term_capital_gains = max(self.short_term_capital_gains, 0)
                return sale_amount + overdraw
            else:
                return 0

        def apply_transfer(self, transfer_amount) -> float:
            actual_transfer_amount = 0
            if (transfer_amount != 0):
                overdraw = min(self.balance + transfer_amount, 0)
                actual_transfer_amount = transfer_amount - overdraw
                self.balance += actual_transfer_amount
            return actual_transfer_amount


    def take(self, start_date: date, n_days: int) -> List[Tuple]:
        result = []
        balance: Generator = self.simulate(start_date)
        try:
            for n in range(n_days):
                result.append(next(balance))
        except StopIteration:
            pass
        return result

    def simulate(self, date: date) -> Tuple[date, ...]:
        accounts_by_name = {account.name: self.AccountContainer(account) for account in self._accounts}
        primary_account = accounts_by_name.get(self._primary_account.name)

        wages: float = 0
        w2_withholdings: float = 0
        social_security_benefits: float = 0
        dividends: float = 0
        ira_distributions: float = 0
        annuities: float = 0
        capital_gains: float = 0
        taxes: float = 0

        while True:
            for account in accounts_by_name.values():
                assessment: Assessment = account.assess(date, account.balance)
                account.balance += sum([assessment.income, assessment.expenses, assessment.interest, assessment.social_security_benefits, assessment.dividends,
                                        assessment.annuities, assessment.capital_gains])
                wages += assessment.income + assessment.w2_withholdings
                w2_withholdings += assessment.w2_withholdings
                social_security_benefits += assessment.social_security_benefits
                dividends += assessment.dividends
                annuities += assessment.annuities
                account.accumulate_capital_gains(assessment.capital_gains)
                # deductions += getDeductions()?

            for ira_distribution in self._ira_distribution_models:
                source = accounts_by_name.get(ira_distribution.source.name)
                destination = accounts_by_name.get(ira_distribution.destination.name)
                distribution_amount = ira_distribution.assess(date, source.balance)
                source.balance -= distribution_amount
                destination.balance += distribution_amount
                ira_distributions += distribution_amount

            for transfer in self._transfer_models:
                source = accounts_by_name.get(transfer.source.name)
                destination = accounts_by_name.get(transfer.destination.name)
                transfer_amount = transfer.assess_revenue(date)
                actual_transfer_amount = -source.apply_transfer(-transfer_amount)
                destination.apply_transfer(actual_transfer_amount)
                capital_gains += source.realize_capital_gains(actual_transfer_amount)

            if is_first_of_the_year(date):
                tax_worksheet = TaxWorksheet(wages=wages,
                                             w2_withholdings=w2_withholdings,
                                             social_security_benefits=social_security_benefits,
                                             dividends=dividends,
                                             ira_distributions=ira_distributions,
                                             annuities=annuities,
                                             capital_gains=capital_gains)
                wages, w2_withholdings, social_security_benefits, dividends, ira_distributions, annuities, capital_gains = 0, 0, 0, 0, 0, 0, 0
                taxes = calculate_tax(tax_worksheet)
                primary_account.balance += taxes

            yield (date,) + tuple([account.balance for account in accounts_by_name.values()]) + (taxes,)
            date += timedelta(days=1)
            taxes = 0

    def get_balance_sheet(self, simulation: List[Tuple]) -> DataFrame:
        balance_sheet = DataFrame(
            data=simulation,
            columns=['date'] + [account.name for account in self._accounts] + ['taxes'])
        balance_sheet.set_index('date', inplace=True)
        balance_sheet.index = pandas.to_datetime(balance_sheet.index)
        balance_sheet['total'] = balance_sheet[[account.name for account in self._accounts]].sum(axis=1)
        return balance_sheet

    def tabulate_composition(self, balance_sheet: DataFrame) -> Series:
        total_composition = {}
        for account in self._accounts:
            account_balance = balance_sheet[account.name].iloc[-2]
            account_composition: Dict[str, float] = account.composition
            for ticker, percent_per_ticker in account_composition.items():
                total_composition[ticker] = total_composition.get(ticker, 0) + (account_balance * percent_per_ticker)
        return Series(total_composition)

    def simulate_and_plot(self, start_date: date, simulation_period: int) -> DataFrame:
        balance_sheet = self.simulate(start_date, simulation_period)
        composition = self.tabulate_composition(balance_sheet)

        # just plot the line chart
        balance_sheet.plot()

        # plot with line and pie chart
        # fig, axes = pyplot.subplots(1, 2)
        # balance_sheet.plot(ax=axes[0], x='date', y='total')
        # composition.plot.pie(
        #     ax = axes[1],
        #     shadow = False,
        #     startangle = 90,
        #     autopct = '%1.1f%%',
        #     figsize = (15,5))
        pyplot.show()
        return balance_sheet

def date_range(start_date: date, simulation_period: int) -> date:
    for n in range(simulation_period):
        yield start_date + timedelta(n)