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
"""

from datetime import timedelta
from typing import Dict, List, Tuple, Any

import bytewax.operators as op
from bytewax.dataflow import Stream, operator
from bytewax.bytewax_azure_ai_search import AzureSearchSink
from typing_extensions import TypeAlias

KeyedStream: TypeAlias = Stream[Tuple[str, Dict[str, Any]]]
"""A {py:obj}`~bytewax.dataflow.Stream` of `(key, value)` 2-tuples."""


@operator
def _to_azure_sink(
    step_id: str,
    up: KeyedStream[Dict[str, Any]],
    timeout: timedelta,
    max_size: int,
    schema: Dict[str, Any],
) -> KeyedStream[List[Dict[str, Any]]]:
    """Convert records to batches ready for Azure Search Sink."""

    def shim_mapper(
        key__batch: Tuple[str, List[Dict[str, Any]]],
    ) -> List[Dict[str, Any]]:
        _, batch = key__batch
        return batch

    return op.collect("batch", up, timeout=timeout, max_size=max_size).then(
        op.map, "map", shim_mapper
    )


@operator
def output(
    step_id: str,
    up: KeyedStream[Dict[str, Any]],
    azure_search_service: str,
    index_name: str,
    search_api_version: str,
    search_admin_key: str,
    schema: Dict[str, Any],
    timeout: timedelta = timedelta(seconds=1),
    max_size: int = 50,
) -> None:
    """Produce to Azure Search as an output sink.

    Default partition routing is used.

    Workers are the unit of parallelism.

    :arg step_id: Unique ID.

    :arg up: Stream of records. Key must be a `String`
        and value must match the schema defined for the Azure Search Sink.

    :arg azure_search_service: Name of the Azure Search service.

    :arg index_name: The name of the index to insert documents into.

    :arg search_api_version: The API version for Azure Search.

    :arg search_admin_key: The admin key for the Azure Search service.

    :arg schema: A dictionary defining the schema of the data.

    :arg timeout: A timedelta of the amount of time to wait for
        new data before writing. Defaults to 1 second.

    :arg max_size: The number of items to wait before writing
        defaults to 50.
    """
    return _to_azure_sink(
        "to_azure_sink", up, timeout=timeout, max_size=max_size, schema=schema
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
