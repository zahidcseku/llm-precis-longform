# RAG

## Prepare search data (once per document)
- Collect: We'll download bom process
- Chunk: Documents are split into short, mostly self-contained sections to be embedded
- Embed: Each section is embedded with the OpenAI API
- Store: Embeddings are saved (for large datasets, use a vector database)

## Search (once per query)
- Given a day's forecast, generate an embedding for the query from the OpenAI API
- Using the embeddings, rank the text sections by relevance to the query

## Ask (once per query)
- Insert the question and the most relevant sections into a message to GPT
- Return GPT's answer

## Knowledgebase creation
[] load docs
[] chunking
[] embed chunks
[] load in VDB

## Retriever
