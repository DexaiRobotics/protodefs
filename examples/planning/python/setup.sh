#!/bin/bash

pip install grpcio
pip install -r requirements.txt


PROTO_PATH=../../../proto/planning
protofiles=($PROTO_PATH/*.proto)
echo "Compiling definitions for protofiles located at: $PROTO_PATH"
BUILD_DIR=build
mkdir -p $BUILD_DIR
python3 -m grpc_tools.protoc -I$PROTO_PATH --python_out=$BUILD_DIR --pyi_out=$BUILD_DIR --grpc_python_out=$BUILD_DIR "${protofiles[@]}"
