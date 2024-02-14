project(protodefs)

message("----------------------------------------")
message("protos CMakeLists.txt")
message("----------------------------------------")
message("CMAKE_CXX_STANDARD: " ${CMAKE_CXX_STANDARD})
message("CMAKE_CXX_STANDARD_REQUIRED: " ${CMAKE_CXX_STANDARD_REQUIRED})
message("CMAKE_CXX_FLAGS: " ${CMAKE_CXX_FLAGS})
message("CMAKE_CXX_COMPILER: " ${CMAKE_CXX_COMPILER})

# Protobuf
include(FindProtobuf)
find_package(Protobuf REQUIRED)
# gRPC must be located via pkg-config
find_package(PkgConfig REQUIRED)
pkg_search_module(GRPC REQUIRED grpc)
pkg_search_module(GRPCPP REQUIRED grpc++>=1.16.1)
# plugin which will generate gRPC C++ code
find_program(GRPC_CPP_PLUGIN grpc_cpp_plugin)
if (NOT GRPC_CPP_PLUGIN)
    message(FATAL_ERROR "grpc_cpp_plugin not found!")
endif()
# create library
file(GLOB PROTODEF_FILES 
    ${CMAKE_CURRENT_SOURCE_DIR}/proto/planning/*.proto
)
add_library(protodefs SHARED ${PROTODEF_FILES})
target_link_libraries(protodefs PUBLIC 
    protobuf::libprotobuf
    grpc
    grpc++
)
set(PROTO_BINARY_DIR "${CMAKE_CURRENT_BINARY_DIR}")
# generate C++ code for Protobuf message types
protobuf_generate(
    TARGET protodefs
    OUT_VAR PROTO_GENERATED_FILES
    APPEND_PATH
    PROTOC_OUT_DIR ${PROTO_BINARY_DIR}
)
set_source_files_properties(${PROTO_GENERATED_FILES} PROPERTIES GENERATED TRUE)
# generate C++ code for gRPC methods
protobuf_generate(
    TARGET protodefs
    OUT_VAR PROTO_GENERATED_FILES
    LANGUAGE grpc
    GENERATE_EXTENSIONS .grpc.pb.h .grpc.pb.cc
    PLUGIN "protoc-gen-grpc=${GRPC_CPP_PLUGIN}"
    APPEND_PATH
    PROTOC_OUT_DIR ${PROTO_BINARY_DIR}
)
set_source_files_properties(${PROTO_GENERATED_FILES} PROPERTIES  GENERATED TRUE)

target_include_directories(protodefs PUBLIC "$<BUILD_INTERFACE:${PROTO_BINARY_DIR}>")
