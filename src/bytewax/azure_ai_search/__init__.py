"""Azure Search Sink Implementation.

This module provides a dynamic sink for writing data to an Azure Search
index using Bytewax's streaming data processing framework. The sink is
capable of creating and managing a connection to Azure Search and
inserting documents in batches based on a user-defined schema.

Classes:
    AzureSearchSink: A dynamic sink that connects to an Azure Search service,
                     manages the index, and writes data in batches.
    _AzureSearchPartition: A stateless partition responsible for writing batches of
                           data to the Azure Search index.

Usage:
    - The `AzureSearchSink` class is used to define a sink that can be
      connected to a Bytewax dataflow.
    - The `build` method of `AzureSearchSink` creates an `_AzureSearchPartition`
      that handles the actual data writing process.
    - The sink supports inserting documents based on a user-defined schema,
      ensuring that the data is formatted correctly for the target index.

Logging:
    The module uses Python's logging library to log important events such
    as index operations, API requests, and error messages.

**Sample usage**:

```python
from bytewax.bytewax_azure_ai_search import AzureSearchSink

schema = {
    "id": {"type": "string", "default": None},
    "content": {"type": "string", "default": None},
    "meta": {"type": "string", "default": None},
    "vector": {"type": "collection", "default": []},
}

# Initialize the AzureSearchSink with your schema
azure_sink = AzureSearchSink(
    azure_search_service="your-service-name",
    index_name="your-index-name",
    search_api_version="2024-07-01",
    search_admin_key="your-api-key",
    schema=schema,  # Pass the custom schema
)
```
**Note** The above assumes you have created a schema through Azure AI
Search configuration. For more information, review
[the README](https://github.com/bytewax/bytewax-azure-ai-search/blob/main/README.md).

Complete examples can be found
[here](https://github.com/bytewax/bytewax-azure-ai-search/tree/main/examples)
"""

import json
import logging
import os
import sys
from typing import Any, Dict, List, Optional, TypeVar, Union

import requests
from typing_extensions import override

from bytewax.outputs import DynamicSink, StatelessSinkPartition

if "BYTEWAX_LICENSE" not in os.environ:
    msg = (
        "`bytewax-azure-ai-search` is commercially licensed "
        "with publicly available source code.\n"
        "You are welcome to prototype using this module for free, "
        "but any use on business data requires a paid license.\n"
        "See https://modules.bytewax.io/ for a license. "
        "Set the env var `BYTEWAX_LICENSE=1` to suppress this message."
    )
    print(msg, file=sys.stderr)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Type variables for flexibility in typing
V = TypeVar("V")

# Type aliases for common types
Document = Dict[str, Any]
Schema = Dict[str, Dict[str, Union[str, Optional[Any]]]]
Batch = List[Document]


class _AzureSearchPartition(StatelessSinkPartition):
    """Stateless partition writing batches of data to an Azure Search index.

    This class manages the connection to the Azure Search service and handles the
    formatting and insertion of data into the specified index.
    """

    def __init__(
        self,
        azure_search_service: str,
        index_name: str,
        search_api_version: str,
        search_admin_key: str,
        schema: Schema,
    ) -> None:
        """Initialize the _AzureSearchPartition."""
        self.azure_search_service = azure_search_service
        self.index_name = index_name
        self.search_api_version = search_api_version
        self.search_admin_key = search_admin_key
        self.schema = schema

    @override
    def write_batch(self, batch: Batch) -> None:
        """Write a batch of data to the Azure Search index."""
        search_endpoint = (
            f"https://{self.azure_search_service}.search.windows.net/"
            f"indexes/{self.index_name}/docs/index?api-version={self.search_api_version}"
        )
        headers = {
            "Content-Type": "application/json",
            "api-key": self.search_admin_key,
        }

        body: Dict[str, List[Document]] = {"value": []}

        for document in batch:
            if not self.validate_document(document, self.schema):
                logger.error(f"Invalid document: {document}")
                continue
            doc_body = {"@search.action": "upload"}
            for field_name, field_details in self.schema.items():
                # Add fields to the document body based on the schema provided
                if field_name == "vector":
                    doc_body[field_name] = document.get(field_name, "")
                else:
                    doc_body[field_name] = document.get(
                        field_name, field_details.get("default")
                    )

            body["value"].append(doc_body)

        body_json = json.dumps(body)

        logger.debug(f"Uploading document to Azure Search: {body_json}")

        try:
            response = requests.post(search_endpoint, headers=headers, data=body_json)
            response.raise_for_status()
            logger.info(f"Document uploaded successfully to index '{self.index_name}'.")
        except requests.exceptions.RequestException as req_err:
            logger.error(f"Request error occurred: {req_err}")
            logger.error(f"Response content: {response.text}")

    def validate_document(self, document: Document, schema: Schema) -> bool:
        """Validate the document against the schema."""
        for field_name, field_details in schema.items():
            if field_name in document:
                value = document[field_name]
                if field_details["type"] == "collection" and not isinstance(
                    value, list
                ):
                    logger.error(f"'{field_name}' should be a list, got {type(value)}.")
                    return False
                if field_details["type"] == "string" and not isinstance(value, str):
                    logger.error(
                        f"'{field_name}' should be a string, got {type(value)}."
                    )
                    return False
        return True


class AzureSearchSink(DynamicSink):
    """A dynamic sink for writing data to an Azure Search index in a dataflow."""

    def __init__(
        self,
        azure_search_service: str,
        index_name: str,
        search_api_version: str,
        search_admin_key: str,
        schema: Schema,
    ) -> None:
        """Initialize the AzureSearchSink."""
        self.azure_search_service = azure_search_service
        self.index_name = index_name
        self.search_api_version = search_api_version
        self.search_admin_key = search_admin_key
        self.schema = schema

    @override
    def build(
        self, step_id: str, worker_index: int, worker_count: int
    ) -> _AzureSearchPartition:
        """Build a sink partition for writing to Azure Search."""
        return _AzureSearchPartition(
            azure_search_service=self.azure_search_service,
            index_name=self.index_name,
            search_api_version=self.search_api_version,
            search_admin_key=self.search_admin_key,
            schema=self.schema,
        )
