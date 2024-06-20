import duckdb
import dataclasses

from datetime import datetime
from simulation_data import (
    LOCATIONS,
    STATIONS,
    CHARGEPOINTS,
)


class ChargeCloudDB:
    def __init__(self, db_path: str, setup_file_path: str):
        self._conn = duckdb.connect(db_path)
        with open(setup_file_path) as f:
            self._conn.sql(f.read())

        for location in LOCATIONS:
            self.insert_value(location, "locations")

        for station in STATIONS:
            self.insert_value(station, "stations")

        for chargepoint in CHARGEPOINTS:
            self.insert_value(chargepoint, "chargepoints")

    def insert_value(self, value, table_name):
        fields = [field.name for field in dataclasses.fields(value)]
        attributes = []
        for field in fields:
            if value.__getattribute__(field) is not None:
                attributes.append(f"'{str(value.__getattribute__(field))}'")
            else:
                attributes.append("Null")

        self._conn.execute(f"INSERT INTO {table_name} VALUES ({','.join(attributes)});")

    def insert_price(self, timestamp: datetime, price: float):
        self._conn.execute(f"INSERT INTO kwh_price VALUES ('{timestamp}', {price});")

    def get_current_price(self) -> float:
        df = self._conn.execute(
            "SELECT price FROM kwh_price ORDER BY ts DESC LIMIT 1;"
        ).fetchdf()
        if df.empty:
            raise ValueError("kwh_price cannot be empty")
        return df["price"][0].item()
