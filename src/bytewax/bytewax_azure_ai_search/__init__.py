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

Sample usage

# Define a custom schema for the data
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
    schema=schema  # Pass the custom schema
)
"""

import json
import logging
from typing import Any, Dict, List

import requests
from typing_extensions import override

from bytewax.outputs import DynamicSink, StatelessSinkPartition

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class _AzureSearchPartition(StatelessSinkPartition):
    """Stateless partition writing batches of data to an Azure Search index.

    This class manages the connection to the Azure Search service and handles the
    formatting and insertion of data into the specified index.

    Attributes:
        azure_search_service (str): The name of the Azure Search service.
        index_name (str): The name of the target index.
        search_api_version (str): The API version to use for the Azure Search service.
        search_admin_key (str): The admin API key for authentication.
        schema (dict): The schema that defines the structure of the data being inserted.
    """

    def __init__(
        self,
        azure_search_service: str,
        index_name: str,
        search_api_version: str,
        search_admin_key: str,
        schema: Dict[str, Any],
    ):
        """Initialize the _AzureSearchPartition.

        Args:
            azure_search_service (str): The Azure Search service name.
            index_name (str): The name of the index to insert documents into.
            search_api_version (str): The API version for Azure Search.
            search_admin_key (str): The admin key for Azure Search.
            schema (dict): A dictionary defining the schema of the data.
        """
        self.azure_search_service = azure_search_service
        self.index_name = index_name
        self.search_api_version = search_api_version
        self.search_admin_key = search_admin_key
        self.schema = schema

    @override
    def write_batch(self, batch: List[Dict[str, Any]]) -> Dict[str, str]:
        """Write a batch of data to the Azure Search index.

        Constructs and sends a request to the Azure Search service to upload
        documents based on the provided schema.

        Args:
            batch (List[Dict[str, Any]]): A batch of documents to be inserted.

        Returns:
            dict: A dictionary containing the status of the operation.
        """
        search_endpoint = f"https://{self.azure_search_service}.search.windows.net/indexes/{self.index_name}/docs/index?api-version={self.search_api_version}"
        headers = {
            "Content-Type": "application/json",
            "api-key": self.search_admin_key,
        }

        document = batch[0]  # Assuming batch size of 1 for this example

        # Construct the body using the provided schema
        body = {
            "value": [
                {
                    "@search.action": "upload",
                }
            ]
        }

        # Add fields to the body according to the schema
        for field_name, field_details in self.schema.items():
            body["value"][0][field_name] = document.get(
                field_name, field_details.get("default", None)
            )

        body_json = json.dumps(body)

        # Log the request body for debugging purposes
        logger.debug(f"Uploading document to Azure Search: {body_json}")

        response = requests.post(search_endpoint, headers=headers, data=body_json)

        # Log the response status
        if response.status_code == 200:
            logger.info(f"Document uploaded successfully to index '{self.index_name}'.")
            return {"status": "success"}
        else:
            logger.error(f"Failed to upload document: {response.text}")
            return {"status": response.text}


class AzureSearchSink(DynamicSink):
    """A dynamic sink for writing data to an Azure Search index in a Bytewax dataflow.

    The AzureSearchSink class provides functionality to connect to an Azure Search
    service and manage the insertion of documents into a specified index using a
    user-defined schema.

    Methods:
        build(step_id, worker_index, worker_count) -> _AzureSearchPartition:
            Constructs an _AzureSearchPartition instance that manages the actual data
            writing process.
    """

    def __init__(
        self,
        azure_search_service: str,
        index_name: str,
        search_api_version: str,
        search_admin_key: str,
        schema: Dict[str, Any],
    ):
        """Initialize the AzureSearchSink.

        Sets up the connection parameters for the Azure Search service.

        Args:
            azure_search_service (str): The Azure Search service name.
            index_name (str): The name of the index to insert documents into.
            search_api_version (str): The API version for Azure Search.
            search_admin_key (str): The admin key for the Azure Search service.
            schema (dict): A dictionary defining the schema of the data.
        """
        self.azure_search_service = azure_search_service
        self.index_name = index_name
        self.search_api_version = search_api_version
        self.search_admin_key = search_admin_key
        self.schema = schema

    @override
    def build(
        self, step_id: str, worker_index: int, worker_count: int
    ) -> _AzureSearchPartition:
        """Build a sink partition for writing to Azure Search.

        This method constructs an instance of `_AzureSearchPartition`, which will
        handle the actual data writing to the Azure Search index for the specified
        worker in a distributed Bytewax dataflow.

        Args:
            step_id (str): The ID of the step in the Bytewax dataflow.
            worker_index (int): The index of the worker in the dataflow.
            worker_count (int): The total number of workers in the dataflow.

        Returns:
            _AzureSearchPartition: An instance of `_AzureSearchPartition` that will
            manage the data writing for this worker.
        """
        return _AzureSearchPartition(
            azure_search_service=self.azure_search_service,
            index_name=self.index_name,
            search_api_version=self.search_api_version,
            search_admin_key=self.search_admin_key,
            schema=self.schema,
        )
