import React from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  List,
  ListItem,
  ListItemText,
  Chip,
  LinearProgress,
} from '@mui/material';
import {
  FolderOutlined,
  ScienceOutlined,
} from '@mui/icons-material';
import type { DiagnosticsConfig } from '@/types/api';

// =============================================================================
// DIAGNOSTICS CARD
// =============================================================================

interface DiagnosticsCardProps {
  config: DiagnosticsConfig;
  loading?: boolean;
}

export const DiagnosticsCard: React.FC<DiagnosticsCardProps> = ({
  config,
  loading = false,
}) => {
  return (
    <Card>
      <CardContent>
        {loading && <LinearProgress sx={{ mb: 2 }} />}
        
        <Typography variant="h6" component="h2" gutterBottom>
          诊断配置
        </Typography>

        {/* Results Root */}
        <Box mb={3}>
          <Box display="flex" alignItems="center" gap={1} mb={1}>
            <FolderOutlined fontSize="small" />
            <Typography variant="subtitle2">
              结果根目录
            </Typography>
          </Box>
          <Typography
            variant="body2"
            sx={{
              backgroundColor: 'grey.100',
              p: 1,
              borderRadius: 1,
              fontFamily: 'monospace',
              wordBreak: 'break-all',
            }}
          >
            {config.results_root}
          </Typography>
        </Box>

        {/* Visible Experiments */}
        <Box mb={2}>
          <Box display="flex" alignItems="center" gap={1} mb={1}>
            <ScienceOutlined fontSize="small" />
            <Typography variant="subtitle2">
              可见实验 ({config.count} 个)
            </Typography>
          </Box>
          
          {config.visible_experiments.length > 0 ? (
            <List dense>
              {config.visible_experiments.map((experimentId, index) => (
                <ListItem key={index} sx={{ px: 0, py: 0.5 }}>
                  <ListItemText
                    primary={
                      <Chip
                        label={experimentId}
                        size="small"
                        variant="outlined"
                        sx={{ fontFamily: 'monospace' }}
                      />
                    }
                  />
                </ListItem>
              ))}
            </List>
          ) : (
            <Typography variant="body2" color="text.secondary" textAlign="center" py={2}>
              暂无可见实验
            </Typography>
          )}
        </Box>

        {/* Summary */}
        <Box
          sx={{
            backgroundColor: 'primary.light',
            color: 'primary.contrastText',
            p: 2,
            borderRadius: 1,
            textAlign: 'center',
          }}
        >
          <Typography variant="body2">
            系统当前管理 <strong>{config.count}</strong> 个实验
          </Typography>
        </Box>
      </CardContent>
    </Card>
  );
};
