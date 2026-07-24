import { Route } from "react-router";
import { DashboardIndex } from "./DashboardIndex";
import { RoleDashboard } from "./RoleDashboard";
import { roleDashboardProfiles } from "./roleDashboardMatrix";

export const crownDashboardRouteElements = (
  <>
    <Route path="/dashboards" element={<DashboardIndex />} />
    {roleDashboardProfiles.map((profile) => (
      <Route
        key={profile.key}
        path={profile.route}
        element={<RoleDashboard roleKey={profile.key} />}
      />
    ))}
  </>
);