import React from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Chip,
  LinearProgress,
} from '@mui/material';
import {
  CheckCircleOutlined,
  ErrorOutlined,
} from '@mui/icons-material';
import type { HealthCheck, CheckStatus } from '@/types/api';

// =============================================================================
// CHECK STATUS INDICATOR
// =============================================================================

interface CheckStatusIndicatorProps {
  status: CheckStatus;
}

const CheckStatusIndicator: React.FC<CheckStatusIndicatorProps> = ({ status }) => {
  const config = status === 'pass' 
    ? { color: 'success' as const, icon: <CheckCircleOutlined />, label: '通过' }
    : { color: 'error' as const, icon: <ErrorOutlined />, label: '失败' };

  return (
    <Chip
      icon={config.icon}
      label={config.label}
      color={config.color}
      size="small"
      variant="filled"
    />
  );
};

// =============================================================================
// HEALTH CHECKS CARD
// =============================================================================

interface HealthChecksCardProps {
  ready: boolean;
  checks: HealthCheck[];
  timestamp: string;
  loading?: boolean;
}

export const HealthChecksCard: React.FC<HealthChecksCardProps> = ({
  ready,
  checks,
  timestamp,
  loading = false,
}) => {
  const formatTimestamp = (timestamp: string) => {
    try {
      return new Date(timestamp).toLocaleString('zh-CN');
    } catch {
      return timestamp;
    }
  };

  const passedChecks = checks.filter(check => check.status === 'pass').length;
  const totalChecks = checks.length;

  return (
    <Card>
      <CardContent>
        {loading && <LinearProgress sx={{ mb: 2 }} />}
        
        <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={2}>
          <Typography variant="h6" component="h2">
            就绪检查
          </Typography>
          <Chip
            label={ready ? '就绪' : '未就绪'}
            color={ready ? 'success' : 'error'}
            variant="filled"
          />
        </Box>

        <Box mb={2}>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            检查结果: {passedChecks}/{totalChecks} 通过
          </Typography>
          <Typography variant="body2" color="text.secondary">
            检查时间: {formatTimestamp(timestamp)}
          </Typography>
        </Box>

        {checks.length > 0 ? (
          <List dense>
            {checks.map((check, index) => (
              <ListItem key={index} sx={{ px: 0 }}>
                <ListItemIcon sx={{ minWidth: 40 }}>
                  <CheckStatusIndicator status={check.status} />
                </ListItemIcon>
                <ListItemText
                  primary={check.name}
                  secondary={check.message}
                  primaryTypographyProps={{ fontWeight: 500 }}
                />
              </ListItem>
            ))}
          </List>
        ) : (
          <Typography variant="body2" color="text.secondary" textAlign="center" py={2}>
            暂无检查项目
          </Typography>
        )}
      </CardContent>
    </Card>
  );
};
