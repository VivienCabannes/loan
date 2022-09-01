
## Installation
Go to the parent folder and run `pip` installation in a terminal.
```shell
pip install -e .
```

## **Database**
#### **Initialization**
- Install postgres and create a new database called `loan`.
```shell
$ createdb loan
```
- Initialize the database by running the script `init_db`.
```shell
$ init_db
```
- Initialize the `timeline` table by running the script `init_timeline`.
```shell
$ init_timeline
```

#### **Manual entry**
Manual entries are recorded in the scripts `manual_entry.py`.

#### **Postgres command**
To delete the database, run
```shell
$ dropdb loan
```
To launch postgres interface on this database, run
```shell
$ psql loan
```
#### **Structure**
The database is structured around three main users.
- `joint` for the joint account.
- `user_1` (resp. `user_2`) for user_1's (resp. user_2's) balance regarding the joint account.

The `wire` table keeps track of all past transactions in accounting style. 

The `balance` table keeps track of individual balance.
The `joint` balance represents the money due by the bank to the joint account. It matches the real account balance.
It is split between the individual balances, represents how much money is the joint account owe to each individual.

The `timeline` table is a timeline of loan repayment.
To account for recent loan repayment, run the script `timeline_update`.
```shell
$ timeline_update
```

NB: In the database, amounts are saved as integers, which represent money in cents.