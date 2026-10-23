import { Navigate } from "react-router";
import { PATHS } from "../routes/paths";

/**
 * Historical Master Control URLs must not display illustrative uptime, user,
 * support, certification, or revenue figures as if they were live platform
 * operations. The canonical owner console enforces server-side authority.
 */
export default function MasterControlDashboard() {
  return <Navigate to={PATHS.MASTER_CONTROL} replace />;
}
