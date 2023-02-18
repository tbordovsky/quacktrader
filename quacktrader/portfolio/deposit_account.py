from datetime import date, timedelta
from typing import Dict, List, Tuple
from pandas import DataFrame
import pandas

from quacktrader.portfolio.account import Account
from quacktrader.portfolio.revenue import FixedExpense, FixedIncome, CompoundInterest, Payment, Salary, is_new_year

class DepositAccount(Account):
    def __init__(self, name: str, initial_deposit_date: date, initial_deposit_amount: float):
        self.name = name
        self.initial_deposit_date = initial_deposit_date
        self.initial_deposit_amount = initial_deposit_amount
        self.income_models: List[FixedIncome] = []
        self.expense_models: List[FixedExpense] = []
        self.transfer_models: List[Payment] = []
        self.salary_model: Salary = None #Salary(payment=0, credit_period=lambda x: False, annual_gross=0, w2_withholdings=0)
        self.interest_model: CompoundInterest = None
        self.composition: Dict[str, float] = {'$USD': 100}

    def with_income(self, income: FixedIncome):
        self.income_models.append(income)

    def with_expense(self, expense: FixedExpense):
        self.expense_models.append(expense)

    def with_transfer(self, transfer: Payment):
        self.transfer_models.append(transfer)

    def with_salary(self, salary: Salary):
        self.salary_model = salary

    def with_interest(self, interest_model: CompoundInterest):
        self.interest_model = interest_model

    def assess(self, date: date) -> Tuple[date, ...]:
        balance = self.initial_deposit_amount
        while True:
            interest = self.interest_model.assess_revenue(balance, date) if self.interest_model else 0
            income = self.salary_model.assess_revenue(date) if self.salary_model else 0
            w2_withholdings = self.salary_model.assess_withholdings(date) if self.salary_model else 0
            income = sum([income_model.assess_revenue(date) for income_model in self.income_models])
            transfers = sum([transfer.assess_revenue(date) for transfer in self.transfer_models])
            expenses = sum([expense_model.assess_revenue(date) for expense_model in self.expense_models])
            balance += income + interest + transfers + expenses
            wages = income + w2_withholdings

            yield date, balance, wages, w2_withholdings, interest
            date += timedelta(days = 1)

    def get_balance_sheet(self, start_date: date, n_days: int) -> DataFrame:
        full_sheet = DataFrame(
            data=self.take(start_date, n_days),
            columns=['date', 'balance', 'wages', 'w2_withholdings', 'interest'])
        full_sheet.set_index('date', inplace=True)
        full_sheet.index = pandas.to_datetime(full_sheet.index)
        return full_sheet