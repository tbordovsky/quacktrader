import abc
from datetime import date
from functools import partial
from typing import Callable, Dict, Generator, List, Tuple
from pandas import DataFrame
import pandas

from quacktrader.portfolio.revenue import FixedExpense, FixedIncome, after, before


class Account(metaclass=abc.ABCMeta):
    @classmethod
    def __subclasshook__(cls, subclass):
        return (hasattr(subclass, 'name')
            and hasattr(subclass, 'initial_deposit_amount')
            and hasattr(subclass, 'composition')
            and hasattr(subclass, 'simulate') 
            and callable(subclass.simulate)
            and hasattr(subclass, 'assess') 
            and callable(subclass.assess)
            and hasattr(subclass, 'with_income') 
            and callable(subclass.with_income)
            and hasattr(subclass, 'with_expense')
            and callable(subclass.with_expense)
            or NotImplemented)

    @abc.abstractmethod
    def assess(self, start_date: date) -> Tuple[date, ...]:
        """Assess incremental accounting information for a given date."""
        raise NotImplementedError

    @abc.abstractmethod
    def with_income(self, income: FixedIncome):
        """Register a new income model"""
        raise NotImplementedError

    @abc.abstractmethod
    def with_expense(self, expense: FixedExpense):
        """Register a new expense model"""
        raise NotImplementedError

    @abc.abstractmethod
    def get_balance_sheet(self, start_date: date, n_days: int) -> DataFrame:
        """Get the account's balance sheet as a DataFrame"""
        raise NotImplementedError

    def take(self, start_date: date, n_days: int) -> List[Tuple]:
        result = []
        balance: Generator = self.simulate(start_date)
        try:
            for n in range(n_days):
                result.append(next(balance))
        except StopIteration:
            pass
        return result


# def transfer(amount: float, transfer_period: Callable[[date], bool], source: Account, destination: Account, start_date: date = None, end_date: date = None):
#     modified_transfer_period = transfer_period
#     if start_date:
#         modified_transfer_period = lambda current_date: transfer_period(current_date) and partial(after, current_date)(start_date)
#     if end_date:
#         modified_transfer_period = lambda current_date: transfer_period(current_date) and partial(before, current_date)(end_date)
#     source.with_transfer(FixedExpense(amount, modified_transfer_period))
#     destination.with_transfer(FixedIncome(amount, modified_transfer_period))