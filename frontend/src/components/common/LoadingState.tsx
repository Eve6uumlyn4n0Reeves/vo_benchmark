import React from 'react';
import {
  Box,
  CircularProgress,
  Skeleton,
  Typography,
  Card,
  CardContent,
} from '@mui/material';

// =============================================================================
// LOADING SPINNER
// =============================================================================

interface LoadingSpinnerProps {
  size?: number;
  message?: string;
  fullHeight?: boolean;
}

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  size = 40,
  message = '加载中...',
  fullHeight = false,
}) => {
  return (
    <Box
      display="flex"
      flexDirection="column"
      alignItems="center"
      justifyContent="center"
      gap={2}
      minHeight={fullHeight ? '400px' : '200px'}
      role="status"
      aria-label={message}
    >
      <CircularProgress size={size} />
      {message && (
        <Typography variant="body2" color="text.secondary">
          {message}
        </Typography>
      )}
    </Box>
  );
};

// =============================================================================
// SKELETON LOADERS
// =============================================================================

export const CardSkeleton: React.FC = () => {
  return (
    <Card>
      <CardContent>
        <Skeleton variant="text" width="60%" height={32} sx={{ mb: 1 }} />
        <Skeleton variant="text" width="100%" height={20} sx={{ mb: 0.5 }} />
        <Skeleton variant="text" width="80%" height={20} sx={{ mb: 2 }} />
        <Skeleton variant="rectangular" width="100%" height={60} />
      </CardContent>
    </Card>
  );
};

export const TableSkeleton: React.FC<{ rows?: number }> = ({ rows = 5 }) => {
  return (
    <Box>
      {Array.from({ length: rows }).map((_, index) => (
        <Box key={index} display="flex" gap={2} mb={1}>
          <Skeleton variant="text" width="20%" height={40} />
          <Skeleton variant="text" width="30%" height={40} />
          <Skeleton variant="text" width="25%" height={40} />
          <Skeleton variant="text" width="25%" height={40} />
        </Box>
      ))}
    </Box>
  );
};

export const MetricsSkeleton: React.FC = () => {
  return (
    <Box display="flex" flexDirection="column" gap={2}>
      <Skeleton variant="text" width="40%" height={32} />
      <Box display="grid" gridTemplateColumns="repeat(auto-fit, minmax(200px, 1fr))" gap={2}>
        {Array.from({ length: 4 }).map((_, index) => (
          <Card key={index}>
            <CardContent>
              <Skeleton variant="text" width="70%" height={24} sx={{ mb: 1 }} />
              <Skeleton variant="text" width="50%" height={36} sx={{ mb: 1 }} />
              <Skeleton variant="text" width="80%" height={16} />
            </CardContent>
          </Card>
        ))}
      </Box>
    </Box>
  );
};

// =============================================================================
// LOADING OVERLAY
// =============================================================================

interface LoadingOverlayProps {
  loading: boolean;
  children: React.ReactNode;
  message?: string;
}

export const LoadingOverlay: React.FC<LoadingOverlayProps> = ({
  loading,
  children,
  message = '加载中...',
}) => {
  return (
    <Box position="relative">
      {children}
      {loading && (
        <Box
          position="absolute"
          top={0}
          left={0}
          right={0}
          bottom={0}
          display="flex"
          alignItems="center"
          justifyContent="center"
          bgcolor="rgba(255, 255, 255, 0.8)"
          zIndex={1}
          role="status"
          aria-label={message}
        >
          <Box display="flex" flexDirection="column" alignItems="center" gap={2}>
            <CircularProgress />
            <Typography variant="body2" color="text.secondary">
              {message}
            </Typography>
          </Box>
        </Box>
      )}
    </Box>
  );
};
