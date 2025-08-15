import React from 'react';
import { Chip, Tooltip } from '@mui/material';
import {
  PlayArrowOutlined,
  CheckCircleOutlined,
  ErrorOutlined,
  CancelOutlined,

  HourglassEmptyOutlined,
} from '@mui/icons-material';
import type { TaskStatus } from '@/types/api';

// =============================================================================
// TASK STATUS CHIP
// =============================================================================

interface TaskStatusChipProps {
  status: TaskStatus;
  size?: 'small' | 'medium';
  showIcon?: boolean;
  tooltip?: boolean;
}

export const TaskStatusChip: React.FC<TaskStatusChipProps> = ({
  status,
  size = 'small',
  showIcon = true,
  tooltip = true,
}) => {
  const getStatusConfig = () => {
    switch (status) {
      case 'pending':
        return {
          color: 'default' as const,
          icon: <HourglassEmptyOutlined />,
          label: '等待中',
          description: '任务等待执行',
        };
      case 'running':
        return {
          color: 'primary' as const,
          icon: <PlayArrowOutlined />,
          label: '运行中',
          description: '任务正在执行中',
        };
      case 'completed':
        return {
          color: 'success' as const,
          icon: <CheckCircleOutlined />,
          label: '已完成',
          description: '任务已成功完成',
        };
      case 'failed':
        return {
          color: 'error' as const,
          icon: <ErrorOutlined />,
          label: '失败',
          description: '任务执行失败',
        };
      case 'cancelled':
        return {
          color: 'warning' as const,
          icon: <CancelOutlined />,
          label: '已取消',
          description: '任务已被取消',
        };

      default:
        return {
          color: 'default' as const,
          icon: <HourglassEmptyOutlined />,
          label: '未知',
          description: '未知状态',
        };
    }
  };

  const config = getStatusConfig();

  const chip = (
    <Chip
      icon={showIcon ? config.icon : undefined}
      label={config.label}
      color={config.color}
      size={size}
      variant="filled"
    />
  );

  if (tooltip) {
    return (
      <Tooltip title={config.description} arrow>
        {chip}
      </Tooltip>
    );
  }

  return chip;
};
