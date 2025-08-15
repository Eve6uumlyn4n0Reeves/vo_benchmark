import { Component, ErrorInfo, ReactNode } from 'react';
import { env } from '@/utils/env';
import {
  Box,
  Typography,
  Button,
  Alert,
  AlertTitle,
  Container,
  Paper,
} from '@mui/material';
import { RefreshOutlined, BugReportOutlined } from '@mui/icons-material';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    };
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    return {
      hasError: true,
      error,
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    this.setState({
      error,
      errorInfo,
    });

    // Log error to console
    console.error('ErrorBoundary caught an error:', error, errorInfo);

    // Call custom error handler if provided
    this.props.onError?.(error, errorInfo);

    // In production, you might want to send this to an error reporting service
    if (env.isProd()) {
      // Example: Send to error reporting service
      // errorReportingService.captureException(error, { extra: errorInfo });
    }
  }

  handleRetry = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    });
  };

  handleReload = () => {
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      // Custom fallback UI
      if (this.props.fallback) {
        return this.props.fallback;
      }

      // Default error UI
      return (
        <Container maxWidth="md" sx={{ py: 4 }}>
          <Paper elevation={3} sx={{ p: 4 }}>
            <Alert severity="error" sx={{ mb: 3 }}>
              <AlertTitle>
                <Box display="flex" alignItems="center" gap={1}>
                  <BugReportOutlined />
                  应用程序遇到错误
                </Box>
              </AlertTitle>
              很抱歉，应用程序遇到了意外错误。请尝试刷新页面或联系技术支持。
            </Alert>

            <Box sx={{ mb: 3 }}>
              <Typography variant="h6" gutterBottom>
                错误详情
              </Typography>
              <Typography
                variant="body2"
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
                {this.state.error?.message || '未知错误'}
              </Typography>
            </Box>

            {env.isDev() && this.state.errorInfo && (
              <Box sx={{ mb: 3 }}>
                <Typography variant="h6" gutterBottom>
                  组件堆栈 (开发模式)
                </Typography>
                <Typography
                  variant="body2"
                  component="pre"
                  sx={{
                    backgroundColor: 'grey.100',
                    p: 2,
                    borderRadius: 1,
                    overflow: 'auto',
                    fontFamily: 'monospace',
                    fontSize: '0.75rem',
                    whiteSpace: 'pre-wrap',
                    wordBreak: 'break-word',
                    maxHeight: 200,
                  }}
                >
                  {this.state.errorInfo.componentStack}
                </Typography>
              </Box>
            )}

            <Box display="flex" gap={2} flexWrap="wrap">
              <Button
                variant="contained"
                startIcon={<RefreshOutlined />}
                onClick={this.handleRetry}
                aria-label="重试"
              >
                重试
              </Button>
              <Button
                variant="outlined"
                onClick={this.handleReload}
                aria-label="刷新页面"
              >
                刷新页面
              </Button>
            </Box>
          </Paper>
        </Container>
      );
    }

    return this.props.children;
  }
}
