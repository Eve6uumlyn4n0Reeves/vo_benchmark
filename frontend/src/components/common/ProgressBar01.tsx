import React from 'react';
import { Box, LinearProgress, Typography } from '@mui/material';

interface ProgressBar01Props {
  /** 进度值，范围 0.0 到 1.0 */
  value01: number;
  /** 进度条高度，默认 4px */
  height?: number;
  /** 是否显示百分比标签，默认 true */
  showLabel?: boolean;
  /** 自定义样式 */
  sx?: object;
}

/**
 * 统一进度条组件
 * 接收 0..1 范围的进度值，自动转换为百分比显示
 */
export const ProgressBar01: React.FC<ProgressBar01Props> = ({
  value01,
  height = 4,
  showLabel = true,
  sx = {},
}) => {
  // 确保进度值在有效范围内
  const clampedValue = Math.max(0, Math.min(1, value01));
  const percentage = Math.round(clampedValue * 100);

  return (
    <Box sx={{ width: '100%', ...sx }}>
      <LinearProgress
        variant="determinate"
        value={percentage}
        sx={{
          height,
          borderRadius: height / 2,
          backgroundColor: 'rgba(0, 0, 0, 0.1)',
          '& .MuiLinearProgress-bar': {
            borderRadius: height / 2,
          },
        }}
      />
      {showLabel && (
        <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 0.5 }}>
          <Typography variant="body2" color="text.secondary">
            {percentage}%
          </Typography>
        </Box>
      )}
    </Box>
  );
};

export default ProgressBar01;
