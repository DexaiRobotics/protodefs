/// @file client.h

#include <grpc/grpc.h>
#include <grpcpp/channel.h>
#include <grpcpp/client_context.h>
#include <grpcpp/create_channel.h>
#include <grpcpp/security/credentials.h>

#include "proto/planning/api.grpc.pb.h"

// aliases for readability
using plan_id_t = uint16_t;
using robot_conf_t = std::vector<double>;
using system_conf_t = std::map<std::string, robot_conf_t>;
using point_3d_t = std::array<3, double>;

using proto::MotionPlanner;
using proto::RetrievePlanRequest;
using proto::RetrievePlanResponse;
using proto::RetrieveType;
using proto::StartPlanRequest;
using proto::StartPlanResponse;
/** Convert a system configuration to its corresponding protobuf message. */
proto::SystemConf FromSysConf(const system_conf_t& sys_conf);

/** Construct an angle constraint from its constituent arguments. */
proto::AngleBetweenVectorsConstraint ConstructAngleBetweenVectorsConstraint(
    const std::string& frame_A, const std::string& frame_B,
    const point_3d_t& a_A, const point_3d_t& b_B, const double angle_tolerance);

/** Construct a position (bounding box) constraint from its constituent
 * arguments. */
proto::PositionConstraint ConstructPositionConstraint(
    const std::string& frame_A, const std::string& frame_B,
    const point_3d_t& p_AQ_lower, const point_3d_t& p_AQ_upper);

/** Convert a protobuf message representing a piecewise polynomial to its
 * corresponding Drake counterpart. */
PPType ToPwisePoly(const proto::Poly& poly_pb);
/** Convert a protobuf message representing a "system polynomial" to its
 * corresponding Drake counterpart. */
system_poly_t ToSysPoly(const proto::SysPoly& sys_poly_pb);

/**
 * @brief A simple client which can publish
 *
 */
class MotionPlannerClient {
 public:
  MotionPlannerClient(const std::string& addr) {
    channel_ =
        grpc::CreateCustomChannel(addr, grpc::InsecureChannelCredentials());
    stub_ = MotionPlanner::NewStub(channel_);
  }

 private:
  /**
   * @brief Return a new ID
   */
  inline plan_id_t new_request_id() {
    return last_id_++;
  }
  /**
   * @brief Send a StartPlanRequest to the planning service, and populate a
   * StartPlanResponse with the results.
   *
   * @param req Request containing all information to solve a given planning
   * problem
   * @param resp Response with success and additional error information on
   * failure
   * @return bool indicating success
   */
  bool SendStartRequest(const StartPlanRequest& req, StartPlanResponse* resp);
  /**
   * @brief Send a RetrievePlanRequest to the planning service, and populate a
   * RetrievePlanResponse with the results.
   *
   * @param req Request containing all information to retrieve a given
   * planning problem
   * @param resp Response containing serialized plan on success and additional
   * information on failure
   *
   * @return bool indicating success
   */
  bool SendRetrieveRequest(const RetrievePlanRequest& req,
                           RetrievePlanResponse* resp);

  std::atomic<plan_id_t> last_id_ {0};
  std::shared_ptr<grpc::Channel> channel_;
  std::unique_ptr<MotionPlanner::Stub> stub_;
};
