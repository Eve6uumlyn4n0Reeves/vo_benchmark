import React from 'react';
import {
  Box,
  Typography,
  Button,
  Paper,
  Alert,
  Chip,
} from '@mui/material';
import {
  RefreshOutlined,
  PlayArrowOutlined,
  PauseOutlined,
} from '@mui/icons-material';
import { useTasks, useCancelTask } from '@/api/services';
import { usePagination } from '@/hooks';
import {
  LoadingSpinner,
  ErrorState,
  NoData,
  PaginationControls,
} from '@/components/common';
import {
  TasksList,
  TasksFilters,
} from '../components';
import type { TasksListParams } from '@/types/api';
import { useTaskEvents } from '../hooks/useTaskEvents';

// =============================================================================
// TASKS PAGE
// =============================================================================

const TasksPage: React.FC = () => {
  const [autoRefresh, setAutoRefresh] = React.useState(true);
  const [filters, setFilters] = React.useState<TasksListParams>({
    page: 1,
    per_page: 20,
  });

  const pagination = usePagination({
    initialPage: filters.page,
    initialPerPage: filters.per_page,
  });

  // Sync pagination with filters
  React.useEffect(() => {
    setFilters(prev => ({
      ...prev,
      page: pagination.page,
      per_page: pagination.per_page,
    }));
  }, [pagination.page, pagination.per_page]);

  // 当 SSE 连接成功时可选择关闭轮询，这里保持开关行为：SSE 连接成功则暂停轮询
  const sse = useTaskEvents(true);
  const tasksQuery = useTasks(filters, { autoRefresh: autoRefresh && !sse.isConnected, refetchMs: 30_000 });
  const cancelTaskMutation = useCancelTask();

  // Auto-refresh control
  React.useEffect(() => {
    if (autoRefresh) {
      tasksQuery.refetch();
    }
  }, [autoRefresh]);

  const handleFiltersChange = (newFilters: TasksListParams) => {
    setFilters(newFilters);
    if (newFilters.page !== pagination.page) {
      pagination.setPage(newFilters.page || 1);
    }
  };

  const handlePageChange = (page: number) => {
    pagination.setPage(page);
  };

  const handlePageSizeChange = (pageSize: number) => {
    pagination.setPerPage(pageSize);
  };

  const handleRefresh = () => {
    tasksQuery.refetch();
  };

  const handleToggleAutoRefresh = () => {
    setAutoRefresh(!autoRefresh);
  };

  const handleCancelTask = (taskId: string) => {
    cancelTaskMutation.mutate(taskId);
  };

  // Data processing - moved to top level to follow hooks rules
  const tasks = tasksQuery.data || [];
  const paginationData = undefined as any;

  // Count tasks by status
  const statusCounts = React.useMemo(() => {
    const counts = {
      pending: 0,
      running: 0,
      completed: 0,
      failed: 0,
      cancelled: 0,
    };

    tasks.forEach(task => {
      if (task.status in counts) {
        counts[task.status as keyof typeof counts]++;
      }
    });

    return counts;
  }, [tasks]);

  // Loading state for initial load
  if (tasksQuery.isLoading && !tasksQuery.data) {
    return (
      <Box>
        <Typography variant="h4" component="h1" gutterBottom>
          任务管理
        </Typography>
        <LoadingSpinner message="加载任务列表..." fullHeight />
      </Box>
    );
  }

  // Error state
  if (tasksQuery.error && !tasksQuery.data) {
    return (
      <Box>
        <Typography variant="h4" component="h1" gutterBottom>
          任务管理
        </Typography>
        <ErrorState
          error={tasksQuery.error}
          onRetry={handleRefresh}
          title="无法加载任务列表"
          description="请检查后端服务是否正常运行"
          fullHeight
        />
      </Box>
    );
  }

  return (
    <Box>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" component="h1">
          任务管理
        </Typography>
        <Box display="flex" gap={2}>
          <Button
            variant="outlined"
            startIcon={autoRefresh ? <PauseOutlined /> : <PlayArrowOutlined />}
            onClick={handleToggleAutoRefresh}
            color={autoRefresh ? 'primary' : 'inherit'}
          >
            {autoRefresh ? '停止自动刷新' : '开启自动刷新'}
          </Button>
          <Button
            variant="outlined"
            startIcon={<RefreshOutlined />}
            onClick={handleRefresh}
            disabled={tasksQuery.isFetching}
          >
            刷新
          </Button>
        </Box>
      </Box>

      {/* Auto-refresh indicator */}
      {autoRefresh && (
        <Alert severity="info" sx={{ mb: 3 }}>
          自动刷新已开启，每30秒更新一次任务状态
        </Alert>
      )}

      {/* Status Summary */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Typography variant="subtitle2" gutterBottom>
          任务状态统计
        </Typography>
        <Box display="flex" flexWrap="wrap" gap={1}>
          <Chip label={`等待中: ${statusCounts.pending}`} color="default" size="small" />
          <Chip label={`运行中: ${statusCounts.running}`} color="primary" size="small" />
          <Chip label={`已完成: ${statusCounts.completed}`} color="success" size="small" />
          <Chip label={`失败: ${statusCounts.failed}`} color="error" size="small" />
          <Chip label={`已取消: ${statusCounts.cancelled}`} color="warning" size="small" />
        </Box>
      </Paper>

      {/* Error Alert */}
      {tasksQuery.error && tasksQuery.data && (
        <Alert severity="warning" sx={{ mb: 3 }}>
          数据可能不是最新的，请尝试刷新页面
        </Alert>
      )}

      {/* Filters */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <TasksFilters
          filters={filters}
          onFiltersChange={handleFiltersChange}
          loading={tasksQuery.isFetching}
        />
      </Paper>

      {/* Content */}
      {tasks.length === 0 ? (
        <NoData
          title="暂无任务"
          description="当前没有正在执行或已完成的任务"
        />
      ) : (
        <>
          <TasksList
            tasks={tasks}
            onCancel={handleCancelTask}
            cancelLoading={cancelTaskMutation.isPending}
          />

          {/* Pagination */}
          {paginationData && paginationData.total_pages > 1 && (
            <Paper sx={{ mt: 3 }}>
              <PaginationControls
                pagination={paginationData}
                onPageChange={handlePageChange}
                onPageSizeChange={handlePageSizeChange}
                loading={tasksQuery.isFetching}
              />
            </Paper>
          )}
        </>
      )}
    </Box>
  );
};

export default TasksPage;
