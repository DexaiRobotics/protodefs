import grpc
import sys
import yaml
import os
import os.path
from typing import List, Tuple

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
    PlanContextId,
)
from build.generate_id_pb2 import (
    RegisterPlanContextRequest,
    RegisterPlanContextResponse,
)
from build.generate_id_pb2_grpc import PlanContextRegistryStub
from build.builder_pb2 import StartBuildFromConfsRequest, StartBuildResponse
from build.builder_pb2_grpc import IrisBuilderStub


def make_position_constraint_msg(
    frame_A: str,
    frame_B: str,
    p_AQ_lower: Tuple[float, float, float],
    p_AQ_upper: Tuple[float, float, float],
    position_BQ: Tuple[float, float, float],
) -> PositionConstraint:
    """Make a Protobuf message for a position constraint on a point Q atached
    to a frame B, measured and expressed in frame A.

    Args:
        frame_A (str): The frame in which point Q's position is measured
        frame_B (str): The frame to which point Q is rigidly attached.
        p_AQ_lower (Tuple[float, float, float]): The lower bound on the position of point Q,
        measured and expressed in frame A.
        p_AQ_upper (Tuple[float, float, float]): The upper bound on the position of point Q,
        measured and expressed in frame A.
        position_BQ (Tuple[float, float, float]): The position of the point Q, rigidly
        attached to frame B, measured and expressed in frame B.

    Returns:
        types_pb2.PositionConstraint
    """
    return PositionConstraint(
        frame_A=frame_A,
        frame_B=frame_B,
        p_AQ_lower=p_AQ_lower,
        p_AQ_upper=p_AQ_upper,
        position_BQ=position_BQ,
    )


def make_angular_constraint_msg(
    frame_A: str,
    frame_B: str,
    a_A: Tuple[float, float, float],
    b_B: Tuple[float, float, float],
    angle_lower: float,
    angle_upper: float,
) -> AngleBetweenVectorsConstraint:
    """Make a Protobuf message for an angular constraint between a vector a
    and a vector b.


    Args:
        frame_A (str): The frame in which point Q's position is measured
        frame_B (str): The frame to which point Q is rigidly attached.
        a_A (Tuple[float, float, float]): The vector a fixed to frame A, expressed in
        frame A.
        b_B (Tuple[float, float, float]): The vector b fixed to frame B, expressed in
        frame B.
        angle_lower (float): The lower bound on the angle between a and b.
        angle_upper (float): The upper bound on the angle between a and b.

    Returns:
        types_pb2.AngleBetweenVectorsConstraint
    """
    return AngleBetweenVectorsConstraint(
        frame_A=frame_A,
        frame_B=frame_B,
        a_A=a_A,
        b_B=b_B,
        angle_lower=angle_lower,
        angle_upper=angle_upper,
    )


