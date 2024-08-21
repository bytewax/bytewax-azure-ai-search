# Building embeddings in real time with Haystack by deepset and Bytewax

This example is based on code used in our blog ["Real time RAG with Bytewax and Haystac 2.0"](https://bytewax.io/blog/real-time-rag-with-bytewax-and-haystack-2-0)

In this example you can find three files:

* `connection.py` - execute it once to establish a connection to your Azure AI Search and Azure OpenAI services, and define a schema
* `indexing.py` - contains Haystack custom components to parse, extract content and generate embeddings from urls in a JSONL file in [here](./data/news_out.jsonl)
* `dataflow.py` - contains a complete Bytewax dataflow to parse the entries in the JSONL dataset, apply the custom component as a map operator step, and store the vectors in your Azure AI Search instante through the bytewax-azure-ai-search sink.

## Execution

To configure the connection and schema.


```bash
python connection.py
```

To generate embeddings and populate the Azure AI Search instance through the Bytewax sink.

```bash
python -m bytewax.run dataflow:flow
```
