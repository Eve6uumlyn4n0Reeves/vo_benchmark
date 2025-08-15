import { useState, useCallback, useMemo } from 'react';
import { env } from '@/utils/env';

export interface PaginationState {
  page: number;
  per_page: number;
}

export interface PaginationControls {
  page: number;
  per_page: number;
  setPage: (page: number) => void;
  setPerPage: (perPage: number) => void;
  nextPage: () => void;
  prevPage: () => void;
  reset: () => void;
  canGoNext: boolean;
  canGoPrev: boolean;
}

export interface UsePaginationOptions {
  initialPage?: number;
  initialPerPage?: number;
  maxPerPage?: number;
  total?: number;
}

/**
 * Hook for managing pagination state
 * Supports both page/per_page and start/limit patterns from the API contract
 */
export const usePagination = (options: UsePaginationOptions = {}): PaginationControls => {
  const {
    initialPage = 1,
    initialPerPage = env.defaultPageSize(),
    maxPerPage = env.maxPageSize(),
    total = 0,
  } = options;

  const [page, setPageState] = useState(initialPage);
  const [per_page, setPerPageState] = useState(Math.min(initialPerPage, maxPerPage));

  const setPage = useCallback((newPage: number) => {
    setPageState(Math.max(1, newPage));
  }, []);

  const setPerPage = useCallback((newPerPage: number) => {
    const clampedPerPage = Math.min(Math.max(1, newPerPage), maxPerPage);
    setPerPageState(clampedPerPage);
    // Reset to first page when changing page size
    setPageState(1);
  }, [maxPerPage]);

  const nextPage = useCallback(() => {
    setPage(page + 1);
  }, [page, setPage]);

  const prevPage = useCallback(() => {
    setPage(page - 1);
  }, [page, setPage]);

  const reset = useCallback(() => {
    setPageState(initialPage);
    setPerPageState(Math.min(initialPerPage, maxPerPage));
  }, [initialPage, initialPerPage, maxPerPage]);

  const canGoNext = useMemo(() => {
    if (total === 0) return false;
    const totalPages = Math.ceil(total / per_page);
    return page < totalPages;
  }, [page, per_page, total]);

  const canGoPrev = useMemo(() => {
    return page > 1;
  }, [page]);

  return {
    page,
    per_page,
    setPage,
    setPerPage,
    nextPage,
    prevPage,
    reset,
    canGoNext,
    canGoPrev,
  };
};

/**
 * Convert page/per_page to start/limit for APIs that use offset-based pagination
 */
export const pageToOffset = (page: number, per_page: number) => ({
  start: (page - 1) * per_page,
  limit: per_page,
});

/**
 * Convert start/limit to page/per_page for display purposes
 */
export const offsetToPage = (start: number, limit: number) => ({
  page: Math.floor(start / limit) + 1,
  per_page: limit,
});
