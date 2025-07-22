#!/bin/bash

# Generate Python gRPC code from proto files

python -m grpc_tools.protoc \
    --proto_path=./proto \
    --python_out=./src/grpc \
    --grpc_python_out=./src/grpc \
    ./proto/*.proto

# Check if generation was successful
if [ $? -ne 0 ]; then
    echo "Error generating gRPC code. Please check your proto files and try again."
    exit 1
fi


echo "gRPC code generated successfully for Sensor layer services."