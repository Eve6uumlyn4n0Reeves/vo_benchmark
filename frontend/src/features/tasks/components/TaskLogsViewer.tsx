import React from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  Button,
  IconButton,
  Tooltip,
  LinearProgress,
  Alert,
} from '@mui/material';
import {
  RefreshOutlined,
  DownloadOutlined,
  FullscreenOutlined,
  FullscreenExitOutlined,
  PlayArrowOutlined,
  PauseOutlined,
} from '@mui/icons-material';
import { NoData } from '@/components/common';

// =============================================================================
// TASK LOGS VIEWER
// =============================================================================

interface TaskLogsViewerProps {
  logs: string[];
  loading?: boolean;
  onRefresh?: () => void;
  onDownload?: () => void;
  autoRefresh?: boolean;
  onAutoRefreshChange?: (enabled: boolean) => void;
}

export const TaskLogsViewer: React.FC<TaskLogsViewerProps> = ({
  logs,
  loading = false,
  onRefresh,
  onDownload,
  autoRefresh = false,
  onAutoRefreshChange,
}) => {
  const [isFullscreen, setIsFullscreen] = React.useState(false);
  const [shouldScrollToBottom, setShouldScrollToBottom] = React.useState(true);
  const logsContainerRef = React.useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new logs arrive
  React.useEffect(() => {
    if (shouldScrollToBottom && logsContainerRef.current) {
      logsContainerRef.current.scrollTop = logsContainerRef.current.scrollHeight;
    }
  }, [logs, shouldScrollToBottom]);

  // Check if user has scrolled up
  const handleScroll = () => {
    if (logsContainerRef.current) {
      const { scrollTop, scrollHeight, clientHeight } = logsContainerRef.current;
      const isAtBottom = scrollTop + clientHeight >= scrollHeight - 10;
      setShouldScrollToBottom(isAtBottom);
    }
  };

  const handleToggleFullscreen = () => {
    setIsFullscreen(!isFullscreen);
  };

  const handleToggleAutoRefresh = () => {
    if (onAutoRefreshChange) {
      onAutoRefreshChange(!autoRefresh);
    }
  };

  const formatLogLine = (line: string, index: number) => {
    // Simple log formatting - could be enhanced with syntax highlighting

    return (
      <Box
        key={index}
        component="div"
        sx={{
          fontFamily: 'monospace',
          fontSize: '0.75rem',
          lineHeight: 1.4,
          py: 0.25,
          px: 1,
          borderLeft: 3,
          borderColor: line.toLowerCase().includes('error') ? 'error.main' :
                      line.toLowerCase().includes('warn') ? 'warning.main' :
                      line.toLowerCase().includes('info') ? 'info.main' : 'transparent',
          backgroundColor: index % 2 === 0 ? 'grey.50' : 'transparent',
          '&:hover': {
            backgroundColor: 'action.hover',
          },
        }}
      >
        <Box component="span" color="text.secondary" mr={1}>
          [{String(index + 1).padStart(4, '0')}]
        </Box>
        {line}
      </Box>
    );
  };

  return (
    <Card sx={{ height: isFullscreen ? '100vh' : 'auto' }}>
      <CardContent sx={{ height: isFullscreen ? '100%' : 'auto', display: 'flex', flexDirection: 'column' }}>
        {loading && <LinearProgress sx={{ mb: 2 }} />}
        
        {/* Header */}
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Typography variant="h6" component="h3">
            任务日志
          </Typography>
          
          <Box display="flex" gap={1}>
            {onAutoRefreshChange && (
              <Tooltip title={autoRefresh ? '停止自动刷新' : '开启自动刷新'}>
                <IconButton
                  size="small"
                  onClick={handleToggleAutoRefresh}
                  color={autoRefresh ? 'primary' : 'default'}
                >
                  {autoRefresh ? <PauseOutlined /> : <PlayArrowOutlined />}
                </IconButton>
              </Tooltip>
            )}
            
            {onRefresh && (
              <Tooltip title="刷新日志">
                <IconButton size="small" onClick={onRefresh} disabled={loading}>
                  <RefreshOutlined />
                </IconButton>
              </Tooltip>
            )}
            
            {onDownload && logs.length > 0 && (
              <Tooltip title="下载日志">
                <IconButton size="small" onClick={onDownload}>
                  <DownloadOutlined />
                </IconButton>
              </Tooltip>
            )}
            
            <Tooltip title={isFullscreen ? '退出全屏' : '全屏显示'}>
              <IconButton size="small" onClick={handleToggleFullscreen}>
                {isFullscreen ? <FullscreenExitOutlined /> : <FullscreenOutlined />}
              </IconButton>
            </Tooltip>
          </Box>
        </Box>

        {/* Auto-refresh indicator */}
        {autoRefresh && (
          <Alert severity="info" sx={{ mb: 2 }}>
            自动刷新已开启，每5秒更新一次日志
          </Alert>
        )}

        {/* Logs Content */}
        {logs.length === 0 ? (
          <NoData
            title="暂无日志"
            description="该任务尚未生成日志信息"
            compact
          />
        ) : (
          <Box
            ref={logsContainerRef}
            onScroll={handleScroll}
            sx={{
              flexGrow: 1,
              border: 1,
              borderColor: 'divider',
              borderRadius: 1,
              backgroundColor: 'grey.900',
              color: 'grey.100',
              overflow: 'auto',
              maxHeight: isFullscreen ? 'calc(100vh - 200px)' : 400,
              minHeight: 200,
            }}
          >
            {logs.map((line, index) => formatLogLine(line, index))}
          </Box>
        )}

        {/* Footer Info */}
        <Box mt={2} display="flex" justifyContent="space-between" alignItems="center">
          <Typography variant="body2" color="text.secondary">
            共 {logs.length} 行日志
            {!shouldScrollToBottom && ' | 滚动到底部查看最新日志'}
          </Typography>
          
          {!shouldScrollToBottom && (
            <Button
              size="small"
              onClick={() => {
                setShouldScrollToBottom(true);
                if (logsContainerRef.current) {
                  logsContainerRef.current.scrollTop = logsContainerRef.current.scrollHeight;
                }
              }}
            >
              滚动到底部
            </Button>
          )}
        </Box>
      </CardContent>
    </Card>
  );
};
