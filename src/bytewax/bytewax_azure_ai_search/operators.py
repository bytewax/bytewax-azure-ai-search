"""Operators for the Azure AI Search Sink.

It's suggested to import operators like this:

```
from bytewax.connectors.azure_ai_search import operators as aop
```

And then you can use the operators like this:

from bytewax.dataflow import Dataflow

flow = Dataflow("azure-ai-search-out")
input = kop.input("kafka_inp", flow, brokers=[...], topics=[...])
aop.output(
"azure-search-out",
input,
)


This implementation aims to provide a more straightforward
and user-friendly way to batch and validate data against
the Azure Search schema before inserting it into the index.

The operators ensure that the data conforms to the schema,
making the integration seamless and reducing the potential f
or errors when interacting with Azure Search.
"""

from datetime import timedelta
from typing import Any, Dict, List, Tuple

from typing_extensions import TypeAlias

import bytewax.operators as op
from bytewax.bytewax_azure_ai_search import AzureSearchSink
from bytewax.dataflow import Stream, operator

KeyedStream: TypeAlias = Stream[Tuple[str, Dict[str, Any]]]
"""A Stream of (key, value) 2-tuples where the value matches the Azure Search schema."""


@operator
def _prepare_azure_batch(
    step_id: str,
    up: KeyedStream,
    timeout: timedelta,
    max_size: int,
    schema: Dict[str, Any],
) -> KeyedStream:
    """Batch records and ensure they match the Azure Search schema."""

    def validate_and_prepare(
        key__batch: Tuple[str, List[Dict[str, Any]]],
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """Ensure the batch conforms to the Azure Search schema."""
        key, batch = key__batch

        # Apply schema defaults and validate data
        for document in batch:
            for field_name, field_details in schema.items():
                if field_name not in document:
                    document[field_name] = field_details.get("default")

        return key, batch

    return op.collect("batch", up, timeout=timeout, max_size=max_size).then(
        op.map, "validate_and_prepare", validate_and_prepare
    )


@operator
def azure_output(
    step_id: str,
    up: KeyedStream,
    azure_search_service: str,
    index_name: str,
    search_api_version: str,
    search_admin_key: str,
    schema: Dict[str, Any],
    timeout: timedelta = timedelta(seconds=1),
    max_size: int = 50,
) -> None:
    """Produce data to Azure Search as an output sink.

    :arg step_id: Unique ID for the operation.

    :arg up: Stream of records to be inserted into Azure Search.

    :arg azure_search_service: Name of the Azure Search service.

    :arg index_name: The name of the index to insert documents into.

    :arg search_api_version: The API version for Azure Search.

    :arg search_admin_key: The admin key for the Azure Search service.

    :arg schema: A dictionary defining the schema of the data.

    :arg timeout: A timedelta specifying how long to wait for new data before writing.
                    Defaults to 1 second.

    :arg max_size: The number of items to wait for before writing. Defaults to 50.
    """
    return _prepare_azure_batch(
        "prepare_azure_batch", up, timeout=timeout, max_size=max_size, schema=schema
    ).then(
        op.output,
        "azure_search_output",
        AzureSearchSink(
            azure_search_service,
            index_name,
            search_api_version,
            search_admin_key,
            schema,
        ),
    )
