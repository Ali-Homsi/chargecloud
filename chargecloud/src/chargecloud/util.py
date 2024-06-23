import logging
import pathlib

import numpy as np
import pandas as pd

from datetime import datetime, timedelta
from geopy.geocoders import Nominatim
from tqdm import tqdm


geolocator = Nominatim(user_agent="chargecloud_monitoring")

tqdm.pandas()
logger = logging.getLogger(__name__)

LOCATIONS_CACHE_PATH = str(
    pathlib.Path(__file__).parent.resolve()
    / "resources/locations_with_city_state_country.csv"
)


# returns the previous quarter-hour of the input timestamp
# e.g. 16:05 -> returns 16:00:00
# input ts is an iso timestamp string
def previous_quarter_hour(ts: str):
    ts = datetime.fromisoformat(ts)
    # Calculate the minutes and seconds to subtract to reach the previous quarter-hour
    minutes_to_subtract = ts.minute % 15
    seconds_to_subtract = ts.second

    # If it's already on a quarter-hour, no need to subtract minutes
    if minutes_to_subtract == 0 and seconds_to_subtract == 0:
        return ts.replace(second=0, microsecond=0)

    previous_qh = ts - timedelta(
        minutes=minutes_to_subtract, seconds=seconds_to_subtract
    )
    previous_qh = previous_qh.replace(second=0, microsecond=0)
    return previous_qh


def update_locations_cache(conn):
    def add_city_state(row):
        try:
            location = geolocator.reverse(
                f"{row['latitude']}, {row['longitude']}", exactly_one=True, timeout=10
            )
            address = location.raw["address"]
        except Exception as e:
            logger.error(f"Failed to get location for locationId {row['id']}: {e}")
            return row

        # fallback to municipality -> town -> village if no city data is available
        row["city"] = address.get(
            "city",
            address.get(
                "municipality", address.get("town", address.get("village", ""))
            ),
        )
        row["state"] = address.get("state")
        row["country"] = address.get("country", address.get("country_code", ""))
        return row

    df = conn.execute("SELECT * FROM locations").df()

    df = df.progress_apply(add_city_state, axis=1)

    # export as a csv to the cache path
    df.to_csv(LOCATIONS_CACHE_PATH, index=False)


def load_locations_df() -> pd.DataFrame:
    # load cached locations and making sure id is int and np.nan values are converted to None
    return pd.read_csv(LOCATIONS_CACHE_PATH).astype({"id": int}).replace({np.nan: None})


def check_and_update_locations_cache(conn, overwrite=False):
    if overwrite or not pathlib.Path(LOCATIONS_CACHE_PATH).exists():
        logger.info("Updating locations cache")
        update_locations_cache(conn)
