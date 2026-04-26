import schoolAdministratorDashboard from './schoolAdministratorDashboard.js';
import teacherDashboard from './teacherDashboard.js';
import parentDashboard from './parentDashboard.js';
import studentDashboard from './studentDashboard.js';
import admissionsDashboard from './admissionsDashboard.js';
import attendanceDashboard from './attendanceDashboard.js';
import gradebookDashboard from './gradebookDashboard.js';
import financeDashboard from './financeDashboard.js';
import communicationsDashboard from './communicationsDashboard.js';

export const DASHBOARD_TEMPLATE_MAP = {
  dashboard: schoolAdministratorDashboard,
  schoolAdministrator: schoolAdministratorDashboard,
  teacher: teacherDashboard,
  parent: parentDashboard,
  student: studentDashboard,
  admissions: admissionsDashboard,
  attendance: attendanceDashboard,
  gradebook: gradebookDashboard,
  finance: financeDashboard,
  communications: communicationsDashboard,
};

export function getDashboardTemplate(key) {
  return DASHBOARD_TEMPLATE_MAP[key] || schoolAdministratorDashboard;
}
