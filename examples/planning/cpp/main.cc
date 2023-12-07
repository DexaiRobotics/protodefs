
#include "client.h"

int main(int argc, char* argv[]) {
  const std::string& robot_name {"robot_arm"};
  const std::string& system_name {"test-system"};
  const std::string& model_directive {"example_geometry"};
  const robot_conf_t start {}, goal {};

  StartPlanRequest req;

  // ID
  req->set_id(0);
  // problem definition
  proto::ProblemDef def;
  def.set_name(ppd.plan_name);
  *def.mutable_goal() = FromSysConf({{robot_name, goal}});
  *def.mutable_start() = FromSysConf({{robot_name, start}});
  *req->mutable_def() = def;
  // parameters specifying system geometry
  req->mutable_params()->set_system_name(system_name);
  req->mutable_params()->set_model_directive(model_directive);
  req->mutable_params()->set_robot_name(robot_name);
  StartPlanResponse resp;
  if (const auto result {SendStartRequest(req, &resp)}; !result) {
    std::cout << "Start RPC call failed!" << std::endl;
  }
  const auto id {resp.id()};

  RetrievePlanRequest req;
  req.set_id(id);
  req.set_retrieve_type(retrieve_type);
  if (timeout_ms) {
    req.set_timeout_ms(*timeout_ms);
  }
  RetrievePlanResponse resp;
  if (const auto result {SendRetrieveRequest(req, &resp)}; !result) {
    std::cout << "Retrieval RPC call failed!" << std::endl;
  }
  const auto sys_poly {ToSysPoly(resp.plan())};

  // TODO(@davebambrick): "run" and display the trajectory
  return 0;
}
