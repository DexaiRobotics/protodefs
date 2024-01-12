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

from build.types_pb2 import (
    Constraints,
    Model,
    SystemConf,
    Conf,
    PositionConstraint,
    AngleBetweenVectorsConstraint,
)
from build.generate_id_pb2 import RegisterPlanContextRequest
from build.generate_id_pb2_grpc import PlanContextRegistryStub
from build.builder_pb2 import StartBuildFromConfsRequest
from build.builder_pb2_grpc import IrisBuilderStub

# position_constraints:
#   - frame_A: hotel_pan_sixth_6in_024
#     frame_B: disher_2oz_face
#     position_BQ: [0.0, 0.0, 0.0]
#     position_AQ_lower: [-0.15, -0.08, -0.02]
#     position_AQ_upper: [0.15, 0.08, 0.66]
#   - frame_A: hotel_pan_sixth_6in_024
#     frame_B: disher_2oz_tip
#     position_BQ: [0.0, 0.0, 0.0]
#     position_AQ_lower: [-0.15, -0.08, -0.02]
#     position_AQ_upper: [0.15, 0.08, 0.66]


def make_constraints(constraints_name):
    with open(os.path.join(DATA_DIR, "constraints", f"{constraints_name}.yaml")) as f:
        data = yaml.load(f)
    pos_constraints = []
    angle_constraints = []
    if "pos_constraints" in data:
        for constraint in data["pos_constraints"]:
            pos_constraints.append(
                PositionConstraint(
                    frame_A=constraint["frame_A"],
                    frame_B=constraint["frame_B"],
                    p_AQ_lower=constraint["position_AQ_lower"],
                    p_AQ_upper=constraint["position_AQ_upper"],
                    position_BQ=constraint["position_BQ"],
                )
            )
    if "angle_constraints" in data:
        for constraint in data["angle_constraints"]:
            angle_constraints.append(
                AngleBetweenVectorsConstraint(
                    frame_A=constraint["frame_A"],
                    frame_B=constraint["frame_B"],
                    a_A=constraint["a_A"],
                    b_B=constraint["b_B"],
                    angle_lower=constraint["angle_lower"],
                    angle_upper=constraint["angle_upper"],
                )
            )
    return Constraints(
        pos_constraints=pos_constraints, angle_constraints=angle_constraints
    )


def raw_dmd(dmd_name):
    with open(os.path.join(DATA_DIR, "dmd", f"{dmd_name}.dmd.yaml")) as dmd:
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


def make_id_request(system_name, package_name, dmd_name, constraints_name):
    return RegisterPlanContextRequest(
        system_name=system_name,
        package_name=package_name,
        model_directive_yaml=raw_dmd(dmd_name),
        models=make_models(),
        constraints=make_constraints(constraints_name),
    )


def make_build_request(context_id, configs_fname):
    seed_configs = []
    with open(os.path.join(DATA_DIR, configs_fname)) as f:
        data = yaml.load(f)
        for _, sysconf in data.items():
            sysconf_data = {}
            for robot, conf_data in sysconf.items():
                sysconf_data[robot] = Conf(data=conf_data)
            seed_configs.append(SystemConf(data=sysconf_data))
    return StartBuildFromConfsRequest(
        id="TEST_ID", context_id=context_id, seed_configs=seed_configs
    )


def run():
    req = make_id_request("iiwa-test", "iiwa_models", "iiwa_boxes", "default")
    with grpc.insecure_channel("0.0.0.0:5151") as channel:
        stub = PlanContextRegistryStub(channel)
        resp = stub.HandleRegisterPlanContextRequest(req)
    print(f"Got ID: {resp.context_id.value}")
    with grpc.insecure_channel("0.0.0.0:5150") as channel:
        stub = IrisBuilderStub(channel)
        req = make_build_request(resp.context_id, "key_configs.yaml")
        resp = stub.HandleStartBuildFromConfsRequest(req)


if __name__ == "__main__":
    run()
