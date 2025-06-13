from openai import OpenAI
from dotenv import load_dotenv
import os
import time
import json
from google import genai
from pydantic import BaseModel
from groq import Groq
from langchain.retrievers import BM25Retriever, EnsembleRetriever
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document


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

CHROMA_DB_PATH = "./chroma_db"
# EMBEDDING_MODEL_NAME = "dwzhu/e5-base-4k"
EMBEDDING_MODEL_NAME = (
    "BAAI/bge-small-en-v1.5"  # Good default, balance of speed/accuracy
)


def apply_llm(hourly_forecast_data, var_definitions):
    """
    Apply the LLM to generate summaries from hourly forecast data.

    :param hourly_forecast_data: Dictionary containing hourly forecast data.
    :param var_definitions: definitions of the selected variables.
    """
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    gclient = genai.Client(api_key=os.getenv("GOOGLE_GENAI_API_KEY"))

    ## Setting up the retriever
    print("Setting up RAG pipeline...")
    embeddings_model = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)

    # vector store initialization
    # Load Chroma Vector Store
    print(f"Loading Chroma DB from: {CHROMA_DB_PATH}")
    vector_store = Chroma(
        persist_directory=CHROMA_DB_PATH, embedding_function=embeddings_model
    )
    print("Chroma DB loaded.")

    # Create semantic retriever
    semantic_retriever = vector_store.as_retriever(
        search_type="similarity_score_threshold",
        search_kwargs={"k": 5, "score_threshold": 0.25},
    )
    # 4. BM25 Retriever
    # Fetch all documents from Chroma to build the BM25 index.
    # This could be slow if the DB is very large.
    print("Fetching documents for BM25 retriever...")
    retrieved_docs_for_bm25_dict = vector_store.get(include=["documents", "metadatas"])
    documents_for_bm25 = []
    if retrieved_docs_for_bm25_dict and retrieved_docs_for_bm25_dict.get("documents"):
        for doc_content, meta in zip(
            retrieved_docs_for_bm25_dict["documents"],
            retrieved_docs_for_bm25_dict["metadatas"],
        ):
            documents_for_bm25.append(Document(page_content=doc_content, metadata=meta))
        print(f"Retrieved {len(documents_for_bm25)} documents for BM25.")

    if documents_for_bm25:
        bm25_retriever = BM25Retriever.from_documents(
            documents=documents_for_bm25,
            k=3,  # k=3 for BM25 part of ensemble
        )
        # Ensemble Retriever
        ensemble_retriever = EnsembleRetriever(
            retrievers=[semantic_retriever, bm25_retriever], weights=[0.7, 0.3]
        )
        print("Ensemble retriever created.")
    else:
        print(
            "Warning: BM25Retriever could not be initialized (no documents found). Falling back to semantic retriever."
        )
        ensemble_retriever = semantic_retriever  # Fallback

    # Combine both retrievers
    # ensemble_retriever = EnsembleRetriever(
    #    retrievers=[semantic_retriever, text_retriever], weights=[0.7, 0.3]
    # )
    # Formulate Query for RAG
    rag_query = (
        "Guidelines for writing weather precis and detailed "
        "summaries, including cloud, precipitation, and wind descriptions "
        "and definitions of common weather terms."
    )
    print(f"RAG Query: {rag_query}")

    # Retrieve and Format Context
    retrieved_rag_docs = ensemble_retriever.invoke(rag_query)
    formatted_rag_context = "\n\n---\n\n".join(
        [doc.page_content for doc in retrieved_rag_docs]
    )
    # print(
    #    f"Retrieved RAG context: {formatted_rag_context}..."
    # )  # Print start of context
    # exit()
    # create prompts
    # --- Define the static part of the prompt and combine with file data ---
    PROMPT = f"""You are a weather expert. Based on the following hourly 
    forecast data, please provide two summaries.
    Retrieved Context for Guidance:
    ---
    {formatted_rag_context}
    ---
    
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
