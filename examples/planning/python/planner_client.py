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

from build.basic_types_pb2 import PlanContextId, ProblemDef
from build.planner_pb2 import StartPlanRequest, RetrievePlanRequest
from build.planner_pb2_grpc import MotionPlannerStub


def make_start_plan_request(
    req_id: str,
    context_id: PlanContextId,
) -> StartPlanRequest:
    """Make a Protobuf request message to generate a set of IRIS regions for a
    unique planning context and set of seed data.

    Args:
        context_id (types_pb2.PlanContextId): unique ID for the target context
        seed_data_file (str): file containing seed configuration data

    Returns:
        builder_pb2.StartBuildFromConfsRequest
    """
    return StartPlanRequest(id=req_id, context_id=context_id)


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
