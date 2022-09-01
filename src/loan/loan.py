
import datetime
import logging

from .db import DB

log = logging.getLogger('db')
log.setLevel('DEBUG')


class Loan:
    """
    Computer for loan payment

    Class Attributes
    ----------------
    annual_rate: float
        Annual interest rate.
    percentage_cost: float
        Camca cost at 1.1 percent of total amount.
    length: int
        Number of months to repay the credit.
    """
    annual_rate = 2 / 100
    percentage_cost = 1.1 / 100
    length = 25 * 12
    
    def __init__(self, amount, processing_cost, monthly_cost):
        """
        Parameters
        ----------
        amount: float
            Amount borrowed (in euros).
        processing_cost: float
            Amount in euros to process the applications
        monthly_cost: float
            Amount of the monthly insurance.
        """
        self.rate = self.annual_rate / 12
        self.upfront_cost = self.percentage_cost * amount
        self.processing_cost = processing_cost
        self.monthly_cost = monthly_cost
        self.monthly_repay = self.period_repay(self.rate, self.length) * amount

    @staticmethod
    def period_repay(rate, num_periods):
        return rate * (1 + rate) ** num_periods / ((1 + rate) ** num_periods - 1)

    @property
    def total_repay(self):
        return self.monthly_cost * self.length
    
    @property
    def total_cost(self):
        return (self.monthly_repay + self.monthly_cost) * self.length + self.upfront_cost + self.processing_cost


async def populate_timeline(database: DB):
    """
    Populate `timeline` table in the specified database

    Parameters
    ----------
    database: DB Object
    """
    joint_loan = Loan(100000, 1000, 2*30)
    user_1_loan = Loan(60000, 600, 30)
    user_2_loan = Loan(40000, 400, 30)

    amount = joint_loan.processing_cost
    user_1 = user_1_loan.processing_cost
    user_2 = user_2_loan.processing_cost
    date = datetime.date(2022, 7, 6)
    await database.write_mensuality(amount, user_1, user_2, date, 1, 'fee')

    amount = joint_loan.upfront_cost
    user_1 = user_1_loan.upfront_cost
    user_2 = user_2_loan.upfront_cost
    await database.write_mensuality(amount, user_1, user_2, date, 1, 'fee')

    log.info('Loan upfront cost written.')

    for i in range(joint_loan.length):
        amount = joint_loan.monthly_repay
        user_1 = user_1_loan.monthly_repay
        user_2 = user_2_loan.monthly_repay

        month = (7 + i) % 12 + 1
        year = (7 + i) // 12 + 2022
        date = datetime.date(year, month, 6)
        await database.write_mensuality(amount, user_1, user_2, date, i + 1, 'loan')

        amount = joint_loan.monthly_cost
        user_1 = user_1_loan.monthly_cost
        user_2 = user_2_loan.monthly_cost
        await database.write_mensuality(amount, user_1, user_2, date, i + 1, 'insurance')
    
    log.info('Loan mensuality written.')
