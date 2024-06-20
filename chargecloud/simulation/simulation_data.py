from enum import Enum
from uuid import UUID
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


class Status(Enum):
    IDLE = "IDLE"
    CHARGING = "CHARGING"
    BLOCKING = "BLOCKING"


@dataclass
class Location:
    id: int
    latitude: float
    longitude: float
    city: str
    bundesland: str


@dataclass
class Station:
    id: int
    name: str
    location_id: int


@dataclass
class ChargePoint:
    id: int
    name: str
    station_id: int


@dataclass
class Transaction:
    id: UUID
    total_kw: float
    total_eur: float
    start_ts: Optional[datetime]
    end_ts: Optional[datetime]
    chargepoint_id: int


@dataclass
class StatusUpdate:
    event_ts: datetime
    curr_cost: Optional[float]
    curr_kw: Optional[float]
    status: Status
    transaction_id: Optional[UUID]
    chargepoint_id: int


LOCATIONS = [
    Location(1, 53.5549737, 10.0080211, "Hamburg", "Hamburg"),  # Hamburg HBF
    Location(2, 53.54, 10.0122, "Hamburg", "Hamburg"),  # Hamburg HafenCity Uni
    Location(3, 53.6341667, 10.0075, "Hamburg", "Hamburg"),  # Hamburg Airport
    Location(4, 50.9419444, 6.96166666, "NRW", "Cologne"),  # Koeln HBF
    Location(5, 50.9275, 6.92888, "NRW", "Cologne"),  # Koeln Uni
]

STATIONS = [
    Station(1, "Hamburg_HBF", 1),
    Station(2, "Hamburg_HafenCity_Uni", 2),
    Station(3, "Hamburg_Airport", 3),
    Station(4, "Cologne_HBF", 4),
    Station(5, "Cologne_Uni", 5),
]

CHARGEPOINTS = [
    ChargePoint(1, "Hamburg_HBF_A", 1),
    ChargePoint(2, "Hamburg_HBF_B", 1),
    ChargePoint(3, "Hamburg_HBF_C", 1),
    ChargePoint(4, "Hamburg_HBF_D", 1),
    ChargePoint(5, "Hamburg_HBF_E", 1),
    ChargePoint(6, "Hamburg_HafenCity_Uni_A", 2),
    ChargePoint(7, "Hamburg_Airport_A", 3),
    ChargePoint(8, "Hamburg_Airport_B", 3),
    ChargePoint(9, "Hamburg_Airport_C", 3),
    ChargePoint(10, "Cologne_HBF_A", 4),
    ChargePoint(11, "Cologne_HBF_B", 4),
    ChargePoint(12, "Cologne_HBF_C", 4),
    ChargePoint(13, "Cologne_HBF_D", 4),
    ChargePoint(14, "Cologne_HBF_E", 4),
    ChargePoint(15, "Cologne_Uni_A", 5),
]
