import React from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  LinearProgress,
} from '@mui/material';

// =============================================================================
// SYSTEM CONFIG CARD
// =============================================================================

interface SystemConfigCardProps {
  config: Record<string, unknown>;
  loading?: boolean;
}

export const SystemConfigCard: React.FC<SystemConfigCardProps> = ({
  config,
  loading = false,
}) => {
  return (
    <Card>
      <CardContent>
        {loading && <LinearProgress sx={{ mb: 2 }} />}
        
        <Typography variant="h6" component="h2" gutterBottom>
          系统配置
        </Typography>

        <Typography variant="body2" color="text.secondary" gutterBottom>
          非敏感系统配置信息
        </Typography>

        {Object.keys(config).length > 0 ? (
          <Box
            component="pre"
            sx={{
              backgroundColor: 'grey.100',
              p: 2,
              borderRadius: 1,
              overflow: 'auto',
              fontFamily: 'monospace',
              fontSize: '0.75rem',
              maxHeight: 400,
              whiteSpace: 'pre-wrap',
              wordBreak: 'break-word',
            }}
          >
            {JSON.stringify(config, null, 2)}
          </Box>
        ) : (
          <Typography variant="body2" color="text.secondary" textAlign="center" py={4}>
            暂无系统配置信息
          </Typography>
        )}
      </CardContent>
    </Card>
  );
};
