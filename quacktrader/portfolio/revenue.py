import abc
from datetime import date, timedelta
from functools import partial
import math
from typing import Callable, Self


class Payment(metaclass=abc.ABCMeta):
    @classmethod
    def __subclasshook__(cls, subclass):
        return (hasattr(subclass, 'payment') 
            and hasattr(subclass, 'assess_revenue') 
            and callable(subclass.assess_revenue)
            and hasattr(subclass, 'starting') 
            and callable(subclass.starting)
            and hasattr(subclass, 'until') 
            and callable(subclass.until)
            or NotImplemented)

    @abc.abstractmethod
    def assess_revenue(self, current_date: date) -> float:
        """Assess revenue from the given start date and on"""
        raise NotImplementedError

    @abc.abstractmethod
    def starting(self, start_date: date) -> Self:
        """Omit income assessments before the start date"""
        raise NotImplementedError

    @abc.abstractmethod
    def until(self, end_date: date) -> Self:
        """Omit income assessments after the end date"""
        raise NotImplementedError


class FixedIncome(Payment):
    def __init__(self, payment: float, credit_period: Callable[[date], bool]):
        self.payment = payment
        self.credit_period = credit_period

    def assess_revenue(self, current_date: date) -> float:
        return self.payment if self.credit_period(current_date) else 0

    def starting(self, start_date: date) -> Self:
        credit_period = self.credit_period
        self.credit_period = lambda current_date: credit_period(current_date) and partial(after, current_date)(start_date)
        return self

    def until(self, end_date: date) -> Self:
        credit_period = self.credit_period
        self.credit_period = lambda current_date: credit_period(current_date) and partial(before, current_date)(end_date)
        return self


class FixedExpense(Payment):
    def __init__(self, payment: float, debit_period: Callable[[date], bool]):
        self.payment = payment
        self.debit_period = debit_period

    def assess_revenue(self, current_date: date) -> float:
        return -self.payment if self.debit_period(current_date) else 0

    def starting(self, start_date: date) -> Self:
        debit_period = self.debit_period
        self.debit_period = lambda current_date: debit_period(current_date) and partial(after, current_date)(start_date)
        return self

    def until(self, end_date: date) -> Self:
        debit_period = self.debit_period
        self.debit_period = lambda current_date: debit_period(current_date) and partial(before, current_date)(end_date)
        return self

class RequiredMinimumDistribution(Payment):
    def __init__(self, debit_period: Callable[[date], bool]):
        self.debit_period = debit_period

    def assess_revenue(self, current_date: date, current_balance: float) -> float:
        age = current_date - birthday
        return calculate_required_min_distribution(age, current_balance, debit_period) if age >= 72 and self.debit_period(current_date) else 0





class Salary(Payment):
    # todo: use payment or annual gross, not both
    def __init__(self, payment: float, credit_period: Callable[[date], bool], annual_gross: float, w2_withholdings: float):
        """Constructs a new Salary object with its required attributes.

        Parameters
        ----------
            payment: float
                payment received excepting after-tax deductions, which should be handled as transfers
            credit_period: Callable[[date], bool]
                a function that returns True given an expected payday
            w2_withholdings: float
                expected annual federal withholdings, excluding other employee taxes or fees like social security and medicare
        """
        self.payment = payment
        self.credit_period = credit_period
        self.annual_payment_periods = count_annual_occurrences(credit_period)
        self.w2_withholdings = w2_withholdings

    def assess_revenue(self, current_date: date) -> float:
        return self.payment if self.credit_period(current_date) else 0

    def assess_withholdings(self, current_date: date) -> float:
        return self.w2_withholdings / self.annual_payment_periods if self.credit_period(current_date) else 0

    def starting(self, start_date: date) -> Self:
        credit_period = self.credit_period
        self.credit_period = lambda current_date: credit_period(current_date) and partial(after, current_date)(start_date)
        return self

    def until(self, end_date: date) -> Self:
        credit_period = self.credit_period
        self.credit_period = lambda current_date: credit_period(current_date) and partial(before, current_date)(end_date)
        return self


class CapitalGains(metaclass=abc.ABCMeta):
    @classmethod
    def __subclasshook__(cls, subclass):
        return (hasattr(subclass, 'assess_capital_gains') 
            and callable(subclass.assess_capital_gains)
            or NotImplemented)

    @abc.abstractmethod
    def assess_revenue(self, balance: float, current_date: date) -> float:
        """Assess revenue from the given start date and on"""
        raise NotImplementedError


class CompoundInterest(CapitalGains):
    """Model returns as compound interest."""
    def __init__(self, interest_rate: float, compounding_period: Callable[[date], bool]):
        self.interest_rate = interest_rate
        self.compounding_period = compounding_period

    def assess_revenue(self, current_balance: float, current_date: date) -> float:
        return max(self.interest_rate * current_balance, 0) if self.compounding_period(current_date) else 0

class SimpleReturns(CapitalGains):
    """
    Model returns as compound interest, with some adjustments made to account for a larger number of compounding periods like in market returns.
    """
    def __init__(self, annualized_return: float, credit_period: Callable[[date], bool]):
        self.annualized_return = annualized_return
        self.credit_period = credit_period
        self._return_per_period = periodize_annual_returns(annualized_return, credit_period)

    def assess_revenue(self, current_balance: float, current_date: date) -> float:
        return max(self._return_per_period * current_balance, 0) if self.credit_period(current_date) else 0

