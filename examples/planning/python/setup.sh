#!/bin/bash
set -eufo pipefail
echo "beginning setup"
pip install virtualenv
sudo apt install python3-venv
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

DIRNAME=$(dirname "$(realpath "$0")")
pushd "$DIRNAME"
PROTO_ROOT=$(dirname "$(dirname "$(dirname "$DIRNAME")")")
PROTO_PATH=$PROTO_ROOT/proto/planning
declare -a protofiles=(
  $PROTO_PATH/builder.proto
  $PROTO_PATH/generate_id.proto
  $PROTO_PATH/planner.proto
  $PROTO_PATH/types.proto
)
echo "Compiling definitions for protofiles located at: $PROTO_PATH"
BUILD_DIR=build
mkdir -p $BUILD_DIR
python3 -m grpc_tools.protoc -I$PROTO_PATH --python_out=$BUILD_DIR --pyi_out=$BUILD_DIR --grpc_python_out=$BUILD_DIR "${protofiles[@]}"
popd
echo "setup complete"
