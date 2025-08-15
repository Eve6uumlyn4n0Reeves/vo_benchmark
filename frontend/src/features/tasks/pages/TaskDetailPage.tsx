import React from 'react';
import {
  Box,
  Typography,
  Button,
  Tabs,
  Tab,
  Card,
  CardContent,
  Grid,

  Alert,
  LinearProgress,
} from '@mui/material';
import {
  ArrowBackOutlined,
  RefreshOutlined,
  CancelOutlined,

} from '@mui/icons-material';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import { useTask, useTaskLogs, useCancelTask } from '@/api/services';
import {
  LoadingSpinner,
  ErrorState,
  CardSkeleton,
} from '@/components/common';
import { TaskStatusChip, TaskLogsViewer } from '../components';
import { useTaskEvents } from '../hooks/useTaskEvents';
import { ConfirmDialog } from '@/components/common';

// =============================================================================
// TASK DETAIL PAGE
// =============================================================================

const TaskDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  
  const currentTab = searchParams.get('tab') || 'details';
  const [autoRefreshLogs, setAutoRefreshLogs] = React.useState(true);

  // Subscribe to SSE task updates
  useTaskEvents(true);

  const taskQuery = useTask(id!, { autoRefresh: currentTab === 'details', refetchMs: 10_000 });
  const logsQuery = useTaskLogs(id!, { autoRefresh: currentTab === 'logs' && autoRefreshLogs, refetchMs: 5_000 });
  const cancelTaskMutation = useCancelTask();
  const [confirmOpen, setConfirmOpen] = React.useState(false);

  const handleTabChange = (_event: React.SyntheticEvent, newValue: string) => {
    setSearchParams({ tab: newValue });
  };

  const handleBack = () => {
    navigate('/tasks');
  };

  const handleRefresh = () => {
    taskQuery.refetch();
    if (currentTab === 'logs') {
      logsQuery.refetch();
    }
  };

  const handleCancelTask = () => {
    setConfirmOpen(true);
  };

  const handleDownloadLogs = () => {
    if (logsQuery.data?.logs) {
      const logContent = logsQuery.data.logs.join('\n');
      const blob = new Blob([logContent], { type: 'text/plain' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `task-${id}-logs.txt`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    }
  };

  const formatDate = (dateString: string) => {
    try {
      return new Date(dateString).toLocaleString('zh-CN');
    } catch {
      return dateString;
    }
  };



  // Loading state
  if (taskQuery.isLoading && !taskQuery.data) {
    return (
      <Box>
        <Box display="flex" alignItems="center" gap={2} mb={3}>
          <Button
            startIcon={<ArrowBackOutlined />}
            onClick={handleBack}
          >
            返回列表
          </Button>
          <Typography variant="h4" component="h1">
            任务详情
          </Typography>
        </Box>
        <LoadingSpinner message="加载任务详情..." fullHeight />
      </Box>
    );
  }

  // Error state
  if (taskQuery.error && !taskQuery.data) {
    return (
      <Box>
        <Box display="flex" alignItems="center" gap={2} mb={3}>
          <Button
            startIcon={<ArrowBackOutlined />}
            onClick={handleBack}
          >
            返回列表
          </Button>
          <Typography variant="h4" component="h1">
            任务详情
          </Typography>
        </Box>
        <ErrorState
          error={taskQuery.error}
          onRetry={handleRefresh}
          title="无法加载任务详情"
          description="请检查任务ID是否正确或网络连接"
          fullHeight
        />
      </Box>
    );
  }

  const task = taskQuery.data;
  if (!task) {
    return null;
  }

  const canCancel = task.status === 'pending' || task.status === 'running';

  return (
    <Box>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={3}>
        <Box>
          <Box display="flex" alignItems="center" gap={2} mb={1}>
            <Button
              startIcon={<ArrowBackOutlined />}
              onClick={handleBack}
            >
              返回列表
            </Button>
            <TaskStatusChip status={task.status} />
          </Box>
          <Typography variant="h4" component="h1">
            任务详情
          </Typography>
          <Typography variant="body1" color="text.secondary" sx={{ mt: 1 }}>
            任务ID: {task.task_id}
          </Typography>
        </Box>
        
        <Box display="flex" gap={2}>
          <Button
            variant="outlined"
            startIcon={<RefreshOutlined />}
            onClick={handleRefresh}
            disabled={taskQuery.isFetching}
          >
            刷新
          </Button>
          {canCancel && (
            <Button
              variant="outlined"
              color="warning"
              startIcon={<CancelOutlined />}
              onClick={handleCancelTask}
              disabled={cancelTaskMutation.isPending}
            >
              {cancelTaskMutation.isPending ? '取消中...' : '取消任务'}
            </Button>
          )}
        </Box>
      </Box>

      {/* Error Alert */}
      {taskQuery.error && taskQuery.data && (
        <Alert severity="warning" sx={{ mb: 3 }}>
          数据可能不是最新的，请尝试刷新页面
        </Alert>
      )}

      <ConfirmDialog
        open={confirmOpen}
        title="确认取消任务"
        description="是否确定要取消该任务？此操作不可恢复。"
        confirming={cancelTaskMutation.isPending}
        onClose={() => setConfirmOpen(false)}
        onConfirm={() => {
          if (id) cancelTaskMutation.mutate(id, { onSettled: () => setConfirmOpen(false) });
        }}
        confirmText="确认取消"
        cancelText="返回"
      />

      {/* Tabs */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={currentTab} onChange={handleTabChange}>
          <Tab label="详细信息" value="details" />
          <Tab label="日志" value="logs" />
        </Tabs>
      </Box>

      {/* Tab Content */}
      {currentTab === 'details' && (
        <Grid container spacing={3}>
          {/* Basic Info */}
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  基本信息
                </Typography>
                <Grid container spacing={2}>
                  <Grid item xs={6}>
                    <Typography variant="body2" color="text.secondary">
                      任务ID
                    </Typography>
                    <Typography variant="body2" fontFamily="monospace">
                      {task.task_id}
                    </Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="body2" color="text.secondary">
                      任务类型
                    </Typography>
                    <Typography variant="body2">
                      任务
                    </Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="body2" color="text.secondary">
                      状态
                    </Typography>
                    <TaskStatusChip status={task.status} size="small" />
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="body2" color="text.secondary">
                      优先级
                    </Typography>
                    <Typography variant="body2">
                      Normal
                    </Typography>
                  </Grid>
                </Grid>
              </CardContent>
            </Card>
          </Grid>

          {/* Progress */}
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  执行进度
                </Typography>
                {task.progress !== undefined ? (
                  <Box>
                    <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
                      <Typography variant="body2" color="text.secondary">
                        完成进度
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {Math.round(task.progress * 100)}%
                      </Typography>
                    </Box>
                    <LinearProgress 
                      variant="determinate" 
                      value={task.progress * 100} 
                      sx={{ height: 8, borderRadius: 4 }}
                    />
                  </Box>
                ) : (
                  <Typography variant="body2" color="text.secondary">
                    暂无进度信息
                  </Typography>
                )}
              </CardContent>
            </Card>
          </Grid>

          {/* Timing Info */}
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  时间信息
                </Typography>
                <Grid container spacing={2}>
                  <Grid item xs={12}>
                    <Typography variant="body2" color="text.secondary">
                      创建时间
                    </Typography>
                    <Typography variant="body2">
                      {formatDate(task.created_at)}
                    </Typography>
                  </Grid>
                  <Grid item xs={12}>
                    <Typography variant="body2" color="text.secondary">
                      更新时间
                    </Typography>
                    <Typography variant="body2">
                      {formatDate(task.updated_at)}
                    </Typography>
                  </Grid>
                  {false && (
                    <Grid item xs={12}>
                      <Typography variant="body2" color="text.secondary">
                        开始时间
                      </Typography>
                      <Typography variant="body2">
                        -
                      </Typography>
                    </Grid>
                  )}
                  {task.completed_at && (
                    <Grid item xs={12}>
                      <Typography variant="body2" color="text.secondary">
                        完成时间
                      </Typography>
                      <Typography variant="body2">
                        {formatDate(task.completed_at)}
                      </Typography>
                    </Grid>
                  )}
                  {false && (
                    <Grid item xs={12}>
                      <Typography variant="body2" color="text.secondary">
                        运行时长
                      </Typography>
                      <Typography variant="body2">
                        -
                      </Typography>
                    </Grid>
                  )}
                </Grid>
              </CardContent>
            </Card>
          </Grid>

          {/* Related Info */}
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  关联信息
                </Typography>
                <Grid container spacing={2}>
                  {task.experiment_id && (
                    <Grid item xs={12}>
                      <Typography variant="body2" color="text.secondary">
                        关联实验
                      </Typography>
                      <Typography variant="body2" fontFamily="monospace">
                        {task.experiment_id}
                      </Typography>
                    </Grid>
                  )}
                  {false && (
                    <Grid item xs={12}>
                      <Typography variant="body2" color="text.secondary">
                        执行节点
                      </Typography>
                      <Typography variant="body2">
                        -
                      </Typography>
                    </Grid>
                  )}
                </Grid>
              </CardContent>
            </Card>
          </Grid>

          {/* Error Details */}
          {task.error_details && (
            <Grid item xs={12}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom color="error">
                    错误详情
                  </Typography>
                  <Typography
                    variant="body2"
                    sx={{
                      backgroundColor: 'error.light',
                      p: 2,
                      borderRadius: 1,
                      fontFamily: 'monospace',
                      fontSize: '0.875rem',
                      whiteSpace: 'pre-wrap',
                      wordBreak: 'break-word',
                    }}
                  >
                    {typeof task.error_details === 'string' ? task.error_details : JSON.stringify(task.error_details || {}, null, 2)}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          )}
        </Grid>
      )}

      {currentTab === 'logs' && (
        <Grid container spacing={3}>
          <Grid item xs={12}>
            {logsQuery.isLoading && !logsQuery.data ? (
              <CardSkeleton />
            ) : logsQuery.error ? (
              <ErrorState
                error={logsQuery.error}
                onRetry={() => logsQuery.refetch()}
                variant="alert"
              />
            ) : (
              <TaskLogsViewer
                logs={logsQuery.data?.logs || []}
                loading={logsQuery.isFetching}
                onRefresh={() => logsQuery.refetch()}
                onDownload={handleDownloadLogs}
                autoRefresh={autoRefreshLogs}
                onAutoRefreshChange={setAutoRefreshLogs}
              />
            )}
          </Grid>
        </Grid>
      )}
    </Box>
  );
};

export default TaskDetailPage;
