import React from 'react';
import {
  Box,
  Typography,
  Button,
  Alert,
  AlertTitle,
  Paper,
  Collapse,
  IconButton,
} from '@mui/material';
import {
  ErrorOutlineOutlined,
  RefreshOutlined,
  ExpandMoreOutlined,
  ExpandLessOutlined,
  BugReportOutlined,
} from '@mui/icons-material';
import { isApiError } from '@/api/httpClient';

// =============================================================================
// ERROR STATE TYPES
// =============================================================================

interface ErrorStateProps {
  error: Error | unknown;
  onRetry?: () => void;
  title?: string;
  description?: string;
  showDetails?: boolean;
  fullHeight?: boolean;
  variant?: 'alert' | 'page' | 'inline';
}

// =============================================================================
// ERROR STATE COMPONENT
// =============================================================================

export const ErrorState: React.FC<ErrorStateProps> = ({
  error,
  onRetry,
  title,
  description,
  showDetails = false,
  fullHeight = false,
  variant = 'page',
}) => {
  const [detailsOpen, setDetailsOpen] = React.useState(false);

  // Extract error information
  const getErrorInfo = () => {
    if (isApiError(error)) {
      return {
        title: error.apiError.error_code || 'API错误',
        message: error.apiError.message || error.message,
        details: error.apiError.details,
        requestId: error.apiError.request_id,
        status: (error as any).status,
      };
    }

    if (error instanceof Error) {
      return {
        title: '应用错误',
        message: error.message,
        details: null,
        requestId: null,
        status: null,
      };
    }

    return {
      title: '未知错误',
      message: '发生了未知错误',
      details: null,
      requestId: null,
      status: null,
    };
  };

  const errorInfo = getErrorInfo();
  const finalTitle = title || errorInfo.title;
  const finalDescription = description || errorInfo.message;

  // Alert variant
  if (variant === 'alert') {
    return (
      <Alert
        severity="error"
        action={
          onRetry ? (
            <Button
              color="inherit"
              size="small"
              onClick={onRetry}
              startIcon={<RefreshOutlined />}
            >
              重试
            </Button>
          ) : undefined
        }
      >
        <AlertTitle>{finalTitle}</AlertTitle>
        {finalDescription}
        {showDetails && errorInfo.requestId && (
          <Typography variant="caption" display="block" sx={{ mt: 1 }}>
            请求ID: {errorInfo.requestId}
          </Typography>
        )}
      </Alert>
    );
  }

  // Inline variant
  if (variant === 'inline') {
    return (
      <Box
        display="flex"
        alignItems="center"
        gap={2}
        p={2}
        bgcolor="error.light"
        color="error.contrastText"
        borderRadius={1}
      >
        <ErrorOutlineOutlined />
        <Box flexGrow={1}>
          <Typography variant="body2" fontWeight={500}>
            {finalTitle}
          </Typography>
          <Typography variant="caption">
            {finalDescription}
          </Typography>
        </Box>
        {onRetry && (
          <IconButton
            size="small"
            onClick={onRetry}
            sx={{ color: 'inherit' }}
            aria-label="重试"
          >
            <RefreshOutlined />
          </IconButton>
        )}
      </Box>
    );
  }

  // Page variant (default)
  return (
    <Box
      display="flex"
      flexDirection="column"
      alignItems="center"
      justifyContent="center"
      textAlign="center"
      minHeight={fullHeight ? '400px' : '200px'}
      p={4}
      role="alert"
      aria-label={finalTitle}
    >
      {/* Error Icon */}
      <ErrorOutlineOutlined
        sx={{
          fontSize: 64,
          color: 'error.main',
          mb: 2,
        }}
      />

      {/* Title */}
      <Typography
        variant="h5"
        color="error.main"
        gutterBottom
        sx={{ fontWeight: 500 }}
      >
        {finalTitle}
      </Typography>

      {/* Description */}
      <Typography
        variant="body1"
        color="text.secondary"
        sx={{ mb: 3, maxWidth: 500 }}
      >
        {finalDescription}
      </Typography>

      {/* Action Buttons */}
      <Box display="flex" gap={2} flexWrap="wrap" justifyContent="center">
        {onRetry && (
          <Button
            variant="contained"
            startIcon={<RefreshOutlined />}
            onClick={onRetry}
          >
            重试
          </Button>
        )}

        {showDetails && (errorInfo.details || errorInfo.requestId) && (
          <Button
            variant="outlined"
            startIcon={detailsOpen ? <ExpandLessOutlined /> : <ExpandMoreOutlined />}
            onClick={() => setDetailsOpen(!detailsOpen)}
          >
            {detailsOpen ? '隐藏详情' : '显示详情'}
          </Button>
        )}
      </Box>

      {/* Error Details */}
      {showDetails && (
        <Collapse in={detailsOpen} sx={{ mt: 3, width: '100%', maxWidth: 600 }}>
          <Paper elevation={1} sx={{ p: 2, bgcolor: 'grey.50' }}>
            <Box display="flex" alignItems="center" gap={1} mb={2}>
              <BugReportOutlined fontSize="small" />
              <Typography variant="subtitle2" fontWeight={500}>
                错误详情
              </Typography>
            </Box>

            {errorInfo.status && (
              <Typography variant="body2" sx={{ mb: 1 }}>
                <strong>状态码:</strong> {errorInfo.status}
              </Typography>
            )}

            {errorInfo.requestId && (
              <Typography variant="body2" sx={{ mb: 1 }}>
                <strong>请求ID:</strong> {errorInfo.requestId}
              </Typography>
            )}

            {errorInfo.details && (
              <Box>
                <Typography variant="body2" sx={{ mb: 1 }}>
                  <strong>详细信息:</strong>
                </Typography>
                <Typography
                  variant="body2"
                  component="pre"
                  sx={{
                    backgroundColor: 'grey.100',
                    p: 1,
                    borderRadius: 1,
                    overflow: 'auto',
                    fontFamily: 'monospace',
                    fontSize: '0.75rem',
                    whiteSpace: 'pre-wrap',
                    wordBreak: 'break-word',
                  }}
                >
                  {JSON.stringify(errorInfo.details, null, 2)}
                </Typography>
              </Box>
            )}
          </Paper>
        </Collapse>
      )}
    </Box>
  );
};
