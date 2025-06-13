from langchain.document_loaders import PyPDFLoader, UnstructuredMarkdownLoader
from langchain.text_splitter import MarkdownTextSplitter, RecursiveCharacterTextSplitter
from langchain_experimental.text_splitter import SemanticChunker
from langchain_huggingface import HuggingFaceEmbeddings  # Updated import
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document

# from langchain_community.document_loaders import PyPDFLoader
# from langchain_community.document_loaders import UnstructuredMarkdownLoader

# --- Configuration ---
PDF_PATH = "adfdUserGuide.pdf"
MARKUP_PATH = "bom_terms.md"

CHROMA_DB_PATH = "./chroma_db"
# EMBEDDING_MODEL_NAME = "dwzhu/e5-base-4k"
EMBEDDING_MODEL_NAME = (
    "BAAI/bge-small-en-v1.5"  # Good default, balance of speed/accuracy
)
# LLM_MODEL_NAME = "gemini-1.5-flash-latest"  # Or "gpt-4o", "llama2"


# --- 1. Ingestion & Parsing ---
def load_documents(pdf_path, markup_path):
    print(f"Loading PDF from: {pdf_path}")
    # Load PDF
    pdf_loader = PyPDFLoader(f"bom_kb/{pdf_path}")
    pdf_pages = pdf_loader.load_and_split()  # Automatically splits by page

    # Load Markdown
    md_loader = UnstructuredMarkdownLoader(f"bom_kb/{markup_path}")
    md_docs = md_loader.load()  # Loads entire MD file

    # return {"pdf": pdf_pages, "md": md_docs}
    return pdf_pages + md_docs


# --- 2. Chunking & 3. Embedding (Handled by LangChain/Chroma with embedding model) ---
def create_vector_store(documents, db_path, embedding_model_name):
    # chunking
    print("Chunking documents...")
    # Initialize embedding model
    embeddings_model = HuggingFaceEmbeddings(model_name=embedding_model_name)

    semantic_splitter = SemanticChunker(
        embeddings_model,
        breakpoint_threshold_type="percentile",  # "standard_deviation" also works
        breakpoint_threshold_amount=0.4,  # Lower = more chunks
        add_start_index=True,  # Preserve positional info
    )

    # Step 3: Split documents with semantic awareness
    chunks = []
    for doc in documents:
        # Preserve existing metadata
        metadata = doc.metadata.copy()

        # Add document-specific enhancements
        if "source" not in metadata:
            metadata["source"] = "unknown"

        # Special handling for Markdown
        if doc.metadata.get("source", "").endswith(".md"):
            metadata["doc_type"] = "markdown"
            # Extract first header if exists
            if "# " in doc.page_content[:100]:
                metadata["section"] = doc.page_content.split("# ")[1].split("\n")[0]

        # Process with semantic splitter
        doc_chunks = semantic_splitter.split_text(doc.page_content)

        for i, chunk in enumerate(doc_chunks):
            chunk_metadata = metadata.copy()
            chunk_metadata["chunk_index"] = i
            # chunks.append({"page_content": chunk, "metadata": chunk_metadata})
            chunks.append(Document(page_content=chunk, metadata=chunk_metadata))

    # Step 4: Create vector store
    vector_store = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings_model,
        persist_directory=db_path,
        collection_metadata={"hnsw:space": "cosine"},  # Optimize for similarity
    )
    vector_store.persist()


"""
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
"""

# --- Main Execution ---
if __name__ == "__main__":
    # 1. Load and parse documents
    all_documents = load_documents(PDF_PATH, MARKUP_PATH)
    # print(all_documents)

    # 2. Create vector store (chunks documents, embeds them, and stores)
    create_vector_store(all_documents, CHROMA_DB_PATH, EMBEDDING_MODEL_NAME)
    # print(chroma_collection)
    exit()
    """
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
    """
