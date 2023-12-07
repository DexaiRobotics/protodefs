/*
 * Copyright © 2023 Dexai Robotics. All rights reserved.
 */

/// @file planner_client.cc
#include "client.h"

using grpc::ClientContext;
using grpc::Status;

proto::SystemConf FromSysConf(const system_conf_t& sys_conf) {
  proto::SystemConf sys_conf_pb;
  for (const auto& [robot, conf] : sys_conf) {
    proto::Conf conf_pb;
    *conf_pb.mutable_data() = {conf.begin(), conf.end()};
    (*sys_conf_pb.mutable_data())[robot] = conf_pb;
  }
  return sys_conf_pb;
}

proto::AngleBetweenVectorsConstraint ConstructAngleBetweenVectorsConstraint(
    const std::string& frame_A, const std::string& frame_B,
    const point_3d_t& a_A, const point_3d_t& b_B,
    const double angle_tolerance) {
  proto::AngleBetweenVectorsConstraint constraint;
  constraint.set_frame_a(frame_A);
  constraint.set_frame_b(frame_B);
  *constraint.mutable_a_a() = {a_A.begin(), a_A.end()};
  *constraint.mutable_b_b() = {b_B.begin(), b_B.end()};
  constraint.set_angle_lower(0);
  constraint.set_angle_upper(std::abs(angle_tolerance));
  return constraint;
}

proto::PositionConstraint ConstructPositionConstraint(
    const std::string& frame_A, const std::string& frame_B,
    const point_3d_t& p_AQ_lower, const point_3d_t& p_AQ_upper) {
  proto::PositionConstraint constraint;
  constraint.set_frame_a(frame_A);
  constraint.set_frame_b(frame_B);

  *constraint.mutable_p_aq_lower() = {p_AQ_lower.begin(), p_AQ_lower.end()};
  *constraint.mutable_p_aq_upper() = {p_AQ_upper.begin(), p_AQ_upper.end()};
  // we always use the origin of frame B
  const point_3d_t p_BQ {0., 0., 0.};
  *constraint.mutable_p_bq() = {p_BQ.begin(), p_BQ.end()};
  return constraint;
}

// PPType ToPwisePoly(const proto::Poly& poly_pb) {
//   std::vector<double> breaks {poly_pb.breaks().begin(),
//   poly_pb.breaks().end()}; std::vector<Eigen::VectorXd> coeffs; for (const
//   auto& coeff : poly_pb.coeffs()) {
//     coeffs.push_back(dru::v_to_e(
//         std::vector<double>(coeff.data().begin(), coeff.data().end())));
//   }
//   auto info {drake::trajectories::PiecewisePolynomialInfo(
//       breaks, poly_pb.rows(), poly_pb.cols(), coeffs)};
//   return info.GetTrajectory();
// }
//
// system_poly_t ToSysPoly(const proto::SysPoly& sys_poly_pb) {
//   system_poly_t sys_poly;
//   for (const auto& [robot, poly_pb] : sys_poly_pb.data()) {
//     sys_poly.emplace(robot, ToPwisePoly(poly_pb));
//   }
//   return sys_poly;
// }

bool MotionPlannerClient::SendStartRequest(const StartPlanRequest& req,
                                           StartPlanResponse* resp) {
  ClientContext context;
  Status status {stub_->HandleStartRequest(&context, req, resp)};
  if (!status.ok()) {
    std::cout << "MotionPlannerClient:SendStartRequest: RPC failed with error: "
              << status.error_message() << std::endl;
    return false;
  }
  std::cout << "MotionPlannerClient:SendStartRequest: Successfully "
               "sent request to server"
            << std::endl;
  return true;
}

bool MotionPlannerClient::SendRetrieveRequest(const RetrievePlanRequest& req,
                                              RetrievePlanResponse* resp) {
  ClientContext context;
  Status status {stub_->HandleRetrieveRequest(&context, req, resp)};
  if (!status.ok()) {
    std::cout
        << "MotionPlannerClient:SendRetrieveRequest: RPC failed with error: "
        << status.error_message() << std::endl;
    return false;
  }
  std::cout << "MotionPlannerClient:SendRetrieveRequest: "
               "Successfully sent request to server"
            << std::endl;
  return true;
}
