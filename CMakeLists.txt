project(protodefs)

message("----------------------------------------")
message("protos CMakeLists.txt")
message("----------------------------------------")
message("CMAKE_CXX_STANDARD: " ${CMAKE_CXX_STANDARD})
message("CMAKE_CXX_STANDARD_REQUIRED: " ${CMAKE_CXX_STANDARD_REQUIRED})
message("CMAKE_CXX_FLAGS: " ${CMAKE_CXX_FLAGS})
message("CMAKE_CXX_COMPILER: " ${CMAKE_CXX_COMPILER})

# gRPC/Protobuf packages
find_package(protobuf CONFIG REQUIRED)
find_package(gRPC CONFIG REQUIRED)

# create a new library pointing to the api definition
add_library(protodefs ${CMAKE_CURRENT_SOURCE_DIR}/proto/planning/api.proto)
# link against protobuf and gRPC
target_link_libraries(protodefs
    PUBLIC
    protobuf::libprotobuf
    gRPC::grpc++
    gRPC::grpc++_reflection
)
# add to include directories
target_include_directories(protodefs PUBLIC ${CMAKE_CURRENT_BINARY_DIR})
# 1.) generate protobuf serializations
protobuf_generate(
    TARGET protodefs
    LANGUAGE cpp
    OUT_VAR PROTO_FILES
)
# 2.) generate gRPC files using serializations from the previous step
get_target_property(grpc_cpp_plugin_location gRPC::grpc_cpp_plugin LOCATION)
protobuf_generate(
    TARGET protodefs
    LANGUAGE grpc
    OUT_VAR PROTO_FILES
    GENERATE_EXTENSIONS .grpc.pb.h .grpc.pb.cc
    PLUGIN "protoc-gen-grpc=${grpc_cpp_plugin_location}"
)
# set as generated
set_source_files_properties(${PROTO_FILES} PROPERTIES GENERATED TRUE)

