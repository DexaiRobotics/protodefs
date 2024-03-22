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
IIWA_ID = 16791776422234053788
if BUILDFILES_DIR not in sys.path:
    sys.path.append(BUILDFILES_DIR)

from build.basic_types_pb2 import PlanContextId

from build.visualizer_pb2 import StartVisualizerRequest
from build.visualizer_pb2_grpc import VisualizerStub
from build.basic_types_pb2 import Null


@click.group()
def cli():
    """
    A collection of all client methods to interact with the Visualizer.
    """


@cli.command("start", help="Start the visualizer for the targeted model.")
@click.option(
    "--id",
    type=int,
    help="ID of the planning context which you would like to visualize.",
)
@click.option(
    "--dmd",
    type=str,
    help="Name of the DMD file which you would like to visualize.",
)
@click.option(
    "-f",
    "--force",
    is_flag=True,
    default=False,
    help="Force reload of the visualizer with a new model.",
)
def start(id, dmd, force) -> None:
    print(id, dmd, force)
    if id is not None:
        req = StartVisualizerRequest(
            context_id=PlanContextId(value=id), enable_sliders=True, force_reload=force
        )
    elif dmd is not None:
         req = StartVisualizerRequest(
            dmd_filename=dmd, enable_sliders=True, force_reload=force
        )
    else:
        raise ValueError("A reference to a model was not added to the request!")
    
    with grpc.insecure_channel("0.0.0.0:5550") as channel:
        stub = VisualizerStub(channel)
        resp = stub.StartVisualizer(req)
    print(resp)

@cli.command("stop", help="Stop the visualizer.")
def stop() -> None:
    with grpc.insecure_channel("0.0.0.0:5550") as channel:
        stub = VisualizerStub(channel)
        resp = stub.StopVisualizer(Null())


if __name__ == "__main__":
    cli()
