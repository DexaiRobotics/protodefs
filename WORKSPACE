# This file marks a workspace root for the Bazel build system.
# See `https://bazel.build/`.

workspace(name = "protodefs")

# Set all our versions
RULES_PROTO_VERSION = "4.4.0"

# Rule to load and build repositories from online sources
load("@bazel_tools//tools/build_defs/repo:http.bzl", "http_archive")

# Rules for generating gRPC and Protobuf code
http_archive(
    name = "rules_proto_grpc",
    sha256 = "928e4205f701b7798ce32f3d2171c1918b363e9a600390a25c876f075f1efc0a",
    strip_prefix = "rules_proto_grpc-{}".format(RULES_PROTO_VERSION),
    urls = ["https://github.com/rules-proto-grpc/rules_proto_grpc/releases/download/4.4.0/rules_proto_grpc-{}.tar.gz".format(RULES_PROTO_VERSION)],
)

load("@rules_proto_grpc//:repositories.bzl", "rules_proto_grpc_repos", "rules_proto_grpc_toolchains")

rules_proto_grpc_toolchains()

rules_proto_grpc_repos()

load("@rules_proto//proto:repositories.bzl", "rules_proto_dependencies", "rules_proto_toolchains")

rules_proto_dependencies()

rules_proto_toolchains()

load("@rules_proto_grpc//cpp:repositories.bzl", rules_proto_grpc_cpp_repos = "cpp_repos")

rules_proto_grpc_cpp_repos()
