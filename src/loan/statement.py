
import logging

from .utility import (
    AmountConverter,
    Config,
    parse_date
)

log = logging.getLogger('statement')
log.setLevel('INFO')


class TexHandler:
    """
    Object generating tex macros to output pdf statement.
    """
    def __init__(self, user: str, start_date=None, stop_date=None):
        log.debug('Parsing statement arguments.')
        if user not in Config.DB_USERS:
            raise ValueError(f'User {user} not recognized.')
        self.user = user
        if start_date is None:
            start_date = '2022-01-01'
        if stop_date is None:
            stop_date = '2050-01-01'
        self.start_date = parse_date(start_date)
        self.stop_date = parse_date(stop_date)

    def generate_macros(self):
        """
        Generate tex macros for statement computation.
        """
        log.info('Generating macros.')
        macros = '\\newcommand{\\user}{' + self.user.capitalize() + '}\n'
        macros += '\\newcommand{\\startdate}{' + self.start_date.strftime('%Y-%m-%d') + '}\n'
        macros += '\\newcommand{\\stopdate}{' + self.stop_date.strftime('%Y-%m-%d') + '}\n'
        return macros

    def record_to_latex(self, wire_records, balance=0):
        """
        Generate core array for statement

        Parameters
        ----------
        records: list of asyncpg.Record
            User record loaded from wire table.
        balance: float
            Amount of money credited to the user
        """
        log.info('Generating tex main array.')
        tex = '\\begin{tabular}{|L{3cm}|L{5cm}|R{2cm}|R{2cm}|}\n'
        tex += '\\hline\n'
        tex += " {\\bf date} & {\\bf operation} & {\\bf debit} & {\\bf credit} \\\\\n"
        tex += '\\hline\n'
        if balance < 0:
            tex += f" {self.start_date.strftime('%Y-%m-%d')} & balance & {-balance} & \\\\\n"
        else:
            tex += f" {self.start_date.strftime('%Y-%m-%d')} & balance & & {balance} \\\\\n"
        tex += '&&&\\\\\n'
        for record in wire_records:
            debit = AmountConverter.from_db(record['debit'])
            credit = AmountConverter.from_db(record['credit'])
            if not debit:
                tex += f"{record['date']} & {record['object']} : {record['operation']} & & {credit} \\\\\n"
            elif not credit:
                tex += f"{record['date']} & {record['object']} : {record['operation']} & {debit} & \\\\\n"
            else:
                tex += f"{record['date']} & {record['object']} : {record['operation']} & {debit} & {credit} \\\\\n"
            balance += credit - debit

        tex += '&&&\\\\\n'
        tex += '\\hline\n'
        balance = AmountConverter.from_db(AmountConverter.to_db(balance))
        if balance < 0:
            tex += f" {self.stop_date.strftime('%Y-%m-%d')} & balance & {-balance} & \\\\\n"
        else:
            tex += f" {self.stop_date.strftime('%Y-%m-%d')} & balance & & {balance} \\\\\n"
        tex += '\\hline\n'
        tex += '\\end{tabular}'
        return tex

    def generate_tex_file(self, records, balance):
        """
        Generate tex file inside `latex` folder.

        Parameters
        ----------
        records: list of asyncpg.Record
            User record loaded from wire table.
        balance: float
            Amount of money credited to the user
        """
        tex = self.generate_macros()
        with open(Config.PATH / 'latex' / 'macro.tex', 'w') as f:
            f.write(tex)
        tex = self.record_to_latex(records, balance)
        with open(Config.PATH / 'latex' / 'array.tex', 'w') as f:
            f.write(tex)
        log.info('Generated tex main array.')
