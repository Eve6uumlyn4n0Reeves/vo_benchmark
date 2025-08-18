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
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
  Chip,
} from '@mui/material';
import {
  VisibilityOutlined,
  AssessmentOutlined,
  HistoryOutlined,
  DeleteOutlined,
  MoreVertOutlined,
} from '@mui/icons-material';
import { useResultsDiagnostics } from '@/api/services/results';

import { useNavigate } from 'react-router-dom';
import type { Experiment } from '@/types/api';
import { ExperimentStatusChip } from './ExperimentStatusChip';

// =============================================================================
// EXPERIMENT CARD
// =============================================================================

interface ExperimentCardProps {
  experiment: Experiment;
  onDelete?: (experimentId: string) => void;
}

const ExperimentCard: React.FC<ExperimentCardProps> = ({ experiment, onDelete }) => {
  const navigate = useNavigate();
  const [menuAnchorEl, setMenuAnchorEl] = React.useState<null | HTMLElement>(null);
  const menuOpen = Boolean(menuAnchorEl);

  const formatDate = (dateString: string) => {
    try {
      return new Date(dateString).toLocaleString('zh-CN');
    } catch {
      return dateString;
    }
  };

  // Check if results are ready for viewing: use backend diagnostics
  const isExperimentCompleted = experiment.status === 'COMPLETED';
  const { data: diag, isLoading: diagLoading } = useResultsDiagnostics(experiment.experiment_id);
  const resultReady = React.useMemo(() => {
    if (!isExperimentCompleted) return false;
    const p = (diag as any)?.per_algorithm || {};
    return Object.values(p).some((v: any) => v && (v as any).metrics_exists);
  }, [isExperimentCompleted, diag])
  // 避免闪烁：仅在诊断已返回且明确不可用时显示“结果未就绪”
  const showResultsNotReady = isExperimentCompleted && !diagLoading && !resultReady;

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setMenuAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setMenuAnchorEl(null);
  };

  const handleDelete = () => {
    handleMenuClose();
    if (onDelete) {
      onDelete(experiment.experiment_id);
    }
  };

  const canDelete = experiment.status !== 'RUNNING';

  const handleViewDetails = () => {
    navigate(`/experiments/${experiment.experiment_id}`);
  };

  const handleViewResults = () => {
    navigate(`/results/${experiment.experiment_id}`);
  };

  const handleViewHistory = () => {
    navigate(`/experiments/${experiment.experiment_id}?tab=history`);
  };

  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        {/* Header */}
        <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={2}>
          <Box flexGrow={1} mr={2}>
            <Typography variant="h6" component="h3" gutterBottom>
              {experiment.name}
            </Typography>
            {experiment.description && (
              <Typography variant="body2" color="text.secondary" gutterBottom>
                {experiment.description}
              </Typography>
            )}
          </Box>
          <Box display="flex" alignItems="center" gap={1}>
            <ExperimentStatusChip status={experiment.status} />
            {showResultsNotReady && (
              <Tooltip title="结果未就绪">
                <Chip
                  label="结果未就绪"
                  size="small"
                  color="warning"
                  variant="outlined"
                />
              </Tooltip>
            )}
            <IconButton size="small" onClick={handleMenuOpen}>
              <MoreVertOutlined />
            </IconButton>
          </Box>
        </Box>

        {/* Metadata */}
        <Grid container spacing={2} sx={{ mb: 2 }}>
          <Grid item xs={6}>
            <Typography variant="caption" color="text.secondary">
              创建时间
            </Typography>
            <Typography variant="body2">
              {formatDate(experiment.created_at)}
            </Typography>
          </Grid>
          <Grid item xs={6}>
            <Typography variant="caption" color="text.secondary">
              更新时间
            </Typography>
            <Typography variant="body2">
              {formatDate(experiment.updated_at)}
            </Typography>
          </Grid>
        </Grid>

        {/* Config Summary */}
        <Box mb={2}>
          <Typography variant="caption" color="text.secondary">
            配置概要
          </Typography>
          <Typography variant="body2">
            特征({experiment.config.feature_types.length}) × 估计({experiment.config.ransac_types.length})
            = 组合 {experiment.config.feature_types.length * experiment.config.ransac_types.length}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            序列 {experiment.config.sequences.length} × 次数 {experiment.config.num_runs}
          </Typography>
        </Box>

        {/* Summary Stats */}
        {experiment.summary && (
          <Box mb={2}>
            <Typography variant="caption" color="text.secondary">
              执行统计
            </Typography>
            <Typography variant="body2">
              成功: {experiment.summary.successful_runs}/{experiment.summary.total_runs} ·
              平均FPS: {experiment.summary.average_fps.toFixed(1)}
            </Typography>
          </Box>
        )}

        <Divider sx={{ my: 2 }} />

        {/* Actions */}
        <Box display="flex" justifyContent="flex-end" gap={1}>
          <Tooltip title="查看详情">
            <IconButton size="small" onClick={handleViewDetails}>
              <VisibilityOutlined />
            </IconButton>
          </Tooltip>

          {experiment.status === 'COMPLETED' && (
            <Tooltip title="查看结果">
              <IconButton size="small" onClick={handleViewResults}>
                <AssessmentOutlined />
              </IconButton>
            </Tooltip>
          )}

          <Tooltip title="查看历史">
            <IconButton size="small" onClick={handleViewHistory}>
              <HistoryOutlined />
            </IconButton>
          </Tooltip>
        </Box>

        {/* Action Menu */}
        <Menu
          anchorEl={menuAnchorEl}
          open={menuOpen}
          onClose={handleMenuClose}
          anchorOrigin={{
            vertical: 'bottom',
            horizontal: 'right',
          }}
          transformOrigin={{
            vertical: 'top',
            horizontal: 'right',
          }}
        >
          <MenuItem onClick={handleDelete} disabled={!canDelete}>
            <ListItemIcon>
              <DeleteOutlined fontSize="small" />
            </ListItemIcon>
            <ListItemText>
              {canDelete ? '删除实验' : '运行中无法删除'}
            </ListItemText>
          </MenuItem>
        </Menu>
      </CardContent>
    </Card>
  );
};

// =============================================================================
// EXPERIMENTS LIST
// =============================================================================

interface ExperimentsListProps {
  experiments: Experiment[];
  loading?: boolean;
  onDelete?: (experimentId: string) => void;
}

export const ExperimentsList: React.FC<ExperimentsListProps> = ({
  experiments,
  onDelete,
}) => {
  if (experiments.length === 0) {
    return (
      <Box textAlign="center" py={8}>
        <Typography variant="h6" color="text.secondary" gutterBottom>
          暂无实验
        </Typography>
        <Typography variant="body2" color="text.disabled">
          点击"创建实验"开始您的第一个实验
        </Typography>
      </Box>
    );
  }

  return (
    <Grid container spacing={3}>
      {experiments.map((experiment) => (
        <Grid item xs={12} sm={6} lg={4} key={experiment.experiment_id}>
          <ExperimentCard experiment={experiment} onDelete={onDelete} />
        </Grid>
      ))}
    </Grid>
  );
};
