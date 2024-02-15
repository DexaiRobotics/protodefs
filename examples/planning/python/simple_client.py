import grpc
import sys
import yaml
import os
import click
import os.path
from typing import List, Tuple, Union

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(os.path.dirname(ROOT_DIR), "data")
BUILDFILES_DIR = os.path.join(ROOT_DIR, "build")
if BUILDFILES_DIR not in sys.path:
    sys.path.append(BUILDFILES_DIR)

from build.types_pb2 import (
    Constraints,
    Model,
    SystemConf,
    SystemConfEdge,
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
from build.builder_pb2 import (
    StartBuildFromConfsRequest,
    StartBuildFromEdgesRequest,
    StartBuildResponse,
)
from build.builder_pb2_grpc import IrisBuilderStub


# YAML overhead for DMDs
class RotationTag(yaml.YAMLObject):
    yaml_tag = "!Rpy"

    def __init__(self, rot):
        self.rot = rot

    def __repr__(self):
        v = os.environ.get(self.rot) or ""
        return "RPY"

    @classmethod
    def from_yaml(cls, loader, node):
        return "RPY"

    @classmethod
    def to_yaml(cls, dumper, data):
        return dumper.represent_scalar(cls.yaml_tag, data.rot)


# Required for safe_load
yaml.SafeLoader.add_constructor("!Rpy", RotationTag.from_yaml)


def make_position_constraint_msg(
    frame_A: str,
    frame_B: str,
    p_AQ_lower: Tuple[float, float, float],
    p_AQ_upper: Tuple[float, float, float],
    p_BQ: Tuple[float, float, float],
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
        p_BQ (Tuple[float, float, float]): The position of the point Q, rigidly
        attached to frame B, measured and expressed in frame B.

    Returns:
        types_pb2.PositionConstraint
    """
    return PositionConstraint(
        frame_A=frame_A,
        frame_B=frame_B,
        p_AQ_lower=p_AQ_lower,
        p_AQ_upper=p_AQ_upper,
        p_BQ=p_BQ,
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
    and a vector b, where a is fixed to a frame A, while b is fixed to a frame B.


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
    if "position_constraints" in data:
        for constraint in data["position_constraints"]:
            pos_constraints.append(
                make_position_constraint_msg(
                    frame_A=constraint["frame_A"],
                    frame_B=constraint["frame_B"],
                    p_AQ_lower=constraint["position_AQ_lower"],
                    p_AQ_upper=constraint["position_AQ_upper"],
                    p_BQ=constraint["position_BQ"],
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


def make_models(dmd_file: str, urdf_dir: str) -> List[Model]:
    """Make a vector of Protobuf messages of robot models for all URDFs
    located at the target directory.

    Args:
        urdf_dir (str): Directory containing all URDF data

    Returns:
        Vector[types_pb2.Model]
    """
    models = []
    with open(dmd_file) as f:
        dmd_yaml = yaml.safe_load(f)
    for d in dmd_yaml["directives"]:
        if "add_model" in d:
            urdf_full = d["add_model"]["file"]
            urdf_fname = urdf_full.split("/")[-1]
            urdf_path = os.path.join(urdf_dir, urdf_fname)
            if not os.path.isfile(urdf_path):
                raise FileNotFoundError(f"The URDF {urdf_path} could not be found!")
            models.append(
                Model(
                    name=urdf_fname[: urdf_fname.find(".urdf")],
                    urdf_raw=raw_file_contents(urdf_path),
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
        located. This MUST match the package provided for ALL models defined
        in the DMD.
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
        models=make_models(dmd_file, urdf_dir),
        constraints=make_constraints_msg_from_yaml(constraints_file),
    )


def make_sysconf_msg(sysconf_yaml):
    sysconf_data = {}
    for robot, conf_list in sysconf_yaml.items():
        conf_data = [c for c in conf_list]
        sysconf_data[robot] = Conf(data=conf_data)
    sysconf = SystemConf(data=sysconf_data)
    return sysconf


def make_build_from_confs_request(
    req_id: str,
    context_id: PlanContextId,
    seed_data_file: str,
) -> StartBuildFromConfsRequest:
    """Make a Protobuf request message to generate a set of IRIS regions for a
    unique planning context and set of seed data.

    Args:
        context_id (types_pb2.PlanContextId): unique ID for the target context
        seed_data_file (str): file containing seed configuration data

    Returns:
        builder_pb2.StartBuildFromConfsRequest
    """
    seed_configs = []
    with open(seed_data_file) as f:
        data = yaml.safe_load(f)
        for _, sysconf in data.items():
            seed_configs.append(make_sysconf_msg(sysconf))
    return StartBuildFromConfsRequest(
        id=req_id, context_id=context_id, seed_configs=seed_configs
    )


def make_build_from_edges_request(
    req_id: str,
    context_id: PlanContextId,
    seed_data_file: str,
) -> StartBuildFromEdgesRequest:
    """Make a Protobuf request message to generate a set of IRIS regions for a
    unique planning context and set of seed data.

    Args:
        context_id (types_pb2.PlanContextId): unique ID for the target context
        seed_data_file (str): file containing seed configuration data

    Returns:
        builder_pb2.StartBuildFromConfsRequest
    """
    seed_edges = []
    with open(seed_data_file) as f:
        data = yaml.safe_load(f)
        for edge in data["edges"]:
            v1 = make_sysconf_msg(edge["u"])
            v2 = make_sysconf_msg(edge["v"])
            edge_msg = SystemConfEdge(v1=v1, v2=v2)
            seed_edges.append(edge_msg)
    return StartBuildFromEdgesRequest(
        id=req_id, context_id=context_id, seed_edges=seed_edges
    )


def get_plan_context_id(req: RegisterPlanContextRequest) -> RegisterPlanContextResponse:
    """Send a populated request to the plan context registry service."""
    with grpc.insecure_channel("0.0.0.0:5151") as channel:
        stub = PlanContextRegistryStub(channel)
        return stub.HandleRegisterPlanContextRequest(req)


def start_iris_build_from_edges(
    req: StartBuildFromEdgesRequest,
) -> StartBuildResponse:
    """Send a populated request to the IRIS generation service."""
    with grpc.insecure_channel("0.0.0.0:5150") as channel:
        stub = IrisBuilderStub(channel)
        return stub.HandleStartBuildFromEdgesRequest(req)


def start_iris_build_from_confs(
    req: StartBuildFromConfsRequest,
) -> StartBuildResponse:
    """Send a populated request to the IRIS generation service."""
    with grpc.insecure_channel("0.0.0.0:5150") as channel:
        stub = IrisBuilderStub(channel)
        return stub.HandleStartBuildFromConfsRequest(req)


@click.group(invoke_without_command=True)
@click.option(
    "-s",
    "--system_name",
    default="kuka-iiwa",
    type=str,
    help="""Top-level namespace under which all underlying data is stored""",
)
@click.option(
    "-p",
    "--package_name",
    default="iiwa_models",
    type=str,
    help="""Package name under which all constituent modles must be located.
    This name MUST MATCH the package name of all model paths in the DMD.""",
)
@click.option(
    "-d",
    "--dmd",
    default=os.path.join(DATA_DIR, "dmd", "iiwa_boxes.dmd.yaml"),
    type=str,
    help="Path to target DMD file",
)
@click.option(
    "-c",
    "--constraints",
    default=os.path.join(DATA_DIR, "constraints", "default.yaml"),
    type=str,
    help="Path to target constraints file",
)
@click.option(
    "-u",
    "--urdf_dir",
    default=os.path.join(DATA_DIR, "urdf"),
    type=str,
    help="Path to directory in which the URDFs used by the DMD can be found for upload",
)
@click.option(
    "--seed_data_file",
    default=os.path.join(DATA_DIR, "key_configs.yaml"),
    type=str,
    help="Path to file containing seed data",
)
@click.option(
    "--from-edges/--from-confs",
    default=False,
    help="Whether or not the desired request is sending conf (point) or edge data.",
)
def run(
    system_name, package_name, dmd, constraints, urdf_dir, seed_data_file, from_edges
) -> None:

    # construct and send the ID request
    id_req = make_id_request(
        system_name=system_name,
        package_name=package_name,  # this must match the package in the DMD
        dmd_file=dmd,
        urdf_dir=urdf_dir,
        constraints_file=constraints,
    )
    id_resp = get_plan_context_id(id_req)
    print(f"Got ID: {id_resp.context_id.value}")
    # construct and send the IRIS build request
    print("Constructing build request...")
    if from_edges:
        build_req = make_build_from_edges_request(
            req_id="TEST_ID",
            context_id=id_resp.context_id,
            seed_data_file=seed_data_file,
        )
        print("Sending request...")
        build_resp = start_iris_build_from_edges(build_req)
    else:
        build_req = make_build_from_confs_request(
            req_id="TEST_ID",
            context_id=id_resp.context_id,
            seed_data_file=seed_data_file,
        )
        print("Sending request...")
        build_resp = start_iris_build_from_confs(build_req)

    if build_resp.success:
        print("Started IRIS job successfully")
    else:
        print(f"IRIS job failed to start: {build_resp.msg}")


if __name__ == "__main__":
    run()
