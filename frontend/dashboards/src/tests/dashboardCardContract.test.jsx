// @vitest-environment jsdom
import { cleanup, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';
import dashboardRegistry from '../config/dashboardRegistry';
import CrownLaunchDashboardPage from '../pages/CrownLaunchDashboardPage.jsx';
import CrownLaunchModulePage from '../pages/CrownLaunchModulePage.jsx';
import TeacherDashboard from '../pages/TeacherDashboard.jsx';
import ParentDashboard from '../pages/ParentDashboard.jsx';
import StudentDashboard from '../pages/StudentDashboard.jsx';

afterEach(() => {
  cleanup();
});

describe('dashboard registry contract', () => {
  it('all dashboards have a title', () => {
    for (const item of dashboardRegistry) {
      expect(Boolean(item.title)).toBe(true);
    }
  });

  it('all dashboards have a path', () => {
    for (const item of dashboardRegistry) {
      expect(Boolean(item.path)).toBe(true);
    }
  });

  it('all dashboard paths are unique', () => {
    const paths = dashboardRegistry.map((item) => item.path);
    expect(new Set(paths).size).toBe(paths.length);
  });

  it('launch dashboard renders the canonical CROWN shell without legacy fallback chrome', () => {
    render(<CrownLaunchDashboardPage activePath="/admin" />);

    expect(screen.getByText('CROWN')).toBeTruthy();
    expect(screen.getAllByText('Christian School Management Solution').length).toBeGreaterThan(0);
    expect(screen.getByText('Good morning, Sarah!')).toBeTruthy();
    expect(screen.getAllByText('Heritage Christian Academy').length).toBeGreaterThan(0);
    expect(screen.getByText('Sandbox preview data shown. Connect backend for live records.')).toBeTruthy();

    expect(screen.getByText('Total Students')).toBeTruthy();
    expect(screen.getByText('1,248')).toBeTruthy();
    expect(screen.getByText('Faculty & Staff')).toBeTruthy();
    expect(screen.getByText('156')).toBeTruthy();
    expect(screen.getByText('Attendance Rate')).toBeTruthy();
    expect(screen.getByText('96.2%')).toBeTruthy();
    expect(screen.getByText('Tuition Collected')).toBeTruthy();
    expect(screen.getByText('$2.4M')).toBeTruthy();

    expect(screen.queryByText('Offline / Fallback')).toBeNull();
    expect(screen.queryByText('Build: missing')).toBeNull();
    expect(screen.queryByText('Dashboard unavailable')).toBeNull();
    expect(screen.queryByText('Dev JWT Login')).toBeNull();
  });

  it('module launch pages render through the same template shell', () => {
    render(<CrownLaunchModulePage moduleKey="gradebook" activePath="/gradebook" />);

    expect(screen.getByText('CROWN')).toBeTruthy();
    expect(screen.getAllByText('Christian School Management Solution').length).toBeGreaterThan(0);
    expect(screen.getByText('Academic Performance View')).toBeTruthy();
    expect(screen.getByText('Assignments Graded')).toBeTruthy();
  });

  it('teacher, parent, and student routes use canonical shared shell', () => {
    const { unmount } = render(<TeacherDashboard />);
    expect(screen.getByText('Teacher Dashboard')).toBeTruthy();
    expect(screen.getByText('Classes Today')).toBeTruthy();
    unmount();

    const parentRender = render(<ParentDashboard />);
    expect(screen.getByText('Parent Dashboard')).toBeTruthy();
    expect(screen.getByText('Children Enrolled')).toBeTruthy();
    parentRender.unmount();

    render(<StudentDashboard />);
    expect(screen.getByText('Student Dashboard')).toBeTruthy();
    expect(screen.getByText('Current Average')).toBeTruthy();
  });
});
