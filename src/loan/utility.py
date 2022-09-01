
import datetime
from pathlib import Path


class Config:
    DB_NAME = 'loan'
    DB_USERS = [
        'joint',
        'user_1',
        'user_2', 
    ]
    REQUESTERS = [
        'fee',
        'insurance',
        'loan'
    ]
    STACKHOLDERS = [
        'appliances',
        'bank',
        'dosmetic',
        'furniture',
        'insurance',
        'joint',
        'user_1',
        'user_2'
    ]
    PROPERTY_PERCENTAGE = 42
    LOAN_PERCENTAGE = 48.55
    PATH = Path.home() / 'code' / 'loan'
    TARGET_PATH = Path.home() / 'Documents' / 'loan_statements'


def get_most_recent_path(dirpath):
    """
    Enumerate filename into a dirpath and get the most recent one, which is supposed to be the last one with lexicographic order.
    """
    pass


def parse_date(date):
    if date is None:
        return datetime.date.today()
    if isinstance(date, datetime.date):
        return date
    if isinstance(date, datetime.datetime):
        return date.date()
    if isinstance(date, str):
        if '/' in date:
            return datetime.datetime.strptime(date, '%Y/%m/%d').date()
        if '-' in date:
            return datetime.datetime.strptime(date, '%Y-%m-%d').date()


class AmountConverter:
    @staticmethod
    def to_db(amount):
        return round(amount * 100)

    @staticmethod
    def from_db(amount):
        return amount / 100