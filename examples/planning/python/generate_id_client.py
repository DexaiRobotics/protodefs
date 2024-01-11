import grpc
import sys
import yaml
import os
import os.path

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(os.path.dirname(ROOT_DIR), "data")
BUILDFILES_DIR = os.path.join(ROOT_DIR, "build")
if BUILDFILES_DIR not in sys.path:
    sys.path.append(BUILDFILES_DIR)

from build.types_pb2 import Constraints, Model
from build.generate_id_pb2 import (
    RegisterPlanContextRequest,
    RegisterPlanContextResponse,
)
from build.generate_id_pb2_grpc import PlanContextRegistryStub


def make_empty_constraints():
    return Constraints(pos_constraints=[], angle_constraints=[])


def raw_dmd():
    with open(os.path.join(DATA_DIR, "dmd", "iiwa_boxes.dmd.yaml")) as dmd:
        data = dmd.read()
    return data


def make_models():
    models = []
    urdf_dir = os.path.join(DATA_DIR, "urdf")
    for fname in os.listdir(urdf_dir):
        if fname.endswith(".urdf"):
            with open(os.path.join(urdf_dir, fname)) as urdf:
                models.append(
                    Model(name=os.path.splitext(fname)[0], urdf_raw=urdf.read())
                )
    return models


def make_id_request():
    return RegisterPlanContextRequest(
        system_name="iiwa-test",
        package_name="iiwa_models",
        model_directive_yaml=raw_dmd(),
        models=make_models(),
        constraints=make_empty_constraints(),
    )


def run():
    req = make_id_request()
    with grpc.insecure_channel("localhost:5051") as channel:
        stub = PlanContextRegistryStub(channel)
        resp = stub.HandleRegisterPlanContextRequest(req)
        print(resp.context_id.value)


if __name__ == "__main__":
    run()
