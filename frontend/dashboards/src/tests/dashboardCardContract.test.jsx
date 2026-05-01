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
    const paths = ['/admin', '/school-admin', '/school-administrator'];

    for (const path of paths) {
      const view = render(<CrownLaunchDashboardPage activePath={path} />);

      expect(screen.getByText('CROWN')).toBeTruthy();
      expect(screen.getAllByText('Christian School Management Solution').length).toBeGreaterThan(0);
      expect(screen.getByText('Good morning, Sarah!')).toBeTruthy();
      expect(screen.getAllByText('Heritage Christian Academy').length).toBeGreaterThan(0);
      expect(screen.getAllByText('Sandbox preview data shown. Connect backend for live records.').length).toBeGreaterThan(0);

      expect(screen.getByText('Total Students')).toBeTruthy();
      expect(screen.getAllByText('Attendance Rate').length).toBeGreaterThan(0);
      expect(screen.getByText('Tuition Collected')).toBeTruthy();
      expect(screen.getByText('Open Admissions')).toBeTruthy();
      expect(screen.getByText('Active Alerts')).toBeTruthy();

      expect(screen.getAllByText('Admissions / Enrollment').length).toBeGreaterThan(0);
      expect(screen.getAllByText('Attendance').length).toBeGreaterThan(0);
      expect(screen.getAllByText('Academics / Gradebook').length).toBeGreaterThan(0);
      expect(screen.getAllByText('Finance / Billing').length).toBeGreaterThan(0);
      expect(screen.getAllByText('Communications').length).toBeGreaterThan(0);
      expect(screen.getAllByText('Staff / HR').length).toBeGreaterThan(0);
      expect(screen.getAllByText('Student Life / Discipline').length).toBeGreaterThan(0);
      expect(screen.getAllByText('Health / Safety').length).toBeGreaterThan(0);
      expect(screen.getAllByText('System / IT / Integrations').length).toBeGreaterThan(0);

      expect(screen.getByText('Prayer Requests')).toBeTruthy();
      expect(screen.getByText('Daily Devotion')).toBeTruthy();
      expect(screen.getByText('Announcements')).toBeTruthy();
      expect(screen.getByText("Today's Calendar")).toBeTruthy();
      expect(screen.getByText('Administrator To-Dos')).toBeTruthy();
      expect(screen.getByText('Communications Inbox')).toBeTruthy();
      expect(screen.getByText('Approvals Needed')).toBeTruthy();
      expect(screen.getByText('Critical Alerts')).toBeTruthy();
      expect(screen.getByText('Mrs. Carter surgery recovery')).toBeTruthy();
      expect(screen.getByText('8 family replies need response')).toBeTruthy();

      expect(screen.queryByText('Offline / Fallback')).toBeNull();
      expect(screen.queryByText('Build: missing')).toBeNull();
      expect(screen.queryByText('Dashboard unavailable')).toBeNull();
      expect(screen.queryByText('Dev JWT Login')).toBeNull();

      view.unmount();
    }
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
