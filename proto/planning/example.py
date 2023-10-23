import grpc
from api_pb2_grpc import (
    StartPlanRequest,
    StartPlanResponse,
    RetrievePlanRequest,
    RetrievePlanResponse,
    RetrieveType,
    PositionConstraint,
)

# initialize the channel
channel = grpc.insecure_channel("localhost:5050")
stub = api_pb2_grpc.MotionPlanner(channel)

params = Params()
params.system_name = "dexai-alfred"
params.urdf = "some_urdf.urdf"

pdef = ProblemDef()
pdef.name = "plan"
pdef.start = some_start
pdef.goal = some_goal
# simple bounding box constraint over the bowl
pc = PositionConstraint()
pc.frame_A = "franka_head"
pc.frame_B = "bowl_center_location"
pc.p_AQ_lower = [-0.1, -0.1, -0.02]
pc.p_AQ_upper = [0.1, 0.1, 1.0]
pc.p_BQ = [0, 0, 0]

start_req = StartPlanRequest()
start_req.id = unique_id
start_req.constraints.append(pc)

stub.HandleStartPlanRequest(start_req)

retrieve_req = RetrievePlanRequest()
retrieve_req.id = unique_id
retrieve_req.retrieve_type = RetrieveType.BLOCKING

resp = stub.HandleRetrievePlanRequest(retrieve_req)

visualizer.display(resp.plan)
