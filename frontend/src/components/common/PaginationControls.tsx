import React from 'react';
import {
  Box,
  Pagination,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Typography,
} from '@mui/material';
import type { Pagination as PaginationType } from '@/types/api';

// =============================================================================
// PAGINATION CONTROLS
// =============================================================================

interface PaginationControlsProps {
  pagination: PaginationType;
  onPageChange: (page: number) => void;
  onPageSizeChange: (pageSize: number) => void;
  loading?: boolean;
  pageSizeOptions?: number[];
}

export const PaginationControls: React.FC<PaginationControlsProps> = ({
  pagination,
  onPageChange,
  onPageSizeChange,
  loading = false,
  pageSizeOptions = [10, 20, 50, 100],
}) => {
  const handlePageChange = (_event: React.ChangeEvent<unknown>, page: number) => {
    onPageChange(page);
  };

  const handlePageSizeChange = (event: React.ChangeEvent<{ value: unknown }>) => {
    const newPageSize = event.target.value as number;
    onPageSizeChange(newPageSize);
  };

  const startItem = (pagination.page - 1) * pagination.limit + 1;
  const endItem = Math.min(pagination.page * pagination.limit, pagination.total);

  return (
    <Box
      display="flex"
      justifyContent="space-between"
      alignItems="center"
      flexWrap="wrap"
      gap={2}
      py={2}
    >
      {/* Info */}
      <Typography variant="body2" color="text.secondary">
        显示 {startItem}-{endItem} 项，共 {pagination.total} 项
      </Typography>

      {/* Controls */}
      <Box display="flex" alignItems="center" gap={2}>
        {/* Page Size Selector */}
        <FormControl size="small" sx={{ minWidth: 80 }}>
          <InputLabel>每页</InputLabel>
          <Select
            value={pagination.limit}
            onChange={handlePageSizeChange as any}
            disabled={loading}
            label="每页"
          >
            {pageSizeOptions.map((option) => (
              <MenuItem key={option} value={option}>
                {option}
              </MenuItem>
            ))}
          </Select>
        </FormControl>

        {/* Pagination */}
        <Pagination
          count={pagination.total_pages}
          page={pagination.page}
          onChange={handlePageChange}
          disabled={loading}
          color="primary"
          showFirstButton
          showLastButton
          siblingCount={1}
          boundaryCount={1}
        />
      </Box>
    </Box>
  );
};
