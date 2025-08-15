import React from 'react';
import {
  Box,
  Typography,
  Grid,
  Button,
  Tabs,
  Tab,
  Alert,
  AlertTitle,
} from '@mui/material';
import {
  RefreshOutlined,
  OpenInNewOutlined,
} from '@mui/icons-material';
import { useHealth, useHealthDetailed, useHealthReady } from '@/api/services';
import { LoadingSpinner, ErrorState, CardSkeleton } from '@/components/common';
import {
  HealthStatusCard,
  HealthChecksCard,
  HealthMetricsCard,
} from '../components';

// =============================================================================
// HEALTH PAGE COMPONENT
// =============================================================================

const HealthPage: React.FC = () => {
  const [tabValue, setTabValue] = React.useState(0);

  // API queries
  const healthQuery = useHealth();
  const healthDetailedQuery = useHealthDetailed();
  const healthReadyQuery = useHealthReady();

  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const handleRefresh = () => {
    healthQuery.refetch();
    healthDetailedQuery.refetch();
    healthReadyQuery.refetch();
  };

  const handleOpenDocs = () => {
    window.open('/api/v1/docs/', '_blank');
  };

  // Loading state for initial load
  if (healthQuery.isLoading && !healthQuery.data) {
    return (
      <Box>
        <Typography variant="h4" component="h1" gutterBottom>
          系统健康
        </Typography>
        <LoadingSpinner message="加载健康状态..." fullHeight />
      </Box>
    );
  }

  // Error state
  if (healthQuery.error && !healthQuery.data) {
    return (
      <Box>
        <Typography variant="h4" component="h1" gutterBottom>
          系统健康
        </Typography>
        <ErrorState
          error={healthQuery.error}
          onRetry={handleRefresh}
          title="无法获取健康状态"
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
          系统健康
        </Typography>
        <Box display="flex" gap={2}>
          <Button
            variant="outlined"
            startIcon={<RefreshOutlined />}
            onClick={handleRefresh}
            disabled={healthQuery.isFetching}
          >
            刷新
          </Button>
          <Button
            variant="outlined"
            startIcon={<OpenInNewOutlined />}
            onClick={handleOpenDocs}
          >
            API文档
          </Button>
        </Box>
      </Box>

      {/* Status Alert */}
      {healthQuery.data && healthQuery.data.status !== 'healthy' && (
        <Alert severity={healthQuery.data.status === 'degraded' ? 'warning' : 'error'} sx={{ mb: 3 }}>
          <AlertTitle>系统状态异常</AlertTitle>
          系统当前处于 {healthQuery.data.status === 'degraded' ? '降级' : '异常'} 状态，请检查详细信息。
        </Alert>
      )}

      {/* Tabs */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={tabValue} onChange={handleTabChange}>
          <Tab label="基础状态" />
          <Tab label="详细指标" />
          <Tab label="就绪检查" />
        </Tabs>
      </Box>

      {/* Tab Content */}
      {tabValue === 0 && (
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            {healthQuery.data ? (
              <HealthStatusCard
                status={healthQuery.data.status}
                version={healthQuery.data.version}
                uptime={healthQuery.data.uptime}
                timestamp={healthQuery.data.timestamp}
                loading={healthQuery.isFetching}
              />
            ) : (
              <CardSkeleton />
            )}
          </Grid>
        </Grid>
      )}

      {tabValue === 1 && (
        <Grid container spacing={3}>
          <Grid item xs={12}>
            {healthDetailedQuery.isLoading && !healthDetailedQuery.data ? (
              <CardSkeleton />
            ) : healthDetailedQuery.error ? (
              <ErrorState
                error={healthDetailedQuery.error}
                onRetry={() => healthDetailedQuery.refetch()}
                variant="alert"
              />
            ) : healthDetailedQuery.data ? (
              <HealthMetricsCard
                data={healthDetailedQuery.data}
                loading={healthDetailedQuery.isFetching}
              />
            ) : null}
          </Grid>
        </Grid>
      )}

      {tabValue === 2 && (
        <Grid container spacing={3}>
          <Grid item xs={12} md={8}>
            {healthReadyQuery.isLoading && !healthReadyQuery.data ? (
              <CardSkeleton />
            ) : healthReadyQuery.error ? (
              <ErrorState
                error={healthReadyQuery.error}
                onRetry={() => healthReadyQuery.refetch()}
                variant="alert"
              />
            ) : healthReadyQuery.data ? (
              <HealthChecksCard
                ready={healthReadyQuery.data.ready}
                checks={healthReadyQuery.data.checks}
                timestamp={healthReadyQuery.data.timestamp}
                loading={healthReadyQuery.isFetching}
              />
            ) : null}
          </Grid>
        </Grid>
      )}
    </Box>
  );
};

export default HealthPage;
