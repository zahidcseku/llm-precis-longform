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
## Prompts from deepseek
```
Generate two weather summaries using:
1. 5 words: Prioritize extreme events (cyclone, storms, wind) + temp.
2. 20 words: Use structure: 
   "[Colud coverage]. [precip type] [intensity] [direction]. [Wind]. [Temp descriptors]. [Special conditions]."

Rules:
- Precipitation: Only include if PoP ≥35%
- Wind: Use "windy" if >40 km/h sustained
- Temp: Apply region/season tables
- Cyclone warnings override all
- Ignore frost; fog only for Day 0/1
```

## From deepseek V2
```
You are a weather forecaster generating two summaries from daily weather data:
    1. 5-word summary (extremely concise, dominant condition only)
    2. 20-word summary (structured details)

    Follow these strict rules:

    --- WEATHER PRIORITY HIERARCHY ---
    1. Cyclone warnings (if present)
    2. Thunderstorms (with attributes: tornadoes > destructive winds > flash flooding > hail)
    3. Heavy precipitation (snow > rain > showers)
    4. Windy conditions (sustained ≥40km/h)
    5. Fog/frost (only for Day 0/1)
    6. Cloud cover

    --- INPUT COLUMN MAPPING ---
    * Use `wind_kmh` for wind speed
    * Use `precip` for rainfall (mm)
    * Use `tcc` for cloud cover (%)
    * Use `frost_prob_cat` for frost likelihood
    * Use `storm_prob_idx` for thunderstorm probability

    --- SUMMARY RULES ---
    «5-WORD SUMMARY»
    - Maximum 5 words
    - Select ONE dominant condition:
    • Cyclone → "Cyclone warning."
    • Thunderstorms → "Thunderstorms." / "Severe storms."
    • Precipitation → "Showers." / "Heavy rain." / "Shower or two."
    • Windy → "Windy."
    • Frost → "Frost." (only if frost_prob_cat ≠ 'NO_FROST' in morning hours)
    • Default → Cloud cover ("Sunny." / "Partly cloudy.")

    «20-WORD SUMMARY»
    Follow this structure:
    1. CLOUD: Map avg `tcc` to:
    - ≤15% → "Sunny"
    - 16-30% → "Mostly sunny"
    - 31-65% → "Partly cloudy"
    - >65% → "Cloudy"
    2. PRECIPITATION (only if expected):
    - Chance terms:
        20-30% chance → "Slight chance"
        40-60% chance → "Medium chance"
        70-90% chance → "High chance"
        ≥90% chance → "Very high chance"
    - Type: 
        Convective/isolated → "showers"
        Widespread/steady → "rain"
    - Timing: Use local time brackets from guidelines
    - Attributes: Include hail if heavy precip + cold temps
    3. FROST (only for Day 0/1):
    - "Areas of morning frost" if frost_prob_cat ≠ 'NO_FROST' before 7am
    4. WIND:
    - ≥40km/h → "Windy." + direction + speed range
    - Changes → "[Direction1] becoming [Direction2]"
    5. ORDER: [Cloud] → [Precip] → [Frost] → [Wind]

    --- SPECIAL CASES ---
    - Ignore frost after Day 1
    - Never combine "dry" with precipitation terms
    - Use compass directions (SSW, NNE)
    - Time references: Morning=1-11am, Afternoon=1-9pm

    === EXAMPLES ===
    Input: [HOURLY DATA]
    5 words: [CONCISE PHRASE] 
    20 words: [STRUCTURED DESCRIPTION]

    Now generate for new input:

    Example of the JSON structure:
    {{
      "precis": "Concise summary here.",
      "long_form_text": "Detailed summary here."
    }}

    Do NOT include any other text, explanations, or markdown formatting before or after the JSON object.

    The definitions of the variables in the data are as follows:
    {var_definitions}   
            
    Hourly Forecast Data:
    {hourly_forecast_data}
    """
```

