from openai import OpenAI
from dotenv import load_dotenv
import os
import time
import json
from google import genai
from pydantic import BaseModel
from groq import Groq


class LLMResponse(BaseModel):
    precis: str
    long_form_text: str


# Load environment variables from .env file
load_dotenv()

# client = OpenAI(
#    base_url="https://openrouter.ai/api/v1",
#    api_key=os.getenv("OPEN_REUTERS_API_KEY"),
# )

# CLIENT = OpenAI(
#    base_url="https://api.groq.com/openai/v1", api_key=os.environ.get("GROQ_API_KEY")
# )


def apply_llm(hourly_forecast_data, var_definitions):
    """
    Apply the LLM to generate summaries from hourly forecast data.

    :param hourly_forecast_data: Dictionary containing hourly forecast data.
    :param var_definitions: definitions of the selected variables.
    """
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    gclient = genai.Client(api_key=os.getenv("GOOGLE_GENAI_API_KEY"))

    # create prompts
    # --- Define the static part of the prompt and combine with file data ---
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

    model_outputs = {}
    for model in [
        # "deepseek/deepseek-chat-v3-0324:free",
        # "meta-llama/llama-4-maverick:free",
        # "mistralai/mistral-small-24b-instruct-2501:free",
        "llama-3.1-8b-instant",
        "deepseek-r1-distill-llama-70b",
        "mistral-saba-24b",
    ]:
        # Record start time
        start_time = time.time()
        response_content = "Error: No response."
        input_tokens = "N/A"
        output_tokens = "N/A"
        latency_seconds = 0.0  # Initialize latency

        try:
            completion = client.chat.completions.create(
                # completion = CLIENT.beta.chat.completions.parse(
                extra_body={},
                model=model,  # Simplified
                messages=[
                    {
                        "role": "user",
                        "content": PROMPT,
                    }
                ],
                # response_format=LLMResponse,
                response_format={"type": "json_object"},
            )
            response_content = completion.choices[0].message.content

            # Try to parse as JSON
            try:
                output_data = LLMResponse.model_validate_json(response_content)
                parsed_output_str = output_data.model_dump_json(indent=2)
                print(f"\nModel {model}: Successfully parsed and validated JSON.")
                print("\nSuccessfully parsed as JSON!")
            except json.JSONDecodeError:
                print("\nFailed to parse as JSON. Response is not valid JSON.")

        except Exception as e:
            response_content = f"Error during API call for model {model}: {e}"
            print(response_content)

        # Record end time
        end_time = time.time()
        # Calculate latency
        latency_seconds = end_time - start_time
        # Extract token usage
        input_tokens = 0
        output_tokens = 0
        if completion.usage:
            input_tokens = completion.usage.prompt_tokens
            output_tokens = completion.usage.completion_tokens

        # Print to console (optional, but good for live feedback)
        print(f"Response: {response_content}")
        print(f"Input Tokens: {input_tokens}")
        print(f"Output Tokens: {output_tokens}")
        print(f"Latency: {latency_seconds:.4f} seconds")

        model_outputs[model] = {
            "precis": output_data.precis,
            "long_form_text": output_data.long_form_text,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "latency_seconds": latency_seconds,
        }

    # Apply gemini model
    start_time = time.time()
    gemini_input_tokens = 0
    gemini_output_tokens = 0

    response = gclient.models.generate_content(
        model="gemini-2.0-flash",
        contents=PROMPT,
        config={
            "response_mime_type": "application/json",
            "response_schema": LLMResponse,
        },
    )
    gemini_response = response.text
    # gemini_output = LLMResponse.model_validate_json(gemini_response)
    end_time = time.time()
    latency_seconds = end_time - start_time
    print(f"Gemini Response: {gemini_response}")
    print(f"Gemini Latency: {latency_seconds:.4f} seconds")

    if hasattr(response, "usage_metadata") and response.usage_metadata:
        gemini_input_tokens = response.usage_metadata.prompt_token_count
        gemini_output_tokens = response.usage_metadata.candidates_token_count

    gemini_output_data = LLMResponse.model_validate_json(gemini_response)
    model_outputs["gemini-2.0-flash"] = {
        "precis": gemini_output_data.precis,
        "long_form_text": gemini_output_data.long_form_text,
        "input_tokens": gemini_input_tokens,
        "output_tokens": gemini_output_tokens,
        "latency_seconds": latency_seconds,
    }

    # Return the model outputs
    return model_outputs
