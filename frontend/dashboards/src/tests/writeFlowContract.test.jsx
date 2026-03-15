// @vitest-environment jsdom
import { Alert, Button, Stack, TextField } from '@mui/material';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { useApiAction } from '../hooks/useApiAction';
import { useWizardDraft } from '../hooks/useWizardDraft';

const mockCreate = vi.fn();

function TestWriteWizard({ onSuccess }) {
  const { value, setValue, saveDraft, clearDraft } = useWizardDraft('test-write-wizard', {
    first_name: '',
  });

  const { run, loading, error } = useApiAction(async (payload) => {
    return await mockCreate(payload);
  });

  const handleChange = (event) => {
    const next = event.target.value;
    setValue((prev) => ({ ...prev, first_name: next }));
  };

  const handleSaveDraft = () => {
    saveDraft(value);
  };

  const handleSubmit = async () => {
    try {
      await run(value);
      clearDraft();
      onSuccess?.();
    } catch {
      saveDraft(value);
    }
  };

  return (
    <Stack spacing={2}>
      {error ? <Alert severity="error">{error.message}</Alert> : null}

      <TextField
        label="First Name"
        value={value.first_name}
        onChange={handleChange}
        helperText={error?.fieldErrors?.first_name || ''}
        error={Boolean(error?.fieldErrors?.first_name)}
      />

      <Button onClick={handleSaveDraft}>Save Draft</Button>

      <Button variant="contained" onClick={handleSubmit} disabled={loading}>
        {loading ? 'Submitting...' : 'Submit'}
      </Button>
    </Stack>
  );
}

describe('write flow contract', () => {
  afterEach(() => {
    cleanup();
  });

  beforeEach(() => {
    window.localStorage.clear();
    mockCreate.mockReset();
  });

  it('clears draft only on successful submit', async () => {
    const onSuccess = vi.fn();

    mockCreate.mockResolvedValueOnce({ id: 123 });

    render(<TestWriteWizard onSuccess={onSuccess} />);

    fireEvent.change(screen.getByLabelText('First Name'), {
      target: { value: 'John' },
    });

    fireEvent.click(screen.getByText('Save Draft'));

    expect(
      window.localStorage.getItem('crown_wizard_draft:test-write-wizard'),
    ).toContain('John');

    fireEvent.click(screen.getByText('Submit'));

    await waitFor(() => {
      expect(onSuccess).toHaveBeenCalledTimes(1);
    });

    expect(
      window.localStorage.getItem('crown_wizard_draft:test-write-wizard'),
    ).toBeNull();
  });

  it('preserves draft and shows field errors on failed submit', async () => {
    const onSuccess = vi.fn();

    mockCreate.mockRejectedValueOnce({
      message: 'Validation failed.',
      status: 400,
      fieldErrors: {
        first_name: 'This field is required.',
      },
    });

    render(<TestWriteWizard onSuccess={onSuccess} />);

    fireEvent.change(screen.getByLabelText('First Name'), {
      target: { value: 'Bad Value' },
    });

    fireEvent.click(screen.getByText('Save Draft'));
    fireEvent.click(screen.getByText('Submit'));

    await screen.findByText('Validation failed.');
    await screen.findByText('This field is required.');
    expect(onSuccess).not.toHaveBeenCalled();

    expect(
      window.localStorage.getItem('crown_wizard_draft:test-write-wizard'),
    ).toContain('Bad Value');
  });

  it('locks the submit button during request', async () => {
    let resolver;

    mockCreate.mockImplementationOnce(
      () =>
        new Promise((resolve) => {
          resolver = resolve;
        }),
    );

    render(<TestWriteWizard onSuccess={() => {}} />);

    fireEvent.change(screen.getByLabelText('First Name'), {
      target: { value: 'Jane' },
    });

    fireEvent.click(screen.getByText('Submit'));

    expect(screen.getByRole('button', { name: 'Submitting...' }).disabled).toBe(true);

    resolver({ id: 999 });

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Submit' })).toBeDefined();
    });
  });
});
