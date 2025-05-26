import json

var_dictionary = {
    "actual_vap_pres": "Actual Vapor Pressure (float, hPa): The actual vapor pressure in the atmosphere.",
    "bulk_shear_300_1000": "Bulk Shear 300–1000 hPa (float, m/s): Wind shear measurement between 300 hPa and 1000 hPa levels.",
    "bulk_shear_500_1000": "Bulk Shear 500–1000 hPa (float, m/s): Wind shear measurement between 500 hPa and 1000 hPa levels.",
    "bulk_shear_850_1000": "Bulk Shear 850–1000 hPa (float, m/s): Wind shear measurement between 850 hPa and 1000 hPa levels.",
    "cape_srf": "Convective Available Potential Energy (float, J/kg): Measures atmospheric instability.",
    "chill_stress_idx": "Chill Stress Index (float): Quantifies cold stress impact on humans and livestock. Stress level: < 900: NEGLIGIBLE, > 900: LOW, > 1000: MODERATE, > 1100: HIGH, > 1200: SEVERE",
    "dew_pt": "Dew Point (float, degC): How much moisture is in the air in °C.",
    "frost_prob_cat": "Frost Probability Category (string): Categorical frost occurrence likelihood: NO_FROST: No frost expected, CHANCE_FROST: Frost possible, FROST_LIKELY: Frost likely, SEVERE_FROST: Severe frost expected",
    "geo_height_1000": "Geopotential Height at 1000 hPa (float, m): Altitude of the 1000 hPa pressure level.",
    "geo_height_500": "Geopotential Height at 500 hPa (float, m): Altitude of the 500 hPa pressure level.",
    "ghi": "Global Horizontal Irradiance (float, MJ/m²): The hourly measure of solar radiation received on a horizontal surface.",
    "gust_kmh": "Wind Gust (float, km/h): Strongest gust over the hour.",
    "hcc": "High Cloud Cover (float, %): Percentage of high-altitude cloud cover (above 20,000 feet).",
    "lcc": "Low Cloud Cover (float, %): Percentage of low-altitude cloud cover (below 6,500 feet).",
    "mcc": "Middle Cloud Cover (float, %): Percentage of mid-altitude cloud cover (between 6,500 and 20,000 feet).",
    "tcc": "Total Cloud Cover (float, %): Percentage of the sky covered by clouds.",
    "apparent_temp": "Apparent Temperature (float, degC): Apparent temperature in °C (takes into account wind and moisture in the air).",
    "heat_stress_rating": "Heat Stress Rating (string): rating on heat stress, using wet bulb globe temperature: NEGLIGIBLE: < 27.0°C, LOW: 27.0°C to 28.9°C, MODERATE: 29.0°C to 29.9°C, DANGEROUS: >= 30.0°C",
    "hli": "Heat Load Index (float): Quantifies heat stress intensity.",
    "hli_max": "Maximum Heat Load Index (float): Highest value of the heat load index.",
    "k_idx": "K Index (float): Measure of thunderstorm potential.",
    "lifted_idx": "Lifted Index (float): Atmospheric stability index used to predict convection.",
    "precip": "Precipitation Total (float, mm): Total amount of precipitation, including rain and snow.",
    "precip_conf": "Precipitation Confidence (string): Confidence level in precipitation forecast.",
    "precip_prob": "Precipitation Probability (float, %): Chance of precipitation occurring.",
    "pres_msl": "Pressure at Mean Sea Level (float, hPa): Atmospheric pressure adjusted to sea level.",
    "rel_hum": "Relative Humidity (float, %): The humidity relative to the air temperature, as a percentage.",
    "sat_vap_pres": "Saturated Vapor Pressure (float, hPa): The saturated vapor pressure in the atmosphere.",
    "soil_moisture_0_1": "Soil Moisture 0 to 1 cm (float, kg/m²): Moisture content in the top 1 cm of soil.",
    "soil_moisture_0_10": "Soil Moisture 0 to 10 cm (float, kg/m²): Moisture content in the top 10 cm of soil.",
    "soil_moisture_10_28": "Soil Moisture 10 to 28 cm (float, kg/m²): Moisture content in mid-soil layers.",
    "soil_moisture_28_100": "Soil Moisture 28 to 100 cm (float, kg/m²): Moisture content in lower soil layers.",
    "soil_moisture_100_289": "Soil Moisture 100 to 289 cm (float, kg/m²): Moisture content in deeper soil layers.",
    "soil_temp": "Soil Temperature (float, degC): Temperature of the soil at the surface.",
    "soil_temp_0_10": "Soil Temperature 0 to 10 cm (float, degC): Temperature of soil in the top 10 cm.",
    "soil_temp_10_28": "Soil Temperature 10 to 28 cm (float, degC): Temperature of soil in mid layers.",
    "soil_temp_28_100": "Soil Temperature 28 to 100 cm (float, degC): Temperature of soil in lower layers.",
    "soil_temp_100_289": "Soil Temperature 100 to 289 cm (float, degC): Temperature of soil in deeper layers.",
    "storm_prob_idx": "Storm Probability Index (float): Likelihood of storm occurrence.",
    "temp": "Temperature (float, degC): 2-meter temperature in °C.",
    "temp_850": "Temperature at 850 hPa (float, degC): Temperature at the 850 hPa pressure level.",
    "temp_inv_prob_idx": "Temperature Inversion Probability Index (float): Likelihood of temperature inversion occurrence.",
    "thickness": "Atmospheric Thickness (float, m): Measures the height of the air column between the ground and ~5 km. Key values: 5200 m: Snow to sea level, 5240 m: Snow to 300 m, 5280 m: Snow to 600 m, 5320 m: Snow to 900 m, 5360 m: Snow to 1,200 m, 5400 m: Snow to 1,500 m, 5440 m: Snow to 1,800 m, 5720 m: Hot weather, 5780 m: Extreme heat",
    "total_totals_idx": "Total Totals Index (float): Used to assess thunderstorm potential.",
    "uv_idx_clear": "UV Index Clear Sky (float): The maximum UV rating you can experience during this hour assuming a clear sky.",
    "vap_pres_deficit": "Vapor Pressure Deficit (float, hPa): The difference between the amount of moisture in the air and the maximum moisture the air can hold, driving plant transpiration and influencing water stress.",
    "wbgt": "Wet Bulb Globe Temperature (float, degC): A raw measure of heat stress in direct sunlight, taking into account temperature, humidity, wind speed, and solar radiation.",
    "wind_850": "Wind Speed at 850 hPa (float, m/s): Wind speed at the 850 hPa pressure level.",
    "wind_dir": "Wind Direction (float, deg): Wind direction in degrees (e.g., 181.125448654848); "
    "the direction from which the wind is blowing.",
    "wind_dir_compass": "Wind Direction Compass (string): Wind direction in cardinal points (e.g., N, NE, E).",
    "wind_gust": "Wind Gust (float, km/h): Strongest gust over the hour.",
    "wind_kmh": "Wind Speed (float, km/h): Average wind speed over the hour.",
}


def get_var_definitions(var_list):
    """
    Retrieves definitions for a list of variables from the var_dictionary.

    Args:
        var_list (list): A list of variable names (strings).

    Returns:
        str: A JSON string containing the definitions for the supplied variables.
             If a variable is not found, it is excluded from the output.
    """
    definitions = {}
    for var in var_list:
        if var in var_dictionary:
            definitions[var] = var_dictionary[var]

    return json.dumps(definitions, indent=4)  # Use indent for readability
