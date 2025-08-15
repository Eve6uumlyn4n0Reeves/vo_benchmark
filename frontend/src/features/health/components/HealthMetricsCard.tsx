import React from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  Grid,
  LinearProgress,
} from '@mui/material';
import type { HealthDetailedResponse } from '@/types/api';

// =============================================================================
// METRIC ITEM
// =============================================================================

interface MetricItemProps {
  label: string;
  value: string | number;
  unit?: string;
  color?: 'primary' | 'secondary' | 'success' | 'warning' | 'error';
}

const MetricItem: React.FC<MetricItemProps> = ({
  label,
  value,
  unit,
  color = 'primary',
}) => {
  return (
    <Box textAlign="center">
      <Typography variant="h4" color={`${color}.main`} fontWeight={600}>
        {value}
        {unit && (
          <Typography component="span" variant="body2" color="text.secondary" ml={0.5}>
            {unit}
          </Typography>
        )}
      </Typography>
      <Typography variant="body2" color="text.secondary">
        {label}
      </Typography>
    </Box>
  );
};

// =============================================================================
// HEALTH METRICS CARD
// =============================================================================

interface HealthMetricsCardProps {
  data: HealthDetailedResponse;
  loading?: boolean;
}

export const HealthMetricsCard: React.FC<HealthMetricsCardProps> = ({
  data,
  loading = false,
}) => {
  const formatNumber = (num: number) => {
    if (num >= 1000000) {
      return `${(num / 1000000).toFixed(1)}M`;
    }
    if (num >= 1000) {
      return `${(num / 1000).toFixed(1)}K`;
    }
    return num.toString();
  };

  return (
    <Card>
      <CardContent>
        {loading && <LinearProgress sx={{ mb: 2 }} />}
        
        <Typography variant="h6" component="h2" gutterBottom>
          系统指标
        </Typography>

        <Grid container spacing={3}>
          <Grid item xs={6} sm={3}>
            <MetricItem
              label="活跃实验"
              value={data.active_experiments}
              color="primary"
            />
          </Grid>
          
          <Grid item xs={6} sm={3}>
            <MetricItem
              label="总实验数"
              value={formatNumber(data.total_experiments)}
              color="secondary"
            />
          </Grid>
          
          <Grid item xs={6} sm={3}>
            <MetricItem
              label="队列大小"
              value={data.queue_size}
              color={data.queue_size > 10 ? 'warning' : 'success'}
            />
          </Grid>
          
          <Grid item xs={6} sm={3}>
            <MetricItem
              label="运行时间"
              value={Math.floor(data.uptime / 3600)}
              unit="小时"
              color="success"
            />
          </Grid>
        </Grid>

        {/* System Metrics */}
        {data.system_metrics && Object.keys(data.system_metrics).length > 0 && (
          <Box mt={3}>
            <Typography variant="subtitle2" gutterBottom>
              系统资源
            </Typography>
            <Box
              component="pre"
              sx={{
                backgroundColor: 'grey.100',
                p: 2,
                borderRadius: 1,
                overflow: 'auto',
                fontFamily: 'monospace',
                fontSize: '0.75rem',
                maxHeight: 200,
              }}
            >
              {JSON.stringify(data.system_metrics, null, 2)}
            </Box>
          </Box>
        )}

        {/* Dependencies */}
        {data.dependencies && Object.keys(data.dependencies).length > 0 && (
          <Box mt={2}>
            <Typography variant="subtitle2" gutterBottom>
              依赖服务
            </Typography>
            <Box
              component="pre"
              sx={{
                backgroundColor: 'grey.100',
                p: 2,
                borderRadius: 1,
                overflow: 'auto',
                fontFamily: 'monospace',
                fontSize: '0.75rem',
                maxHeight: 200,
              }}
            >
              {JSON.stringify(data.dependencies, null, 2)}
            </Box>
          </Box>
        )}
      </CardContent>
    </Card>
  );
};
