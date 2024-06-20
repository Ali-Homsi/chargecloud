import asyncio
import random
import math
import logging
from typing import Optional, List
from uuid import UUID, uuid4

from chargecloud_db import ChargeCloudDB
from simulation_data import Transaction, StatusUpdate, Status
from datetime import datetime, timedelta


class FakeChargePoint:
    def __init__(self, id: int, name: str, station_id: int, db: ChargeCloudDB):
        self._id = id
        self._name = name
        self._station_id = station_id
        self._db = db
        self._current_kwh = 0
        self._logger = logging.getLogger(f"FakeChargePoint_{self._name}")
        self._logger.setLevel(logging.DEBUG)

        # the higher the success rate, the more reliable the charge point is sending events
        self._event_success_rate_pct = random.randint(90, 100)

    async def run(self):
        self._logger.debug(f"Simulating previous transactions")
        self._logger.debug(f"Event success rate: {self._event_success_rate_pct}")

        kwh_price = random.uniform(0.38, 0.42)

        # simulate transactions from 60 mins ago
        last_event_ts = await self._simulate_transactions(
            start_time=datetime.now() - timedelta(hours=6),
            count=10,
            is_live=False,
            kwh_price=kwh_price,
        )

        # pad idle events from the last previous event until now
        await self._send_non_charging_events(
            duration_seconds=math.ceil(
                (datetime.now() - last_event_ts).total_seconds()
            ),
            last_ts=last_event_ts,
            status=Status.IDLE,
            is_live=False,
        )

        while True:
            self._logger.debug(f"========= Simulating live transaction =======")
            kwh_price = self._db.get_current_price()
            await self._simulate_transactions(
                start_time=datetime.now(), count=1, is_live=True, kwh_price=kwh_price
            )

    async def _simulate_transactions(
        self, start_time: datetime, count: int, is_live: bool, kwh_price: float
    ) -> datetime:
        for transaction in self._generate_random_transactions(
            count, kwh_price=kwh_price
        ):
            # assume that charging 1 kw takes 1 minute
            end_time = start_time + timedelta(minutes=transaction.total_kw)
            transaction.start_ts = start_time
            transaction.end_ts = end_time
            self._db.insert_value(transaction, "transactions")

            # assume that the chargepoint is blocked for 10% of the charging time after a charge
            blocking_duration_seconds = math.ceil((transaction.total_kw / 10) * 60)

            # random idle time < 30 mins between two transactions
            # idle_duration_seconds = random.randint(0, 30) * 60
            idle_duration_seconds = 5

            # start_time for the next transaction is the timestamp of the last idle event
            start_time = await self._send_transaction_events(
                transaction,
                blocking_duration_seconds,
                idle_duration_seconds,
                is_live,
                kwh_price,
            )
        return start_time

    def _generate_random_transactions(
        self, count: int, kwh_price: float
    ) -> List[Transaction]:
        transactions = []

        for _ in range(count):
            transactions.append(self._generate_random_transaction(kwh_price))
        return transactions

    def _generate_random_transaction(self, kwh_price: float):
        total_kw = random.uniform(20.0, 40.0)
        # total_kw = random.uniform(1.0, 2.0)
        total_eur = total_kw * kwh_price
        return Transaction(
            id=uuid4(),
            total_kw=total_kw,
            total_eur=total_eur,
            start_ts=None,
            end_ts=None,
            chargepoint_id=self._id,
        )

    # returns the timestamp of the last sent event
    async def _send_transaction_events(
        self,
        transaction,
        blocking_duration_seconds: int,
        idle_duration_seconds: int,
        is_live: bool,
        kwh_price: float,
    ) -> datetime:
        self._logger.debug(f"Sending charging events for transaction {transaction.id}")
        charge_duration_seconds = math.ceil(
            (transaction.end_ts - transaction.start_ts).total_seconds()
        )
        curr_kw = 0
        event_ts = transaction.start_ts if not is_live else datetime.now()
        for _ in range(charge_duration_seconds):
            # charging 1 kw takes 1 minute <-> charging speed = 1/60 kw/s
            curr_kw = curr_kw + 1 / 60
            if curr_kw > transaction.total_kw:
                curr_kw = transaction.total_kw
            curr_cost = kwh_price * curr_kw
            self._insert_event(
                event_ts=event_ts,
                curr_kw=curr_kw,
                curr_cost=curr_cost,
                status=Status.CHARGING,
                transaction_id=transaction.id,
            )
            if is_live:
                await asyncio.sleep(1)
                event_ts = datetime.now()
            else:
                event_ts = event_ts + timedelta(seconds=1)

        event_ts = await self._send_non_charging_events(
            blocking_duration_seconds, event_ts, Status.BLOCKING, is_live
        )
        event_ts = await self._send_non_charging_events(
            idle_duration_seconds, event_ts, Status.IDLE, is_live
        )
        return event_ts

    async def _send_non_charging_events(
        self, duration_seconds: int, last_ts: datetime, status: Status, is_live: bool
    ) -> datetime:
        self._logger.debug(f"Sending {status} events")
        event_ts = last_ts if not is_live else datetime.now()
        for _ in range(duration_seconds):
            self._insert_event(
                event_ts=event_ts,
                curr_kw=None,
                curr_cost=None,
                status=status,
                transaction_id=None,
            )
            if is_live:
                await asyncio.sleep(1)
                event_ts = datetime.now()
            else:
                event_ts = event_ts + timedelta(seconds=1)
        return event_ts

    def _insert_event(
        self,
        event_ts: datetime,
        curr_kw: Optional[float],
        curr_cost: Optional[float],
        status: Status,
        transaction_id: Optional[UUID],
    ):
        # insert events based on the chargepoint event success rate
        if random.randrange(100) < self._event_success_rate_pct:
            self._db.insert_value(
                value=StatusUpdate(
                    event_ts=event_ts,
                    curr_cost=curr_cost,
                    curr_kw=curr_kw,
                    status=status,
                    transaction_id=transaction_id,
                    chargepoint_id=self._id,
                ),
                table_name="transaction_meter_values",
            )
