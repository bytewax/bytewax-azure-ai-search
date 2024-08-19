from bytewax.outputs import DynamicSink
from typing_extensions import override
from .partition import _AzureSearchPartition


class AzureSearchSink(DynamicSink):
    """Write each output item to Azure Search"""

    @override
    def build(
        self, _step_id: str, _worker_index: int, _worker_count: int
    ) -> _AzureSearchPartition:
        return _AzureSearchPartition()
