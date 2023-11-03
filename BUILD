load("@rules_proto_grpc//cpp:defs.bzl", "cpp_grpc_library")

proto_library(
    name = "api_proto",
    srcs = ["proto/planning/api.proto"],
)

cpp_grpc_library(
    name = "api_cc_grpc",
    protos = [":api_proto"],
    visibility = ["//visibility:public"],
)
