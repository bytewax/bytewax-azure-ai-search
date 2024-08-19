import json
import requests
from bytewax.outputs import StatelessSinkPartition
from typing_extensions import override


class _AzureSearchPartition(StatelessSinkPartition):
    @override
    def write_batch(self, dictionary) -> None:
        index_name = "bytewax-index"
        search_api_version = "2023-11-01"
        search_endpoint = f"https://bytewax-workshop.search.windows.net/indexes/{index_name}/docs/index?api-version={search_api_version}"
        headers = {
            "Content-Type": "application/json",
            "api-key": os.getenv("AZURE_SEARCH_ADMIN_KEY"),
        }

        dictionary = dictionary[0]
        flattened_meta = dictionary["meta"]

        body = json.dumps(
            {
                "value": [
                    {
                        "@search.action": "upload",
                        "id": dictionary["id"],
                        "content": dictionary["content"],
                        "meta": flattened_meta,
                        "vector": dictionary["vector"],
                    }
                ]
            }
        )

        response = requests.post(search_endpoint, headers=headers, data=body)
        return {"status": "success" if response.status_code == 200 else response.text}
