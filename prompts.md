# Prompts

## Basic prompt
```
PROMPT = f"""You are a weather expert. Based on the following hourly 
    forecast data, please provide two summaries.
    Your response MUST be a single, valid JSON object with two keys: "precis" and "long_form_text".
    - "precis": A very concise 5-word summary.
    - "long_form_text": A detailed 20-word summary.
    
    Example of the JSON structure:
    {{
      "precis": "Concise summary here.",
      "long_form_text": "Detailed summary here."
    }}
    
    Do NOT include any other text, explanations, or markdown formatting before or after the JSON object.
    
    Mention temperature trends, precipitation chances, cloud conditions, and any significant weather events. 
    Use natural, easy-to-understand language suitable for a general audience.    

    The definitions of the variables in the data are as follows:
    {var_definitions}   
            
    Hourly Forecast Data:
    {hourly_forecast_data}
    """
```

## With Jane's instruction
```
PROMPT = f"""You are a weather expert. Based on the following hourly 
    forecast data, please provide two summaries.
    Your response MUST be a single, valid JSON object with two keys: "precis" and "long_form_text".
    - "precis": A very concise 5-word summary.
    - "long_form_text": A detailed 20-word summary.

    The long_form_text made up of the following structure: Cloud / Precipitation / Winds. 
    - Cloud: Describe the cloud conditions using the wording - sunny, mostly sunny, 
             partly cloudy, mostly cloudy, cloudy and include any transitions across 
             windows of the day (ie cloudy in the morning, partly cloudy in the afternoon). 
    - Precip: only use per weather words (showers, rain, thunderstorms, drizzle etc).
    - Wind: describe the day using direction and ranges from the weather words wind table, 
            in km/h - ie moderate is 20 to 29 km/h, including changes across windows of the day
    
    Example of the JSON structure:
    {{
      "precis": "Concise summary here.",
      "long_form_text": "Detailed summary here."
    }}
    
    Do NOT include any other text, explanations, or markdown formatting before or after the JSON object.
    
    Mention temperature trends, precipitation chances, cloud conditions, and any significant weather events. 
    Use natural, easy-to-understand language suitable for a general audience.    

    The definitions of the variables in the data are as follows:
    {var_definitions}   
            
    Hourly Forecast Data:
    {hourly_forecast_data}
    """
```