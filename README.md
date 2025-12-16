# Testcontainers SpiceDB - Python

Python module for Testcontainers that provides a SpiceDB container for integration testing.

This is a Python port of the Go `testcontainers-spicedb` module. All credit to @Mariscal6 for the [original module](https://github.com/Mariscal6/testcontainers-spicedb-go)

## Installation

Install from source:

```bash
pip install -e .
```

## Requirements

- Python 3.8+
- Docker

## Usage

### Basic Usage

```python
from testcontainers_spicedb import SpiceDBContainer

# Using context manager (recommended)
with SpiceDBContainer(image="authzed/spicedb:v1.47.1") as spicedb:
    endpoint = spicedb.get_endpoint()
    secret_key = spicedb.get_secret_key()

    # Use endpoint and secret_key with your SpiceDB client
    # ...
```

### Custom Secret Key

```python
from testcontainers_spicedb import SpiceDBContainer

with SpiceDBContainer(secret_key="mycustomsecret") as spicedb:
    endpoint = spicedb.get_endpoint()
    secret_key = spicedb.get_secret_key()  # Returns "mycustomsecret"
```

### Pre-load Schema

```python
from testcontainers_spicedb import SpiceDBContainer

schema = """
    definition user {}

    definition document {
        relation owner: user
        relation viewer: user
        permission view = viewer + owner
    }
"""

with SpiceDBContainer(
    model=schema,
    model_secret_key="somepresharedkey"
) as spicedb:
    endpoint = spicedb.get_endpoint()
    # Schema is already loaded, ready to use
```

### With SpiceDB Client

```python
from testcontainers_spicedb import SpiceDBContainer
from authzed.api.v1 import Client, WriteSchemaRequest

with SpiceDBContainer() as spicedb:
    # Create client
    client = Client(
        spicedb.get_endpoint(),
        spicedb.get_secret_key(),
        use_tls=False
    )

    # Write schema
    schema = """
        definition user {}
        definition resource {
            relation owner: user
        }
    """
    response = client.WriteSchema(WriteSchemaRequest(schema=schema))
```

## Testing

Run tests using pytest:

```bash
pytest tests/
```

## Examples

See the `examples/` directory for more usage examples:

```bash
python examples/example_spicedb.py
```

## API Reference

### SpiceDBContainer

Main container class for SpiceDB.

**Parameters:**
- `image` (str): Docker image to use (default: "authzed/spicedb:v1.47.1")
- `secret_key` (str): gRPC pre-shared key (default: "somepresharedkey")
- `model` (str, optional): Schema to load on startup
- `model_secret_key` (str, optional): Secret key for schema writer
- `schema_writer` (callable, optional): Custom schema writer function
- `port` (int): Port to expose (default: 50051)

**Methods:**
- `get_endpoint()`: Returns the gRPC endpoint (host:port)
- `get_secret_key()`: Returns the configured secret key
- `start()`: Starts the container
- `stop()`: Stops and removes the container

## Links

- [SpiceDB](https://authzed.com/spicedb)
- [SpiceDB Python Client](https://github.com/authzed/authzed-py)
- [Testcontainers Python](https://testcontainers-python.readthedocs.io/)
- [Original Go Module](https://github.com/Mariscal6/testcontainers-spicedb-go)