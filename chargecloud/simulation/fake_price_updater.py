import asyncio
import logging
from datetime import datetime
import random

from chargecloud_db import ChargeCloudDB


class FakePriceUpdater:
    def __init__(self, db: ChargeCloudDB, frequency_seconds):
        self._db = db
        self._logger = logging.getLogger("FakePriceUpdater")
        self._frequency_seconds = frequency_seconds

    async def run(self):
        while True:
            new_price = round(random.uniform(0.38, 0.42), 3)
            self._logger.debug(f"New price update: {new_price}")
            self._db.insert_price(timestamp=datetime.now(), price=new_price)
            await asyncio.sleep(self._frequency_seconds)
