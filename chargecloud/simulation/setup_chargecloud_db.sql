DROP TABLE IF EXISTS charging_status;
DROP TABLE IF EXISTS transaction_meter_values;
DROP TABLE IF EXISTS transactions;
DROP TABLE IF EXISTS chargepoints;
DROP TABLE IF EXISTS stations;
DROP TABLE IF EXISTS locations;
DROP TABLE IF EXISTS kwh_price;

CREATE TABLE locations (
                         id INTEGER PRIMARY KEY NOT NULL,
                         latitude FLOAT,
                         longitude FLOAT,
                         city TEXT,
                         bundesland TEXT);

CREATE TABLE stations(
                         id INTEGER PRIMARY KEY,
                         name TEXT NOT NULL UNIQUE,
                         location_id INTEGER,
                         CONSTRAINT location_id_constraint FOREIGN KEY (location_id) REFERENCES locations (id)
);

CREATE TABLE chargepoints(
                         id INTEGER PRIMARY KEY,
                         name TEXT NOT NULL UNIQUE,
                         station_id INTEGER,
                         CONSTRAINT station_id_constraint FOREIGN KEY (station_id) REFERENCES stations (id)
);

CREATE TABLE transactions(
                             id UUID PRIMARY KEY,
                             total_kw FLOAT,
                             total_eur FLOAT,
                             start_ts TIMESTAMPTZ,
                             end_ts TIMESTAMPTZ,
                             chargepoint_id INTEGER,
                             CONSTRAINT chargepoint_id_constraint FOREIGN KEY (chargepoint_id) REFERENCES chargepoints (id)
);

CREATE TABLE transaction_meter_values(
                             event_ts TIMESTAMPTZ,
                             curr_cost FLOAT,
                             curr_kw FLOAT,
                             status TEXT, -- ["IDLE", "CHARGING", "BLOCKING"]
                             transaction_id UUID,
                             chargepoint_id INTEGER,
                             CONSTRAINT transaction_id_constraint FOREIGN KEY (transaction_id) REFERENCES transactions (id) ,
                             CONSTRAINT chargepoint_id_constraint FOREIGN KEY (chargepoint_id) REFERENCES chargepoints (id)
);

CREATE TABLE charging_status(
                             chargepoint_id INTEGER,
                             status TEXT,
                             CONSTRAINT chargepoint_id_constraint FOREIGN KEY (chargepoint_id) REFERENCES chargepoints (id)
);

CREATE TABLE kwh_price(
                                ts TIMESTAMP,
                                price FLOAT
);