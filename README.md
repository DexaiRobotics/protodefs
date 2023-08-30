# Protodefs

Repository holding `protobuf` Message definitions and `gRPC` Service definitions.

## Usage

We currently support building against this repository with CMake and Bazel.

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

### Bazel
// TODO
