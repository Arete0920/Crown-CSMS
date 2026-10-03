import { act, cleanup, renderHook, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { useAsyncPageData } from './useAsyncPageData';

afterEach(cleanup);

describe('asynchronous page loading', () => {
  it('does not refetch an inline loader on rerender and manual reload uses its latest value', async () => {
    const request = vi.fn(async (label) => label);
    const { result, rerender } = renderHook(({ label }) => useAsyncPageData(() => request(label), []), { initialProps: { label: 'first' } });
    await waitFor(() => expect(result.current.data).toBe('first'));
    rerender({ label: 'second' });
    expect(request).toHaveBeenCalledTimes(1);
    await act(async () => { await result.current.reload(); });
    expect(result.current.data).toBe('second');
    expect(request).toHaveBeenCalledTimes(2);
  });

  it('loads a changed record and discards an older request that finishes later', async () => {
    let finishFirst;
    const request = vi.fn((id) => id === 1 ? new Promise((resolve) => { finishFirst = resolve; }) : Promise.resolve('new record'));
    const { result, rerender } = renderHook(({ id }) => useAsyncPageData(() => request(id), [id]), { initialProps: { id: 1 } });
    rerender({ id: 2 });
    await waitFor(() => expect(result.current.data).toBe('new record'));
    await act(async () => { finishFirst('obsolete record'); });
    expect(result.current.data).toBe('new record');
    expect(result.current.loading).toBe(false);
    expect(request).toHaveBeenCalledTimes(2);
  });

  it('shows a request failure and clears it after a successful manual retry', async () => {
    const failure = new Error('API unavailable');
    const request = vi.fn().mockRejectedValueOnce(failure).mockResolvedValueOnce(['invoice']);
    const { result } = renderHook(() => useAsyncPageData(() => request(), []));
    await waitFor(() => expect(result.current.error).toBe(failure));
    await act(async () => { await result.current.reload(); });
    expect(result.current.error).toBeNull();
    expect(result.current.data).toEqual(['invoice']);
  });
});
