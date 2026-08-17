// @vitest-environment jsdom
import { cleanup, render, screen } from '@testing-library/react';
import { afterEach, beforeAll, describe, expect, it, vi } from 'vitest';

vi.mock('../utils/authClient', () => ({
  authenticatedJson: vi.fn(),
}));

import { authenticatedJson } from '../utils/authClient';

let SandboxStudentSelfService;
let ParentSandboxDailyPanel;

beforeAll(async () => {
  vi.stubEnv('VITE_SANDBOX_MODE', '1');
  ({ default: SandboxStudentSelfService } = await import('../components/student/SandboxStudentSelfService.jsx'));
  ({ default: ParentSandboxDailyPanel } = await import('../features/parentJourney/ParentSandboxDailyPanel.jsx'));
});

afterEach(() => {
  cleanup();
  authenticatedJson.mockReset();
});

describe('sandbox payload validation', () => {
  it('fails closed instead of rendering a malformed student payload', async () => {
    authenticatedJson.mockResolvedValue({ student: { name: 'Student' } });

    render(<SandboxStudentSelfService />);

    const alert = await screen.findByRole('alert');
    expect(alert.textContent).toContain('Unable to load student self-service data.');
    expect(screen.queryByTestId('student-self-service-name')).toBeNull();
  });

  it('fails closed instead of rendering a malformed parent daily-work payload', async () => {
    authenticatedJson.mockResolvedValue({ child: { name: 'Child' } });

    render(<ParentSandboxDailyPanel />);

    const alert = await screen.findByRole('alert');
    expect(alert.textContent).toContain('Unable to load family daily-work data.');
    expect(screen.queryByTestId('parent-daily-child')).toBeNull();
  });
});
