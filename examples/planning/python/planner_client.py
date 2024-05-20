import grpc
import sys
import os
import click
import os.path
from typing import Mapping, List, Any
import numpy as np

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(os.path.dirname(ROOT_DIR), "data")
BUILDFILES_DIR = os.path.join(ROOT_DIR, "build")
if BUILDFILES_DIR not in sys.path:
    sys.path.append(BUILDFILES_DIR)

from build.basic_types_pb2 import (
    PlanContextId,
    ProblemDef,
    SystemConf,
    Conf,
    SystemPolynomial,
    PlanType,
    RetrieveType,
)
from build.planner_pb2 import (
    StartPlanRequest,
    StartPlanResponse,
    RetrievePlanRequest,
    RetrievePlanResponse,
)
from build.planner_pb2_grpc import MotionPlannerStub

# the degree of all trajectories returned by our planner
POLYNOMIAL_DEGREE = 4


class PiecewiseCubicPolynomial:
    """Custom implementation for a piecewise polynomial trajectory."""

    def __init__(self, breaks, P_arr: np.ndarray):
        self.degree = POLYNOMIAL_DEGREE
        self.breaks = np.array(breaks)
        self.start, self.end = self.breaks[0], self.breaks[-1]
        if P_arr.shape[-1] != self.degree:
            raise ValueError(
                f"Polynomial array of shape: {P_arr.shape} is not permitted for a cubic piecewise polynomial"
            )
        self.P_arr = P_arr

    def rows(self):
        return self.P_arr.shape[1]

    def cols(self):
        return self.P_arr.shape[2]

    def value(self, t: float) -> np.ndarray:
        """Compute the value of the piecewise polynomial at time t.

        Args:
            t (float): time

        Returns:
            np.ndarray: joint positions at time t
        """
        if t < self.start or t > self.end:
            raise ValueError(
                f"Polynomial is undefined for t={t} outside [{self.start}, {self.end}]!"
            )
        t_vec = np.array([[1, t, t**2, t**3]])
        if t == self.start:
            P_idx = 0
        elif t == self.end:
            P_idx = self.P_arr.shape[0] - 1
        else:
            P_idx = np.searchsorted(self.breaks[:-1], t) - 1
        poly = self.P_arr[P_idx]

        return np.sum(np.dot(poly, t_vec.T), axis=1).T


def convert_piecewise_polynomial(
    system_poly_msg: SystemPolynomial,
) -> Mapping[str, PiecewiseCubicPolynomial]:
    """Convert a system polynomial Protobuf message into a corresponding native
    representation. In our case, we represent each set of polynomials as an
    array of T "breaks" [t_0, t_1, ..., t_T] and a 4-dimensional array of size
    (T-1, R, C, K), where R is the number of joints in the robot, C the number
    of polynomials per joint (typically 1), and K=4 is the degree of each
    individual polynomial.

    Args:
        system_poly_msg (SystemPolynomial): The Protobuf message

    Returns:
        Mapping[str, PiecewiseCubicPolynomial]: Map of robot names to polynomial representations
    """
    system_poly = {}
    for robot, poly_msg in system_poly_msg.data.items():
        t = len(poly_msg.breaks)
        r, c = poly_msg.rows, poly_msg.cols
        P_arr = np.ndarray(shape=[t - 1, r, c, POLYNOMIAL_DEGREE], dtype="float")
        for i in range(t - 1):
            for j in range(r):
                for k in range(c):
                    P_arr[i, j, k] = poly_msg.coeffs[(i * r * c) + (j * c) + k].data
        system_poly[robot] = PiecewiseCubicPolynomial(
            breaks=poly_msg.breaks, P_arr=P_arr
        )
    return system_poly


def positions_from_polynomial(
    system_poly: Mapping[str, PiecewiseCubicPolynomial], sampling_freq_hz: float
) -> Mapping[str, np.ndarray]:
    """Return a trajectory as an array of joint positions sampled from the
    given system polynomial at a frequency in Hz.

    Args:
        system_poly (Mapping[str, Mapping[str, PiecewiseCubicPolynomial]]): Input system polynomial
        sampling_freq_hz (float): Sampling frequency in Hz
    Returns:
        Mapping[str, np.ndarray]: Map of robot names to sampled joint positions
    """
    system_trajectory = {}
    for robot, poly in system_poly.items():
        t = poly.start
        t_final = poly.end
        traj = poly.value(t)
        t += 1.0 / sampling_freq_hz
        while t < t_final:
            traj = np.vstack([traj, poly.value(t)])
            t += 1.0 / sampling_freq_hz
        system_trajectory[robot] = traj
    return system_trajectory


