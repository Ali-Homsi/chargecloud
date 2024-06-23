# Charge Cloud Monitoring

## Purpose
A webserver backend that offers monitoring statistics of Electric Vehicles (EV) Charging stations. 

## Documentation

- [Core logic](./doc/coreLogic.md)
- [API](./doc/api.md)

------------------------------------------------------------------------------------------------

## Requirements

- python >= 3.11
- bottle
- duckdb
- pandas
- geopy
- tqdm

------------------------------------------------------------------------------------------------

## Build

From base the project directory:
- create a python venv  `python3.11 -m venv venv`
- activate the venv: `. venv/bin/activate`
- install the project requirements in it `pip install -r requirements.txt`

## Config

Configure the server by setting the following environment variables:
- `VERBOSE` (boolean): Enable debug logging for the server (default: False)
- `DB_PATH` (string): The path to the duckdb database file (default: `"src/chargecloud/resources/hiring_test.db"`)
- `WEBSERVER_PORT`(int): The local port to run the server on (default: 8080)


## Run

run the script `chargecloud/src/server.py` after setting the config environment variables

Example:
```couchbasequery
VERBOSE=True DB_Path='path/to/duckdb.db' WEBSERVER_PORT=8185 python chargecloud/src/server.py
```


