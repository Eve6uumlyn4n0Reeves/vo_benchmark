import React from 'react';
import {
  Box,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  InputAdornment,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  SearchOutlined,
  ClearOutlined,
  FilterListOutlined,
} from '@mui/icons-material';
import type { TaskStatus, TasksListParams } from '@/types/api';

// =============================================================================
// TASKS FILTERS
// =============================================================================

interface TasksFiltersProps {
  filters: TasksListParams;
  onFiltersChange: (filters: TasksListParams) => void;
  loading?: boolean;
}

export const TasksFilters: React.FC<TasksFiltersProps> = ({
  filters,
  onFiltersChange,
  loading = false,
}) => {
  const [searchValue, setSearchValue] = React.useState(filters.q || '');

  // Debounced search
  React.useEffect(() => {
    const timer = setTimeout(() => {
      if (searchValue !== filters.q) {
        onFiltersChange({
          ...filters,
          q: searchValue || undefined,
          page: 1, // Reset to first page when searching
        });
      }
    }, 300);

    return () => clearTimeout(timer);
  }, [searchValue, filters, onFiltersChange]);

  const handleSearchChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setSearchValue(event.target.value);
  };

  const handleClearSearch = () => {
    setSearchValue('');
  };

  const handleStatusChange = (event: any) => {
    const status = event.target.value as TaskStatus | '';
    onFiltersChange({
      ...filters,
      status: status || undefined,
      page: 1, // Reset to first page when filtering
    });
  };

  const handleTaskTypeChange = (event: any) => {
    const taskType = event.target.value as string;
    onFiltersChange({
      ...filters,
      task_type: taskType || undefined,
      page: 1, // Reset to first page when filtering
    });
  };

  const handleSortChange = (event: any) => {
    const [sortBy, sortOrder] = (event.target.value as string).split(':');
    onFiltersChange({
      ...filters,
      sort_by: sortBy as any,
      sort_order: sortOrder as any,
      page: 1, // Reset to first page when sorting
    });
  };

  const handleClearFilters = () => {
    setSearchValue('');
    onFiltersChange({
      page: 1,
      per_page: filters.per_page,
    });
  };

  const hasActiveFilters = !!(filters.q || filters.status || filters.task_type || filters.sort_by);

  return (
    <Box display="flex" gap={2} alignItems="center" flexWrap="wrap">
      {/* Search */}
      <TextField
        placeholder="搜索任务ID或类型..."
        value={searchValue}
        onChange={handleSearchChange}
        disabled={loading}
        size="small"
        sx={{ minWidth: 250 }}
        InputProps={{
          startAdornment: (
            <InputAdornment position="start">
              <SearchOutlined />
            </InputAdornment>
          ),
          endAdornment: searchValue && (
            <InputAdornment position="end">
              <IconButton size="small" onClick={handleClearSearch}>
                <ClearOutlined />
              </IconButton>
            </InputAdornment>
          ),
        }}
      />

      {/* Status Filter */}
      <FormControl size="small" sx={{ minWidth: 120 }}>
        <InputLabel>状态</InputLabel>
        <Select
          value={filters.status || ''}
          onChange={handleStatusChange}
          disabled={loading}
          label="状态"
        >
          <MenuItem value="">全部</MenuItem>
          <MenuItem value="pending">等待中</MenuItem>
          <MenuItem value="running">运行中</MenuItem>
          <MenuItem value="completed">已完成</MenuItem>
          <MenuItem value="failed">失败</MenuItem>
          <MenuItem value="cancelled">已取消</MenuItem>
        </Select>
      </FormControl>

      {/* Task Type Filter */}
      <FormControl size="small" sx={{ minWidth: 140 }}>
        <InputLabel>任务类型</InputLabel>
        <Select
          value={filters.task_type || ''}
          onChange={handleTaskTypeChange}
          disabled={loading}
          label="任务类型"
        >
          <MenuItem value="">全部</MenuItem>
          <MenuItem value="experiment">实验执行</MenuItem>
          <MenuItem value="data_processing">数据处理</MenuItem>
          <MenuItem value="analysis">结果分析</MenuItem>
          <MenuItem value="export">数据导出</MenuItem>
          <MenuItem value="cleanup">清理任务</MenuItem>
        </Select>
      </FormControl>

      {/* Sort */}
      <FormControl size="small" sx={{ minWidth: 140 }}>
        <InputLabel>排序</InputLabel>
        <Select
          value={`${filters.sort_by || 'created_at'}:${filters.sort_order || 'desc'}`}
          onChange={handleSortChange}
          disabled={loading}
          label="排序"
        >
          <MenuItem value="created_at:desc">创建时间 ↓</MenuItem>
          <MenuItem value="created_at:asc">创建时间 ↑</MenuItem>
          <MenuItem value="updated_at:desc">更新时间 ↓</MenuItem>
          <MenuItem value="updated_at:asc">更新时间 ↑</MenuItem>
          <MenuItem value="status:asc">状态 ↑</MenuItem>
          <MenuItem value="status:desc">状态 ↓</MenuItem>
        </Select>
      </FormControl>

      {/* Clear Filters */}
      {hasActiveFilters && (
        <Tooltip title="清除筛选">
          <IconButton onClick={handleClearFilters} disabled={loading}>
            <FilterListOutlined />
          </IconButton>
        </Tooltip>
      )}
    </Box>
  );
};
