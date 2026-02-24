import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { useDebounce } from './use-debounce';

describe('useDebounce', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('should return initial value immediately', () => {
    const { result } = renderHook(() => useDebounce('initial', 500));
    expect(result.current).toBe('initial');
  });

  it('should debounce value changes', async () => {
    const { result, rerender } = renderHook(
      ({ value }) => useDebounce(value, 500),
      { initialProps: { value: 'initial' } }
    );

    // Change value
    rerender({ value: 'changed' });
    
    // Value should not change immediately
    expect(result.current).toBe('initial');

    // Fast-forward time
    vi.advanceTimersByTime(500);

    // Now value should be updated
    await waitFor(() => {
      expect(result.current).toBe('changed');
    });
  });

  it('should reset timer on rapid changes', async () => {
    const { result, rerender } = renderHook(
      ({ value }) => useDebounce(value, 500),
      { initialProps: { value: 'initial' } }
    );

    // Change value multiple times rapidly
    rerender({ value: 'change1' });
    vi.advanceTimersByTime(300);
    
    rerender({ value: 'change2' });
    vi.advanceTimersByTime(300);
    
    rerender({ value: 'change3' });
    vi.advanceTimersByTime(500);

    // Should only have the final value
    await waitFor(() => {
      expect(result.current).toBe('change3');
    });
  });

  it('should use custom delay', async () => {
    const { result, rerender } = renderHook(
      ({ value }) => useDebounce(value, 1000),
      { initialProps: { value: 'initial' } }
    );

    rerender({ value: 'changed' });
    
    // Should not change after 500ms
    vi.advanceTimersByTime(500);
    expect(result.current).toBe('initial');

    // Should change after 1000ms
    vi.advanceTimersByTime(500);
    await waitFor(() => {
      expect(result.current).toBe('changed');
    });
  });
});
