import React from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  IconButton,
  Tooltip,
  Grid,
  Divider,
  Button,
  Link,
} from '@mui/material';
import {
  VisibilityOutlined,
  CancelOutlined,
  DescriptionOutlined,
  LaunchOutlined,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import type { Task } from '@/types/api';
import { TaskStatusChip } from './TaskStatusChip';
import { ConfirmDialog, ProgressBar01 } from '@/components/common';
import { useMonotonicTaskProgress } from '../hooks/useMonotonicTaskProgress';

// =============================================================================
// TASK CARD
// =============================================================================

interface TaskCardProps {
  task: Task;
  onCancel?: (taskId: string) => void;
  cancelLoading?: boolean;
}

const TaskCard: React.FC<TaskCardProps> = ({ task, onCancel, cancelLoading = false }) => {
  const navigate = useNavigate();

  const formatDate = (dateString: string) => {
    try {
      return new Date(dateString).toLocaleString('zh-CN');
    } catch {
      return dateString;
    }
  };



  const handleViewDetails = () => {
    navigate(`/tasks/${task.task_id}`);
  };

  const handleViewLogs = () => {
    navigate(`/tasks/${task.task_id}?tab=logs`);
  };

  const handleViewExperiment = () => {
    if (task.experiment_id) {
      navigate(`/experiments/${task.experiment_id}`);
    }
  };

  const [confirmOpen, setConfirmOpen] = React.useState(false);

  const handleCancel = () => {
    setConfirmOpen(true);
  };

  const canCancel = task.status === 'pending' || task.status === 'running';

  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        {/* Header */}
        <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={2}>
          <Box flexGrow={1} mr={2}>
            <Typography variant="h6" component="h3" gutterBottom>
              任务
            </Typography>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              ID: {task.task_id}
            </Typography>
          </Box>
          <TaskStatusChip status={task.status} />
        </Box>

        {/* Progress */}
        {(task.progress !== undefined || task.status === 'running' || task.status === 'completed') && (
          <Box mb={2}>
            <Typography variant="body2" color="text.secondary" mb={1}>
              进度
            </Typography>
            <ProgressBar01
              value01={useMonotonicTaskProgress(task.task_id, task.progress, task.status)}
              height={6}
              showLabel={true}
            />
          </Box>
        )}

        {/* Metadata */}
        <Grid container spacing={2} sx={{ mb: 2 }}>
          <Grid item xs={6}>
            <Typography variant="caption" color="text.secondary">
              创建时间
            </Typography>
            <Typography variant="body2">
              {formatDate(task.created_at)}
            </Typography>
          </Grid>
          <Grid item xs={6}>
            <Typography variant="caption" color="text.secondary">
              更新时间
            </Typography>
            <Typography variant="body2">
              {formatDate(task.updated_at)}
            </Typography>
          </Grid>
          {false && (
            <Grid item xs={6}>
              <Typography variant="caption" color="text.secondary">
                运行时长
              </Typography>
              <Typography variant="body2">
                -
              </Typography>
            </Grid>
          )}
          {task.experiment_id && (
            <Grid item xs={6}>
              <Typography variant="caption" color="text.secondary">
                关联实验
              </Typography>
              <Link
                component="button"
                variant="body2"
                fontFamily="monospace"
                onClick={handleViewExperiment}
                sx={{
                  textAlign: 'left',
                  textDecoration: 'none',
                  '&:hover': {
                    textDecoration: 'underline',
                  },
                }}
              >
                {task.experiment_id}
              </Link>
            </Grid>
          )}
        </Grid>

        {/* Error Details */}
        {task.error_details && (
          <Box mb={2}>
            <Typography variant="caption" color="error">
              错误信息
            </Typography>
            <Typography variant="body2" color="error" sx={{ 
              backgroundColor: 'error.light', 
              p: 1, 
              borderRadius: 1,
              fontFamily: 'monospace',
              fontSize: '0.75rem',
            }}>
              {typeof task.error_details === 'string' ? task.error_details : JSON.stringify(task.error_details || {}, null, 2)}
            </Typography>
          </Box>
        )}

        <Divider sx={{ my: 2 }} />

        {/* Actions */}
        <Box display="flex" justifyContent="space-between" alignItems="center">
          <Box display="flex" gap={1}>
            <Tooltip title="查看详情">
              <IconButton size="small" onClick={handleViewDetails}>
                <VisibilityOutlined />
              </IconButton>
            </Tooltip>
            
            <Tooltip title="查看日志">
              <IconButton size="small" onClick={handleViewLogs}>
                <DescriptionOutlined />
              </IconButton>
            </Tooltip>

            {task.experiment_id && (
              <Tooltip title="查看关联实验">
                <IconButton size="small" onClick={handleViewExperiment}>
                  <LaunchOutlined />
                </IconButton>
              </Tooltip>
            )}
          </Box>

          {canCancel && (
            <>
              <Button
                size="small"
                color="warning"
                variant="outlined"
                startIcon={<CancelOutlined />}
                onClick={handleCancel}
                disabled={cancelLoading}
              >
                {cancelLoading ? '取消中...' : '取消任务'}
              </Button>
              <ConfirmDialog
                open={confirmOpen}
                title="确认取消任务"
                description="是否确定要取消该任务？此操作不可恢复。"
                confirming={cancelLoading}
                onClose={() => setConfirmOpen(false)}
                onConfirm={() => {
                  setConfirmOpen(false);
                  onCancel?.(task.task_id);
                }}
                confirmText="确认取消"
                cancelText="返回"
              />
            </>
          )}
        </Box>
      </CardContent>
    </Card>
  );
};

// =============================================================================
// TASKS LIST
// =============================================================================

interface TasksListProps {
  tasks: Task[];
  loading?: boolean;
  onCancel?: (taskId: string) => void;
  cancelLoading?: boolean;
}

export const TasksList: React.FC<TasksListProps> = ({
  tasks,
  onCancel,
  cancelLoading = false,
}) => {
  if (tasks.length === 0) {
    return (
      <Box textAlign="center" py={8}>
        <Typography variant="h6" color="text.secondary" gutterBottom>
          暂无任务
        </Typography>
        <Typography variant="body2" color="text.disabled">
          当前没有正在执行或已完成的任务
        </Typography>
      </Box>
    );
  }

  return (
    <Grid container spacing={3}>
      {tasks.map((task) => (
        <Grid item xs={12} sm={6} lg={4} key={task.task_id}>
          <TaskCard 
            task={task} 
            onCancel={onCancel}
            cancelLoading={cancelLoading}
          />
        </Grid>
      ))}
    </Grid>
  );
};
