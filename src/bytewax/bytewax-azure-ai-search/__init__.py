"""Custom sink for Azure AI Search."""

from .connection import index_client, search_indexer_client
from .sink import AzureSearchSink

__all__ = ["index_client", "search_indexer_client", "AzureSearchSink"]
