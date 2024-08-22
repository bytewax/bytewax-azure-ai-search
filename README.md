[![Actions Status](https://github.com/bytewax/bytewax-azure-ai-search/actions/workflows/CI.yml/badge.svg)](https://github.com/bytewax/bytewax-azure-ai-search/actions)
[![PyPI](https://img.shields.io/pypi/v/bytewax-azure-ai-search.svg?style=flat-square)](https://pypi.org/project/bytewax-azure-ai-search/)
[![Bytewax User Guide](https://img.shields.io/badge/user-guide-brightgreen?style=flat-square)](https://docs.bytewax.io/projects/bytewax-azure-ai-search/en/latest/index.html)

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://user-images.githubusercontent.com/6073079/195393689-7334098b-a8cd-4aaa-8791-e4556c25713e.png" width="350">
  <source media="(prefers-color-scheme: light)" srcset="https://user-images.githubusercontent.com/6073079/194626697-425ade3d-3d72-4b4c-928e-47bad174a376.png" width="350">
  <img alt="Bytewax">
</picture>

## bytewax-azure-ai-search

Custom sink for [Azure AI Search](https://learn.microsoft.com/en-us/azure/search/search-what-is-azure-search) vector database for real time indexing.

bytewax-azure-ai-search is commercially licensed with publicly available source code. Please see the full details in [LICENSE](https://github.com/bytewax/bytewax-azure-ai-search/blob/main/LICENSE.md).

## Installation and import sample

To install you can run

```bash
pip install bytewax-azure-ai-search
```

Then import

```python
from bytewax.bytewax_azure_ai_search import AzureSearchSink
```

You can then add it to your dataflow

```python
azure_sink = AzureSearchSink(
    azure_search_service=service_name,
    index_name="bytewax-index",
    search_api_version="2024-07-01",
    search_admin_key=api_key,
    schema={
        "id": {"type": "string", "default": None},
        "content": {"type": "string", "default": None},
        "meta": {"type": "string", "default": None},
        "vector": {"type": "collection", "item_type": "single", "default": []},
    },
)

flow = Dataflow("indexing-pipeline")
input_data = op.input("input", flow, FileSource("data/news_out.jsonl"))
deserialize_data = op.map("deserialize", input_data, safe_deserialize)
extract_html = op.map("extract_html", deserialize_data, process_event)
op.output("output", extract_html, azure_sink)
```

**Note**

This installation includes the following dependencies:

```ssh
azure-search-documents==11.5.1
azure-common==1.1.28
azure-core==1.30.2
openai==1.34.0
```

These are used to write the vectors on the appropriate services based on an Azure schema provided. We will provide an example in this README for working versions of schema definition under these versions.

## Setting up Azure AI services

**This asumes you have set up an Azure AI Search service on the Azure portal. For more instructions, visit [their documentation](https://learn.microsoft.com/en-us/azure/search/search-create-service-portal)**

**Optional**
To generate embeddings, you can set up an [Azure OpenAI service](https://learn.microsoft.com/en-us/azure/ai-services/openai/how-to/create-resource?pivots=web-portal) and deploy an embedding model such as `text-ada-002-embedding`

Once you have set up the resources, ensure to idenfity and store the following information from the Azure portal:

* You Azure AI Search admin key
* You Azure AI Search service name
* You Azure AI Search service endpoint url

If you deployed an embedding model through Azure AI OpenAI service:

* You Azure OpenAI endpoint url
* You Azure OpenAI API key
* Your Azure OpenAI service name
* You Azure OpenAI embedding deployment name
* Your Azure OpenAI embedding name (e.g. text-ada-002-embedding`)

## Sample usage

You can find a complete example under the [`examples/` folder](https://github.com/bytewax/bytewax-azure-ai-search/tree/main/examples).

To execute the examples, you can generate a `.env` file with the following keywords:

```bash
# OpenAI
AZURE_OPENAI_ENDPOINT= <your-azure-openai-endpoint>
AZURE_OPENAI_API_KEY= <your-azure-openai-key>
AZURE_OPENAI_SERVICE=<your-azure-openai-named-service>
# Azure Document Search
AZURE_SEARCH_ADMIN_KEY=<your-azure-ai-search-admin-key>
AZURE_SEARCH_SERVICE=<your-azure-ai-search-named-service>
AZURE_SEARCH_SERVICE_ENDPOINT=<your-azure-ai-search-endpoint-url>

# Optional - if you prefer to generate embeddings with embedding models deployed on Azure
AZURE_EMBEDDING_DEPLOYMENT_NAME=<your-azure-openai-given-deployment-name>
AZURE_EMBEDDING_MODEL_NAME=<your-azure-openai-model-name>

# Optional - if you prefer to generate the embeddings with OpenAI
OPENAI_API_KEY=<your-openai-key>
```

Set up the connection and schema by running

```bash
python connection.py
```

You can verify the creation of the index was successful by visiting the portal.

![](https://github.com/bytewax/bytewax-azure-ai-search/blob/main/docs/images/sample-index.png)

If you click on the created index and press "Search" you can verify it was created - but empty at this point.

![](https://github.com/bytewax/bytewax-azure-ai-search/blob/main/docs/images/sample-empty-index.png)

Generate the embeddings and store in Azure AI Search through the bytewax-azure-ai-search sink

```bash
python -m bytewax.run dataflow:flow
```

Verify the index was populated by pressing "Search" with an empty query.

![](https://github.com/bytewax/bytewax-azure-ai-search/blob/main/docs/images/sample-filled-index.png)

**Note**

In the dataflow we initialized the custom sink as follows:

```python
from bytewax.bytewax_azure_ai_search import AzureSearchSink

azure_sink = AzureSearchSink(
    azure_search_service=service_name,
    index_name="bytewax-index",
    search_api_version="2024-07-01",
    search_admin_key=api_key,
    schema={
        "id": {"type": "string", "default": None},
        "content": {"type": "string", "default": None},
        "meta": {"type": "string", "default": None},
        "vector": {"type": "collection", "item_type": "single", "default": []},
    },
)
```

The schema and structure need to match how you configure the schema through the Azure AI Search Python API. For more information, [visit their page](https://pypi.org/project/azure-search-documents/)

In this example:

```python
from azure.search.documents.indexes.models import (
    SimpleField,
    SearchFieldDataType,
)

# Define schema
fields = [
    SimpleField(
        name="id",
        type=SearchFieldDataType.String,
        searchable=True,
        filterable=True,
        sortable=True,
        facetable=True,
        key=True,
    ),
    SearchableField(
        name="content",
        type=SearchFieldDataType.String,
        searchable=True,
        filterable=False,
        sortable=False,
        facetable=False,
        key=False,
    ),
    SearchableField(
        name="meta",
        type=SearchFieldDataType.String,
        searchable=True,
        filterable=False,
        sortable=False,
        facetable=False,
        key=False,
    ),
    SimpleField(
        name="vector",
        type=SearchFieldDataType.Collection(SearchFieldDataType.Double),
        searchable=False,
        filterable=False,
        sortable=False,
        facetable=False,
        vector_search_dimensions=DIMENSIONS,
        vector_search_profile_name="myHnswProfile",
    ),
]
```

## For developers - Setting up the project

### Install `just`

We use [`just`](https://just.systems/man/en/) as a command runner for
actions / recipes related to developing Bytewax. Please follow [the
installation
instructions](https://github.com/casey/just?tab=readme-ov-file#installation).
There's probably a package for your OS already.

### Install `pyenv` and Python 3.12

I suggest using [`pyenv`](https://github.com/pyenv/pyenv)
to manage python versions.
[the installation instructions](https://github.com/pyenv/pyenv?tab=readme-ov-file#installation).

You can also use your OS's package manager to get access to different
Python versions.

Ensure that you have Python 3.12 installed and available as a "global
shim" so that it can be run anywhere. The following will make plain
`python` run your OS-wide interpreter, but will make 3.12 available
via `python3.12`.

```console
$ pyenv global system 3.12
```

### Install `uv`

We use [`uv`](https://github.com/astral-sh/uv) as a virtual
environment creator, package installer, and dependency pin-er. There
are [a few different ways to install
it](https://github.com/astral-sh/uv?tab=readme-ov-file#getting-started),
but I recommend installing it through either
[`brew`](https://brew.sh/) on macOS or
[`pipx`](https://pipx.pypa.io/stable/).

## Development

We have a `just` recipe that will:

1. Set up a venv in `venvs/dev/`.

2. Install all dependencies into it in a reproducible way.

Start by adding any dependencies that are needed into [pyproject.toml](pyproject.toml) or into
[requirements/dev.in](requirements/dev.in) if they are needed for development.

Next, generate the pinned set of dependencies with

```console
> just venv-compile-all
```

## Create and activate a virtual environment

Once you have compiled your dependencies, run the following:

```console
> just get-started
```

Activate your development environment and run the development task:

```console
> . venvs/dev/bin/activate
> just develop
```

## License

bytewax-azure-ai-search is commercially licensed with publicly available source code. Please see the full details in [LICENSE](./LICENSE.md).
