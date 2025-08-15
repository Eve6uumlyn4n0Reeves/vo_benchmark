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
  Chip,
  Divider,
  Alert,
} from '@mui/material';
import {
  ArrowBackOutlined,
  RefreshOutlined,
  AssessmentOutlined,
} from '@mui/icons-material';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import { useExperiment, useExperimentHistory } from '@/api/services';
import {
  LoadingSpinner,
  ErrorState,
  CardSkeleton,
} from '@/components/common';
import { ExperimentStatusChip } from '../components';

// =============================================================================
// EXPERIMENT DETAIL PAGE
// =============================================================================

const ExperimentDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();

  const currentTab = searchParams.get('tab') || 'details';

  const experimentQuery = useExperiment(id!);
  const historyQuery = useExperimentHistory(id!);

  const handleTabChange = (_event: React.SyntheticEvent, newValue: string) => {
    setSearchParams({ tab: newValue });
  };

  const handleBack = () => {
    navigate('/experiments');
  };

  const handleRefresh = () => {
    experimentQuery.refetch();
    if (currentTab === 'history') {
      historyQuery.refetch();
    }
  };

  const handleViewResults = () => {
    navigate(`/results/${id}`);
  };

  const formatDate = (dateString: string) => {
    try {
      return new Date(dateString).toLocaleString('zh-CN');
    } catch {
      return dateString;
    }
  };

  // Loading state
  if (experimentQuery.isLoading && !experimentQuery.data) {
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
            实验详情
          </Typography>
        </Box>
        <LoadingSpinner message="加载实验详情..." fullHeight />
      </Box>
    );
  }

  // Error state
  if (experimentQuery.error && !experimentQuery.data) {
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
            实验详情
          </Typography>
        </Box>
        <ErrorState
          error={experimentQuery.error}
          onRetry={handleRefresh}
          title="无法加载实验详情"
          description="请检查实验ID是否正确或网络连接"
          fullHeight
        />
      </Box>
    );
  }

  const experiment = experimentQuery.data;
  if (!experiment) {
    return null;
  }

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
            <ExperimentStatusChip status={experiment.status} />
          </Box>
          <Typography variant="h4" component="h1">
            {experiment.name}
          </Typography>
          {experiment.description && (
            <Typography variant="body1" color="text.secondary" sx={{ mt: 1 }}>
              {experiment.description}
            </Typography>
          )}
        </Box>

        <Box display="flex" gap={2}>
          <Button
            variant="outlined"
            startIcon={<RefreshOutlined />}
            onClick={handleRefresh}
            disabled={experimentQuery.isFetching}
          >
            刷新
          </Button>
          {experiment.status === 'COMPLETED' && (
            <Button
              variant="contained"
              startIcon={<AssessmentOutlined />}
              onClick={handleViewResults}
            >
              查看结果
            </Button>
          )}
        </Box>
      </Box>

      {/* Error Alert */}
      {experimentQuery.error && experimentQuery.data && (
        <Alert severity="warning" sx={{ mb: 3 }}>
          数据可能不是最新的，请尝试刷新页面
        </Alert>
      )}

      {/* Tabs */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={currentTab} onChange={handleTabChange}>
          <Tab label="详细信息" value="details" />
          <Tab label="配置" value="config" />
          <Tab label="历史记录" value="history" />
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
                      实验ID
                    </Typography>
                    <Typography variant="body2" fontFamily="monospace">
                      {experiment.experiment_id}
                    </Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="body2" color="text.secondary">
                      状态
                    </Typography>
                    <ExperimentStatusChip status={experiment.status} size="small" />
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="body2" color="text.secondary">
                      创建时间
                    </Typography>
                    <Typography variant="body2">
                      {formatDate(experiment.created_at)}
                    </Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="body2" color="text.secondary">
                      更新时间
                    </Typography>
                    <Typography variant="body2">
                      {formatDate(experiment.updated_at)}
                    </Typography>
                  </Grid>
                  {experiment.completed_at && (
                    <Grid item xs={12}>
                      <Typography variant="body2" color="text.secondary">
                        完成时间
                      </Typography>
                      <Typography variant="body2">
                        {formatDate(experiment.completed_at)}
                      </Typography>
                    </Grid>
                  )}
                </Grid>
              </CardContent>
            </Card>
          </Grid>

          {/* Summary Stats */}
          {experiment.summary && (
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    执行统计
                  </Typography>
                  <Grid container spacing={2}>
                    <Grid item xs={6}>
                      <Typography variant="body2" color="text.secondary">
                        总运行次数
                      </Typography>
                      <Typography variant="h6">
                        {experiment.summary.total_runs}
                      </Typography>
                    </Grid>
                    <Grid item xs={6}>
                      <Typography variant="body2" color="text.secondary">
                        成功次数
                      </Typography>
                      <Typography variant="h6" color="success.main">
                        {experiment.summary.successful_runs}
                      </Typography>
                    </Grid>
                    <Grid item xs={6}>
                      <Typography variant="body2" color="text.secondary">
                        失败次数
                      </Typography>
                      <Typography variant="h6" color="error.main">
                        {experiment.summary.failed_runs}
                      </Typography>
                    </Grid>
                    <Grid item xs={6}>
                      <Typography variant="body2" color="text.secondary">
                        平均FPS
                      </Typography>
                      <Typography variant="h6">
                        {experiment.summary.average_fps.toFixed(1)}
                      </Typography>
                    </Grid>
                  </Grid>
                </CardContent>
              </Card>
            </Grid>
          )}

          {/* Algorithms */}
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  测试算法
                </Typography>
                <Box display="flex" flexWrap="wrap" gap={1}>
                  {experiment.algorithms.map((algorithm) => (
                    <Chip
                      key={algorithm}
                      label={algorithm}
                      variant="outlined"
                      size="small"
                    />
                  ))}
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {currentTab === 'config' && (
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              实验配置
            </Typography>
            <Box
              component="pre"
              sx={{
                backgroundColor: 'grey.100',
                p: 2,
                borderRadius: 1,
                overflow: 'auto',
                fontFamily: 'monospace',
                fontSize: '0.875rem',
                whiteSpace: 'pre-wrap',
                wordBreak: 'break-word',
              }}
            >
              {JSON.stringify(experiment.config, null, 2)}
            </Box>
          </CardContent>
        </Card>
      )}

      {currentTab === 'history' && (
        <Box>
          {historyQuery.isLoading ? (
            <CardSkeleton />
          ) : historyQuery.error ? (
            <ErrorState
              error={historyQuery.error}
              onRetry={() => historyQuery.refetch()}
              variant="alert"
            />
          ) : historyQuery.data && historyQuery.data.length > 0 ? (
            <Grid container spacing={2}>
              {historyQuery.data.map((historyItem, index) => (
                <Grid item xs={12} key={index}>
                  <Card>
                    <CardContent>
                      <Box display="flex" justifyContent="space-between" alignItems="center">
                        <Typography variant="subtitle1">
                          版本 {index + 1}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          {formatDate(historyItem.updated_at)}
                        </Typography>
                      </Box>
                      <Divider sx={{ my: 1 }} />
                      <Typography variant="body2">
                        状态: <ExperimentStatusChip status={historyItem.status} size="small" />
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
              ))}
            </Grid>
          ) : (
            <Typography variant="body1" color="text.secondary" textAlign="center" py={4}>
              暂无历史记录
            </Typography>
          )}
        </Box>
      )}
    </Box>
  );
};

export default ExperimentDetailPage;
