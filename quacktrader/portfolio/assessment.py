from dataclasses import dataclass
from datetime import date


@dataclass
class Assessment:
    date: date
    balance: float
    income: float = 0
    w2_withholdings: float = 0
    expenses: float = 0
    interest: float = 0
    social_security_benefits: float = 0
    dividends: float = 0
    ira_distributions: float = 0
    annuities: float = 0
    capital_gains: float = 0
