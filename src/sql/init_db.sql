
CREATE TYPE users AS ENUM (
    'joint',
    'user_1',
    'user_2' 
);

CREATE TYPE stackholders AS ENUM (
    'appliances',
    'bank',
    'dosmetic',
    'furniture',
    'insurance',
    'joint',
    'user_1',
    'user_2'
);

CREATE TYPE requester AS ENUM (
    'fee',
    'insurance',
    'loan'
);

CREATE TABLE wire (
    id SERIAL PRIMARY KEY,
    account users,
    date DATE,
    object stackholders,
    operation VARCHAR NULL,
    debit INT,
    credit INT
);

CREATE TABLE timeline (
    id SERIAL PRIMARY KEY,
    amount INT,
    user_1 INT,
    user_2 INT,
    date DATE,
    fill BOOLEAN,
    month SMALLINT,
    request requester
);

CREATE TABLE balance (
    account users PRIMARY KEY,
    date DATE,
    debit INT,
    credit INT,
    balance INT
);

INSERT INTO balance(account, date, balance, debit, credit) 
    VALUES ('joint', '2022-07-01', 0, 0, 0);
INSERT INTO balance(account, date, balance, debit, credit) 
    VALUES ('user_1', '2022-07-01', 0, 0, 0);
INSERT INTO balance(account, date, balance, debit, credit) 
    VALUES ('user_2', '2022-07-01', 0, 0, 0);