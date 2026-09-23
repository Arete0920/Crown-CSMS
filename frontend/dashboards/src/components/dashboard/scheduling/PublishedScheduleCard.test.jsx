import React from 'react';
import { afterEach, expect, it, vi } from 'vitest';
import { cleanup, render, screen } from '@testing-library/react';
import PublishedScheduleCard from './PublishedScheduleCard.jsx';
import { apiFetch } from '../../../lib/api.js';
vi.mock('../../../lib/api.js', () => ({apiFetch:vi.fn()}));
vi.mock('../../crown/CrownCard.jsx', () => ({default:({children,title})=><section><h2>{title}</h2>{children}</section>}));
afterEach(cleanup);
it('renders only published meeting data', async()=>{
  apiFetch.mockResolvedValue({ok:true,json:async()=>[{section_id:'s',course:{name:'Published Biology'},meetings:[{placement_id:'p',template_code:'MON',start_time:'09:00:00',end_time:'10:00:00',room_code:'LAB'}]}]});
  render(<PublishedScheduleCard />);
  expect(screen.getByRole('status').textContent).toContain('Loading');
  await screen.findByText('Published Biology');
  expect(screen.getByText(/Room LAB/).textContent).toContain('09:00–10:00');
  expect(screen.queryByText('Grade 7 Bible')).toBeNull();
});
it('shows an honest empty state',async()=>{
  apiFetch.mockResolvedValue({ok:true,json:async()=>[]});render(<PublishedScheduleCard />);
  await screen.findByText('No published meetings are available for your account.');
});
it('shows errors without sample classes',async()=>{
  apiFetch.mockResolvedValue({ok:false});render(<PublishedScheduleCard />);
  await screen.findByRole('alert');expect(screen.queryByText('Grade 9 English')).toBeNull();
});