## Deepseek new prompt
```
f"""
Your task is to summarize hourly weather conditions for a given location into two distinct summaries: 
    5-word summary: extremely concise, dominant condition only
    20-word summary: [Colud coverage]. [precip type] [intensity] [direction]. [Wind]. [Temp descriptors]. [Special conditions]. 
You must adhere to the following guidelines derived from meteorological definitions and common forecast terminology:

### Summary Guidelines
**General Principles:**
* **Brevity and Standardization:** Both summaries should be concise and use standardized meteorological terms.
* **Contextual Understanding:** Interpret weather data to reflect the impact for a specific location and time.

**Weather Elements:**
* **Precipitation:** Any liquid (rain, drizzle) or solid (hail, snow) water falling from clouds.
    * **Showers:** Usually begin and end suddenly. Relatively short-lived, but may last half an hour. Fall from cumulus clouds, often separated by blue sky. Showers may fall in patches rather than across the whole forecast area. Range in intensity from light to very heavy.
    * **Rain:** In contrast to showers, rain is steadier and normally falls from stratiform (layer) cloud. Liquid water drops greater than 0.5 mm in diameter. Rain can range in intensity from light to very heavy.
    * **Drizzle:** Fairly uniform precipitation composed exclusively of very small water droplets (less than 0.5 mm in diameter) very close to one another.
    * **Frost:** Deposit of soft white ice crystals or frozen dew drops on objects near the ground; formed when surface temperature falls below freezing point.
    * **Fog:** Suspension of very small water droplets in the air, reducing visibility at ground level to less than a kilometre.
    * **Mist:** Similar to fog, but visibility remains more than a kilometre.
    * **Thunderstorms (Storms):** Convective clouds with lightning and thunder. Severe thunderstorms include hail (≥ 2 cm), wind gusts (≥ 90 km/h), tornadoes, or very heavy rain causing flash flooding.
    * **Snow showers:** Short, sudden, from convective clouds.
* **Windy:** Average wind speeds exceeding 40 km/h for a prolonged period during the day.
* **Fine:** Absence of rain or other precipitation (hail, snow, etc.). Avoid using if excessively cloudy, windy, foggy, or dusty.

**Timing:**
* **Early in the morning:** Before 7 am.
* **In the morning:** Between 1 am and 11 am.
* **In the late morning:** Between 9 am and midday.
* **During early afternoon:** Between 12 pm and 4 pm.
* **During the afternoon:** Between 1 pm and 9 pm.
* **In the evening:** Between 6 pm and midnight.
* **Later in the evening:** After 9 pm.

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
* **Possible, Chance, Risk:** May be used interchangeably for location forecasts, indicating a chance due to random nature. "Risk" generally associated with thunderstorms.
* **Slight chance (20-30%), Medium chance (40-60%), High chance (70-80%), Very high chance (90-100%):** Indicate likelihood of receiving ≥ 0.2 mm rainfall.
* **No mention of rainfall:** 0-10% chance of rain.

**Attributes (e.g., for Thunderstorms, Frozen Precipitation, Precipitation):**
* Prioritize the highest impact attribute present. Common attributes include: Tornadoes, Destructive winds, Flash flooding, Damaging winds, Large hail, Heavy rain(fall), Hail, Dry, Gusty winds, None.

### Input Data:
{hourly_forecast_data}

### Output Format:
Example of the JSON structure:
{{
    "precis": "Concise summary here.",
    ""long_form_text": "Detailed summary here."
}}

### Input and Output Examples:
**Input:**
date	time	apparent_temp	chill_stress_idx	dew_pt	frost_prob_cat	heat_stress_rating	k_idx	pres_msl	rain	rel_hum	snow	storm_prob_idx	tcc	temp	temp_inv_prob_idx	total_totals_idx	wind_dir	wind_dir_compass	wind_kmh
2025-06-04	10:00	6.483518829	905.7937321	1.709985352	NO_FROST	NEGLIGIBLE	-4.049993896	1025.199951	0	52	0	0	30	11.20998535	0	35.9999939	167.9052387	SSE	15.46324102
2025-06-04	11:00	6.666432906	910.3536017	2.330010986	NO_FROST	NEGLIGIBLE	-3.15	1025.400024	0	53	0	0	20	11.77001343	0	35.93331299	167.3474399	SSE	18.07902185
2025-06-04	12:00	7.271713491	900.9534943	2.659997559	NO_FROST	NEGLIGIBLE	-2.250006104	1024.900024	0	52	0	0	62	12.26000366	0	35.8666626	168.2317033	SSE	17.65101817
2025-06-04	13:00	7.49393284	897.9986198	2.510003662	NO_FROST	NEGLIGIBLE	-1.350012207	1024.400024	0	51	0	0	70	12.54000244	0	35.79998169	169.5922774	S	17.9350787
2025-06-04	14:00	7.582345083	895.3533135	2.240014648	NO_FROST	NEGLIGIBLE	-3.216680908	1024.5	0	49	0	0	64	12.67998657	0	35.89998779	171.8698956	S	17.81908612
2025-06-04	15:00	7.786140705	889.7379768	1.879998779	NO_FROST	NEGLIGIBLE	-5.083349609	1024.800049	0	48	0	0	69	12.70998535	0	35.99996338	172.5685893	S	16.70027001
2025-06-04	16:00	8.071006233	883.7679546	2.260003662	NO_FROST	NEGLIGIBLE	-6.950018311	1025.5	0	49	0	0	83	12.70998535	0	36.09996948	178.6677701	S	15.48418623
2025-06-04	17:00	8.134889544	883.8268771	3.039971924	NO_FROST	NEGLIGIBLE	-10.65	1026.199951	0	52	0	0	98	12.58001099	0	36.43331299	181.3639276	S	15.12428442
2025-06-04	18:00	8.302689722	882.595118	4.020013428	NO_FROST	NEGLIGIBLE	-14.34998169	1026.5	0	57	0	0	64	12.39998779	0	36.76665649	178.5679033	S	14.40449415
2025-06-04	19:00	8.321784307	879.5524156	4.080010986	NO_FROST	NEGLIGIBLE	-18.04997864	1026.900024	0	58	0	0	14	12.20998535	0	37.1	173.8298249	S	13.3976119
2025-06-04	20:00	8.620412363	862.5083909	3.800012207	NO_FROST	NEGLIGIBLE	-17.31664124	1027	0	57	0	0	5	12.04000244	0	36.7333313	170.2175933	S	10.5940364
2025-06-04	21:00	8.776065153	855.2111652	3.629998779	NO_FROST	NEGLIGIBLE	-16.58331909	1027	0	57	0	0	2	11.85	0	36.36669312	177.614056	S	8.647497091
2025-06-04	22:00	8.687928745	857.7929355	3.790002441	NO_FROST	NEGLIGIBLE	-15.84998169	1027.199951	0	59	0	0	11	11.54000244	0	36.00002441	190.7843057	S	7.695915605
2025-06-04	23:00	8.636904986	861.6254444	4.490014648	NO_FROST	NEGLIGIBLE	-13.61664429	1026.900024	0	64	0	0	20	11.02001343	0	36.10003052	194.0362435	SSW	5.937272189


**Output:**
{{"precis": "Partly cloudy.",
  "long_form_text": "Partly cloudy. Medium chance of showers in the northwest suburbs, slight chance elsewhere. Areas of morning frost in the northeast suburbs. Winds southerly 20 to 30 km/h becoming light in the evening."
}}

**Input:**
date	time	apparent_temp	chill_stress_idx	dew_pt	frost_prob_cat	heat_stress_rating	k_idx	pres_msl	rain	rel_hum	snow	storm_prob_idx	tcc	temp	temp_inv_prob_idx	total_totals_idx	wind_dir	wind_dir_compass	wind_kmh
2025-06-06	00:00	4.795512192	938.0923362	2.990014648	NO_FROST	NEGLIGIBLE	-27.05000916	1021.599976	0	64	0	0	100	9.580010986	0	25.2000061	4.864512742	N	16.9811722
2025-06-06	01:00	4.303676223	947.4090867	2.869989014	NO_FROST	NEGLIGIBLE	-28.45000305	1021.099976	0	64	0	0	98	9.35	0	23.7000061	6.842773682	N	18.12913678
2025-06-06	02:00	4.125314153	951.3291402	2.869989014	NO_FROST	NEGLIGIBLE	-25.2500061	1021	0	65	0	0	95	9.240014648	0	23.2333313	8.914943591	N	18.58451018
2025-06-06	03:00	4.074088772	950.8317011	2.899987793	NO_FROST	NEGLIGIBLE	-22.05000916	1020.599976	0	66	0	0	100	9.050012207	0	22.76665649	15.15406264	NNE	17.90254172
2025-06-06	04:00	3.722551339	959.1199506	2.929986572	NO_FROST	NEGLIGIBLE	-18.85001221	1019.700012	0	66	0	0	100	9.010003662	0	22.29998169	19.44005017	NNE	19.46997836
2025-06-06	05:00	3.066966865	973.9438411	2.85	NO_FROST	NEGLIGIBLE	-9.65	1018.900024	0	65	0	0	98	9.080010986	0	23.8666626	11.88865889	NNE	23.06678685
2025-06-06	06:00	2.757619541	980.3606161	2.730004883	NO_FROST	NEGLIGIBLE	-0.449987793	1018.599976	0	64	0	0	100	9.179986572	0	25.43331299	5.440332082	N	25.06088822
2025-06-06	07:00	2.717727497	981.9636988	2.760003662	NO_FROST	NEGLIGIBLE	8.750024414	1018.799988	0	64	0	0	100	9.300012207	0	26.9999939	7.883139111	N	25.98556706
2025-06-06	08:00	2.552697118	985.2587641	2.800012207	NO_FROST	NEGLIGIBLE	0.050012207	1019.099976	0	64	0	0	100	9.320001221	0	25.39998779	2.526116941	N	26.9541939
2025-06-06	09:00	1.867552038	998.4067808	3.020013428	NO_FROST	NEGLIGIBLE	-8.65	1018.299988	0	65	0	0	100	9.320001221	0	23.79998169	11.16488031	N	30.67658379
2025-06-06	10:00	2.988477853	978.640693	3.049981689	NO_FROST	NEGLIGIBLE	-17.35001221	1018.5	0	63	0	0	100	9.740014648	0	22.19997559	5.042451128	N	27.03262106
2025-06-06	11:00	3.707887048	967.3021407	2.969995117	NO_FROST	NEGLIGIBLE	-10.45001831	1017.700012	0	59	0	0	97	10.76000366	0	24.29998169	4.763647657	N	28.61082821
2025-06-06	12:00	4.199643461	957.5858792	2.679986572	NO_FROST	NEGLIGIBLE	-3.549993896	1015.900024	0	53	0	0	92	11.92998657	0	26.39998779	2.862405269	N	31.71957528
2025-06-06	13:00	4.962304304	944.3747817	2.510003662	NO_FROST	NEGLIGIBLE	3.35	1014.5	0	50	0	0	91	12.77001343	0	28.4999939	0.707319263	N	32.07844964
2025-06-06	14:00	5.562725002	934.0991298	2.679986572	NO_FROST	NEGLIGIBLE	10.68334351	1013.599976	0.100000001	48	0	0	77	13.37999878	0	34.43334351	357.1728813	N	32.11509243
2025-06-06	15:00	5.804668433	931.252134	3.050012207	NO_FROST	NEGLIGIBLE	18.01665649	1013.099976	0	49	0	0	66	13.68999634	0	40.3666626	355.1792347	N	32.98468896
2025-06-06	16:00	5.587073551	937.4269867	3.879998779	NO_FROST	NEGLIGIBLE	25.35	1013.099976	0	53	0	0	33	13.27001343	0	46.30001221	354.4278033	N	32.62617737
2025-06-06	17:00	5.074004643	948.4216938	4.570001221	NO_FROST	NEGLIGIBLE	25.78334961	1013.099976	0	58	0	0	84	12.61998901	0	46.50002441	355.1207262	N	32.59010154
2025-06-06	18:00	4.620472957	959.5423273	5.369989014	NO_FROST	NEGLIGIBLE	26.2166687	1013.299988	0	65	0	0	100	11.87999878	0	46.7000061	358.585577	N	32.08578157
2025-06-06	19:00	4.587602651	966.5808311	6.240014648	NO_FROST	NEGLIGIBLE	26.65001831	1013.700012	0.100000001	71	0	0	100	11.36998901	0	46.90001831	360	N	30.49199924
2025-06-06	20:00	4.744794273	984.5852163	7.379998779	NO_FROST	NEGLIGIBLE	26.55001221	1013.700012	1.000000045	80	0	0	100	10.80001221	0	48.0666748	1.613538979	N	28.12715234
2025-06-06	21:00	4.610601525	1004.196239	7.679986572	NO_FROST	NEGLIGIBLE	26.4500061	1013.400024	1.099999905	83	0	0	100	10.39998779	0	49.2333313	1.684684296	N	26.9396453
2025-06-06	22:00	4.768931113	1000.169941	7.369989014	NO_FROST	NEGLIGIBLE	26.35	1012.900024	0	81	0	0	92	10.46999512	0	50.39998779	0.868058071	N	26.1389995
2025-06-06	23:00	4.986576993	997.6133135	7.399987793	NO_FROST	NEGLIGIBLE	25.6166626	1012.700012	0.100000143	82	0	0	100	10.36998901	0	50.03331909	356.308615	N	24.6030505

**Output:**
{{"precis": "Showers increasing.",
  "long_form_text": "Cloudy. High chance of showers, most likely in the afternoon and evening. Winds northerly 25 to 40 km/h."
}}

**Input:**
date	time	apparent_temp	chill_stress_idx	dew_pt	frost_prob_cat	heat_stress_rating	k_idx	pres_msl	rain	rel_hum	snow	storm_prob_idx	tcc	temp	temp_inv_prob_idx	total_totals_idx	wind_dir	wind_dir_compass	wind_kmh
2025-06-08	00:00	6.313218366	941.8668822	5.770013428	NO_FROST	NEGLIGIBLE	25.2499939	1005	0	75	0	0	100	10.04000244	0	57.26665649	290.7255583	WNW	14.24162925
2025-06-08	01:00	5.733201899	943.7900967	5.85	NO_FROST	NEGLIGIBLE	26.65001831	1004.900024	0	78	0	0	69	9.520013428	0	57.80001221	279.9262453	W	14.61883716
2025-06-08	02:00	5.353462119	943.6374395	5.35	NO_FROST	NEGLIGIBLE	25.51668701	1004.900024	0	77	0	0	38	9.18996582	0	57.6333252	281.5921753	WNW	14.3323414
2025-06-08	03:00	4.80334491	950.3234679	4.85	NO_FROST	NEGLIGIBLE	24.38335571	1004.700012	0	77	0	0	34	8.730004883	0	57.4666687	281.5921753	WNW	14.3323414
2025-06-08	04:00	4.385521779	952.2603439	4.709985352	NO_FROST	NEGLIGIBLE	23.25002441	1004.700012	0	78	0	0	70	8.270013428	0	57.29998169	278.9726523	W	13.84947212
2025-06-08	05:00	4.06935238	956.9727202	4.770013428	NO_FROST	NEGLIGIBLE	23.75002441	1004.799988	0	81	0	0	80	7.899987793	0	57.33330688	276.009031	W	13.75557597
2025-06-08	06:00	3.880704557	958.3072203	4.790002441	NO_FROST	NEGLIGIBLE	24.25002441	1005.200012	0	83	0	0	81	7.619989014	0	57.3666626	274.6354656	W	13.36370625
2025-06-08	07:00	3.730197337	959.9994924	4.800012207	NO_FROST	NEGLIGIBLE	24.75002441	1005.799988	0	83	0	0	95	7.490014648	0	57.39998779	273.0940581	W	13.33944544
2025-06-08	08:00	3.697197474	960.3268606	4.760003662	NO_FROST	NEGLIGIBLE	24.88335571	1006.099976	0	83	0	0	100	7.459985352	0	56.8666626	271.5481577	W	13.32486415
2025-06-08	09:00	3.959566838	955.0393952	4.689996338	NO_FROST	NEGLIGIBLE	25.01665649	1006.400024	0	82	0	0	97	7.649987793	0	56.33330688	271.5911403	W	12.96499869
2025-06-08	10:00	4.520373006	945.3090955	4.619989014	NO_FROST	NEGLIGIBLE	25.14998779	1006.5	0	79	0	0	94	8.149987793	0	55.79998169	271.636602	W	12.60514197
2025-06-08	11:00	5.332669366	933.4024925	4.240014648	NO_FROST	NEGLIGIBLE	24.1166626	1006.299988	0	72	0	0	84	9.080010986	0	55.2000061	260.2724457	W	12.78380132
2025-06-08	12:00	5.664521949	939.3117957	3.490014648	NO_FROST	NEGLIGIBLE	23.08336792	1005.5	0.099999905	63	0	1	92	10.24001465	0	54.6	251.9657155	WSW	16.27980406
2025-06-08	13:00	5.790329621	943.1562941	3.35	NO_FROST	NEGLIGIBLE	22.05004272	1004.900024	0.199999809	61	0	1	91	10.62999878	0	54.00002441	254.5387822	WSW	17.55530618
2025-06-08	14:00	6.235658858	933.9233068	2.790002441	NO_FROST	NEGLIGIBLE	21.51668701	1004.799988	0	57	0	0	83	11.07000122	0	53.86669312	256.5513844	WSW	17.02689606
2025-06-08	15:00	6.120474146	936.1036754	2.179986572	NO_FROST	NEGLIGIBLE	20.98336182	1005	0	54	0	0	86	11.26000366	0	53.7333313	257.3474435	WSW	18.07902688
2025-06-08	16:00	6.145232023	931.9291354	1.909997559	NO_FROST	NEGLIGIBLE	20.4500061	1005.299988	0	53	0	0	75	11.08001099	0	53.6	263.796552	W	16.65753849
2025-06-08	17:00	6.227431973	923.6897263	2.300012207	NO_FROST	NEGLIGIBLE	21.05001221	1005.799988	0	57	0	0	20	10.57000122	0	53.66668091	274.3987276	W	14.08147796
2025-06-08	18:00	5.832714069	923.5130942	2.800012207	NO_FROST	NEGLIGIBLE	21.65001831	1006.400024	0	62	0	0	38	9.869989014	0	53.7333313	289.4400565	WNW	12.97998669
2025-06-08	19:00	5.060511649	928.4351521	2.709985352	NO_FROST	NEGLIGIBLE	22.25002441	1006.900024	0	64	0	0	81	9.179986572	0	53.80001221	299.3577525	WNW	13.21744309
2025-06-08	20:00	4.610217551	934.3775556	2.570001221	NO_FROST	NEGLIGIBLE	22.51665649	1007.099976	0	66	0	0	80	8.709985352	0	54.1333252	307.1847061	NW	13.10419818
2025-06-08	21:00	4.457282561	929.926975	2.659997559	NO_FROST	NEGLIGIBLE	22.78331909	1007.099976	0	68	0	0	61	8.330010986	0	54.4666687	318.6522222	NW	11.98859469
2025-06-08	22:00	4.173694762	931.9279691	2.740014648	NO_FROST	NEGLIGIBLE	23.04995117	1007.200012	0	70	0	0	66	7.959985352	0	54.79998169	334.2306735	NNW	11.59289465
2025-06-08	23:00	3.773921932	939.2870456	2.770013428	NO_FROST	NEGLIGIBLE	23.08327637	1007.200012	0	71	0	0	88	7.649987793	0	55.14998779	344.2913695	NNW	11.9669596

**Output:**
{{"precis": "Showers easing.",
  "long_form_text": "Cloudy. High chance of showers, most likely during the morning. Winds northwesterly 20 to 30 km/h decreasing to 15 to 20 km/h during the day."
}}
"""
```