import React from 'react';
import {
  Box,
  Typography,
  Button,
  Paper,
  SvgIcon,
} from '@mui/material';
import {
  InboxOutlined,
  SearchOffOutlined,
  ErrorOutlineOutlined,
  RefreshOutlined,
} from '@mui/icons-material';

// =============================================================================
// EMPTY STATE TYPES
// =============================================================================

export type EmptyStateVariant = 'no-data' | 'no-results' | 'error' | 'custom';

interface EmptyStateProps {
  variant?: EmptyStateVariant;
  title?: string;
  description?: string;
  icon?: React.ReactElement;
  action?: {
    label: string;
    onClick: () => void;
    variant?: 'contained' | 'outlined' | 'text';
  };
  fullHeight?: boolean;
  compact?: boolean;
}

// =============================================================================
// EMPTY STATE COMPONENT
// =============================================================================

export const EmptyState: React.FC<EmptyStateProps> = ({
  variant = 'no-data',
  title,
  description,
  icon,
  action,
  fullHeight = false,
  compact = false,
}) => {
  // Default content based on variant
  const getDefaultContent = () => {
    switch (variant) {
      case 'no-data':
        return {
          icon: <InboxOutlined />,
          title: '暂无数据',
          description: '当前没有可显示的数据',
        };
      case 'no-results':
        return {
          icon: <SearchOffOutlined />,
          title: '未找到结果',
          description: '请尝试调整搜索条件或筛选器',
        };
      case 'error':
        return {
          icon: <ErrorOutlineOutlined />,
          title: '加载失败',
          description: '数据加载时出现错误，请稍后重试',
        };
      default:
        return {
          icon: <InboxOutlined />,
          title: '空状态',
          description: '',
        };
    }
  };

  const defaultContent = getDefaultContent();
  const finalIcon = icon || defaultContent.icon;
  const finalTitle = title || defaultContent.title;
  const finalDescription = description || defaultContent.description;

  return (
    <Box
      display="flex"
      flexDirection="column"
      alignItems="center"
      justifyContent="center"
      textAlign="center"
      minHeight={fullHeight ? '400px' : compact ? '120px' : '200px'}
      py={compact ? 2 : 4}
      px={2}
      role="status"
      aria-label={finalTitle}
    >
      {/* Icon */}
      <SvgIcon
        sx={{
          fontSize: compact ? 48 : 64,
          color: 'text.disabled',
          mb: compact ? 1 : 2,
        }}
      >
        {finalIcon}
      </SvgIcon>

      {/* Title */}
      <Typography
        variant={compact ? 'h6' : 'h5'}
        color="text.secondary"
        gutterBottom
        sx={{ fontWeight: 500 }}
      >
        {finalTitle}
      </Typography>

      {/* Description */}
      {finalDescription && (
        <Typography
          variant="body2"
          color="text.disabled"
          sx={{
            mb: action ? (compact ? 2 : 3) : 0,
            maxWidth: 400,
            lineHeight: 1.5,
          }}
        >
          {finalDescription}
        </Typography>
      )}

      {/* Action Button */}
      {action && (
        <Button
          variant={action.variant || 'outlined'}
          onClick={action.onClick}
          startIcon={variant === 'error' ? <RefreshOutlined /> : undefined}
          size={compact ? 'small' : 'medium'}
        >
          {action.label}
        </Button>
      )}
    </Box>
  );
};

// =============================================================================
// SPECIALIZED EMPTY STATES
// =============================================================================

interface NoDataProps {
  title?: string;
  description?: string;
  action?: EmptyStateProps['action'];
  compact?: boolean;
}

export const NoData: React.FC<NoDataProps> = (props) => {
  return <EmptyState variant="no-data" {...props} />;
};

export const NoResults: React.FC<NoDataProps> = (props) => {
  return <EmptyState variant="no-results" {...props} />;
};

interface ErrorStateProps extends NoDataProps {
  onRetry?: () => void;
}

export const ErrorState: React.FC<ErrorStateProps> = ({
  onRetry,
  action,
  ...props
}) => {
  const finalAction = action || (onRetry ? {
    label: '重试',
    onClick: onRetry,
    variant: 'contained' as const,
  } : undefined);

  return <EmptyState variant="error" action={finalAction} {...props} />;
};

// =============================================================================
// EMPTY CARD WRAPPER
// =============================================================================

interface EmptyCardProps extends EmptyStateProps {
  elevation?: number;
}

export const EmptyCard: React.FC<EmptyCardProps> = ({
  elevation = 1,
  ...props
}) => {
  return (
    <Paper elevation={elevation} sx={{ p: 2 }}>
      <EmptyState compact {...props} />
    </Paper>
  );
};
