import React from 'react';
import { Chip, Tooltip } from '@mui/material';
import {
  PlayArrowOutlined,
  CheckCircleOutlined,
  ErrorOutlined,
  CancelOutlined,
  FiberManualRecordOutlined,
} from '@mui/icons-material';
import type { ExperimentStatus } from '@/types/api';

// =============================================================================
// EXPERIMENT STATUS CHIP
// =============================================================================

interface ExperimentStatusChipProps {
  status: ExperimentStatus;
  size?: 'small' | 'medium';
  showIcon?: boolean;
  tooltip?: boolean;
}

export const ExperimentStatusChip: React.FC<ExperimentStatusChipProps> = ({
  status,
  size = 'small',
  showIcon = true,
  tooltip = true,
}) => {
  const getStatusConfig = () => {
    switch (status) {
      case 'CREATED':
        return {
          color: 'default' as const,
          icon: <FiberManualRecordOutlined />,
          label: '已创建',
          description: '实验已创建，等待开始',
        };
      case 'RUNNING':
        return {
          color: 'primary' as const,
          icon: <PlayArrowOutlined />,
          label: '运行中',
          description: '实验正在执行中',
        };
      case 'COMPLETED':
        return {
          color: 'success' as const,
          icon: <CheckCircleOutlined />,
          label: '已完成',
          description: '实验已成功完成',
        };
      case 'FAILED':
        return {
          color: 'error' as const,
          icon: <ErrorOutlined />,
          label: '失败',
          description: '实验执行失败',
        };
      case 'CANCELLED':
        return {
          color: 'warning' as const,
          icon: <CancelOutlined />,
          label: '已取消',
          description: '实验已被取消',
        };
      default:
        return {
          color: 'default' as const,
          icon: <FiberManualRecordOutlined />,
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
