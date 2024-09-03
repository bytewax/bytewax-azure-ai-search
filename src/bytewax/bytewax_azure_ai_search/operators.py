"""Operators for embedding generation using Azure OpenAI.

It's suggested to import operators like this:

```
from bytewax.connectors.azure_openai import operators as aoop
```

And then you can use the operators like this:

```
from bytewax.dataflow import Dataflow

flow = Dataflow("embedding-out") input = aoop.input("input", flow, ...)
embedded = aoop.generate_embeddings("embedding_op", input)
aoop.output("output", embedded, ...)
```
"""

import logging
import os
from typing import Any, Dict

# Load environment variables
from dotenv import load_dotenv
from openai import AzureOpenAI

import bytewax.operators as op
from bytewax.bytewax_azure_ai_search import AzureSearchSink
from bytewax.dataflow import Stream, operator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv(override=True)

# Azure OpenAI configuration
AZURE_OPENAI_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_SERVICE = os.getenv("AZURE_OPENAI_SERVICE")
AZURE_EMBEDDING_DEPLOYMENT_NAME = os.getenv("AZURE_EMBEDDING_DEPLOYMENT_NAME")
DIMENSIONS = 1536

# Initialize Azure OpenAI client
client = AzureOpenAI(
    api_key=AZURE_OPENAI_KEY,
    api_version="2023-10-01-preview",
    azure_endpoint=f"https://{AZURE_OPENAI_SERVICE}.openai.azure.com/",
)


@operator
def generate_embeddings(
    step_id: str, up: Stream[Dict[str, Any]]
) -> Stream[Dict[str, Any]]:
    """Operator to generate embeddings for each item in the stream using Azure OpenAI.

    Args:
        step_id (str): Unique ID for the operator.
        up (Stream[Dict[str, Any]]): Input stream of data items.

    Returns:
        Stream[Dict[str, Any]]: Output stream with embeddings added to each item.
    """

    def generate_embedding(item: Dict[str, Any]) -> Dict[str, Any]:
        try:
            # Generate embedding
            model_name = AZURE_EMBEDDING_DEPLOYMENT_NAME or "text-embedding-ada-002"
            embedding_response = client.embeddings.create(
                input=item["text"], model=model_name
            )
            embedding = (
                embedding_response.data[0].embedding
                if embedding_response.data and embedding_response.data[0].embedding
                else [0.0] * DIMENSIONS
            )

            # Check embedding dimension
            if len(embedding) != DIMENSIONS:
                error_message = "Invalid embedding size: expected {}, got {}".format(
                    DIMENSIONS, len(embedding)
                )
                raise ValueError(error_message)
            # Add embedding to the item
            item["vector"] = embedding
            return item
        except Exception as e:
            logger.error(f"Failed to generate embeddings for item {item['id']}: {e}")
            return item

    # Use the map operator to apply the embedding function to each item in the stream
    return op.map(step_id, up, generate_embedding)


@operator
def output(step_id: str, up: Stream[Dict[str, Any]], sink: AzureSearchSink) -> None:
    """Output operator for writing the stream of items to the provided sink.

    Args:
        step_id (str): Unique ID for the operator.
        up (Stream[Dict[str, Any]]): Input stream of data items with embeddings.
        sink: Sink to output data to.
    """
    return op.output(step_id, up, sink)
