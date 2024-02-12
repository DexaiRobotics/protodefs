
#include "client.h"

int main(int argc, char* argv[]) {
  const std::string robot_name {"robot_arm"};
  const std::string system_name {"test-system"};
  const std::string model_directive {"example_geometry"};
  const std::string address {"localhost:5050"};
  const robot_conf_t start {}, goal {};

  MotionPlannerClient client {address};
  StartPlanRequest start_req;
  // ID
  start_req.set_id("test_id");
  // problem definition
  proto::ProblemDef def;
  def.set_name("plan");
  *def.mutable_goal() = FromSysConf({{robot_name, goal}});
  *def.mutable_start() = FromSysConf({{robot_name, start}});
  *start_req.mutable_def() = def;
  // parameters specifying system geometry
  start_req.mutable_params()->set_system_name(system_name);
  start_req.mutable_params()->set_model_directive(model_directive);
  start_req.mutable_params()->set_robot_name(robot_name);
  StartPlanResponse start_resp;
  if (!client.SendStartRequest(start_req, &start_resp)) {
    std::cout << "Start RPC call failed!" << std::endl;
  }
  const auto id {start_resp.id()};

  RetrievePlanRequest retrieve_req;
  retrieve_req.set_id(id);
  retrieve_req.set_retrieve_type(RetrieveType::BLOCKING);
  RetrievePlanResponse retrieve_resp;
  if (!client.SendRetrieveRequest(retrieve_req, &retrieve_resp)) {
    std::cout << "Retrieval RPC call failed!" << std::endl;
  }
  // const auto sys_poly {ToSysPoly(resp.plan())};

  // TODO(@davebambrick): "run" and display the trajectory
  return 0;
}
