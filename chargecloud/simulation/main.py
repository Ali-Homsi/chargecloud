import asyncio
import logging

from chargecloud_db import ChargeCloudDB
from fake_chargepoint import FakeChargePoint
from fake_price_updater import FakePriceUpdater
from simulation_data import (
    CHARGEPOINTS,
)


async def main():
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)-15s:%(name)s: %(levelname)s: %(message)s",
    )

    db = ChargeCloudDB(
        db_path="chargecloud.db", setup_file_path="setup_chargecloud_db.sql"
    )

    fake_price_updater = FakePriceUpdater(db=db, frequency_seconds=15 * 60)

    fake_charge_points = [
        FakeChargePoint(charge_point.id, charge_point.name, charge_point.station_id, db)
        for charge_point in CHARGEPOINTS
    ]
    coroutines = [fake_price_updater.run()]
    for fake_charge_point in fake_charge_points:
        coroutines.append(fake_charge_point.run())

    await asyncio.gather(*coroutines)


if __name__ == "__main__":
    asyncio.run(main())

    # conn.execute("export database '/home/ahomsi/repo/chargecloud/chargecloud/simu/db'")
