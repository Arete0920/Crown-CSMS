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

function isValidDashboardTemplate(template) {
  return Boolean(
    template
    && typeof template === 'object'
    && typeof template.title === 'string'
    && Array.isArray(template.metrics)
  );
}

export function getDashboardTemplate(key) {
  const candidate = DASHBOARD_TEMPLATE_MAP[key] || schoolAdministratorDashboard;
  return isValidDashboardTemplate(candidate) ? candidate : schoolAdministratorDashboard;
}
