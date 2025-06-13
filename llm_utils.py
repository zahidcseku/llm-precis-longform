from openai import OpenAI
from dotenv import load_dotenv
import os
import time
import json
from google import genai
from pydantic import BaseModel
from groq import Groq


class LLMResponse(BaseModel):
    # precis: str
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
    PROMPT = f"""
Your task is to summarize hourly weather conditions for a given location into a concise summary, aiming 
for approximately 20 words.You must adhere to the following guidelines derived from meteorological 
definitions and common forecast terminology:

### Summary Guidelines

**General Principles:**
* **Brevity and Standardization:** the summary should be concise and use standardized meteorological terms.
* **Contextual Understanding:** Interpret weather data to reflect the impact for a specific location and time.
* **Exclusions:** 
    * Do NOT mention "no storms," "no frost." If a condition is not present or significant 
        (e.g., a data value of 0 for snow, or a category like "NO_FROST"), do not explicitly 
        state its absence.
    * Do NOT include temperatures or references to humidity. 
    * Do NOT allow "no significant precipitation"; only describe what is actually present.
**Accuracy Checks and Verification Principles:**
* **Presence Verification:** Before including any weather phenomenon (e.g., frost, snow, 
    thunderstorms, rain, fog), explicitly confirm its occurrence in the input data. If the 
    relevant data field shows zero values or a 'NO_X' category throughout the relevant 
    period, the phenomenon MUST NOT be mentioned in the summary.
* **Temporal Accuracy:** When describing events by time of day (e.g., morning, afternoon, 
    evening), strictly match the event's occurrence time in the input data to the defined 
    time windows. Do not include a time period for an event if it does not occur within 
    that defined window. For events spanning multiple defined time windows, mention all 
    relevant periods or summarize accurately (e.g., "throughout the day" if 
    truly pervasive).
* **Directional Accuracy:** Ensure wind direction words (e.g., 'northerly', 'south-westerly') 
    are accurately derived from the numerical 'wind_dir' values (in degrees) provided in the 
    input data, reflecting the predominant direction or significant shifts. Cross-reference 
    wind direction degrees to cardinal/intercardinal directions precisely.
* **Data Consistency:** Verify that all generated descriptions, especially for weather types 
    (e.g., snow, rain) and wind speeds (e.g., light, moderate), are directly supported by the 
    numerical values and categories in the input data. If a phenomenon has a zero value or 
    falls outside a defined range, it must not be mentioned or categorized incorrectly.

**Weather Elements:**
* **Precipitation:** Any liquid (rain, drizzle) or solid (hail, snow) water falling from clouds. 
    BoM Precipitation Words
    * **Showers:** Usually begin and end suddenly. Relatively short-lived, but may last half 
        an hour. Fall from cumulus clouds, often separated by blue sky. Showers may fall in 
        patches rather than across the whole forecast area. Range in intensity from light to 
        very heavy.
    * **Rain:** In contrast to showers, rain is steadier and normally falls from stratiform 
        (layer) cloud. Liquid water drops greater than 0.5 mm in diameter. Rain can range in 
        intensity from light to very heavy.
    * **Drizzle:** Fairly uniform precipitation composed exclusively of very small water 
        droplets (less than 0.5 mm in diameter) very close to one another.
    * **Frost:** Deposit of soft white ice crystals or frozen dew drops on objects near the 
        ground; formed when surface temperature falls below freezing point.
    * **Fog:** Suspension of very small water droplets in the air, reducing visibility at 
        ground level to less than a kilometre.
    * **Mist:** Similar to fog, but visibility remains more than a kilometre.
    * **Thunderstorms (Storms):** Convective clouds with lightning and thunder. Severe 
        thunderstorms include hail (≥ 2 cm), wind gusts (≥ 90 km/h), tornadoes, or very 
        heavy rain causing flash flooding.
    * **Snow showers:** Short, sudden, from convective clouds.
* **Windy:** Average wind speeds exceeding 40 km/h for a prolonged period during the day.
* **Fine:** Absence of rain or other precipitation (hail, snow, etc.). Avoid using if 
    excessively cloudy, windy, foggy, or dusty.

**Definition of time of day:**
* **early morning:** Before 6 am (00:00 - 05:59).
* **morning:** Between 6 am and 12 pm (06:00 - 11:59).
* **afternoon:** Between 12 pm and 6 pm (12:00 - 17:59).
* **evening:** Between 6 pm and midnight (18:00 - 23:59).

**Duration of Precipitation:**
* **Brief:** Short duration.
* **Intermittent:** Ceases at times.
* **Occasional:** Recurrent, but not frequent.
* **Frequent:** Occurring regularly and often.
* **Continuous:** Does not cease, or ceases only briefly.
* **Periods of Rain:** Rain expected most of the time, but with breaks.

**Distribution of Showers/Thunderstorms:**
* **Over time for a location:**
    * **Shower or two:** Infrequent.
    * **Few:** Small number over a time period.
* **Over areas (States/Territories):**
    * **Isolated:** Well separated (10-25% area coverage).
    * **Local:** Restricted to small areas.
    * **Patchy:** Irregularly over an area (10-25% area coverage).
    * **Scattered:** Irregularly distributed (25-55% area coverage).
    * **Widespread:**
        * For rain: Extensive throughout an area (25-55% area coverage).
        * For showers: Extensive throughout an area (over 55% area coverage).

**Likelihood of Precipitation/Thunderstorms:**
* **Possible, Chance, Risk:** May be used interchangeably for location forecasts, indicating a chance 
    due to random nature. "Risk" generally associated with thunderstorms.
* **Slight chance (20-30%), Medium chance (40-60%), High chance (70-80%), Very high chance (90-100%):** 
    Indicate likelihood of receiving ≥ 0.2 mm rainfall.
* **No mention of rainfall:** 0-10% chance of rain.

**Attributes (e.g., for Thunderstorms, Frozen Precipitation, Precipitation):**
* Prioritize the highest impact attribute present. Common attributes include: Tornadoes, 
    Destructive winds, Flash flooding, Damaging winds, Large hail, Heavy rain(fall), Hail, Dry, 
    Gusty winds, None.
* Tornadoes > Destructive winds > Flash flooding > Damaging winds > Large hail > Heavy rain > Gusty winds > Dry

---

**Wind table:**
|              |Units in km/h|Units in knots|
|:-------------|:--------------|:-------------|
|Calm          |	0          |	0         |
|Light winds   |19 km/h or less|10 knots or less|
|Moderate winds|20 - 29 km/h   |11-16 knots|
|Fresh winds   |30 - 39 km/h   |17-21 knots|
|Strong winds  |40 - 62 km/h   |22-33 knots|
|Gale          |63 - 87 km/h   |34-47 knots|
|Storm         |88 - 117 km/h  |48-63 knots|
|Hurricane	   |118 km/h or more | 64 knots or more |

**Wind words:** Use these cardinal directions for wind descriptions. Numerical wind 
directions should be converted to these compass points like Northern, Northeastern, East, 
Southeast, Southwest, West, Northwest, Easterly, Westernly etc.

---

### Summary Structure:
**Cloud:**
* Describe cloud cover using one type from: sunny, mostly sunny, partly cloudy, mostly cloudy, cloudy.
* Alternatively, describe a transition with a time window, e.g., "cloudy in the morning, partly cloudy 
    in the afternoon."

**Precipitation:**
* Clearly state any precipitation type and its timing/duration (e.g., "possible showers," "light rain at times"). 
    Use only official Bureau of Meteorology (BoM) wording for precipitation types as defined above.

**Wind:**
* Describe the wind for the day using direction (e.g., N, S, SW) and speed ranges in km/h from 
    the weather words wind table.
* **If wind speeds are consistently below 20 km/h, they are considered 'light winds' 
    (as per BoM definition 0-19 km/h).**
* If winds are equal to or below 15 km/h, say "light winds." Do not include a specific speed 
    range or direction for light winds in this case.
* **When describing wind speed ranges, use increments of 5 km/h (e.g., 15, 20, 25, 30 km/h). 
    The range should be from the number below the lowest to the number above the highest 
    (e.g., 20 to 30 km/h). Ensure that the categorization (Light, Moderate, Fresh, etc.) 
    strictly aligns with the BoM definitions (e.g., 'Light' is 0-19 km/h; 'Moderate' is 
    20-39 km/h).**
* Include changes in wind conditions across windows of the day (e.g., "light winds becoming 
    northerly 15 to 20 km/h during the evening").

**Specific Weather Event Phrasing (if occurring in at least two hourly timesteps):**
* **Thunderstorms:** If present in at least two hourly timesteps, phrase as: "The risk of 
    thunderstorms."
* **Fog:** If present in at least two hourly timesteps, phrase as: "Fog patches in the 
    [time of day]."
* **Frost:** If present in at least two hourly timesteps, phrase as: "Frost in the 
    [time of day]."

**Specific Wind Gust Hazard Phrasing:**
* **Damaging Wind Gusts:** If wind gusts exceed 90 km/h, 
    phrase as: "The risk of damaging wind gusts."
* **Destructive Wind Gusts:** If wind gusts exceed 125 km/h, phrase as: 
    "The risk of destructive wind gusts."
    
---

### Input Data:
{hourly_forecast_data}

### Variable Definitions:
{var_definitions}

### Output Format:
**Your output MUST be a valid JSON object ONLY, with no additional text or explanations.**
{{
    ""long_form_text": "Detailed summary here."
}}

---

### Examples:

<input_data id=1>
time	fog_prob_cat	frost_prob_cat	gust_kmh	rain	snow	tcc	weather_icon_precis	wind_dir	wind_kmh
00:00	MODERATE	NO_FROST	13.86796474	0	0	88.33541743	Partly cloudy	26.09273887	9.716022491
01:00	MODERATE	NO_FROST	14.59632683	0	0	83.82656288	Cloudy	18.62793463	10.01686764
02:00	MODERATE	NO_FROST	17.37773514	0	0	88.27499962	Cloudy	19.5580107	12.31215286
03:00	MODERATE	NO_FROST	23.63814583	0	0	86.35000038	Cloudy	21.77157265	15.10348129
04:00	MODERATE	NO_FROST	27.89144783	0	0	93.85000038	Cloudy	18.38027147	19.1056633
05:00	MODERATE	NO_FROST	29.36943436	0	0	93.35000038	Cloudy	10.99785299	18.04513359
06:00	MODERATE	NO_FROST	32.08805962	0	0	97	Cloudy	11.97204452	19.66207886
07:00	MODERATE	NO_FROST	30.61327057	0	0	98	Cloudy	17.9025484	19.62897873
08:00	MODERATE	NO_FROST	30.24129715	0	0	75.8046875	Mostly cloudy	19.58094842	23.46851368
09:00	LOW	NO_FROST	37.69198875	0	0	78.4765625	Cloudy	22.92420204	25.24127674
10:00	LOW	NO_FROST	41.86080017	0	0	86	Mostly cloudy	11.37962301	35.18293095
11:00	LOW	NO_FROST	41.40559769	0	0	86.33333333	Cloudy	14.6348863	35.89234562
12:00	LOW	NO_FROST	42.89334965	0	0	86.66666667	Cloudy	9.959808771	35.33575745
13:00	LOW	NO_FROST	45.64540672	0.002384185791	0	74.5	Cloudy	9.412748352	35.7215723
14:00	LOW	NO_FROST	38.43733215	0.001455511476	0	68.33333333	Mostly cloudy	8.964102586	29.48087196
15:00	LOW	NO_FROST	36.76400986	0.2364506043	0	85.58072917	Light rain at times	6.718757558	26.63264389
16:00	LOW	NO_FROST	32.70405064	0.105456012	0	95.9140625	Cloudy	6.754404124	23.24413414
17:00	LOW	NO_FROST	40.6551918	0.05128954022	0	84.49739583	Possible showers	5.404811778	23.6698143
18:00	MODERATE	NO_FROST	39.68463364	0.1738420584	0	67.45572917	Possible showers	3.783374858	24.17400894
19:00	MODERATE	NO_FROST	40.255896	0.0919252777	0	51.65468788	Partly cloudy	6.424871663	24.33173237
20:00	MODERATE	NO_FROST	38.96947212	0.3141897303	0	81.01822917	Mostly cloudy	7.161968761	25.60299683
21:00	MODERATE	NO_FROST	29.20897713	0.1427510977	0	86.35677083	Light rain at times	13.21580098	24.62383595
22:00	MODERATE	NO_FROST	31.26936016	0.06563162052	0	53.953125	Possible showers	8.820923226	22.04483604
23:00	MODERATE	NO_FROST	29.30796051	0.0005746859314	0	48.09739621	Partly cloudy	11.95081393	18.43786812
</input_data>

<assistant_response id=1>
{{
  "long_form_text": "Mostly cloudy. Possible showers in the late afternoon and evening. Winds northeasterly 10 to 25 km/h increasing to northerly 25 to 35 km/h in the afternoon."
}}
</assistant_response>

<input_data id=2>
time	fog_prob_cat	frost_prob_cat	gust_kmh	rain	snow	tcc	weather_icon_precis	wind_dir	wind_kmh
00:00	MODERATE	NO_FROST	28.19167519	0.0008583342036	0	58.74635379	Partly cloudy	11.48938929	17.84660721
01:00	MODERATE	NO_FROST	25.77644958	0.01676698248	0	39.515625	Mostly clear	12.57908199	15.72667217
02:00	MODERATE	NO_FROST	23.61635723	0.0005124293636	0	66.71406174	Partly cloudy	9.102229011	15.86100292
03:00	MODERATE	NO_FROST	24.02917404	0.0004020829995	0	72	Mostly cloudy	11.27590708	16.45653152
04:00	MODERATE	NO_FROST	26.57766571	0.0002917366355	0	67.45624924	Mostly cloudy	2.513076976	17.40629959
05:00	MODERATE	NO_FROST	26.92052612	0.02132304304	0	76.22812462	Mostly cloudy	359.5504215	17.81403542
06:00	MODERATE	NO_FROST	26.88750229	0.1669771671	0	84.25	Light rain at times	347.7093368	17.45801544
07:00	MODERATE	NO_FROST	25.27144299	0.1041428269	0	96.5	Light rain at times	337.4696642	17.28702927
08:00	MODERATE	NO_FROST	30.3410862	0.4424341326	0	96	Light rain at times	323.8008509	18.31065369
09:00	MODERATE	NO_FROST	35.90483513	0.7585536813	0	93.0234375	Light rain at times	298.816325	19.4750576
10:00	MODERATE	NO_FROST	30.81377602	0.8236936052	0	91.0546875	Light rain at times	290.2036264	19.0437336
11:00	MODERATE	NO_FROST	35.64126129	0.1999351471	0	78.0234375	Possible showers	286.2152203	22.86894436
12:00	LOW	NO_FROST	36.81947346	0.1046450734	0	49.02812481	Possible showers	286.0593048	22.41211815
13:00	LOW	NO_FROST	31.45672531	0.116294703	0	64.46875	Mostly sunny	291.6275114	18.98822975
14:00	LOW	NO_FROST	29.41784973	0.03933461191	0	54.58333333	Mostly sunny	299.7455565	17.41262627
15:00	LOW	NO_FROST	25.17903709	0.03875901302	0	54.21666686	Mostly sunny	316.4237932	15.94003677
16:00	LOW	NO_FROST	19.42583466	0.02483197369	0	72.14999962	Partly cloudy	333.7859171	15.06093597
17:00	MODERATE	NO_FROST	17.0415802	0.2033188719	0	84.66666667	Light rain at times	356.4326952	14.20900726
18:00	MODERATE	NO_FROST	19.5885849	0.4634898901	0	91.33333333	Light rain at times	8.153367757	16.15785027
19:00	MODERATE	NO_FROST	25.0318985	0.6517614943	0	97.8046875	Light rain at times	14.58600499	18.77192497
20:00	MODERATE	NO_FROST	27.78362312	0.5286603788	0	97.609375	Light rain at times	9.658818218	18.09764671
21:00	MODERATE	NO_FROST	24.32979164	0.3905260364	0	97.4140625	Light rain at times	11.57179417	16.36493683
22:00	MODERATE	NO_FROST	19.46658707	0.7344398479	0	86.8671875	Possible showers	26.54270158	14.89098167
23:00	MODERATE	NO_FROST	19.76736259	0.1190240795	0	74.9609375	Possible showers	8.698180131	13.8447237
</input_data>

<assistant_response id=2>
{{
  "long_form_text": "Mostly cloudy. Light rain at times. Winds northerly 15 to 25 km/h."
}}
</assistant_response>

<input_data id=3>
time	fog_prob_cat	frost_prob_cat	gust_kmh	rain	snow	tcc	weather_icon_precis	wind_dir	wind_kmh
00:00	MODERATE	NO_FROST	16.68885803	0.1805706819	0	39.90468788	Possible showers	7.392273501	11.19238758
01:00	MODERATE	NO_FROST	16.75268555	0.1831176862	0	40.08749962	Partly cloudy	10.31564027	9.396507263
02:00	MODERATE	NO_FROST	15.94872284	0.005722045898	0	73.5703125	Mostly cloudy	7.43116887	8.955724716
03:00	MODERATE	NO_FROST	18.61491013	0.08983302116	0	73.7578125	Light rain at times	357.8247229	9.77821064
04:00	MODERATE	NO_FROST	24.07975464	0.6040787101	0	95	Light rain at times	344.9365405	10.79187107
05:00	MODERATE	NO_FROST	23.77142868	0.762694339	0	95.25	Light rain at times	336.7797195	10.61314583
06:00	MODERATE	NO_FROST	25.49667015	1.068448981	0	96.5	Light rain at times	330.8914594	10.84239674
07:00	MODERATE	NO_FROST	27.45936432	1.268277109	0	94	Light rain at times	311.9865864	12.46543217
08:00	MODERATE	NO_FROST	31.290662	0.5517608405	0	97.8046875	Light rain at times	300.9550803	11.3082056
09:00	MODERATE	NO_FROST	29.51920185	0.5045625369	0	98	Light rain at times	309.7428892	11.37682629
10:00	MODERATE	NO_FROST	30.14674702	0.4267016967	0	95.25	Light rain at times	275.8953368	15.74719238
11:00	MODERATE	NO_FROST	27.31938648	0.5977360615	0	92.25	Light rain at times	270.9400594	16.42823029
12:00	MODERATE	NO_FROST	29.21922417	1.134004434	0	97.25	Light rain at times	278.3578082	17.39237595
13:00	MODERATE	NO_FROST	24.09026394	1.435148576	0	98	Light rain at times	258.059182	17.59016228
14:00	MODERATE	NO_FROST	27.23029556	0.8588593381	0	88.25	Light rain at times	241.3398423	16.44479179
15:00	MODERATE	NO_FROST	27.33978615	0.5095712344	0	84.92499924	Light rain at times	230.3787714	15.7940836
16:00	MODERATE	NO_FROST	26.99928818	0.4724245491	0	85.20000076	Light rain at times	225.4709225	15.53553009
17:00	MODERATE	NO_FROST	25.05383186	0.4157065873	0	76.06666629	Light rain at times	224.2140948	14.1019268
18:00	MODERATE	NO_FROST	22.3695816	0.3291657766	0	83.31302007	Light rain at times	227.2351641	14.41904926
19:00	MODERATE	NO_FROST	18.89792252	0.3632990991	0	77.40937519	Possible showers	231.0397059	14.63811016
20:00	MODERATE	NO_FROST	19.23495865	0.2878187895	0	80.63645871	Possible showers	238.9625162	12.57949352
21:00	MODERATE	NO_FROST	18.13416481	0.2310752869	0	89.36822955	Possible showers	242.2628442	11.96976852
22:00	HIGH	NO_FROST	14.39693832	0.2641816735	0	90.6328125	Light rain at times	243.3775797	10.81512928
23:00	HIGH	NO_FROST	16.24528313	1.312397718	0	87.98958333	Light rain at times	242.6842606	11.08910942
</input_data>

<assistant_response id=3>
{{
  "long_form_text": "Mostly cloudy. Light rain at times. Winds northwesterly 10 to 20 km/h tending southwesterly in the afternoon."
}}
</assistant_response>

<input_data id=4>
time	fog_prob_cat	frost_prob_cat	gust_kmh	rain	snow	tcc	weather_icon_precis	wind_dir	wind_kmh
00:00	HIGH	NO_FROST	15.62795258	0.5453933477	0	72.31510417	Light rain at times	255.1133252	10.90005589
01:00	HIGH	NO_FROST	12.58556557	0.200953722	0	73.12812424	Cloudy	267.8757581	9.502864838
02:00	HIGH	NO_FROST	13.18062115	0.4451933702	0	86.56510417	Light rain at times	267.5014386	9.290716171
03:00	HIGH	NO_FROST	12.63520908	0.6344598929	0	88.27864583	Light rain at times	252.3769072	9.841888428
04:00	HIGH	NO_FROST	11.3116827	0.3986840248	0	97.5	Light rain at times	248.5540887	9.526219368
05:00	HIGH	NO_FROST	11.6038084	0.3115461472	0	91.25	Light rain at times	249.2780323	10.27908421
06:00	HIGH	NO_FROST	13.29291248	0.6174788475	0	89.75	Light rain at times	250.8526597	11.54234314
07:00	HIGH	NO_FROST	13.55967999	0.903358638	0	88.5	Light rain at times	248.8802209	10.93873596
08:00	HIGH	NO_FROST	15.07335091	0.866460841	0	93.5546875	Light rain at times	245.2975443	12.09442616
09:00	HIGH	NO_FROST	16.15229225	1.010829687	0	96.72500038	Light rain at times	242.7485257	12.88017368
10:00	HIGH	NO_FROST	10.74371529	1.060557636	0	98	Light rain at times	219.7395352	9.684728622
11:00	MODERATE	NO_FROST	16.65185547	0.7752191038	0	97.93489583	Light rain at times	237.2728493	13.75547028
12:00	MODERATE	NO_FROST	16.5418129	0.5421898421	0	76.36979167	Possible showers	246.5931949	15.1532383
13:00	MODERATE	NO_FROST	16.60446167	0.4997857711	0	87.9296875	Light rain at times	241.0740182	15.94547939
14:00	MODERATE	NO_FROST	18.75907898	0.7005775004	0	96.14479129	Light rain at times	237.3091764	16.43326378
15:00	MODERATE	NO_FROST	22.46339741	1.224096771	0	91.23489507	Light rain at times	221.5412592	17.97955132
16:00	MODERATE	NO_FROST	19.49287796	1.056991566	0	94	Light rain at times	225.4042767	16.74718094
17:00	MODERATE	NO_FROST	17.76420212	1.111095113	0	82.44999981	Light rain at times	224.0231432	15.40674305
18:00	MODERATE	NO_FROST	17.63395691	1.271701074	0	92.5	Light rain at times	223.6990823	14.44076157
19:00	MODERATE	NO_FROST	18.71880341	1.394806652	0	98	Light rain at times	222.277251	13.53162575
20:00	MODERATE	NO_FROST	19.6333313	1.446871434	0	92.5	Light rain at times	222.7669502	12.98313808
21:00	MODERATE	NO_FROST	19.90976143	1.580156657	0	87.5	Possible showers	223.3661275	12.75170231
22:00	MODERATE	NO_FROST	22.16194267	1.64781669	0	95.57500076	Possible showers	226.2402565	11.99480915
23:00	MODERATE	NO_FROST	17.63391495	1.419933139	0	91.125	Possible showers	231.8458358	11.32096672
</input_data>

<assistant_response id=4>
{{
  "long_form_text": "Mostly cloudy. Light rain at times. Light winds west to southwesterly 10 to 20 km/h."
}}
</assistant_response>

<input_data id=5>
time	fog_prob_cat	frost_prob_cat	gust_kmh	rain	snow	tcc	weather_icon_precis	wind_dir	wind_kmh
00:00	HIGH	NO_FROST	15.59533501	1.380805576	0	95.5	Light rain at times	235.6487544	10.47563934
01:00	HIGH	NO_FROST	13.72937584	1.326053013	0	94.32500076	Light rain at times	242.2028077	10.1723423
02:00	HIGH	NO_FROST	10.867836	0.6829457578	0	91.44218826	Light rain at times	247.0970953	9.9391222
03:00	HIGH	NO_FROST	9.751649857	0.5493781132	0	73.234375	Possible showers	252.8429178	8.871017456
04:00	HIGH	NO_FROST	8.711070061	0.4501856595	0	89.2265625	Light rain at times	262.0802689	8.471716881
05:00	HIGH	NO_FROST	9.080807686	0.3137715181	0	71.1427091	Possible showers	273.6970077	6.992213249
06:00	HIGH	NO_FROST	8.743976593	0.1450024994	0	55.05885379	Possible showers	284.7271387	6.697514057
07:00	MODERATE	NO_FROST	12.09841824	0	0	24.125	Mostly sunny	304.1961258	7.387876511
08:00	MODERATE	NO_FROST	12.32828522	0	0	24.1968751	Mostly sunny	294.0544474	7.185968399
09:00	MODERATE	NO_FROST	13.7937212	0	0	26.2437501	Mostly sunny	280.020171	6.902383804
10:00	MODERATE	NO_FROST	13.10745907	0.05353475324	0	32.06562495	Mostly sunny	257.5843988	9.889421463
11:00	MODERATE	NO_FROST	14.12328148	0.1364599107	0	40.39010421	Possible showers	244.6252517	10.44289398
12:00	MODERATE	NO_FROST	15.28523254	0.2352089875	0	51.88958295	Possible showers	229.3440636	11.68332195
13:00	MODERATE	NO_FROST	16.37214279	0.5339578737	0	69.81406212	Possible showers	221.5589006	11.23988533
14:00	MODERATE	NO_FROST	15.30350018	0.9587892428	0	57.1328125	Possible showers	222.6549404	10.28188133
15:00	MODERATE	NO_FROST	15.43133354	0.3250162782	0	34.27656269	Possible showers	221.943906	9.459352493
16:00	MODERATE	NO_FROST	13.78395271	0.2610493655	0	39.42031288	Possible showers	224.5066487	9.46747303
17:00	MODERATE	NO_FROST	11.82518005	0.252865162	0	34.85208352	Possible showers	226.5388657	8.623657227
18:00	MODERATE	NO_FROST	11.40504932	0.2588358388	0	48.53385417	Possible showers	229.705909	7.060014725
19:00	MODERATE	NO_FROST	11.08647346	0.2648065156	0	39.96562481	Possible showers	233.4450016	6.449877262
20:00	MODERATE	NO_FROST	10.39377975	0.2079126614	0	54.10468737	Possible showers	246.5836573	6.511986732
21:00	HIGH	NO_FROST	9.227239609	0.1737285602	0	77.74374994	Light rain at times	256.2074926	7.545598984
22:00	HIGH	NO_FROST	11.15789318	0.139544459	0	90.3828125	Light rain at times	259.0282116	8.195731163
23:00	HIGH	NO_FROST	9.8989048	0.202475927	0	83.48645846	Light rain at times	259.6649774	7.525961399
</input_data>

<assistant_response id=5>
{{
  "long_form_text": "Mostly cloudy. Possible showers tending to light rain at times. Light winds tending west to southwesterly 10 to 15 km/h."
}}
</assistant_response>

<input_data id=6>
time	fog_prob_cat	frost_prob_cat	gust_kmh	rain	snow	tcc	weather_icon_precis	wind_dir	wind_kmh
00:00	HIGH	NO_FROST	9.366769791	0.2611221884	0	90.09010442	Light rain at times	261.5212316	7.616122246
01:00	HIGH	NO_FROST	8.513041496	0.5197682591	0	89.94375038	Light rain at times	264.0033547	7.628046989
02:00	HIGH	NO_FROST	8.981575012	0.3993379815	0	75.12916692	Light rain at times	274.1071315	7.596813679
03:00	HIGH	NO_FROST	10.19873047	0.2039750456	0	62.56458346	Possible showers	275.5682141	7.686081409
04:00	HIGH	NO_FROST	11.6639967	0.2336120144	0	50	Possible showers	270.6005377	7.437998772
05:00	MODERATE	NO_FROST	11.31919765	0.1992429587	0	49.51718775	Possible showers	272.0956378	7.376359463
06:00	HIGH	NO_FROST	10.46029091	0.07272941195	0	56.53437551	Possible showers	273.4891307	7.507913589
07:00	HIGH	NO_FROST	10.2241497	0.07121586521	0	59.30156326	Light rain at times	272.7864789	7.680715084
08:00	HIGH	NO_FROST	10.00687122	0.1028417658	0	67.13437525	Light rain at times	269.7657155	7.087584019
09:00	HIGH	NO_FROST	10.37252998	0.1594359259	0	73.71718725	Light rain at times	262.2145073	6.750928402
10:00	MODERATE	NO_FROST	10.42004013	0.1553175494	0	80.29999924	Light rain at times	249.5621836	7.818613529
11:00	MODERATE	NO_FROST	10.85608482	0.09067811052	0	69.0263017	Possible showers	242.1923275	7.731335163
12:00	MODERATE	NO_FROST	11.79878044	0.1260213078	0	50.75260417	Possible showers	233.4243393	8.143961906
13:00	MODERATE	NO_FROST	12.00567818	0.1863650773	0	47.22890663	Possible showers	224.6191446	8.624032021
14:00	MODERATE	NO_FROST	11.07370377	0.1496787676	0	55.796875	Possible showers	219.2404432	8.58217144
15:00	MODERATE	NO_FROST	9.808582306	0.08847620213	0	58.61484337	Possible showers	213.5384381	8.137290955
16:00	MODERATE	NO_FROST	8.064483643	0.052273732	0	55.68281174	Possible showers	210.425169	7.263463974
17:00	MODERATE	NO_FROST	6.986951828	0.03881837879	0	65.30650965	Partly cloudy	211.1337499	6.491418362
18:00	MODERATE	NO_FROST	6.376948357	0.03238609149	0	73.93020757	Mostly cloudy	212.7367282	6.354819775
19:00	HIGH	NO_FROST	6.648144722	0.02595380418	0	80.05390549	Cloudy	210.6232133	6.469323635
20:00	HIGH	NO_FROST	7.395105982	0.05153512919	0	79.59427039	Light rain at times	221.8104123	6.72282362
21:00	HIGH	NO_FROST	7.963371897	0.1267814111	0	79.13463529	Light rain at times	257.3945302	7.239428997
22:00	HIGH	NO_FROST	8.483953619	0.07702626252	0	78.67500019	Light rain at times	313.0084752	7.712685108
23:00	HIGH	NO_FROST	8.417356777	0.04841650616	0	79.85625013	Mostly cloudy	326.0556234	7.652142525
</input_data>

<assistant_response id=6>
{{
  "long_form_text": "Mostly cloudy. Possible showers tending to light rain at times. Light winds."
}}
</assistant_response>

<input_data id=7>
time	fog_prob_cat	frost_prob_cat	gust_kmh	rain	snow	tcc	weather_icon	wind_dir	wind_kmh
00:00	HIGH	NO_FROST	7.87577486	0.02193837086	0	80.28750006	NIGHT_MOSTLY_CLOUDY	336.3366271	7.82141304
01:00	HIGH	NO_FROST	8.111536026	0.02046033093	0	81.46875	CLOUDY	348.9694385	7.844714165
02:00	HIGH	NO_FROST	8.9337883	0.02046418133	0	81.51666641	CLOUDY	0.1678763783	8.047563553
03:00	HIGH	NO_FROST	9.503983498	0.1200404636	0	80.81458282	LIGHT_RAIN	10.48210477	7.820016861
04:00	HIGH	NO_FROST	10.02709389	0.1946171273	0	80.11249924	NIGHT_SHOWER	22.10857603	8.062550545
05:00	HIGH	NO_FROST	10.08754253	0.1181422531	0	77.76380157	LIGHT_RAIN	22.96753422	8.154411316
06:00	HIGH	NO_FROST	10.01643753	0.1670560907	0	75.41510391	SHOWER	24.22422757	8.257375717
07:00	HIGH	NO_FROST	10.02893162	0.1409696422	0	73.06640625	SHOWER	26.72924643	8.908966064
08:00	HIGH	NO_FROST	9.993537903	0.0422856988	0	71.19270833	MOSTLY_CLOUDY	25.71347073	8.871350288
09:00	HIGH	NO_FROST	10.57460594	0.06924841186	0	69.31901042	SHOWER	22.49564902	8.709899902
10:00	HIGH	NO_FROST	10.72801399	0.1185076657	0	66.9453125	SHOWER	330.6665602	9.000417709
11:00	HIGH	NO_FROST	10.72823143	0.128372584	0	65.91302109	SHOWER	269.6783074	8.14863205
12:00	MODERATE	NO_FROST	10.7035923	0.08918383681	0	66.88072968	SHOWER	232.9433586	7.269650936
13:00	MODERATE	NO_FROST	10.25461578	0.09999575723	0	65.09843826	SHOWER	220.8024208	6.699502468
14:00	MODERATE	NO_FROST	9.911046982	0.145312858	0	65.00781314	SHOWER	218.8938458	6.104848862
15:00	MODERATE	NO_FROST	9.659576416	0.06768549224	0	56.41718801	SHOWER	217.4110991	5.17954874
16:00	MODERATE	NO_FROST	8.935152054	0.04005927093	0	56.07656288	PARTLY_CLOUDY	217.7116869	4.749810219
17:00	MODERATE	NO_FROST	7.781400204	0.02891015418	0	59.61119811	PARTLY_CLOUDY	218.2940862	4.628577709
18:00	MODERATE	NO_FROST	6.266868591	0.01776330265	0	54.64583333	MOSTLY_SUNNY	222.8148907	4.492913723
19:00	MODERATE	NO_FROST	6.530958176	0.006616451122	0	55.18046856	NIGHT_MOSTLY_CLEAR	261.3678563	4.563026428
20:00	HIGH	NO_FROST	6.366413593	0.009398224913	0	60.97343731	NIGHT_PARTLY_CLOUDY	322.7407659	5.23884964
21:00	HIGH	NO_FROST	5.956273079	0.0121799987	0	64.01640606	NIGHT_PARTLY_CLOUDY	322.8220255	5.911664963
22:00	HIGH	NO_FROST	7.339389801	0.01496177249	0	67.55937481	NIGHT_MOSTLY_CLOUDY	315.7482596	6.672172546
23:00	HIGH	NO_FROST	7.004982042	0.01254273187	0	73.79348946	NIGHT_MOSTLY_CLOUDY	294.031424	6.368165493
</input_data>

<assistant_response id=7>
{{
  "long_form_text": "Partly cloudy. Possible showers. Light winds."
}}
</assistant_response>
"""
    model_outputs = {}
    for model in [
        # "deepseek/deepseek-chat-v3-0324:free",
        # "meta-llama/llama-4-maverick:free",
        # "mistralai/mistral-small-24b-instruct-2501:free",
        # "llama-3.1-8b-instant",
        "deepseek-r1-distill-llama-70b",
        # "mistral-saba-24b",
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
                temperature=0.0,  # Set temperature to 0 for deterministic output
            )
            response_content = completion.choices[0].message.content

            # Try to parse as JSON
            try:
                output_data = LLMResponse.model_validate_json(response_content)
                # parsed_output_str = output_data.model_dump_json(indent=2)
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
            # "precis": output_data.precis,
            "long_form_text": output_data.long_form_text,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "latency_seconds": latency_seconds,
        }

    """
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
        "precis": "",  # gemini_output_data.precis,
        "long_form_text": "",  # gemini_output_data.long_form_text,
        "input_tokens": 0,  # gemini_input_tokens,
        "output_tokens": 0,  # gemini_output_tokens,
        "latency_seconds": 0,  # latency_seconds,
    }
    """

    # Return the model outputs
    return model_outputs
