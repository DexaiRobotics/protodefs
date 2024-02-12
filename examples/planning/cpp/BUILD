cc_library(
    name = "client",
    srcs = ["client.cc"],
    hdrs = ["client.h"],
    visibility = ["//visibility:public"],
    deps = [
        "@com_github_grpc_grpc//:grpc++",
        "@com_github_grpc_grpc//:grpc++_reflection",
        "@proto//:api_cc_grpc",
    ],
)

cc_binary(
    name = "main",
    srcs = ["main.cc"],
    deps = [":client"],
)
