import schoolAdministratorDashboard from './schoolAdministratorDashboard.js';
import teacherDashboard from './teacherDashboard.js';
import parentDashboard from './parentDashboard.js';
import studentDashboard from './studentDashboard.js';
import admissionsDashboard from './admissionsDashboard.js';
import attendanceDashboard from './attendanceDashboard.js';
import gradebookDashboard from './gradebookDashboard.js';
import financeDashboard from './financeDashboard.js';
import communicationsDashboard from './communicationsDashboard.js';
import boardDashboard from './boardDashboard.js';
import itDashboard from './itDashboard.js';
import marketingDashboard from './marketingDashboard.js';
import spiritualLifeDashboard from './spiritualLifeDashboard.js';
import officeDashboard from './officeDashboard.js';
import healthDashboard from './healthDashboard.js';
import counselingDashboard from './counselingDashboard.js';
import foodDashboard from './foodDashboard.js';
import athleticsDashboard from './athleticsDashboard.js';
import registrarDashboard from './registrarDashboard.js';

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
  board: boardDashboard,
  it: itDashboard,
  marketing: marketingDashboard,
  spiritualLife: spiritualLifeDashboard,
  office: officeDashboard,
  health: healthDashboard,
  counseling: counselingDashboard,
  food: foodDashboard,
  athletics: athleticsDashboard,
  registrar: registrarDashboard,
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
