#!/bin/bash
go mod init example
go mod tidy
PROTO_PATH=../../../proto/planning
echo "Compiling definitions for protofiles located at: $PROTO_PATH"
BUILD_DIR=build
mkdir -p $BUILD_DIR
protofiles=($PROTO_PATH/*.proto)
protoc -I$PROTO_PATH --go_out=$BUILD_DIR --go_opt=paths=source_relative --go-grpc_out=$BUILD_DIR --go-grpc_opt=paths=source_relative "${protofiles[@]}"
