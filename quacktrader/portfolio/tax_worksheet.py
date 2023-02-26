from bisect import bisect
from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class TaxWorksheet:
    """Based on Federal Tax Form 1040"""
    wages: float = 0
    w2_withholdings: float = 0
    interest: float = 0
    dividends: float = 0
    ira_distributions: float = 0
    annuities: float = 0
    social_security_benefits: float = 0
    capital_gains: float = 0
    deductions: float = 12550
        

federal_tax_brackets_2023: List[Tuple[float]] = [
    (10275, .10),
    (41775, .12),
    (89075, .22),
    (170050, .24),
    (215950, .32),
    (539900, .35),
    (None, .37)
]

def calculate_tax(tax_worksheet: TaxWorksheet) -> float:
    """Calculate tax liability for single filers in 2023"""
    wages = tax_worksheet.wages
    tax_exempt_interest = 0 # todo
    taxable_interest = tax_worksheet.interest
    qualified_dividends = 0 # todo
    ordinary_dividends = tax_worksheet.dividends
    ira_distributons = 0
    taxable_ira_distributions = tax_worksheet.ira_distributions
    annuities = tax_worksheet.annuities
    taxable_annuities = 0 # todo: implement taxable_annuitites for after-tax pension contributions
    social_security_benefits = 0 # todo
    taxable_social_security_benefits = tax_worksheet.social_security_benefits
    capital_gain = tax_worksheet.capital_gains # todo: implement calculation from long-term and short-term gains using 1040 Schedule D
    total_income = wages + taxable_interest + ordinary_dividends + taxable_ira_distributions + taxable_annuities + taxable_social_security_benefits + capital_gain
    other_income = 0 # todo
    adjusted_gross_income = total_income - other_income
    deduction = tax_worksheet.deductions
    charitable_contributions = 0 # todo
    qualified_business_income_deductions = 0 # todo
    total_deductions = deduction + charitable_contributions + qualified_business_income_deductions
    taxable_income = adjusted_gross_income - total_deductions
    income_tax = calculate_income_tax(taxable_income)
    other_taxes = 0 # todo
    total_tax = income_tax + other_taxes
    w2_withholdings = tax_worksheet.w2_withholdings
    form_1099_withholdings = 0 # todo
    other_withholdings = 0 # todo
    total_withholdings = w2_withholdings + form_1099_withholdings + other_withholdings
    previous_year_tax_payments = 0 # todo
    total_other_payments_and_refundable_credits = 0 # todo
    total_payments = total_withholdings + previous_year_tax_payments + total_other_payments_and_refundable_credits
    amount_owed = total_tax - total_payments
    return amount_owed

def calculate_income_tax(taxable_income: float) -> float:
    base_taxes = get_base_taxes(federal_tax_brackets_2023)
    tax_bracket_i = bisect(federal_tax_brackets_2023[:-1], (taxable_income, None))
    if not tax_bracket_i:
        return 0
    base_tax = base_taxes[tax_bracket_i]
    previous_tax_bracket_limit = federal_tax_brackets_2023[tax_bracket_i - 1][0]
    tax_rate = federal_tax_brackets_2023[tax_bracket_i][1]
    tax_in_bracket = (taxable_income - previous_tax_bracket_limit) * tax_rate
    return base_tax + tax_in_bracket

def get_base_taxes(tax_brackets: List[Tuple[float]]) -> List[float]:
        base_taxes = [0]
        last_tax_bracket = 0
        base_tax = 0
        for tax_bracket, tax_rate in tax_brackets[:-1]:
            base_tax += (tax_bracket - last_tax_bracket) * tax_rate
            base_taxes.append(base_tax)
            last_tax_bracket = tax_bracket
        return base_taxes