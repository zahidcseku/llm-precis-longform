"""
This script does the followings:
1. extacts daily forecasts form the JW API given location(s)
2. extracted the variables in  VARS from the API response
3. setup the promt for the LLM to generate a daily overview:
    - instructions
    - varible definitions
    - variables
4. send the prompt to the LLM
5. save the response to a file
"""

import dotenv
from var_dictionary import get_var_definitions
from utils import get_daily_forecasts
from llm_utils import apply_llm
import json

dotenv.load_dotenv()

"""
Setup:
1. LOCS={label: (lat, lon), ...}  # dictionary of tuples with latitude and longitude label will be used to save results
2. VARS=[var, ...]  # List of variable names to extract from the API response
"""
LOCS = {
    "melbourne": ("-37.8136", "144.9631"),
    "sydney": ("-33.86", "151.20"),
    "canberra": ("-35.31", "149.20"),
}  # Example: Melbourne, SYD, CAN  Sydney Lat: -33.86Lon: 151.20 and Canberra Lat: -35.31Lon: 149.20

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


def main():
    for location_label, loc in LOCS.items():
        # get the responses.
        data = get_daily_forecasts(loc, VARS)

        """
        data is a dictionary with the following structure:
        "date": { "hour_minute": {var: value, ...}, ... }, ...}
        """

        # call the LLM with daily data
        for date, hourly_data in data.items():
            # Prepare the variable definitions
            var_definitions = get_var_definitions(VARS)

            # Create the output filename
            output_filename = f"{location_label}_{date.replace('-', '_')}"

            # Apply the LLM to generate summaries
            apply_llm(
                hourly_data,
                var_definitions,
                output_dir="daily_overviews",
                output_filename=output_filename,
            )
        # save response to a directory


if __name__ == "__main__":
    main()