def make_problem_definition(
    name: str,
    start: SystemConf,
    goal: SystemConf,
    context_id: PlanContextId,
) -> ProblemDef:
    """Make a Protobuf message representing a planning problem definition.

    Args:
        name (str): plan name
        start (SystemConf): start system configuration
        goal (SystemConf): goal system configuration
        context_id (PlanContextId): unique identifier

    Returns:
        ProblemDef: _description_
    """
    return ProblemDef(name=name, goal=goal, start=start, context_id=context_id)


def make_start_plan_request(req_id: str, problem_def: ProblemDef) -> StartPlanRequest:
    """Make a Protobuf request message to start a motion plan for a given planning problem definition.

    Args:
        req_id (str): request ID which will be used to retrieve the plan upon completion
        problem_def (types_pb2.ProblemDef): Target planning problem

    Returns:
        planner_pb2.StartPlanRequest
    """
    return StartPlanRequest(id=req_id, problem_def=problem_def)


def make_retrieve_plan_request(
    req_id: str, plan_type: PlanType = PlanType.SYSTEM_POLY, traj_inverval_ms: int = 0
) -> RetrievePlanRequest:
    """Make a Protobuf request message to retrieve a motion plan for a given planning
    problem definition.

    Args:
        req_id (str): request ID to retrieve the completed plan

    Returns:
        planner_pb2.RetrievePlanRequest
    """
    return RetrievePlanRequest(
        id=req_id,
        retrieve_type=RetrieveType.BLOCKING,
        plan_type=plan_type,
        traj_interval_ms=traj_inverval_ms,
    )


def start_plan(req: StartPlanRequest) -> StartPlanResponse:
    """Send a populated start request to the motion planner and return the response."""
    with grpc.insecure_channel("0.0.0.0:5050") as channel:
        stub = MotionPlannerStub(channel)
        try:
            return stub.HandleStartRequest(req)
        except Exception as err:
            print(f"Encountered error starting plan: {err}")
            raise


def retrieve_plan(
    req: RetrievePlanRequest,
) -> RetrievePlanResponse:
    """Send a populated retrieval request to the motion planner and return the response."""
    with grpc.insecure_channel("0.0.0.0:5050") as channel:
        stub = MotionPlannerStub(channel)
        try:
            return stub.HandleRetrieveRequest(req)
        except Exception as err:
            print(f"Encountered error retreiving plan: {err}")
            raise


@click.group(invoke_without_command=True)
@click.option(
    "--context_id",
    type=int,
    help="""Unique identifier for target context""",
)
@click.option(
    "--poly/--traj",
    default=False,
    help="Whether or not the solution is returned as a continuous polynomial or a sequence of waypoints.",
)
@click.option(
    "--interval",
    type=int,
    default=50,
    help="""Sampling interval in milliseconds""",
)
def run(context_id, poly, interval) -> None:
    # example start position for a UR5e robot
    # TODO (@davebambrick): Remove and parameterize

    q_start = [1.045,-1.27,0.5,0.246,0.075,0.182]
    q_goal = [4.586,-0.181,-1.815,-2.818,0.075,-2.61]
    start = SystemConf(data={"ur5e": Conf(data=q_start)})
    goal = SystemConf(data={"ur5e": Conf(data=q_goal)})
    problem_def = make_problem_definition(
        name="test_plan",
        start=start,
        goal=goal,
        context_id=PlanContextId(value=context_id),
    )
    # construct and send the start request
    start_request = make_start_plan_request(req_id="TEST_ID", problem_def=problem_def)
    print(start_request)
    start_resp = start_plan(start_request)
    # construct and send the retrieval request
    type = PlanType.SYSTEM_POLY if poly else PlanType.SYSTEM_TRAJECTORY
    retrieve_request = make_retrieve_plan_request(start_resp.id, type, interval)
    retrieve_resp = retrieve_plan(retrieve_request)
    print(retrieve_request)
    print(retrieve_resp)


if __name__ == "__main__":
    run()
