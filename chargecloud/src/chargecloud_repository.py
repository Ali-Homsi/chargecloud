from enum import Enum

from typing import Tuple
from datetime import datetime


import duckdb


class StatisticsType(Enum):
    TURNOVER = "total_eur"
    POWER_CONSUMPTION = "total_kw"


class StatisticsLevel(Enum):
    STATION = "station_name"
    CITY = "city"
    BUNDESLAND = "bundesland"


class AbstractionLevel(Enum):
    HOURLY = "hourly"
    DAILY = "daily"
    ALL_TIME = "all_time"


class ChargeCloudRepository:
    def __init__(self, db_path: str):
        self._conn = duckdb.connect(database=db_path, read_only=True)

        x, y = self.fetch_statistics_by_datetime_range(
            statistic_type=StatisticsType.TURNOVER,
            statistic_level=StatisticsLevel.STATION,
            from_ts=datetime.fromisoformat("2024-06-18T00:00:00.0+00:00"),
            to_ts=datetime.fromisoformat("2024-06-19T06:00:00.0+00:00"),
            abstraction_level="daily",
        )
        print()

    def run(self):
        pass

    async def _update_cache(self):
        await self._update_hourly_data()

    async def _update_hourly_data(self):
        pass

    async def _update_daily_data(self):
        pass

    def fetch_statistics_by_datetime_range(
        self,
        statistic_type: StatisticsType,
        statistic_level: StatisticsLevel,
        abstraction_level: AbstractionLevel,
        from_ts: datetime,
        to_ts: datetime,
    ) -> Tuple[int, object]:
        if (
            statistic_type not in StatisticsType
            or statistic_level not in StatisticsLevel
            or abstraction_level not in AbstractionLevel
        ):
            return 400, "ERROR: Invalid statistic type"

        transactions = self._conn.execute(
            JOINED_TRANSACTIONS_QUERY.format(str(from_ts), str(to_ts))
        ).df()

        match abstraction_level:
            case AbstractionLevel.HOURLY:
                return 200, transactions.groupby(
                    [
                        transactions.start_ts.dt.hour.rename("hour"),
                        statistic_level.value,
                    ]
                )[statistic_type.value].sum().reset_index().to_json(
                    indent=4, orient="records", lines=True
                )

            case AbstractionLevel.DAILY:
                return 200, transactions.groupby(
                    [
                        transactions.start_ts.dt.date.rename("date"),
                        statistic_level.value,
                    ]
                )[statistic_type.value].sum().reset_index().to_json(
                    indent=4, orient="records", lines=True, date_format="iso"
                )

            case AbstractionLevel.ALL_TIME:
                return 200, transactions.groupby([statistic_level.value])[
                    statistic_type.value
                ].sum().reset_index().to_json(
                    indent=4, orient="records", lines=True, date_format="iso"
                )

            case _:
                return 400, f"Invalid abstraction level: {abstraction_level}"

    def get_turnover_by_station(self, station_name: str):
        pass

    def get_turnover_by_city(self, city_name: str):
        pass

    def get_turnover_by_bundesland(self, bundesland: str):
        pass

    def get_power_consumption_by_station(self, station_name: str):
        pass

    def get_power_consumption_by_city(self, city_name: str):
        pass

    def get_power_consumption_by_bundesland(self, bundesland: str):
        pass

    def get_chargepoint_blocking_duration_after_charge(self, chargepoint_name: str):
        pass

    def get_chargepoint_status_event_quality(self, chargepoint_name: str):
        pass

    def get_nearby_station_by_location_within(self, location, distance):
        pass

    # TODO
    def validate_raw_data(self):
        pass


JOINED_TRANSACTIONS_QUERY = """
SELECT * FROM transactions tr
                  JOIN (
                        SELECT stations.*,
                               cp.id AS chargepoint_id
                            FROM chargepoints cp
                                     JOIN (
                                        SELECT
                                            st.id AS station_id,
                                            st.name AS station_name,
                                            l.city AS city,
                                            l.bundesland AS bundesland
                                        FROM  stations st JOIN locations l ON st.location_id= l.id
                                        ) AS stations ON cp.station_id == stations.station_id

                  ) AS joined_chargepoints ON tr.chargepoint_id == joined_chargepoints.chargepoint_id
         WHERE tr.start_ts > '{}' AND tr.start_ts < '{}';
"""
