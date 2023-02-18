from datetime import date
from typing import Dict, List
from pandas import pandas, DataFrame, Series, Grouper, concat
from matplotlib import pyplot

from quacktrader.portfolio.account import Account
from quacktrader.portfolio.tax_worksheet import TaxWorksheet, calculate_tax


class Portfolio:
    def __init__(self):
        self._accounts: List[Account] = []

    def with_account(self, account: Account):
        self._accounts.append(account)

    def simulate(self, start_date: date, simulation_period: int) -> DataFrame:
        portfolio_balance_sheet = None
        tax_worksheet = None
        for account in self._accounts:
            balance_sheet = account.get_balance_sheet(start_date, simulation_period)
            portfolio_balance_sheet = portfolio_balance_sheet.merge(balance_sheet['balance'], on='date', how='left') if portfolio_balance_sheet is not None else DataFrame(balance_sheet['balance'])
            portfolio_balance_sheet.rename(columns={'balance': account.name}, inplace=True)

        tax_worksheet_columns = DataFrame(columns = ["date", "wages", "interest", "dividends", "ira_distributions", "annuities", "social_security_benefits", "capital_gains", "w2_withholdings"])
        tax_worksheet_columns.set_index('date', inplace=True)
        tax_worksheet_columns.index = pandas.to_datetime(tax_worksheet_columns.index)
        tax_worksheet = concat([tax_worksheet_columns] + [account.get_balance_sheet(start_date, simulation_period) for account in self._accounts], sort=False, axis=1)
        tax_worksheet.drop(columns=['balance', 'short_term_capital_gains', 'long_term_capital_gains'], inplace=True) # we haven't implemented short/long-term at the portfolio level yet
        tax_worksheet = tax_worksheet.groupby(level=0, axis=1).sum()
        tax_worksheet = tax_worksheet.resample('1Y').sum()
        tax_worksheet['total_tax'] = tax_worksheet.apply(lambda x: 
            calculate_tax(TaxWorksheet(wages=x['wages'], 
                                       interest=x['interest'],
                                       dividends=x['dividends'],
                                       ira_distributions=x['ira_distributions'],
                                       annuities=x['annuities'],
                                       social_security_benefits=x['social_security_benefits'],
                                       capital_gains=x['capital_gains'],
                                    #    deduction=get_deductions(), # todo
                                       w2_withholdings=x['w2_withholdings'])), axis=1)
        print(tax_worksheet.tail())

        portfolio_balance_sheet['gross'] = portfolio_balance_sheet.iloc[:, -len(self._accounts):].sum(axis=1)
        portfolio_balance_sheet['taxes'] = tax_worksheet['total_tax']
        portfolio_balance_sheet['taxes'] = portfolio_balance_sheet['taxes'].fillna(0)
        portfolio_balance_sheet['net'] = portfolio_balance_sheet['gross'].subtract(portfolio_balance_sheet['taxes'].cumsum())
        return portfolio_balance_sheet

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
