from dataclasses import astuple
from datetime import date, timedelta
from typing import Dict, List, Tuple
from pandas import DataFrame
import pandas

from quacktrader.portfolio.account import Account
from quacktrader.portfolio.assessment import Assessment
from quacktrader.portfolio.revenue import FixedExpense, FixedIncome, CompoundInterest, Payment, Salary, is_new_year

class DepositAccount(Account):
    def __init__(self, name: str, initial_deposit_date: date, initial_deposit_amount: float):
        self.name = name
        self.initial_deposit_date = initial_deposit_date
        self.initial_deposit_amount = initial_deposit_amount
        self.income_models: List[FixedIncome] = []
        self.expense_models: List[FixedExpense] = []
        self.salary_model: Salary = None #Salary(payment=0, credit_period=lambda x: False, annual_gross=0, w2_withholdings=0)
        self.interest_model: CompoundInterest = None
        self.composition: Dict[str, float] = {'$USD': 100}

    def with_income(self, income: FixedIncome):
        self.income_models.append(income)

    def with_expense(self, expense: FixedExpense):
        self.expense_models.append(expense)

    def with_salary(self, salary: Salary):
        self.salary_model = salary

    def with_interest(self, interest_model: CompoundInterest):
        self.interest_model = interest_model

    def simulate(self, date: date) -> Tuple[date, ...]:
        balance = self.initial_deposit_amount
        while True:
            assessment = self.assess(date, balance)
            balance = assessment.balance
            yield astuple(assessment)
            date += timedelta(days=1)

    def assess(self, date: date, balance: float) -> Assessment:
        interest = self.interest_model.assess_revenue(date, balance) if self.interest_model else 0
        income = self.salary_model.assess_revenue(date) if self.salary_model else 0
        w2_withholdings = self.salary_model.assess_withholdings(date) if self.salary_model else 0
        income += sum([income_model.assess_revenue(date) for income_model in self.income_models])
        expenses = sum([expense_model.assess_revenue(date) for expense_model in self.expense_models])
        social_security_benefits = 0 # todo
        balance += income + interest + expenses + social_security_benefits
        return Assessment(date=date, balance=balance, income=income, w2_withholdings=w2_withholdings, expenses=expenses, interest=interest, social_security_benefits=social_security_benefits)

    def get_balance_sheet(self, simulation: List[Tuple]) -> DataFrame:
        raise NotImplementedError("Fix the column names first")
        balance_sheet = DataFrame(
            data=simulation,
            columns=['date', 'balance', 'income', 'w2_withholdings', 'expenses', 'interest', 'social_security_benefits'])
        balance_sheet.set_index('date', inplace=True)
        balance_sheet.index = pandas.to_datetime(balance_sheet.index)
        return balance_sheet