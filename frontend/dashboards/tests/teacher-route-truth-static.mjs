/* global console */

import fs from 'node:fs';
import path from 'node:path';
import process from 'node:process';
import { fileURLToPath } from 'node:url';
import teacherDashboard from '../src/config/dashboardTemplates/teacherDashboard.js';
import { PATHS } from '../src/routes/paths.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, '..', '..', '..');
const routerPath = path.join(repoRoot, 'frontend', 'dashboards', 'src', 'routes', 'router.jsx');
const routeContractPath = path.join(repoRoot, 'docs', 'completion', '04-ROUTE-CONTRACT.md');
const routerSource = fs.readFileSync(routerPath, 'utf8');
const routeContract = fs.readFileSync(routeContractPath, 'utf8');

const failures = [];

function literalPathCount(routePath) {
  const needle = `path: '${routePath}'`;
  return routerSource.split(needle).length - 1;
}

function blockFromNeedle(needle) {
  const start = routerSource.indexOf(needle);
  if (start === -1) return '';
  const tail = routerSource.slice(start);
  const nextBlock = tail.indexOf('\n  {', needle.length);
  return nextBlock === -1 ? tail : tail.slice(0, nextBlock);
}

function expect(condition, message) {
  if (!condition) failures.push(message);
}

const requiredRoutes = [
  { path: '/teacher', needle: "path: '/teacher'," },
  { path: '/teacher/dashboard', needle: "path: '/teacher/dashboard'," },
  { path: '/teacher/attendance', needle: "path: '/teacher/attendance'," },
  { path: '/teacher/gradebook', needle: 'path: PATHS.TEACHER_GRADEBOOK,' },
  { path: '/teacher/classes', needle: 'path: PATHS.TEACHER_CLASSES,' },
  { path: '/teacher/lesson-plans', needle: "path: '/teacher/lesson-plans'," },
  { path: '/teacher/curriculum', needle: 'path: PATHS.TEACHER_CURRICULUM,' },
  { path: '/teacher/communications', needle: 'path: PATHS.TEACHER_COMMUNICATIONS,' },
  { path: '/teacher/student-support', needle: 'path: PATHS.TEACHER_STUDENT_SUPPORT,' },
  { path: '/teacher/discipline', needle: 'path: PATHS.TEACHER_DISCIPLINE,' },
  { path: '/teacher/remote-day', needle: 'path: PATHS.TEACHER_REMOTE_DAY,' },
];

for (const entry of requiredRoutes) {
  expect(routerSource.includes(entry.needle), `Missing route declaration for ${entry.path}`);
}

expect(literalPathCount('/teacher/attendance') === 1, 'Expected exactly one /teacher/attendance route declaration');

const teacherAttendanceBlock = blockFromNeedle("path: '/teacher/attendance',");
expect(teacherAttendanceBlock.includes('<TeacherAttendancePage />'), '/teacher/attendance does not render TeacherAttendancePage');
expect(teacherAttendanceBlock.includes('<RoleGuard allowedRoles={ROLE_GROUPS.ACADEMIC_TEAM}>'), '/teacher/attendance is missing academic-team RoleGuard');

const teacherBlock = blockFromNeedle("path: '/teacher',");
expect(teacherBlock.includes('<TeacherDashboard />'), '/teacher does not render TeacherDashboard');

const teacherDashboardBlock = blockFromNeedle("path: '/teacher/dashboard',");
expect(teacherDashboardBlock.includes('<TeacherDashboard />'), '/teacher/dashboard does not render TeacherDashboard');

const teacherGradebookBlock = blockFromNeedle('path: PATHS.TEACHER_GRADEBOOK,');
expect(teacherGradebookBlock.includes('<Navigate to="/gradebook" replace />'), '/teacher/gradebook is not an explicit alias to /gradebook');

const duplicateTeacherRoutes = requiredRoutes
  .filter((entry) => entry.needle.startsWith("path: '/"))
  .filter((entry) => literalPathCount(entry.path) > 1)
  .map((entry) => entry.path);
expect(duplicateTeacherRoutes.length === 0, `Duplicate literal teacher routes found: ${duplicateTeacherRoutes.join(', ')}`);

const knownRoutes = new Set(Object.values(PATHS));
const dashboardLinks = [];
for (const module of teacherDashboard.commandModules ?? []) {
  if (module.primaryActionHref) dashboardLinks.push(module.primaryActionHref);
  if (module.backActionHref) dashboardLinks.push(module.backActionHref);
}
for (const action of teacherDashboard.quickActions ?? []) {
  if (action.href) dashboardLinks.push(action.href);
}

for (const href of dashboardLinks) {
  const isKnown = knownRoutes.has(href) || href.startsWith('/academics/teacher-grading') || href === '/teacher/calendar-assignments';
  expect(isKnown, `Teacher dashboard action points to unknown route: ${href}`);
}

const pendingRoutes = ['/teacher/student-support', '/teacher/discipline', '/teacher/remote-day'];
for (const pendingRoute of pendingRoutes) {
  const block = blockFromNeedle(`path: PATHS.${pendingRoute.replace('/teacher/', 'TEACHER_').replace(/-/g, '_').toUpperCase()},`);
  expect(block.includes('TeacherWorkflowPending'), `${pendingRoute} is not routed to explicit pending workflow state`);
}

const lessonPlansBlock = blockFromNeedle("path: '/teacher/lesson-plans',");
expect(lessonPlansBlock.includes('TeacherWorkflowPending'), '/teacher/lesson-plans is not routed to explicit pending workflow state');

for (const route of ['/teacher', '/teacher/dashboard', '/teacher/attendance', '/teacher/gradebook']) {
  expect(routeContract.includes(`| ${route} |`), `Route contract missing row for ${route}`);
}

if (failures.length > 0) {
  console.error('TEACHER_ROUTE_TRUTH_STATIC_FAIL');
  for (const failure of failures) {
    console.error(`- ${failure}`);
  }
  process.exit(1);
}

console.log('TEACHER_ROUTE_TRUTH_STATIC_PASS');
console.log(`Verified routes: ${requiredRoutes.map((entry) => entry.path).join(', ')}`);
console.log(`Validated dashboard links: ${dashboardLinks.length}`);
