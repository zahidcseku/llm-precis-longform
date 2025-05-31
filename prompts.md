# Prompts

## Basic prompts
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