------------------------------------------------------------------------------------------------

# Build And Run

## Content

- [Requirements](#requirements)
- [Build](#build)
- [Config](#config)
- [Run](#run)

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
- create a python venv and install the requirements in it:
  - `python3.11 -m venv venv`
  - `pip install -r requirements.txt`

## Config

Configure the server by setting the following environment variables:
- `VERBOSE` (boolean): Enable debug logging for the server (default: False)
- `DB_PATH` (string): The path to the duckdb database file (default: `"src/chargecloud/resources/hiring_test.db"`)


## Run