def make_constraints_msg_from_yaml(constraints_fname: str) -> Constraints:
    """Given a YAML filename containing constraints data, make a Protobuf
    message for the combined constraints instance.

    Args:
        constraints_fname (str): filename for constraints YAML

    Returns:
        types_pb2.Constraints
    """
    with open(constraints_fname) as f:
        data = yaml.safe_load(f)
    pos_constraints = []
    angle_constraints = []
    if "pos_constraints" in data:
        for constraint in data["pos_constraints"]:
            pos_constraints.append(
                make_position_constraint_msg(
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
                make_angular_constraint_msg(
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


def raw_file_contents(fname: str) -> str:
    """Return the raw contents of the given file."""
    with open(fname) as f:
        data = f.read()
    return data


def make_models(urdf_dir: str) -> List[Model]:
    """Make a vector of Protobuf messages of robot models for all URDFs
    located at the target directory.

    Args:
        urdf_dir (str): Directory containing all URDF data

    Returns:
        Vector[types_pb2.Model]
    """
    models = []
    for fname in os.listdir(urdf_dir):
        if fname.endswith(".urdf"):
            models.append(
                Model(
                    name=os.path.splitext(fname)[0],
                    urdf_raw=raw_file_contents(os.path.join(urdf_dir, fname)),
                )
            )
    return models


def make_id_request(
    system_name: str,
    package_name: str,
    dmd_file: str,
    urdf_dir: str,
    constraints_file: str,
) -> RegisterPlanContextRequest:
    """Make a Protobuf request message to generate a unique ID for the given
    planning problem.

    Args:
        system_name (str): Global identifier for the target system.
        package_name (str): Name of the package from which the models will be
        located.
        dmd_file (str): Path to model directive file.
        urdf_dir (str): Path to directory containing all URDFs
        constraints_file (str): Path to constraints file.

    Returns:
        generate_id_pb2.RegisterPlanContextRequest
    """
    return RegisterPlanContextRequest(
        system_name=system_name,
        package_name=package_name,
        model_directive_yaml=raw_file_contents(dmd_file),
        models=make_models(urdf_dir),
        constraints=make_constraints_msg_from_yaml(constraints_file),
    )


def make_iris_build_request(
    req_id: str, context_id: PlanContextId, seed_configs_file: str
) -> StartBuildFromConfsRequest:
    """Make a Protobuf request message to generate a set of IRIS regions for a
    unique planning context and set of seed data.

    Args:
        context_id (types_pb2.PlanContextId): unique ID for the target context
        seed_configs_file (str): file containing seed configuration data

    Returns:
        builder_pb2.StartBuildFromConfsRequest
    """
    seed_configs = []
    with open(seed_configs_file) as f:
        data = yaml.safe_load(f)
        for _, sysconf in data.items():
            sysconf_data = {}
            for robot, conf_data in sysconf.items():
                sysconf_data[robot] = Conf(data=conf_data)
            seed_configs.append(SystemConf(data=sysconf_data))
    return StartBuildFromConfsRequest(
        id=req_id, context_id=context_id, seed_configs=seed_configs
    )


def get_plan_context_id(req: RegisterPlanContextRequest) -> RegisterPlanContextResponse:
    """Send a populated request to the plan context registry service."""
    with grpc.insecure_channel("0.0.0.0:5151") as channel:
        stub = PlanContextRegistryStub(channel)
        return stub.HandleRegisterPlanContextRequest(req)


def start_iris_build_job(req: StartBuildFromConfsRequest) -> StartBuildResponse:
    """Send a populated request to the IRIS generation service."""
    with grpc.insecure_channel("0.0.0.0:5150") as channel:
        stub = IrisBuilderStub(channel)
        return stub.HandleStartBuildFromConfsRequest(req)


def run() -> None:
    # paths to geometry and constraints data
    dmd_file = os.path.join(DATA_DIR, "dmd", "iiwa_boxes.dmd.yaml")
    urdf_dir = os.path.join(DATA_DIR, "urdf")
    constraints_file = os.path.join(DATA_DIR, "constraints", "default.yaml")
    # construct and send the ID request
    id_req = make_id_request(
        system_name="kuka-iiwa",
        package_name="iiwa_models",  # this must match the package in the DMD
        dmd_file=dmd_file,
        urdf_dir=urdf_dir,
        constraints_file=constraints_file,
    )
    id_resp = get_plan_context_id(id_req)
    print(f"Got ID: {id_resp.context_id.value}")
    seed_configs_file = os.path.join(DATA_DIR, "key_configs.yaml")
    # construct and send the IRIS build request
    build_req = make_iris_build_request(
        req_id="TEST_ID",
        context_id=id_resp.context_id,
        seed_configs_file=seed_configs_file,
    )
    build_resp = start_iris_build_job(build_req)
    if build_resp.success:
        print("Started IRIS job successfully")
    else:
        print(f"IRIS job failed to start: {build_resp.msg}")


if __name__ == "__main__":
    run()
