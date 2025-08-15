import React from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  Grid,
  Chip,
  LinearProgress,
} from '@mui/material';
import type { ClientConfig } from '@/types/api';

// =============================================================================
// CONFIG ITEM
// =============================================================================

interface ConfigItemProps {
  label: string;
  value: string | number | string[];
  unit?: string;
}

const ConfigItem: React.FC<ConfigItemProps> = ({ label, value, unit }) => {
  const renderValue = () => {
    if (Array.isArray(value)) {
      return (
        <Box display="flex" flexWrap="wrap" gap={0.5}>
          {value.map((item, index) => (
            <Chip key={index} label={item} size="small" variant="outlined" />
          ))}
        </Box>
      );
    }

    return (
      <Typography variant="body1" fontWeight={500}>
        {value}
        {unit && (
          <Typography component="span" variant="body2" color="text.secondary" ml={0.5}>
            {unit}
          </Typography>
        )}
      </Typography>
    );
  };

  return (
    <Box>
      <Typography variant="body2" color="text.secondary" gutterBottom>
        {label}
      </Typography>
      {renderValue()}
    </Box>
  );
};

// =============================================================================
// CLIENT CONFIG CARD
// =============================================================================

interface ClientConfigCardProps {
  config: ClientConfig;
  loading?: boolean;
}

export const ClientConfigCard: React.FC<ClientConfigCardProps> = ({
  config,
  loading = false,
}) => {
  return (
    <Card>
      <CardContent>
        {loading && <LinearProgress sx={{ mb: 2 }} />}
        
        <Typography variant="h6" component="h2" gutterBottom>
          客户端配置
        </Typography>

        <Typography variant="subtitle2" gutterBottom sx={{ mt: 2, mb: 1 }}>
          实验默认值
        </Typography>
        
        <Grid container spacing={2}>
          <Grid item xs={12} sm={6} md={4}>
            <ConfigItem
              label="默认运行次数"
              value={config.experiment.defaultRuns}
              unit="次"
            />
          </Grid>
          
          <Grid item xs={12} sm={6} md={4}>
            <ConfigItem
              label="并行任务数"
              value={config.experiment.defaultParallelJobs}
              unit="个"
            />
          </Grid>
          
          <Grid item xs={12} sm={6} md={4}>
            <ConfigItem
              label="最大特征点数"
              value={config.experiment.defaultMaxFeatures}
              unit="个"
            />
          </Grid>
          
          <Grid item xs={12} sm={6} md={4}>
            <ConfigItem
              label="RANSAC阈值"
              value={config.experiment.defaultRansacThreshold}
            />
          </Grid>
          
          <Grid item xs={12} sm={6} md={4}>
            <ConfigItem
              label="RANSAC置信度"
              value={config.experiment.defaultRansacConfidence}
            />
          </Grid>
          
          <Grid item xs={12} sm={6} md={4}>
            <ConfigItem
              label="RANSAC最大迭代"
              value={config.experiment.defaultRansacMaxIters}
              unit="次"
            />
          </Grid>
          
          <Grid item xs={12} sm={6} md={4}>
            <ConfigItem
              label="比率阈值"
              value={config.experiment.defaultRatioThreshold}
            />
          </Grid>
        </Grid>

        <Typography variant="subtitle2" gutterBottom sx={{ mt: 3, mb: 1 }}>
          算法配置
        </Typography>
        
        <Grid container spacing={2}>
          <Grid item xs={12} sm={6}>
            <ConfigItem
              label="特征类型"
              value={config.algorithms.featureTypes}
            />
          </Grid>
          
          <Grid item xs={12} sm={6}>
            <ConfigItem
              label="RANSAC类型"
              value={config.algorithms.ransacTypes}
            />
          </Grid>
        </Grid>
      </CardContent>
    </Card>
  );
};
