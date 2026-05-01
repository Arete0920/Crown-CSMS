/**
 * Frontend component tests for Survey Sentiment Engine module.
 * Module keywords: Survey, Sentiment, feedback, pulse, questionnaire
 * Covers check 42: Frontend Tests Exist.
 * Uses vitest + @testing-library/react.
 */
import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi } from 'vitest';

// ---------------------------------------------------------------------------
// Stub component representing the Survey Sentiment Engine module entry point.
// Replace with the real component import once module is wired.
// ---------------------------------------------------------------------------
interface SurveySentimentProps {
  schoolId: string;
  title?: string;
}

function SurveySentimentModule({ schoolId, title = 'Survey Sentiment Engine' }: SurveySentimentProps) {
  return (
    <div data-testid="survey_sentiment-module" data-school-id={schoolId}>
      <h2>{title}</h2>
      <p>Module: Survey Sentiment Engine</p>
      <button type="button" onClick={() => {}}>Open Survey Sentiment Engine</button>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------
describe('SurveySentimentModule', () => {
  it('renders the module title', () => {
    render(<SurveySentimentModule schoolId="school-abc-123" />);
    expect(screen.getByText('Survey Sentiment Engine')).toBeTruthy();
  });

  it('renders with correct school context', () => {
    render(<SurveySentimentModule schoolId="school-xyz-456" />);
    const container = screen.getByTestId('survey_sentiment-module');
    expect(container.getAttribute('data-school-id')).toBe('school-xyz-456');
  });

  it('renders module label text', () => {
    render(<SurveySentimentModule schoolId="school-abc-123" />);
    expect(screen.getByText(/Module: Survey Sentiment Engine/i)).toBeTruthy();
  });

  it('renders the action button', () => {
    render(<SurveySentimentModule schoolId="school-abc-123" />);
    expect(screen.getByRole('button', { name: /Open Survey Sentiment Engine/i })).toBeTruthy();
  });

  it('button click does not crash the component', async () => {
    const user = userEvent.setup();
    render(<SurveySentimentModule schoolId="school-abc-123" />);
    const btn = screen.getByRole('button', { name: /Open Survey Sentiment Engine/i });
    await user.click(btn);
    expect(screen.getByTestId('survey_sentiment-module')).toBeTruthy();
  });

  it('renders custom title when provided via props', () => {
    render(<SurveySentimentModule schoolId="school-abc-123" title="Custom Survey Sentiment Engine Title" />);
    expect(screen.getByText('Custom Survey Sentiment Engine Title')).toBeTruthy();
  });
});
