# Python
The following comprises a simple Python implementation of a client which can generate a unique identifier for a set of geometry, and initiate an IRIS generation job at the service.

All geometry will be referencing the KUKA IIWA model defined at `protodefs/examples/data`.

## Usage
First, run the setup script, which generates the corresponding Protobuf/GRPC code and the project's Python requirements:
```./setup/sh```

Then, the client is callable via `python3 simple_client.py`.
