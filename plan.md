# 🔧 PHASE 1: Requirements and Inputs
## 🧾 Input Format
Hourly weather data for 24 hours, e.g.:

```
[
  {"hour": 0, "temp": 12.3, "wind": 3.4, "precip": 0.0, "humidity": 87, "condition": "cloudy"},
  {"hour": 1, "temp": 12.0, "wind": 2.9, "precip": 0.1, "humidity": 90, "condition": "rain"},
  ...
]
```

## 🎯 Output Format
5_word_summary: e.g., "Cool, rainy, windy, gloomy day"

20_word_summary: e.g., "A cool and overcast day with periods of light rain, mild wind, and consistent humidity throughout the day."

# 🏗️ PHASE 2: System Architecture
## Backend
- **Data preprocessor**: normalize and summarize hourly data.
- **Prompt generator**: dynamically construct prompts based on preprocessed input.
- **LLM wrapper**: query the language model with the prompt.
- **Postprocessor**: truncate/refine output to match word count.
- **Evaluator** (optional but valuable): automatic scoring, human-in-the-loop feedback.


# 🧠 PHASE 3: Initial Implementation
Step 1: Preprocessing the Weather Data
Summarize hourly data into high-level features:
- Average temperature, wind speed, humidity.
- Min/max values.
- Rain/snow totals.
- Dominant condition (e.g., mostly cloudy).
- Detect trends (e.g., cooling evening, peak wind at noon).
```
summary_features = {
    "avg_temp": 14.5,
    "max_temp": 18.3,
    "min_temp": 10.1,
    "total_rain_mm": 2.3,
    "peak_wind_kph": 15.0,
    "most_common_condition": "cloudy",
    ...
}
```

Step 2: Prompt Engineering
🔹 Basic Prompt Template (First Iteration)
Given the following summary of a day's weather:
- Avg temp: 14.5°C
- Min/Max temp: 10.1°C / 18.3°C
- Total rain: 2.3 mm
- Peak wind: 15 kph
- Most common condition: cloudy

Write:
1. A concise 5-word summary of the day.
2. A 20-word narrative summary of the weather, focusing on trends and highlights.

# 🔁 PHASE 4: Iterative Improvement
## 🧪 A/B Testing Prompts
Compare multiple prompt styles:
- Descriptive (as above)
- Tabular (| Key | Value |)
- Natural language narrative JSON format

Test for fluency, accuracy, and adherence to word count.

## 🧠 Prompt Refinement Techniques
1. Output constraints
Add system messages or instructions like:

Please ensure the first summary has exactly 5 words. The second should have exactly 20 words.

2. Few-shot examples
Use high-quality examples in the prompt to guide behavior:

Example:
Weather Summary:
- Avg temp: 7.2°C
- Rain: 12 mm
- Wind: 30 kph
- Sky: overcast

Output:
5-word: Cold, wet, windy, gray day  
20-word: A wet, cold, windy day with overcast skies and strong breezes. Rain fell intermittently throughout the cloudy afternoon.
Then follow with the user’s data.

3. Chain-of-thought (CoT) prompting
Ask the model to reason internally:

Think step by step about the weather trends before writing the summary.

This can improve coherence of 20-word outputs.

# 🛠️ PHASE 5: Model Selection and Access
Start with GPT-4-turbo or Claude via API.

If latency or cost is an issue:
- Fine-tune Mistral or LLaMA models using LoRA (after collecting ~1k+ prompt-response pairs).

Use OpenAI function calling or tool use to separate weather summarization logic.

# ✅ PHASE 6: Evaluation and Feedback Loop
## 📐 Automatic Metrics
- Word count check
- Relevance score using keyword match
- Coherence via sentence embedding similarity (e.g., using Sentence-BERT)

## 👨‍🔬 Human-in-the-Loop
- Rank output quality
- Mark issues: "Too vague", "Not matching data", "Wrong word count"

Use feedback to:
- Improve prompts
- Add new few-shot examples
- Tune model (if using open-source LLM)

# 🌐 Bonus: Contextual Awareness
In later versions:
- Add location and season as context: “Boston, early December”
- Add user tone preference: “Professional”, “Casual”, “Witty”

---
3. Prompt Engineering
Design a structured prompt with:

Role Definition:
You are a weather expert generating concise 5-word and 20-word summaries from daily data. Prioritize extremes, trends, and key events.

Instructions:

"5 words: Highlight the most critical event or trend. Use abbreviations if needed (e.g., 'PM' for afternoon)."

"20 words: Include temperatures, precipitation, wind, and timing of key events."

Examples:

Example Input: Max 35°C, min 20°C, 0mm rain, wind 15km/h, sunny.  
5-word: "Hot day, breezy evening."  
20-word: "Very hot (35°C) with sunny skies, cooling to 20°C at night. Light winds throughout the day."
Data Injection: Feed preprocessed stats (not raw data) to minimize token usage and focus the LLM.

4. LLM Configuration
Model Selection: Test GPT-4 (accuracy) vs. Claude (conciseness) for optimal results.

Parameters: Use temperature=0.2 for consistency, max_tokens=50 to restrict output length.

5. Post-Processing & Validation
Word Limit Enforcement: Programmatically check summary lengths (e.g., split by spaces).

Keyword Checks: Ensure critical terms (e.g., "rain," "windy") from preprocessing are included.

Fallback: If summaries miss key details, reprocess with a refined prompt (e.g., "Include temperature swing from [X°C to Y°C]").