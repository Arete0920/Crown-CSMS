import React from 'react';
import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import { cleanup, render, screen, fireEvent, waitFor } from '@testing-library/react';
import SectionSchedulerWizard from './SectionSchedulerWizard.jsx';
import { apiFetch } from '../lib/api.js';
vi.mock('../lib/api.js', () => ({ apiFetch: vi.fn() }));
vi.mock('../components/crown/CrownLayout.jsx', () => ({ default: ({ children, title }) => <main><h1>{title}</h1>{children}</main> }));
afterEach(cleanup);
const response = (body, ok = true) => ({ ok, json: async () => body });
beforeEach(() => {
  vi.clearAllMocks();
  apiFetch.mockImplementation(async (url) => {
    if (url.endsWith('scope-options/')) return response({academic_years:[{academic_year_id:'year',name:'2026–2027',is_current:true}],terms:[{term_id:'term',academic_year_id:'year',code:'S1',name:'Semester 1'}]});
    if (url.endsWith('/sessions/')) return response({session_id:'session'});
    if (url.endsWith('/configure/')) return response({status:'configured'});
    if (url.endsWith('/options/')) return response({sections:[{section_id:'section',course_code:'BIBLE',course_name:'Bible'}],rooms:[{room_id:'room',code:'101',name:'Room 101'}],day_templates:[{day_template_id:'day',template_code:'MON',blocks:[{period_block_id:'p1',code:'P1',name:'First'},{period_block_id:'p2',code:'P2',name:'Second'}]}],placements:[{placement_id:'placement',expected_updated_at:'version',section_id:'section',day_template_id:'day',period_block_id:'p1',room_id:'room'}]});
    if (url.endsWith('/commit/')) return response({created:1,updated:1,total:1});
    if (url.endsWith('/verify/')) return response({count:1});
    return response({});
  });
});
async function load() {
  render(<SectionSchedulerWizard />);
  await screen.findByText('Semester 1');
  fireEvent.change(screen.getByLabelText('Term'), {target:{value:'S1'}});
  fireEvent.click(screen.getByRole('button',{name:'Load Schedule'}));
  await screen.findByText('Section Placements');
}
it('loads named scope and publishes a versioned move', async () => {
  await load();
  expect(screen.queryByPlaceholderText('Academic Year ID')).toBeNull();
  fireEvent.change(screen.getByLabelText('Period 1'), {target:{value:'p2'}});
  fireEvent.click(screen.getByRole('button',{name:'Publish Changes'}));
  await screen.findByText('Schedule published');
  const call=apiFetch.mock.calls.find(([url])=>url.endsWith('/sections/'));
  expect(JSON.parse(call[1].body).sections).toEqual([expect.objectContaining({placement_id:'placement',expected_updated_at:'version',period_block_id:'p2'})]);
  fireEvent.click(screen.getByRole('button',{name:'Undo this publication'}));
  await screen.findByText('Publication undone');
});
it('marks one meeting for removal and preserves its identity', async () => {
  await load();
  fireEvent.click(screen.getByRole('button',{name:'Remove'}));
  fireEvent.click(screen.getByRole('button',{name:'Publish Changes'}));
  await screen.findByText('Schedule published');
  const call=apiFetch.mock.calls.find(([url])=>url.endsWith('/sections/'));
  expect(JSON.parse(call[1].body).sections[0]).toMatchObject({action:'remove',placement_id:'placement'});
});
it('shows scope failures instead of invented selections', async () => {
  apiFetch.mockResolvedValue(response({detail:'Permission denied'}, false));
  render(<SectionSchedulerWizard />);
  await waitFor(()=>expect(screen.getByRole('alert').textContent).toContain('Permission denied'));
});

it('keeps a successful publication recoverable if verification fails', async () => {
  const original = apiFetch.getMockImplementation();
  apiFetch.mockImplementation((url, options) => url.endsWith('/verify/')
    ? Promise.resolve(response({detail:'Verification unavailable'}, false)) : original(url, options));
  await load();
  fireEvent.change(screen.getByLabelText('Period 1'), {target:{value:'p2'}});
  fireEvent.click(screen.getByRole('button',{name:'Publish Changes'}));
  await screen.findByText('Schedule published');
  expect(screen.getByRole('button',{name:'Undo this publication'})).toBeTruthy();
  await screen.findByText('Verification unavailable');
});
