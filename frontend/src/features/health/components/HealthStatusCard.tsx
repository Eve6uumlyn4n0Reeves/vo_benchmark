import React from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  Chip,
  LinearProgress,
} from '@mui/material';
import {
  CheckCircleOutlined,
  WarningOutlined,
  ErrorOutlined,
  AccessTimeOutlined,
} from '@mui/icons-material';
import type { HealthStatus } from '@/types/api';

// =============================================================================
// HEALTH STATUS INDICATOR
// =============================================================================

interface HealthStatusIndicatorProps {
  status: HealthStatus;
  size?: 'small' | 'medium';
}

export const HealthStatusIndicator: React.FC<HealthStatusIndicatorProps> = ({
  status,
  size = 'medium',
}) => {
  const getStatusConfig = () => {
    switch (status) {
      case 'healthy':
        return {
          color: 'success' as const,
          icon: <CheckCircleOutlined />,
          label: '健康',
        };
      case 'degraded':
        return {
          color: 'warning' as const,
          icon: <WarningOutlined />,
          label: '降级',
        };
      case 'unhealthy':
        return {
          color: 'error' as const,
          icon: <ErrorOutlined />,
          label: '异常',
        };
      default:
        return {
          color: 'default' as const,
          icon: <AccessTimeOutlined />,
          label: '未知',
        };
    }
  };

  const config = getStatusConfig();

  return (
    <Chip
      icon={config.icon}
      label={config.label}
      color={config.color}
      size={size}
      variant="filled"
    />
  );
};

// =============================================================================
// HEALTH STATUS CARD
// =============================================================================

interface HealthStatusCardProps {
  status: HealthStatus;
  version: string;
  uptime: number;
  timestamp: string;
  loading?: boolean;
}

export const HealthStatusCard: React.FC<HealthStatusCardProps> = ({
  status,
  version,
  uptime,
  timestamp,
  loading = false,
}) => {
  const formatUptime = (seconds: number) => {
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);

    if (days > 0) {
      return `${days}天 ${hours}小时 ${minutes}分钟`;
    }
    if (hours > 0) {
      return `${hours}小时 ${minutes}分钟`;
    }
    return `${minutes}分钟`;
  };

  const formatTimestamp = (timestamp: string) => {
    try {
      return new Date(timestamp).toLocaleString('zh-CN');
    } catch {
      return timestamp;
    }
  };

  return (
    <Card>
      <CardContent>
        {loading && <LinearProgress sx={{ mb: 2 }} />}
        
        <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={2}>
          <Typography variant="h6" component="h2">
            系统状态
          </Typography>
          <HealthStatusIndicator status={status} />
        </Box>

        <Box display="grid" gridTemplateColumns="1fr 1fr" gap={2}>
          <Box>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              版本
            </Typography>
            <Typography variant="body1" fontWeight={500}>
              {version}
            </Typography>
          </Box>

          <Box>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              运行时间
            </Typography>
            <Typography variant="body1" fontWeight={500}>
              {formatUptime(uptime)}
            </Typography>
          </Box>

          <Box gridColumn="1 / -1">
            <Typography variant="body2" color="text.secondary" gutterBottom>
              最后更新
            </Typography>
            <Typography variant="body1" fontWeight={500}>
              {formatTimestamp(timestamp)}
            </Typography>
          </Box>
        </Box>
      </CardContent>
    </Card>
  );
};
