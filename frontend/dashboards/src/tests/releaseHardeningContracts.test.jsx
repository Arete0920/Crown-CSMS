import { describe, expect, it } from 'vitest';
import { readFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { isRoleAllowed } from '../routes/roleGuardRules';
import { ROLE_GROUPS } from '../routes/routeGroups';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const routerPath = path.resolve(__dirname, '../routes/router.jsx');
const routerSource = readFileSync(routerPath, 'utf8');

function extractRouteBlock(routePath) {
  const startNeedle = `path: '${routePath}',`;
  const start = routerSource.indexOf(startNeedle);
  if (start === -1) {
    return '';
  }

  const tail = routerSource.slice(start);
  const nextBlock = tail.indexOf('\n  {', startNeedle.length);
  return nextBlock === -1 ? tail : tail.slice(0, nextBlock);
}

function extractRouteBlockByNeedle(startNeedle) {
  const start = routerSource.indexOf(startNeedle);
  if (start === -1) {
    return '';
  }

  const tail = routerSource.slice(start);
  const nextBlock = tail.indexOf('\n  {', startNeedle.length);
  return nextBlock === -1 ? tail : tail.slice(0, nextBlock);
}

describe('release route hardening contract', () => {
  it('keeps /teacher/attendance route declared', () => {
    expect(routerSource.includes("path: '/teacher/attendance',")).toBe(true);
  });

  it('guards /teacher/attendance with academic team roles', () => {
    const block = extractRouteBlock('/teacher/attendance');
    expect(block.includes('<RoleGuard allowedRoles={ROLE_GROUPS.ACADEMIC_TEAM}>')).toBe(true);
    expect(block.includes('<TeacherAttendancePage />')).toBe(true);
  });

  it('guards /teacher with academic team roles', () => {
    const block = extractRouteBlock('/teacher');
    expect(block.includes('<RoleGuard allowedRoles={ROLE_GROUPS.ACADEMIC_TEAM}>')).toBe(true);
    expect(block.includes('<TeacherDashboard />')).toBe(true);
  });

  it('guards /teacher/dashboard with academic team roles', () => {
    const block = extractRouteBlock('/teacher/dashboard');
    expect(block.includes('<RoleGuard allowedRoles={ROLE_GROUPS.ACADEMIC_TEAM}>')).toBe(true);
    expect(block.includes('<TeacherDashboard />')).toBe(true);
  });

  it('guards /parent/attendance with parent route guard', () => {
    const block = extractRouteBlock('/parent/attendance');
    expect(block.includes('<RoleRouteGuard allowedRoles={["parent"]}>')).toBe(true);
    expect(block.includes('<ParentAttendancePage />')).toBe(true);
  });

  it('guards /parent with parent route guard', () => {
    const block = extractRouteBlock('/parent');
    expect(block.includes('<RoleRouteGuard allowedRoles={["parent"]}>')).toBe(true);
    expect(block.includes('<ParentDashboard />')).toBe(true);
  });

  it('guards /parent/dashboard with parent route guard', () => {
    const block = extractRouteBlock('/parent/dashboard');
    expect(block.includes('<RoleRouteGuard allowedRoles={["parent"]}>')).toBe(true);
    expect(block.includes('<ParentDashboard />')).toBe(true);
  });

  it('guards /parent/students/:id with parent route guard and journey gate', () => {
    const block = extractRouteBlock('/parent/students/:id');
    expect(block.includes('<RoleRouteGuard allowedRoles={["parent"]}>')).toBe(true);
    expect(block.includes('<ParentJourneyRouteGuard stage="activeStudent">')).toBe(true);
    expect(block.includes('<ParentStudent360Page />')).toBe(true);
  });

  it('keeps /teacher/lesson-plans guarded for academic team', () => {
    const block = extractRouteBlock('/teacher/lesson-plans');
    expect(block.includes('<RoleGuard allowedRoles={ROLE_GROUPS.ACADEMIC_TEAM}>')).toBe(true);
    expect(block.includes('<ClassroomsDashboard />')).toBe(true);
  });

  it('keeps /classrooms guarded for parent journey access', () => {
    const block = extractRouteBlockByNeedle('path: PATHS.CLASSROOMS,');
    expect(block.includes('<RoleRouteGuard allowedRoles={["parent"]}>')).toBe(true);
    expect(block.includes('<ParentJourneyRouteGuard stage="classAssignment">')).toBe(true);
    expect(block.includes('<ClassroomsDashboard />')).toBe(true);
  });

  it('keeps /teacher/curriculum guarded for academic team', () => {
    const block = extractRouteBlock('/teacher/curriculum');
    expect(block.includes('<RoleGuard allowedRoles={ROLE_GROUPS.ACADEMIC_TEAM}>')).toBe(true);
    expect(block.includes('<CurriculumPDDashboard />')).toBe(true);
  });

  it('keeps /teacher/calendar-assignments guarded for academic team', () => {
    const block = extractRouteBlock('/teacher/calendar-assignments');
    expect(block.includes('<RoleGuard allowedRoles={ROLE_GROUPS.ACADEMIC_TEAM}>')).toBe(true);
    expect(block.includes('<SchedulingDashboard />')).toBe(true);
  });
});

describe('release role-behavior guard rules', () => {
  it('allows teacher role for academic team guard', () => {
    expect(isRoleAllowed('teacher', ROLE_GROUPS.ACADEMIC_TEAM)).toBe(true);
  });

  it('blocks parent role for academic team guard', () => {
    expect(isRoleAllowed('parent', ROLE_GROUPS.ACADEMIC_TEAM)).toBe(false);
  });

  it('allows parent role for family-view guard', () => {
    expect(isRoleAllowed('parent', ROLE_GROUPS.FAMILY_VIEW)).toBe(true);
  });

  it('normalizes role casing and whitespace in checks', () => {
    expect(isRoleAllowed('  TeAcHeR  ', ROLE_GROUPS.ACADEMIC_TEAM)).toBe(true);
  });
});
