project(protodefs)

message("----------------------------------------")
message("protos CMakeLists.txt")
message("----------------------------------------")
message("CMAKE_CXX_STANDARD: " ${CMAKE_CXX_STANDARD})
message("CMAKE_CXX_STANDARD_REQUIRED: " ${CMAKE_CXX_STANDARD_REQUIRED})
message("CMAKE_CXX_FLAGS: " ${CMAKE_CXX_FLAGS})
message("CMAKE_CXX_COMPILER: " ${CMAKE_CXX_COMPILER})

# gRPC/Protobuf
find_package(protobuf CONFIG REQUIRED)
find_package(gRPC CONFIG REQUIRED)

add_library(protodefs ${CMAKE_CURRENT_SOURCE_DIR}/proto/planning/api.proto)
target_link_libraries(protodefs
    PUBLIC
    protobuf::libprotobuf
    gRPC::grpc++
    gRPC::grpc++_reflection
)
target_include_directories(protodefs SYSTEM PUBLIC ${CMAKE_CURRENT_BINARY_DIR})

protobuf_generate(
    TARGET protodefs
    LANGUAGE cpp
    OUT_VAR PROTO_FILES

)
get_target_property(grpc_cpp_plugin_location gRPC::grpc_cpp_plugin LOCATION)
protobuf_generate(
    TARGET protodefs
    LANGUAGE grpc
    OUT_VAR PROTO_FILES
    GENERATE_EXTENSIONS .grpc.pb.h .grpc.pb.cc
    PLUGIN "protoc-gen-grpc=${grpc_cpp_plugin_location}"
)

set_source_files_properties(${PROTO_FILES} PROPERTIES GENERATED TRUE)

