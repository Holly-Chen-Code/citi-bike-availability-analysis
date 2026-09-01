import os
import requests
import pandas as pd
from datetime import datetime
from zoneinfo import ZoneInfo


STATUS_URL = "https://gbfs.lyft.com/gbfs/2.3/bkn/en/station_status.json"
INFO_URL = "https://gbfs.lyft.com/gbfs/2.3/bkn/en/station_information.json"

MY_STATIONS = [
    "62 Ave & Queens Blvd",
    "Queens Blvd N & 63 Rd",
    "63 Dr & Booth St",
    "Austin St & 63 Dr"
]

FILE_NAME = "rego_park_station_status.csv"

# Only collect between 7 AM and 10 PM New York time
now_ny = datetime.now(ZoneInfo("America/New_York"))

if not (7 <= now_ny.hour < 22):
    print(
        f"Outside collection window: "
        f"{now_ny.strftime('%Y-%m-%d %H:%M:%S')}"
    )
    raise SystemExit(0)


def collect_snapshot():

    # Get real-time station status
    status_response = requests.get(STATUS_URL, timeout=30)
    status_response.raise_for_status()

    status_df = pd.DataFrame(
        status_response.json()["data"]["stations"]
    )

    # Get station information
    info_response = requests.get(INFO_URL, timeout=30)
    info_response.raise_for_status()

    info_df = pd.DataFrame(
        info_response.json()["data"]["stations"]
    )

    station_info = info_df[
        ["station_id", "name", "lat", "lon", "capacity"]
    ]

    # Join status with station information
    merged_df = status_df.merge(
        station_info,
        on="station_id",
        how="left"
    )

    # Keep only our 4 stations
    local_df = merged_df[
        merged_df["name"].isin(MY_STATIONS)
    ].copy()

    snapshot = local_df[
        [
            "station_id",
            "name",
            "num_bikes_available",
            "num_ebikes_available",
            "num_bikes_disabled",
            "num_docks_available",
            "num_docks_disabled",
            "is_installed",
            "is_renting",
            "is_returning",
            "capacity"
        ]
    ].copy()

    # New York local time
    snapshot["snapshot_time"] = datetime.now(
        ZoneInfo("America/New_York")
    )

    return snapshot


snapshot = collect_snapshot()

file_exists = os.path.exists(FILE_NAME)

snapshot.to_csv(
    FILE_NAME,
    mode="a",
    header=not file_exists,
    index=False
)

print(snapshot)
