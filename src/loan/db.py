
import datetime
import logging

import asyncpg

from .utility import (
    AmountConverter,
    Config,
    parse_date
)

log = logging.getLogger('db')
log.setLevel('INFO')


class DB:
    """
    Module to interact with the postgreSQL database.
    """
    def __init__(self):
        pass

    async def start(self):
        """
        Start connection to the database.
        """
        try:
            self.pool = await asyncpg.create_pool(database=Config.DB_NAME)
        except ConnectionRefusedError:
            log.error('Could not connect to database.')
            raise
        else:
            log.info(f'Connected to database {Config.DB_NAME}.')

    async def init(self):
        """
        Initialize the database based on `init_db.sql`.
        """
        with open(Config.PATH / 'src' / 'sql' / 'init_db.sql') as f:
            schema_sql = f.read()
        await self.execute(schema_sql)
        log.info('Database initialized.')

    async def fetch(self, sql, *args):
        async with self.pool.acquire() as connection:
            async with connection.transaction():
                return await connection.fetch(sql, *args)
        
    async def execute(self, sql, *args):
        async with self.pool.acquire() as connection:
            async with connection.transaction():
                return await connection.execute(sql, *args)
        
    async def reset_table(self, name):
        """
        Delete all values in a table.
        """
        log.info(f'Reseting table {name}')
        await self.execute(f'''TRUNCATE TABLE {name}''')

    async def write_mensuality(self, amount: float, user_1: str, user_2: str, date, month: int, requester: str):
        """
        Populate `timeline` table with due mensualities.
        """
        amount = AmountConverter.to_db(amount)
        user_1  = AmountConverter.to_db(user_1)
        user_2 = AmountConverter.to_db(user_2)
        date = parse_date(date)
        if requester not in Config.REQUESTERS:
            log.error(f'Requester {requester} not recognized.')
            raise ValueError

        if user_1 + user_2 != amount:
            log.error(f'Amounts {user_1} and {user_2} do not sum to {amount}.')
            raise ValueError

        # Write transaction to the database
        log.debug(f'Writing {requester} mensuality {month} to timeline table.')
        await self.execute('''
            INSERT INTO timeline(
                amount, user_1, user_2, date, fill, month, request
            ) 
            VALUES(
                $1, $2, $3, $4, $5, $6, $7
            )''',
            amount, user_1, user_2, date, False, month, requester
        )

    async def account_mensuality(self):
        """
        Record all past requests from the bank according to the `timeline` table. 
        """
        date = datetime.date.today()

        records = await self.fetch('''
            SELECT * FROM timeline
            WHERE date < $1 AND fill = $2
        ''', date, False)
        
        if not len(records):
            log.debug(f'All mensualities have been paid so far.')
            return
        elif len(records) == 1:
            log.info(f'Loading due mensuality.')
        else:
            log.info(f'Loading due {len(records)} mensualities.')

        for record in records:
            id = record['id']
            user_1 = AmountConverter.from_db(record['user_1'])
            user_2 = AmountConverter.from_db(record['user_2'])
            amount = AmountConverter.from_db(record['amount'])
            date = record['date']
            operation = record['request']

            if amount != user_2 + user_1:
                log.error(f'Amounts {user_2} and {user_1} do not sum up to {amount}.')

            await self.record_transaction('user_1', -user_1, date, 'bank', operation)
            await self.record_transaction('user_2', -user_2, date, 'bank', operation)
            await self.record_transaction('joint', -amount, date, 'bank', operation)
            log.info(f'Balance updated according to due mensuality {record["month"]}.')

            # Update the timeline record.
            await self.execute('''
                UPDATE timeline 
                    SET fill=$1
                WHERE id=$2
            ''', True, id)

    async def record_transaction(self, user: str, amount: float, date=None, recipient: str=None, operation: str = None):
        """
        Write transactions to the `wire` table in the database.

        A negative `amount` means that we debit money to `user`.
        """
        log.debug('Parsing wire arguments.')
        if user not in Config.DB_USERS:
            log.error(f'Users {user} not recognized')
            raise ValueError 
        db_amount = AmountConverter.to_db(amount)
        if db_amount > 0:
            credit = db_amount
            debit = 0
        else:
            credit = 0
            debit = -db_amount
        date = parse_date(date)

        log.debug('Writing transaction to `wire` table.')
        await self.execute('''
            INSERT INTO wire(
                account, date, object, operation, debit, credit
            ) VALUES(
                $1, $2, $3, $4, $5, $6
            )''',
            user, date, recipient, operation, debit, credit
        )
        await self.update_balance(user, amount, date)

    async def update_balance(self, user: str, amount: float, date: datetime.date):
        """
        Update balance based on wire amount.

        Parameters
        ----------
        user: Account identifier.
        amount: Positive in money flows in, negative it it flows out.
        """
        old_date, debit, credit, balance = await self.get_balance(user)

        log.debug('Parsing balance arguments.')
        amount = AmountConverter.to_db(amount)
        balance += amount
        if amount > 0:
            credit += amount
        else:
            debit -= amount
        date = max(date, old_date)

        await self.execute('''
            UPDATE balance 
                SET (date, debit, credit, balance) = ($1, $2, $3, $4)
            WHERE account=$5
        ''', date, debit, credit, balance, user)
        log.info(f'Updated {user} balance.')

    async def get_balance(self, user: str):
        """
        Get user balance information.
        """
        log.debug(f'Loading {user} balance.')
        records = await self.fetch('''
            SELECT * FROM balance WHERE account=$1
        ''', user)
        record = records[0]
        return record['date'], record['debit'], record['credit'], record['balance']

    async def get_date_balance(self, user, date):
        """
        Get balance for `user` at specified date.
        """
        date = parse_date(date)
        log.info(f'Retriving {user} balance on {date}.')
        records = await self.load_wire(user=user, stop_date=date)
        balance = 0
        for record in records:
            balance += record['credit'] - record['debit']
        return AmountConverter.from_db(balance)

    async def wire(self, issuer: str, recipient: str, amount: float, date: str=None):
        """
        Record wire issued by `issuer` to `recipient` for `amount` euros.

        If money is wired between individuals, we credit and debit accordingly.
        If money is wired to joint account, we credit both the individual and the joint account.
        If money is wire from joint account, we debit both the individual and the joint account.
        """
        log.debug(f'{issuer}, {recipient}')
        match (issuer, recipient):
            case ('user_1' | 'user_2', 'user_1' | 'user_2'):
                log.debug(f'Money is wired between individual')
                await self.record_transaction(issuer, amount, date, recipient, 'wire')
                await self.record_transaction(recipient, -amount, date, issuer, 'wire')
            case ('user_1' | 'user_2', 'joint'):
                log.debug(f'Money is wired to joint account')
                await self.record_transaction(issuer, amount, date, recipient, 'wire')
                await self.record_transaction(recipient, amount, date, issuer, 'wire')
            case ('joint', 'user_1' | 'user_2'):
                log.debug(f'Money is wired from joint account')
                await self.record_transaction(issuer, -amount, date, recipient, 'wire')
                await self.record_transaction(recipient, -amount, date, issuer, 'wire')
        
    async def load_table(self, name: str):
        """
        Get table `name` history.
        """
        log.debug(f'Loading {name} table.')
        records = await self.fetch(f'''
            SELECT * FROM {name} ORDER BY date
        ''')
        return records

    async def load_wire(self, user: str, start_date='2022-07-01', stop_date='2050-01-01'):
        log.debug(f'Loading {user} wire history')
        start = parse_date(start_date)
        stop = parse_date(stop_date)
        records = await self.fetch(f'''
            SELECT * FROM wire 
                WHERE account= $1
                    AND date >= $2
                    AND date < $3
            ORDER BY date
        ''', user, start, stop)
        return records

    async def joint_purchase(self, amount: float, recipient: str, percentage: int = 50, date=None, information: str = None):
        """
        Account for joint purchase

        Parameters
        ----------
        amount: Price of the purchase.
        recipient: Recipient of the purchase.
        percentage: Percentage of the purchase taken care of by user_1.
        """
        user_1 = amount * percentage / 100
        user_2 = amount - user_1

        await self.record_transaction('user_1', -user_1, date, recipient, information)
        await self.record_transaction('user_2', -user_2, date, recipient, information)
        await self.record_transaction('joint', -amount, date, recipient, information)
        log.debug(f'Writing {recipient} wire according to joint payment.')