class SimpleDividends(CapitalGains):
    """
    This is a simplified model of dividends that more closely approximates capital gains.
    The payout ratio is not a true payout ratio, rather it is a return based on equity and is assessed every credit period.
    """
    def __init__(self, payout_ratio: float = 0, credit_period: Callable[[date], bool] = lambda x: False):
        self.payout_ratio = payout_ratio
        self.credit_period = credit_period

    def assess_revenue(self, current_balance: float, current_date: date) -> float:
        return max(self.payout_ratio * current_balance, 0) if self.credit_period(current_date) else 0


def is_every_day(date: date) -> bool:
    return True

def is_friday_biweekly(date: date) -> bool:
    """
    Deposits arrive on Friday, every two weeks.
    These hard-coded values are intended to model a biweekly pay schedule.
    """
    return date.isocalendar()[1] % 2 == 0 and date.timetuple().tm_wday == 4

def is_monday_biweekly(date: date) -> bool:
    return date.isocalendar()[1] % 2 == 0 and date.timetuple().tm_wday == 0

def is_first_of_the_month(date: date) -> bool:
    return date.timetuple().tm_mday == 1

def is_semiannual(date: date) -> bool:
    return (date.isocalendar()[1] == 1 or date.isocalendar()[1] == 27) and date.isocalendar()[2] == 4

def is_quarterly(date: date) -> bool:
    """Assessed quarterly, on Friday"""
    return date.isocalendar()[1] % 16 == 0 and date.isocalendar()[2] == 5

def is_annual(date: date) -> bool:
    """
    Assess annually, at the end of the year.
    """
    return date.isocalendar()[1] == 52 and date.isocalendar()[2] == 1

def is_annual_in_may(date: date) -> bool:
    return date.isocalendar()[1] == 20 and date.isocalendar()[2] == 4

def is_trading_day_2023(date: date) -> bool:
    """
    Assess on trading days, excepting holidays published by the NYSE for 2023.
    This is only accurate for 2023, but it should be a close approximation for other years.
    """
    return (date.isoweekday() in range(1,5) # is a weekday
        and not (date.isocalendar()[1] == 1 and date.isocalendar()[2] == 1) # new years
        and not (date.isocalendar()[1] == 3 and date.isocalendar()[2] == 1) # mlk day
        and not (date.isocalendar()[1] == 8 and date.isocalendar()[2] == 1) # washington's birthday
        and not (date.isocalendar()[1] == 14 and date.isocalendar()[2] == 5) # good friday
        and not (date.isocalendar()[1] == 22 and date.isocalendar()[2] == 1) # memorial day
        and not (date.isocalendar()[1] == 25 and date.isocalendar()[2] == 1) # juneteenth
        and not (date.isocalendar()[1] == 27 and date.isocalendar()[2] == 2) # independence day
        and not (date.isocalendar()[1] == 36 and date.isocalendar()[2] == 1) # labor day
        and not (date.isocalendar()[1] == 47 and date.isocalendar()[2] == 4) # thanksgiving day
        and not (date.isocalendar()[1] == 52 and date.isocalendar()[2] == 1) # christmas day
        )

def is_monthly_on_the_8th(date: date) -> bool:
    return date.timetuple().tm_mday == 8

def is_monthly_on_the_25th(date: date) -> bool:
    return date.timetuple().tm_mday == 25

def is_new_year(date: date) -> bool:
    return date.timetuple().tm_yday == 1

def before(date: date, end_date: date) -> bool:
    return date < end_date

def after(date: date, start_date: date) -> bool:
    return date > start_date
    
# (x^n)^1/n = (y^m)^1/m; where n=1
# (1/n)log(x^n) = (1/m)log(y^m)
# 

# share_price = 100
# annual_growth = .10
# periods = 200
# growth_per_period = pow(1 + annual_growth, 1 / periods)
# for i in range(periods):
#     share_price *= growth_per_period
# print(share_price)

def periodize_annual_returns(annual_returns: float, credit_period: Callable[[date], bool]) -> float:
    """Calculate the geometric average return for a given number of occurrences"""
    annual_compounding_periods = count_annual_occurrences(credit_period)
    return pow(1 + annual_returns, 1 / annual_compounding_periods) - 1

def count_annual_occurrences(credit_period: Callable[[date], bool]) -> int:
    return sum([credit_period(current_date) for current_date in (date(1, 1, 1) + timedelta(n) for n in range(365))])

# Required Minimal Distributions from IRA starting with age 70
RMD = [27.4, 26.5, 25.6, 24.7, 23.8, 22.9, 22.0, 21.2, 20.3, 19.5,  # age 70-79
       18.7, 17.9, 17.1, 16.3, 15.5, 14.8, 14.1, 13.4, 12.7, 12.0,  # age 80-89
       11.4, 10.8, 10.2,  9.6,  9.1,  8.6,  8.1,  7.6,  7.1,  6.7,  # age 90-99
        6.3,  5.9,  5.5,  5.2,  4.9,  4.5,  4.2,  3.9,  3.7,  3.4,  # age 100+
        3.1,  2.9,  2.6,  2.4,  2.1,  1.9,  1.9,  1.9,  1.9,  1.9]

def calculate_required_minimum_distribution(age: int, account_balance: float, credit_period: Callable[[date], bool]) -> float:
    withdrawal_factor = RMD[age - 72]
    annual_withdrawal = account_balance / withdrawal_factor
    annual_withdrawal_occurrences = count_annual_occurrences(credit_period)
    return annual_withdrawal / annual_withdrawal_occurrences
    
