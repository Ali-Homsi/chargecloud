import json
import logging
from collections import defaultdict

import duckdb
import pandas as pd

from datetime import datetime
from geopy.distance import distance
from typing import Tuple, Optional

from .validate import validate_locations, validate_transactions
from .util import (
    check_and_update_locations_cache,
    load_locations_df,
    previous_quarter_hour,
)

STATISTICS_TYPES = ["turnoverEur", "kwhConsumed"]
INTERVAL_TYPES = ["hourly", "daily", "allTime"]


class ChargeCloudRepository:
    def __init__(self, db_path: str):
        self._conn = duckdb.connect(database=db_path, read_only=True)
        self._logger = logging.getLogger(__name__)

        # fetch and cache city/state information from location points
        check_and_update_locations_cache(self._conn, overwrite=False)

    def validate(self) -> Tuple[int, object]:
        issues = defaultdict(list)
        validate_locations(load_locations_df(), issues)
        validate_transactions(self._conn, issues)
        return 200, issues

    def _compute_transaction_turnover(self, row):

        candidate_price = self._conn.execute(
            f"SELECT * FROM kwh_price "
            f"WHERE stationId = '{row['stationId']}' "
            f"AND priceAt < '{row['startedAt']}' "
            f"ORDER BY priceAt DESC LIMIT 1"
        ).df()

        kwh_price_ideal_time = previous_quarter_hour(row["startedAt"].isoformat())
        if candidate_price.empty:
            # found no price for station prior to the transaction time -> use fallback price
            transaction_kwh_price = self._kwh_price_fallback_by_station(
                row["stationId"]
            )
        elif (
            datetime.fromisoformat(candidate_price["priceAt"][0].isoformat())
            != kwh_price_ideal_time
        ):
            # price at station is not up-to-date -> use fallback price
            transaction_kwh_price = self._kwh_price_fallback_by_station(
                row["stationId"]
            )
        else:
            transaction_kwh_price = candidate_price["kwhPrice"][0]

        row["turnoverEur"] = (transaction_kwh_price * row["kwhConsumed"]) / 100

        # useful for debugging
        row["transaction_kwh_price_eur"] = transaction_kwh_price / 100
        return row

    #  use average price of the stations instead of using an old price
    #  falls back to the average price of all stations in case the station didn't have any reported price
    def _kwh_price_fallback_by_station(self, station_id) -> float:
        average_price = self._conn.execute(
            f"SELECT avg(kwhPrice) FROM kwh_price "
            f"WHERE stationId = '{station_id}' "
            f"GROUP BY stationId"
        ).df()
        if average_price.empty:
            return self._kwh_price_last_fallback()

        return average_price["avg(kwhPrice)"][0]

    def _kwh_price_last_fallback(self) -> float:
        average_price = self._conn.execute(f"SELECT avg(kwhPrice) FROM kwh_price").df()
        return average_price["avg(kwhPrice)"][0]

    def _fetch_transactions(self, station_id: Optional[int] = None):
        sql = (
            f"SELECT * FROM transactions tr "
            f"JOIN chargepoints cp "
            f"ON tr.chargePointId == cp.id "
        )

        if station_id:
            sql += f"WHERE cp.stationId = '{station_id}'"

        return self._conn.execute(sql).df().rename(columns={"id": "transactionId"})

    def _aggregate_statistics_by_type_and_interval(
        self, transactions_df: pd.DataFrame, statistics_type: str, interval_type: str
    ):
        def use_average_kwh_consumed(row):
            if row["kwhConsumed"] < 0:
                row["kwhConsumed"] = average_kwh_consumed
            return row

        if not transactions_df[transactions_df["kwhConsumed"] < 0].empty:
            # transactions with negative kwhConsumed are incomplete -> use average kwhConsumed of all transactions
            average_kwh_consumed = self._conn.execute(
                "SELECT avg(kwhConsumed) FROM transactions"
            ).df()["avg(kwhConsumed)"][0]
            transactions_df = transactions_df.apply(use_average_kwh_consumed, axis=1)

        if transactions_df.empty:
            msg = "No transactions found"
            self._logger.warning(msg)
            return 200, {"NoContent": msg}

        match statistics_type:
            case "kwhConsumed":
                return 200, self._aggregate_statistics(
                    transactions_df, statistics_type, interval_type
                )
            case "turnoverEur":
                transactions_df = transactions_df.apply(
                    self._compute_transaction_turnover, axis=1
                )
                return 200, self._aggregate_statistics(
                    transactions_df, statistics_type, interval_type
                )
            case _:
                error_msg = f"Invalid statistics_type : {statistics_type}. Must be one of {STATISTICS_TYPES}"
                self._logger.error(error_msg)
                return 400, {"ERROR": error_msg}

    def get_statistics_by_station(
        self, station_id: int, statistics_type: str, interval_type: str
    ) -> Tuple[int, object]:
        if interval_type not in INTERVAL_TYPES:
            error_msg = f"Invalid interval_type : {interval_type}. Must be one of {INTERVAL_TYPES}"
            self._logger.error(error_msg)
            return 400, error_msg

        transactions_df = self._fetch_transactions(station_id=station_id)
        return self._aggregate_statistics_by_type_and_interval(
            transactions_df=transactions_df,
            statistics_type=statistics_type,
            interval_type=interval_type,
        )

    # location name could be a city or a state
    def get_statistics_by_location(
        self,
        location_name: str,
        for_city: bool,
        statistics_type: str,
        interval_type: str,
    ):

        def location_filter(row):
            # filter on city/state name (case-insensitive)
            val = row.get("city" if for_city else "state", "UNKNOWN")
            if not val:
                return False
            return (
                row["city" if for_city else "state"].casefold()
                == location_name.casefold()
            )

        if interval_type not in INTERVAL_TYPES:
            error_msg = f"Invalid interval_type : {interval_type}. Must be one of {INTERVAL_TYPES}"
            self._logger.error(error_msg)
            return 400, error_msg

        # load cached locations with city / state info
        df = load_locations_df().rename(columns={"id": "locationId"})

        # filter locations within the city / state
        locations_df = df[df.apply(location_filter, axis=1)]

        # all transactions
        transactions_df = self._fetch_transactions()

        # all transactions for city / state
        transactions_df = locations_df.merge(transactions_df, on="locationId")
        return self._aggregate_statistics_by_type_and_interval(
            transactions_df=transactions_df,
            statistics_type=statistics_type,
            interval_type=interval_type,
        )

    def get_blocking_time_by_station(self, station_id: int) -> Tuple[int, object]:
        def compute_blocking_time(row):
            row["blockingTime"] = (
                row["completedAt"] - row["chargingCompletedAt"]
            ).isoformat()
            return row

        df = self._fetch_transactions(station_id=station_id)

        if df.empty:
            msg = f"No transactions found for stationId '{station_id}'"
            self._logger.warning(msg)
            return 200, {"NoContent": msg}

        df = df.apply(compute_blocking_time, axis=1)
        df = df[["transactionId", "chargePointId", "blockingTime"]]
        result = defaultdict(list)
        for _, row in df.iterrows():
            result[row["chargePointId"]].append(
                {
                    "transactionId": row["transactionId"],
                    "blockingTime": row["blockingTime"],
                }
            )

        return 200, json.dumps({"BlockingTimeByChargePointIds": result}, indent=4)

    def get_charge_point_status_event_reliability_pct(self, chargepoint_id: int):

        def compute_expected_and_actual_events_count(row):
            # assumption: a chargepoint with 100% reliability sends at least 1 event every 15 mins
            # -> calculate the number of 15-minute intervals
            # at least 2 events are expected for a transaction (charging_started, charging_stopped)
            transaction_duration_mins = (
                row["completedAt"] - row["startedAt"]
            ).total_seconds() / 60
            row["expectedEventsCount"] = max(int(transaction_duration_mins // 15), 2)
            row["actualEventsCount"] = (
                self._conn.execute(
                    f"SELECT * FROM transaction_meter_values "
                    f"WHERE transactionId = '{row['id']}'"
                )
                .df()
                .shape[0]
            )
            return row

        df = self._conn.execute(
            f"SELECT * FROM transactions " f"WHERE chargePointId = '{chargepoint_id}'"
        ).df()

        if df.empty:
            msg = f"No transactions found for chargePointId '{chargepoint_id}'"
            self._logger.warning(msg)
            return 200, {"NoContent": msg}

        df = df.apply(compute_expected_and_actual_events_count, axis=1)

        # Reliability (%) = (Number of successfully recorded events / Total number of expected events) × 100
        # maxed out at 100%
        reliability_pct = min(
            (df["actualEventsCount"].sum() / df["expectedEventsCount"].sum()) * 100, 100
        )

        return 200, {
            "chargePointId": chargepoint_id,
            "reliability_pct": f"{round(reliability_pct, 2)}%",
        }

    def get_stations_within_radius(
        self, input_latitude: float, input_longitude: float, radius_km: int
    ):
        def is_in_radius(row):
            return (
                distance(
                    (input_latitude, input_longitude),
                    (row["latitude"], row["longitude"]),
                ).km
                <= radius_km
            )

        df = (
            self._conn.execute(f"SELECT * FROM locations")
            .df()
            .rename(columns={"id": "locationId"})
        )

        # filter locations within radius
        try:
            df = df[df.apply(is_in_radius, axis=1)]
        except ValueError as e:
            return 400, {
                "ERROR": f"Invalid latitude / longitude: {input_latitude}, {input_longitude}: {e}"
            }

        if df.empty:
            return 200, {
                "NoContent": f"No locations found within {radius_km} km radius"
            }

        location_ids = df["locationId"].astype(str).to_list()
        del df

        result = self._conn.execute(
            f"SELECT id FROM stations WHERE locationId IN ({', '.join(location_ids)})"
        ).df()

        return 200, {"stationIds": result["id"].to_list(), "count": result.shape[0]}

    def list_all(self, attr):
        if attr in ["stations", "chargepoints"]:
            ids = self._conn.execute(f"SELECT id from {attr}").df()["id"].to_list()
            return 200, {attr: ids, "count": len(ids)}
        else:
            locations = list(
                set([loc for loc in load_locations_df()[attr].to_list() if loc is not None])
            )
            return 200, {attr: locations, "count": len(locations)}

    @staticmethod
    def _aggregate_statistics(df, statistics_type, interval_type):
        def aggregate_sum(input_df, rule):
            return (
                input_df.set_index("startedAt")
                .resample(rule)[statistics_type]
                .sum()
                .to_frame()
                .reset_index()
            )

        match interval_type:
            case "hourly":
                return (
                    aggregate_sum(df, "h")
                    .rename(columns={"startedAt": "hour"})
                    .to_json(indent=4, date_format="iso", orient="records")
                )

            case "daily":
                df = aggregate_sum(df, "D").rename(columns={"startedAt": "date"})
                df["date"] = df["date"].dt.date
                return df.to_json(indent=4, date_format="iso", orient="records")

            case "allTime":
                return {f"allTime_{statistics_type}": df[statistics_type].sum()}
