import React from 'react';
import {
  Box,
  Typography,
  Grid,
  Button,
  Tabs,
  Tab,
} from '@mui/material';
import {
  RefreshOutlined,
} from '@mui/icons-material';
import {
  useClientConfig,
  useSystemConfig,
  useDiagnosticsConfig,
} from '@/api/services';
import { LoadingSpinner, ErrorState, CardSkeleton } from '@/components/common';
import {
  ClientConfigCard,
  SystemConfigCard,
  DiagnosticsCard,
} from '../components';

// =============================================================================
// CONFIG PAGE COMPONENT
// =============================================================================

const ConfigPage: React.FC = () => {
  const [tabValue, setTabValue] = React.useState(0);

  // API queries
  const clientConfigQuery = useClientConfig();
  const systemConfigQuery = useSystemConfig();
  const diagnosticsConfigQuery = useDiagnosticsConfig();

  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const handleRefresh = () => {
    clientConfigQuery.refetch();
    systemConfigQuery.refetch();
    diagnosticsConfigQuery.refetch();
  };

  // Loading state for initial load
  if (clientConfigQuery.isLoading && !clientConfigQuery.data) {
    return (
      <Box>
        <Typography variant="h4" component="h1" gutterBottom>
          系统配置
        </Typography>
        <LoadingSpinner message="加载配置信息..." fullHeight />
      </Box>
    );
  }

  // Error state
  if (clientConfigQuery.error && !clientConfigQuery.data) {
    return (
      <Box>
        <Typography variant="h4" component="h1" gutterBottom>
          系统配置
        </Typography>
        <ErrorState
          error={clientConfigQuery.error}
          onRetry={handleRefresh}
          title="无法获取配置信息"
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
          系统配置
        </Typography>
        <Button
          variant="outlined"
          startIcon={<RefreshOutlined />}
          onClick={handleRefresh}
          disabled={clientConfigQuery.isFetching}
        >
          刷新
        </Button>
      </Box>

      {/* Tabs */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={tabValue} onChange={handleTabChange}>
          <Tab label="客户端配置" />
          <Tab label="系统配置" />
          <Tab label="诊断信息" />
        </Tabs>
      </Box>

      {/* Tab Content */}
      {tabValue === 0 && (
        <Grid container spacing={3}>
          <Grid item xs={12}>
            {clientConfigQuery.data ? (
              <ClientConfigCard
                config={clientConfigQuery.data}
                loading={clientConfigQuery.isFetching}
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
            {systemConfigQuery.isLoading && !systemConfigQuery.data ? (
              <CardSkeleton />
            ) : systemConfigQuery.error ? (
              <ErrorState
                error={systemConfigQuery.error}
                onRetry={() => systemConfigQuery.refetch()}
                variant="alert"
              />
            ) : systemConfigQuery.data ? (
              <SystemConfigCard
                config={systemConfigQuery.data}
                loading={systemConfigQuery.isFetching}
              />
            ) : null}
          </Grid>
        </Grid>
      )}

      {tabValue === 2 && (
        <Grid container spacing={3}>
          <Grid item xs={12} md={8}>
            {diagnosticsConfigQuery.isLoading && !diagnosticsConfigQuery.data ? (
              <CardSkeleton />
            ) : diagnosticsConfigQuery.error ? (
              <ErrorState
                error={diagnosticsConfigQuery.error}
                onRetry={() => diagnosticsConfigQuery.refetch()}
                variant="alert"
              />
            ) : diagnosticsConfigQuery.data ? (
              <DiagnosticsCard
                config={diagnosticsConfigQuery.data}
                loading={diagnosticsConfigQuery.isFetching}
              />
            ) : null}
          </Grid>
        </Grid>
      )}
    </Box>
  );
};

export default ConfigPage;
