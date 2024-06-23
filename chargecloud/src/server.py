import logging
import os
import pathlib

from bottle import run, route, HTTPResponse, request

from chargecloud.repository import ChargeCloudRepository


DB_PATH = (
    os.getenv("DB_PATH")
    if os.getenv("DB_PATH")
    else str(
        pathlib.Path(__file__).parent.resolve() / "chargecloud/resources/hiring_test.db"
    )
)

VERBOSE = os.getenv("VERBOSE", False)

WEBSERVER_PORT = os.getenv("WEBSERVER_PORT", 8080)

logging.basicConfig(
    level=logging.DEBUG if VERBOSE else logging.INFO,
    format="%(asctime)-15s:%(name)s: %(levelname)s: %(message)s",
)


logging.info(">>> Charge Cloud monitoring server starting")

repo = ChargeCloudRepository(DB_PATH)


@route("/", method="GET")
def index():
    return HTTPResponse(status=200, body={"status": "Ready for requests"})


@route("/validate", method="GET")
def validate():
    code, body = repo.validate()
    return HTTPResponse(status=code, body=body)


@route("/station/:station_id/:statistics_type/:interval_type", method="GET")
def station_statistics(station_id, statistics_type, interval_type):
    code, body = repo.get_statistics_by_station(
        station_id=station_id,
        statistics_type=statistics_type,
        interval_type=interval_type,
    )
    return HTTPResponse(status=code, body=body)


@route("/station/:station_id/blockingTime", method="GET")
def station_blocking_time(station_id):
    code, body = repo.get_blocking_time_by_station(station_id=station_id)
    return HTTPResponse(status=code, body=body)


@route("/city/statistics", method="POST")
def city_statistics():
    city_name = request.json["city_name"]
    statistics_type = request.json["statistics_type"]
    interval_type = request.json["interval_type"]

    code, body = repo.get_statistics_by_location(
        location_name=city_name,
        for_city=True,
        statistics_type=statistics_type,
        interval_type=interval_type,
    )
    return HTTPResponse(status=code, body=body)


@route("/state/statistics", method="POST")
def state_statistics():
    state_name = request.json["state_name"]
    statistics_type = request.json["statistics_type"]
    interval_type = request.json["interval_type"]

    code, body = repo.get_statistics_by_location(
        location_name=state_name,
        for_city=False,
        statistics_type=statistics_type,
        interval_type=interval_type,
    )
    return HTTPResponse(status=code, body=body)


@route("/chargepoint/:chargepoint_id/reliability", method="GET")
def chargepoint_reliability(chargepoint_id):
    code, body = repo.get_charge_point_status_event_reliability_pct(
        chargepoint_id=chargepoint_id
    )
    return HTTPResponse(status=code, body=body)


@route("/stationsInRadius", method="POST")
def stations_in_radius():
    latitude = request.json["latitude"]
    longitude = request.json["longitude"]
    radius_km = request.json["radius_km"]

    code, body = repo.get_stations_within_radius(
        input_latitude=latitude, input_longitude=longitude, radius_km=radius_km
    )
    return HTTPResponse(status=code, body=body)


@route("/chargepoints/list", method="GET")
def list_chargepoints():
    code, body = repo.list_all("chargepoints")
    return HTTPResponse(status=code, body=body)


@route("/stations/list", method="GET")
def list_stations():
    code, body = repo.list_all("stations")
    return HTTPResponse(status=code, body=body)


@route("/cities/list", method="GET")
def list_cities():
    code, body = repo.list_all("city")
    return HTTPResponse(status=code, body=body)


@route("/states/list", method="GET")
def list_states():
    code, body = repo.list_all("state")
    return HTTPResponse(status=code, body=body)


run(host="0.0.0.0", port=WEBSERVER_PORT)
