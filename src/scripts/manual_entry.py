
import logging

import asyncio

from loan import DB

logging.basicConfig(
    format="{asctime} {levelname} [{name}:{lineno}] {message}",
    style='{',
    datefmt='%H:%M:%S',
    level='DEBUG',
    handlers=[
        logging.StreamHandler(),
    ],
)


async def main():
    database = DB()
    await database.start()
    # Past
    if False:
        await database.joint_purchase(5, 'bank', percentage=50, date='2022/07/05', information='subscription')
        await database.wire('user_1', 'joint', 500, '2022/07/05')
        await database.wire('joint', 'user_1', 100, '2022/07/11')
        await database.wire('joint', 'user_2', 100, '2022/07/12')
        await database.joint_purchase(1, 'bank', percentage=50, date='2022/08/01', information='account fee')
        await database.wire('user_2', 'joint', 1000, '2022/08/15')
    # Present
    if True:
        pass
    # Future
    if False:
        await database.joint_purchase(1, 'bank', percentage=50, date='2022/09/01', information='account fee')
        await database.joint_purchase(1, 'bank', percentage=50, date='2022/10/01', information='account fee')
        await database.joint_purchase(1, 'bank', percentage=50, date='2022/11/01', information='account fee')


asyncio.run(main())