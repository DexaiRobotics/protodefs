# Protodefs

Repository holding `protobuf` Message definitions and `gRPC` Service definitions.

## Requirements
Your project will require both [gRPC](https://grpc.io) and [Protobuf](https://protobuf.dev) to generate code from these definitions, as well as respective build rules for each.
### Bazel
In Bazel, you can use the `http_archive` rule to pull these dependencies directly into your workspace. Just drop the following code into your `WORKSPACE` file.
```
GRPC_VERSION = <DESIRED_GRPC_VERSION>
RULES_PROTO_VERSION = <DESIRED_RULES_PROTO_VERSION>

# gRPC
http_archive(
    name = "com_github_grpc_grpc",
    strip_prefix = "grpc-{}".format(GRPC_VERSION),
    urls = ["https://github.com/grpc/grpc/archive/refs/tags/v{}.tar.gz".format(GRPC_VERSION)],
)

load("@com_github_grpc_grpc//bazel:grpc_deps.bzl", "grpc_deps")
grpc_deps()

load("@com_github_grpc_grpc//bazel:grpc_extra_deps.bzl", "grpc_extra_deps")
grpc_extra_deps()

# Rules for generating gRPC and Protobuf code
http_archive(
    name = "rules_proto_grpc",
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
```
### CMake/Other
You'll need to install both gRPC and CMake either from source or from a package manager.
// TODO
## Usage

We currently support building against this repository with CMake and Bazel.

### Bazel
// TODO

### CMake
To include these definitions in your CMake project, first add this repository as a submodule:
```
git submodule add git@github.com:DexaiRobotics/protodefs.git
```

Then, in your top-level `CMakeLists.txt` file, add `protodefs` as a subdirectory:
```
add_subdirectory(protodefs)
```

Then, you can link against the library for a given target:
```
add_library(my_target ${TARGET_SRCS})
target_link_libraries(my_target
    protodefs
    ...
)
```

