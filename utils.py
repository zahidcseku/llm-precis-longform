import os
import requests
import dotenv
import json
from collections import defaultdict
from datetime import datetime
import pytz

dotenv.load_dotenv()


def get_daily_forecasts(location, vars_list, jw_model="access-g.13km"):
    """
    Fetch daily forecasts from the JW API for given locations and variables.

    Args:
        locations (list): List of tuples with latitude and longitude.
        vars_list (list): List of variable names to extract from the API response.

    Returns:
        list: List of daily forecast data for each location.
    """
    response = requests.get(
        "https://api.janesweather.com/v2/forecast",
        headers={"X-Api-Key": os.getenv("JW_API_KEY")},
        params={
            "model": jw_model,  # ai_enhanced
            "lat": location[0],
            "lon": location[1],
            "show_contributors": "true",
        },
    )

    if response.status_code == 200:
        data = response.json()
    else:
        print(f"Error fetching data for {location}: {response.status_code}")

    data_by_dates = split_json_by_date(data, vars_list)

    return data_by_dates


def split_json_by_date(input_json, vars):
    """
    Splits a weather JSON file into multiple JSON files, one for each date.
    Each output file will be a dictionary where keys are time identifiers
    (epoch string, time_local, or time_utc) and values are dictionaries
    containing only the weather variables specified in VARS for that hour.
    """
    metadata = input_json.get("metadata")
    original_hourly_data = input_json.get("data_1h", [])
    daily_data_list = input_json.get("data_1d_local", [])

    if not daily_data_list:
        print(
            "No 'data_1d_local' found in the JSON. Cannot determine dates for splitting."
        )
        return

    if not original_hourly_data:
        print("No 'data_1h' (hourly data) found in the JSON. No data to process.")
        return

    if metadata is None or "loc" not in metadata or "tz" not in metadata["loc"]:
        print(
            "Error: Timezone information ('metadata.loc.tz') is missing. "
            "Cannot reliably process hourly data by local date."
        )
        return

    local_tz_str = metadata["loc"]["tz"]
    try:
        local_tz = pytz.timezone(local_tz_str)
    except pytz.UnknownTimeZoneError:
        print(
            f"Error: Unknown timezone '{local_tz_str}' in metadata. Cannot process hourly data."
        )
        return

    hourly_by_date = defaultdict(dict)
    processed_hourly_count = 0
    skipped_hourly_count = 0

    for hour_entry in original_hourly_data:
        date_part = None
        # time_key_for_output = None
        hour_minute_key = None

        # Attempt 1: Use epoch time if available
        epoch_time = hour_entry.get("time")
        if epoch_time is not None and isinstance(epoch_time, (int, float)):
            try:
                utc_dt = datetime.fromtimestamp(epoch_time, tz=pytz.utc)
                local_dt = utc_dt.astimezone(local_tz)
                date_part = local_dt.strftime("%Y-%m-%d")
                # time_key_for_output = str(epoch_time)  # Use epoch string as the key
                hour_minute_key = local_dt.strftime("%H:%M")
            except Exception:  # pylint: disable=broad-except
                date_part = None
                hour_minute_key = None  # Reset on failure

        # Attempt 2: Use time_local if epoch failed or not present/preferred
        if date_part is None or hour_minute_key is None:
            time_str_local = hour_entry.get("time_local")
            if time_str_local and isinstance(time_str_local, str):
                try:
                    # Extract date part from YYYY-MM-DDTHH:MM:SS...
                    current_date_part_candidate = time_str_local.split("T")[0]
                    datetime.strptime(
                        current_date_part_candidate, "%Y-%m-%d"
                    )  # Validate format
                    date_part = current_date_part_candidate
                    # Parse the full time_local string to extract HH:MM correctly
                    dt_obj_local = datetime.fromisoformat(time_str_local)
                    hour_minute_key = dt_obj_local.strftime("%H:%M")
                except (IndexError, ValueError):
                    date_part = None  # Reset on failure
                    hour_minute_key = None

        if date_part and hour_minute_key:
            filtered_vars_data = {k: v for k, v in hour_entry.items() if k in vars}
            if filtered_vars_data:
                hourly_by_date[date_part][hour_minute_key] = filtered_vars_data
                processed_hourly_count += 1
            else:
                # This hour_entry, for the determined time_key, had no data for the VARS.
                skipped_hourly_count += 1
        else:
            # date_part or hour_minute_key could not be determined for this entry
            skipped_hourly_count += 1

    print(
        f"Processed {processed_hourly_count} hourly entries, skipped {skipped_hourly_count}."
    )

    return hourly_by_date


def convert_to_tabular(forecast_data_by_date):
    """
    Converts the nested forecast data dictionary into a flat tabular format (list of dictionaries).

    Args:
        forecast_data_by_date (dict): A dictionary where keys are dates (YYYY-MM-DD strings)
                                     and values are dictionaries. Each inner dictionary
                                     has time (HH:MM strings) as keys and weather variable
                                     dictionaries as values (e.g., {'temp': 20, 'precip': 0}).
                                     Example:
                                     {
                                         "2023-01-01": {
                                             "00:00": {"temp": 10, "precip": 0},
                                             "01:00": {"temp": 11, "precip": 0.1}
                                         },
                                         "2023-01-02": { ... }
                                     }

    Returns:
        list: A list of dictionaries, where each dictionary represents a single hourly forecast
              record. Each dictionary includes 'date', 'time', and all weather variables.
              Returns an empty list if input is None or empty.
              Example:
              [
                  {'date': '2023-01-01', 'time': '00:00', 'temp': 10, 'precip': 0},
                  {'date': '2023-01-01', 'time': '01:00', 'temp': 11, 'precip': 0.1},
                  ...
              ]
    """
    tabular_data = []
    if not forecast_data_by_date:  # Handles None or empty dict/defaultdict
        return tabular_data

    for date_str, hourly_entries in forecast_data_by_date.items():
        for time_str, variables in hourly_entries.items():
            record = {"date": date_str, "time": time_str}
            record.update(variables)
            tabular_data.append(record)
    return tabular_data


if __name__ == "__main__":
    LOCS = [
        (37.8136, 144.9631),
        (-33.86, 151.20),
        (-35.31, 149.20),
    ]  # Example: Melbourne, SYD, CAN  Sydney Lat: -33.86Lon: 151.20 and Canberra Lat: -35.31Lon: 149.20

    VARS = [
        "cape_srf",
        "chill_stress_idx",
        "dew_pt",
        "frost_prob_cat",
        "tcc",
        "apparent_temp",
        "heat_stress_rating",
        "k_idx",
        "precip",
        "precip_conf",
        "precip_prob",
        "pres_msl",
        "rel_hum",
        "storm_prob_idx",
        "temp",
        "temp_inv_prob_idx",
        "total_totals_idx",
        "uv_idx_clear",
        "wind_dir",
        "wind_dir_compass",
        "wind_kmh",
    ]

    VARS_SET = set(VARS)  # Use a set for efficient O(1) average time complexity lookups

    get_daily_forecasts(LOCS[0], VARS_SET)
