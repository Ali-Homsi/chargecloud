# REST API

## Content
- [Misc](#misc)
  - [Validate](#validate)
- [Station Related](#station-related)
  - [Station Statistics](#station-statistics)
  - [Station Blocking Time](#station-blocking-time)
  - [List All Stations](#list-all-stations)
- [Location Related](#location-related)
  - [City Statistics](#city-statistics)
  - [State Statistics](#state-statistics)
  - [Stations In Radius](#stations-in-radius)
  - [List All Cities](#list-all-cities)
  - [List All States](#list-all-states)
- [Charge Point Related](#charge-point-related)
  - [Charge Point Reliability](#charge-point-reliability)
  - [List All Charge Points](#list-all-charge-points)


## Misc

### Validate

Run validation on raw data

**URL** : `/validate`

**Method** : `GET`

**URL Parameters** : None


#### Success Response

**Code** : `200 OK`

**Content examples**


```json
{
  "validation_errors": [
    {
      "validation_error_location_not_in_germany": "Found 2 locations not in Germany",
      "LocationIds": [
        631418,
        122222
      ]
    },
    {
      "validation_error_transaction_no_status_events": "Found 6 transactions with no corresponding status events",
      "transactionsIds": [
        36998452,
        37098591,
        37105532,
        37129757,
        37200486,
        37236591
      ]
    },
    {
      "validation_error_transaction_no_stopped_events": "Found 4 transactions with no charging_stopped status events",
      "transactionsIds": [
        36952919,
        36953568,
        36953570,
        36953657
      ]
    },
    {
      "validation_error_transaction_negative_kwh_consumed": "Found 3 transactions with negative kwhConsumed",
      "transactionsIds": [
        36972780,
        37020053,
        37048117
      ]
    }
  ]
}
```

------------------------------------------------------------------------------------------------

## Station Related

### Station Statistics

The statistics (kwhConsumed, turnoverEur) of a charging stations, aggregated hourly, daily, or all time


**URL** : `/station/:station_id/:statistics_type/:interval_type`

**Method** : `GET`

**URL Parameters** : 
- `station_id=[integer]` the ID of the station
- `statistics_type=[str]` the desired statistics type. allowed values  ["kwhConsumed", "turnoverEur"]
- `interval_type=[str]` the desired interval type. allowed values  ["hourly", "daily", "allTime"]


#### Success Response

**Code** : `200 OK`

**Content examples**

Daily turnoverEur for a station with ID 1058315 on the local database

```json
[
  {
    "date":"2024-01-01T00:00:00.000",
    "turnoverEur":39.0918000978
  },
  {
    "date":"2024-01-02T00:00:00.000",
    "turnoverEur":3.1076484809
  },
  .
  .
  {
    "date":"2024-01-30T00:00:00.000",
    "turnoverEur":31.2240378866
  },
  {
    "date":"2024-01-31T00:00:00.000",
    "turnoverEur":5.4203171179
  }
]
```

allTime turnover for a station with ID 1058315 on the local database

```json
{
  "allTime_turnoverEur": 401.5664734974305
}
```

------------------------------------------------------------------------------------------------

### Station Blocking Time

Get the blocking time for all charge points of a station after a transaction

**URL** : `/station/:station_id/blockingTime`

**Method** : `GET`


**URL Parameters** :
- `station_id=[integer]` where `station_id` is the ID of the station


#### Success Response

**Content examples**

**Code** : `200 OK`

Blocking time for all charge points of station with ID 1058315 after a transaction, reported as a duration in ISO format 

```json
{
  "BlockingTimeByChargePointIds": {
    "3307861": [
      {
        "transactionId": 36952497,
        "blockingTime": "P2DT6H14M36S"
      },
      {
        "transactionId": 37083247,
        "blockingTime": "P0DT0H41M21S"
      }
    ],
    "3307860": [
      {
        "transactionId": 36978933,
        "blockingTime": "P0DT9H44M26S"
      },
      {
        "transactionId": 37012453,
        "blockingTime": "P0DT0H49M46S"
      }
    ]
  }
}  

```

**Code** : `200 OK`
No data found for the selected stationId

```json
{
  "NoContent": "No transactions found for stationId '12'"
}
```

------------------------------------------------------------------------------------------------

### List All stations

List the ids of all stations in the local database

**URL** : `/stations/list`

**Method** : `GET`

**URL Parameters** : None


#### Success Response

**Code** : `200 OK`

**Content examples**

All stationIds currently in the local DB

```json
{
  "stations": [
    139,
    140,
    783,
    788,
    800,
    849,
    851,
    888,
    977,
    1019,
    1039
  ],
  "count": 11
}
```

------------------------------------------------------------------------------------------------

## Location Related

### City Statistics

The statistics (kwhConsumed, turnoverEur) of charging stations per city, aggregated hourly, daily, or all time

**URL** : `/city/statistics`

**Method** : `POST`

**JSON Payload** :
- `city_name=[str]` The city name to retrieve statistics for, 
- `statistics_type=[str]` The desired statistics type. allowed values  ["kwhConsumed", "turnoverEur"]
- `interval_type=[str]` the desired interval type. allowed values  ["hourly", "daily", "allTime"]

**Example Payload** :
```json
{
    "city_name": "Berlin", 
    "statistics_type": "kwhConsumed", 
    "interval_type": "allTime"
}
```

#### Success Response

**Code** : `200 OK`

**Content examples**

Hourly statistics for stations in Berlin

```json
[
  {
    "hour":"2024-01-01T04:00:00.000",
    "turnoverEur":4.2538484965
  },
  {
    "hour":"2024-01-01T05:00:00.000",
    "turnoverEur":0.0
  },
  .
  .
  {
    "hour":"2024-01-31T17:00:00.000",
    "turnoverEur":18.6247509134
  },
  {
    "hour":"2024-01-31T18:00:00.000",
    "turnoverEur":32.2631421239
  }
]
```

allTime kwhConsumed for stations in Hamburg 

```json
{
  "allTime_kwhConsumed": 11392.779999999999
}
```
------------------------------------------------------------------------------------------------

### State Statistics

The statistics (kwhConsumed, turnoverEur) of charging stations in a federal state, aggregated hourly, daily, or all time

**URL** : `/state/statistics`

**Method** : `POST`

**JSON Payload** :
- `state_name=[str]` The city name to retrieve statistics for,
- `statistics_type=[str]` The desired statistics type. allowed values  ["kwhConsumed", "turnoverEur"]
- `interval_type=[str]` the desired interval type. allowed values  ["hourly", "daily", "allTime"]

**Example Payload** :
```json
{
    "city_name": "Nordrhein-Westfalen", 
    "statistics_type": "turnoverEur", 
    "interval_type": "allTime"
}
```

#### Success Response

**Code** : `200 OK`

**Content examples**

Hourly kwhConsumed for stations in Hessen

```json
[
  {
    "date":"2024-01-01T00:00:00.000",
    "kwhConsumed":216.09
  },
  {
    "date":"2024-01-02T00:00:00.000",
    "kwhConsumed":192.35
  },
  .
  .
  {
    "date":"2024-01-30T00:00:00.000",
    "kwhConsumed":387.63
  },
  {
    "date":"2024-01-31T00:00:00.000",
    "kwhConsumed":366.35
  }
]
```

allTime turnover for stations in NRW

```json
{
  "allTime_turnoverEur": 21223.70878457123
}
```

------------------------------------------------------------------------------------------------


### Stations In Radius

Get all stations within a selected radius from a selected location

**URL** : `/stationsInRadius`

**Method** : `POST`

**JSON Payload** :
- `latitude=[float]` The latitude of the center point 
- `longitude=[float]` The longitude of the center point
- `radius_km=[int]` The desired radius to search for stations 

**Example Payload** :
```json
{
  "latitude": 51.16678,
  "longitude": 6.75832,
  "radius_km": 5
}
```

#### Success Response

**Code** : `200 OK`

**Content examples**

The stationIds of within 5km radius of the point (51.16678, 6.75832,)

```json
{
  "stationIds": [
    29440,
    134732,
    275608,
    855805,
    866910,
    1025297,
    1207276,
    1758847,
    2069562,
    2112689
  ],
  "count": 10
}
```

**Code** : `200 Ok`

Invalid input location values

```json
{
  "NoContent": "No locations found within 10 km radius"
}
```



**Code** : `400 Bad Request`

Invalid input location values

```json
{
  "ERROR": "Invalid latitude / longitude: 123, 123: Latitude must be in the [-90; 90] range."
}
```

------------------------------------------------------------------------------------------------


### List all cities

List all cities with charging stations in the local db

**URL** : `/cities/list`

**Method** : `GET`

**URL Parameters** : None


#### Success Response

**Code** : `200 OK`

**Content examples**


```json
{
  "city": [
    "Hamburg",
    "Berlin",
    "Köln"
  ],
  "count": 3
}
```

------------------------------------------------------------------------------------------------

### List all states

List all federal states with charging stations in the local db

**URL** : `/states/list`

**Method** : `GET`

**URL Parameters** : None


#### Success Response

**Code** : `200 OK`

**Content examples**


```json
{
  "state": [
    "Hessen",
    "Sachsen-Anhalt",
    "Hamburg",
    "Bayern",
    "Baden-Württemberg"
  ],
  "count": 5
}
```

------------------------------------------------------------------------------------------------

## Charge Point Related

### Charge Point Reliability

Get the status event reliability of a selected charge point

**URL** : `/chargepoint/:chargepoint_id/reliability`

**Method** : `GET`

**URL Parameters** :
- `chargepoint_id=[integer]` the ID of the chargepoint to get the reliability for



#### Success Response

**Code** : `200 OK`

**Content examples**

Charge point with id 1421061 has status event reliability of 26.78% 
```json
{
  "chargePointId": "1421061",
  "reliability_pct": "26.78%"
}
```

**Code** : `200 OK`
No transaction found for the selected charge point 
```json
{
  "NoContent": "No transactions found for chargePointId '12'"
}
```

------------------------------------------------------------------------------------------------

### List All Charge Points

List ids of all charge points in the local db

**URL** : `/chargepoints/list`

**Method** : `GET`

**URL Parameters** : None


#### Success Response

**Code** : `200 OK`

**Content examples**


```json
{
  "chargepoints": [
    54,
    55,
    56,
    57,
    1501,
    1502
  ],
  "count": 6
}
```

------------------------------------------------------------------------------------------------
