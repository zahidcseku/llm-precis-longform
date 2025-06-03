import os
from unstructured.partition.auto import partition
from sentence_transformers import SentenceTransformer
import chromadb
from langchain_core.documents import Document
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_google_genai import ChatGoogleGenerativeAI  # Or other LLM client
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.embeddings import HuggingFaceEmbeddings  # Or other embeddings

# --- Configuration ---
PDF_PATH = "adfdUserGuide.pdf"
MARKUP_PATH = "bom_terms.md"

# CHROMA_DB_PATH = "./chroma_db"
# EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"  # Good default, balance of speed/accuracy
# LLM_MODEL_NAME = "gemini-1.5-flash-latest"  # Or "gpt-4o", "llama2"


# --- 1. Ingestion & Parsing ---
def load_documents(pdf_path, markup_path):
    print(f"Loading PDF from: {pdf_path}")
    # Using unstructured for robust PDF parsing
    pdf_elements = partition(
        filename=pdf_path, strategy="hi_res", infer_table_structure=True
    )
    pdf_docs = []
    for el in pdf_elements:
        # Each element can be a paragraph, title, table, etc.
        # unstructured often adds metadata like 'page_number'
        metadata = el.metadata.to_dict()
        pdf_docs.append(
            Document(page_content=str(el), metadata={"source": pdf_path, **metadata})
        )

    print(f"Loading Markup from: {markup_path}")
    # Using unstructured for robust markup parsing (handles HTML, MD, etc.)
    markup_elements = partition(filename=markup_path)
    markup_docs = []
    for el in markup_elements:
        metadata = el.metadata.to_dict()
        markup_docs.append(
            Document(page_content=str(el), metadata={"source": markup_path, **metadata})
        )

    return pdf_docs + markup_docs


# --- 2. Chunking & 3. Embedding (Handled by LangChain/Chroma with embedding model) ---
def create_vector_store(documents, db_path, embedding_model_name):
    # Initialize embedding model
    embeddings = HuggingFaceEmbeddings(model_name=embedding_model_name)

    # Initialize ChromaDB client
    client = chromadb.PersistentClient(path=db_path)
    collection_name = "my_rag_collection"

    # Get or create the collection
    try:
        collection = client.get_collection(name=collection_name)
    except:  # This is a simple way to catch if it doesn't exist; more robust error handling might be needed
        collection = client.create_collection(
            name=collection_name, embedding_function=embeddings
        )

    # LangChain's Chroma vectorstore integration handles chunking and adding to collection
    # Note: For LangChain, you'll want to use their specific Chroma class for seamless integration
    # For simplicity, here we'll add directly to the Chroma collection via the embedding function
    print("Adding documents to vector store...")
    ids = [f"doc_{i}" for i in range(len(documents))]  # Simple IDs
    contents = [doc.page_content for doc in documents]
    metadatas = [doc.metadata for doc in documents]

    collection.add(documents=contents, metadatas=metadatas, ids=ids)
    print(f"Added {len(documents)} chunks to the vector store.")
    return collection, embeddings  # Return the collection and embeddings for retrieval


# --- 4. Retrieval & 5. Generation ---
def setup_rag_chain(vector_store_collection, embeddings_model, llm_model_name):
    # Initialize LLM
    llm = ChatGoogleGenerativeLLM(
        model=llm_model_name, temperature=0.2
    )  # Adjust temperature as needed

    # Retriever from ChromaDB collection
    # LangChain's Chroma client wrapper for retrieval:
    from langchain_community.vectorstores import Chroma

    vectorstore_lc = Chroma(
        client=vector_store_collection._client,  # Pass the underlying client
        collection_name=vector_store_collection.name,
        embedding_function=embeddings_model,  # Pass the embedding function used for the collection
    )
    retriever = vectorstore_lc.as_retriever(
        search_kwargs={"k": 4}
    )  # Retrieve top 4 relevant chunks

    # Define the prompt template for the LLM
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are a helpful AI assistant. Answer the user's question based *only* on the provided context. If the answer is not in the context, state that you cannot find the answer in the provided information. Cite the source document and page number (if available) for each piece of information.",
            ),
            ("human", "Context: {context}\n\nQuestion: {input}"),
        ]
    )

    # Create a chain to stuff documents into the prompt
    document_chain = create_stuff_documents_chain(llm, prompt)

    # Create the retrieval chain
    retrieval_chain = create_retrieval_chain(retriever, document_chain)
    return retrieval_chain


# --- Main Execution ---
if __name__ == "__main__":
    # 1. Load and parse documents
    all_documents = load_documents(PDF_PATH, MARKUP_PATH)
    print(all_documents)
    exit()

    # 2. Create vector store (chunks documents, embeds them, and stores)
    chroma_collection, embeddings_model = create_vector_store(
        all_documents, CHROMA_DB_PATH, EMBEDDING_MODEL_NAME
    )

    # 3. Setup RAG chain
    rag_chain = setup_rag_chain(chroma_collection, embeddings_model, LLM_MODEL_NAME)

    # 4. Query the RAG system
    while True:
        query = input("\nEnter your query (type 'exit' to quit): ")
        if query.lower() == "exit":
            break

        print("\nSearching and generating response...")
        response = rag_chain.invoke({"input": query})

        print("\n--- Response ---")
        print(response["answer"])

        # Optional: Print sources
        print("\n--- Sources ---")
        for doc in response["context"]:
            source = doc.metadata.get("source", "Unknown Source")
            page_number = doc.metadata.get("page_number", "N/A")
            print(f"- {source} (Page: {page_number})")
        print("-" * 20)
