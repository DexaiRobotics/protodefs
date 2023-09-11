project(protodefs)

message("----------------------------------------")
message("protos CMakeLists.txt")
message("----------------------------------------")
message("CMAKE_CXX_STANDARD: " ${CMAKE_CXX_STANDARD})
message("CMAKE_CXX_STANDARD_REQUIRED: " ${CMAKE_CXX_STANDARD_REQUIRED})
message("CMAKE_CXX_FLAGS: " ${CMAKE_CXX_FLAGS})
message("CMAKE_CXX_COMPILER: " ${CMAKE_CXX_COMPILER})

# gRPC/Protobuf packages
include(FindProtobuf)
find_package(Protobuf REQUIRED)
find_package(PkgConfig REQUIRED)
pkg_search_module(GRPC REQUIRED grpc)
pkg_search_module(GRPCPP REQUIRED grpc++>=1.16.1)
include_directories(${Protobuf_INCLUDE_DIRS})
include_directories(${CMAKE_CURRENT_BINARY_DIR})
find_program(GRPC_CPP_PLUGIN grpc_cpp_plugin)
if (NOT GRPC_CPP_PLUGIN)
    message(FATAL_ERROR "grpc_cpp_plugin not found!")
endif()

 # create a new library pointing to the api definition
 add_library(protodefs SHARED ${CMAKE_CURRENT_SOURCE_DIR}/proto/planning/api.proto)
 # link against protobuf and gRPC
 target_link_libraries(protodefs
     PUBLIC
     protobuf::libprotobuf
     grpc++
     grpc++_reflection
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
 protobuf_generate(
     TARGET protodefs
     LANGUAGE grpc
     OUT_VAR PROTO_FILES
     GENERATE_EXTENSIONS .grpc.pb.h .grpc.pb.cc
     PLUGIN "protoc-gen-grpc=${GRPC_CPP_PLUGIN}"
 )
 # set as generated
 set_source_files_properties(${PROTO_FILES} PROPERTIES GENERATED TRUE)
 # add to include directories
 target_include_directories(protodefs PRIVATE ${CMAKE_CURRENT_BINARY_DIR})

