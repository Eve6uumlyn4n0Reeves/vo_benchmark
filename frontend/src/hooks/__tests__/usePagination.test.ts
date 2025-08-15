import { renderHook, act } from '@testing-library/react';
import { describe, it, expect } from '@jest/globals';
import { usePagination, pageToOffset, offsetToPage } from '../usePagination';

describe('usePagination', () => {
  it('should initialize with default values', () => {
    const { result } = renderHook(() => usePagination());

    expect(result.current.page).toBe(1);
    expect(result.current.per_page).toBe(20); // Default from env
    expect(result.current.canGoPrev).toBe(false);
    expect(result.current.canGoNext).toBe(false); // No total provided
  });

  it('should initialize with custom values', () => {
    const { result } = renderHook(() =>
      usePagination({
        initialPage: 2,
        initialPerPage: 50,
        total: 200,
      })
    );

    expect(result.current.page).toBe(2);
    expect(result.current.per_page).toBe(50);
    expect(result.current.canGoPrev).toBe(true);
    expect(result.current.canGoNext).toBe(true);
  });

  it('should handle page navigation', () => {
    const { result } = renderHook(() =>
      usePagination({
        initialPage: 1,
        initialPerPage: 10,
        total: 100,
      })
    );

    // Test next page
    act(() => {
      result.current.nextPage();
    });
    expect(result.current.page).toBe(2);

    // Test previous page
    act(() => {
      result.current.prevPage();
    });
    expect(result.current.page).toBe(1);

    // Test direct page setting
    act(() => {
      result.current.setPage(5);
    });
    expect(result.current.page).toBe(5);
  });

  it('should prevent going to invalid pages', () => {
    const { result } = renderHook(() =>
      usePagination({
        initialPage: 1,
        initialPerPage: 10,
        total: 100,
      })
    );

    // Try to go to page 0
    act(() => {
      result.current.setPage(0);
    });
    expect(result.current.page).toBe(1);

    // Try to go to negative page
    act(() => {
      result.current.setPage(-5);
    });
    expect(result.current.page).toBe(1);
  });

  it('should handle per_page changes', () => {
    const { result } = renderHook(() =>
      usePagination({
        initialPage: 3,
        initialPerPage: 10,
        total: 100,
      })
    );

    // Change per_page should reset to page 1
    act(() => {
      result.current.setPerPage(25);
    });
    expect(result.current.per_page).toBe(25);
    expect(result.current.page).toBe(1);
  });

  it('should respect max per_page limit', () => {
    const { result } = renderHook(() =>
      usePagination({
        initialPerPage: 10,
        maxPerPage: 50,
      })
    );

    // Try to set per_page above max
    act(() => {
      result.current.setPerPage(100);
    });
    expect(result.current.per_page).toBe(50);
  });

  it('should calculate canGoNext and canGoPrev correctly', () => {
    const { result } = renderHook(() =>
      usePagination({
        initialPage: 2,
        initialPerPage: 10,
        total: 25, // 3 total pages
      })
    );

    expect(result.current.canGoPrev).toBe(true);
    expect(result.current.canGoNext).toBe(true);

    // Go to last page
    act(() => {
      result.current.setPage(3);
    });
    expect(result.current.canGoPrev).toBe(true);
    expect(result.current.canGoNext).toBe(false);

    // Go to first page
    act(() => {
      result.current.setPage(1);
    });
    expect(result.current.canGoPrev).toBe(false);
    expect(result.current.canGoNext).toBe(true);
  });

  it('should reset to initial values', () => {
    const { result } = renderHook(() =>
      usePagination({
        initialPage: 1,
        initialPerPage: 20,
        total: 100,
      })
    );

    // Change values
    act(() => {
      result.current.setPage(5);
      result.current.setPerPage(50);
    });

    // Reset
    act(() => {
      result.current.reset();
    });

    expect(result.current.page).toBe(1);
    expect(result.current.per_page).toBe(20);
  });
});

describe('pageToOffset', () => {
  it('should convert page/per_page to start/limit', () => {
    expect(pageToOffset(1, 10)).toEqual({ start: 0, limit: 10 });
    expect(pageToOffset(2, 10)).toEqual({ start: 10, limit: 10 });
    expect(pageToOffset(3, 25)).toEqual({ start: 50, limit: 25 });
  });
});

describe('offsetToPage', () => {
  it('should convert start/limit to page/per_page', () => {
    expect(offsetToPage(0, 10)).toEqual({ page: 1, per_page: 10 });
    expect(offsetToPage(10, 10)).toEqual({ page: 2, per_page: 10 });
    expect(offsetToPage(50, 25)).toEqual({ page: 3, per_page: 25 });
  });
});
