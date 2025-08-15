import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from '@jest/globals';
import { ThemeProvider } from '@mui/material/styles';
import { createTheme } from '@/theme';
import { TaskStatusChip } from '../TaskStatusChip';

const theme = createTheme('light');

const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <ThemeProvider theme={theme}>
    {children}
  </ThemeProvider>
);

describe('TaskStatusChip', () => {
  it('should render PENDING status correctly', () => {
    render(
      <TestWrapper>
        <TaskStatusChip status="pending" />
      </TestWrapper>
    );

    expect(screen.getByText('等待中')).toBeInTheDocument();
  });

  it('should render RUNNING status correctly', () => {
    render(
      <TestWrapper>
        <TaskStatusChip status="running" />
      </TestWrapper>
    );

    expect(screen.getByText('运行中')).toBeInTheDocument();
  });

  it('should render COMPLETED status correctly', () => {
    render(
      <TestWrapper>
        <TaskStatusChip status="completed" />
      </TestWrapper>
    );

    expect(screen.getByText('已完成')).toBeInTheDocument();
  });

  it('should render FAILED status correctly', () => {
    render(
      <TestWrapper>
        <TaskStatusChip status="failed" />
      </TestWrapper>
    );

    expect(screen.getByText('失败')).toBeInTheDocument();
  });

  it('should render CANCELLED status correctly', () => {
    render(
      <TestWrapper>
        <TaskStatusChip status="cancelled" />
      </TestWrapper>
    );

    expect(screen.getByText('已取消')).toBeInTheDocument();
  });

  it('should render UNKNOWN status as fallback', () => {
    render(
      <TestWrapper>
        <TaskStatusChip status={"unknown" as any} />
      </TestWrapper>
    );

    expect(screen.getByText('未知')).toBeInTheDocument();
  });

  it('should render without icon when showIcon is false', () => {
    render(
      <TestWrapper>
        <TaskStatusChip status="completed" showIcon={false} />
      </TestWrapper>
    );

    expect(screen.getByText('已完成')).toBeInTheDocument();
    // Icon should not be present
    expect(screen.queryByTestId('CheckCircleOutlinedIcon')).not.toBeInTheDocument();
  });

  it('should render with tooltip by default', () => {
    render(
      <TestWrapper>
        <TaskStatusChip status="completed" />
      </TestWrapper>
    );

    // Tooltip should be present (though not visible without hover)
    expect(screen.getByText('已完成')).toBeInTheDocument();
  });

  it('should render without tooltip when tooltip is false', () => {
    render(
      <TestWrapper>
        <TaskStatusChip status="completed" tooltip={false} />
      </TestWrapper>
    );

    expect(screen.getByText('已完成')).toBeInTheDocument();
  });

  it('should render with small size', () => {
    render(
      <TestWrapper>
        <TaskStatusChip status="completed" size="small" />
      </TestWrapper>
    );

    expect(screen.getByText('已完成')).toBeInTheDocument();
  });

  it('should render with medium size', () => {
    render(
      <TestWrapper>
        <TaskStatusChip status="completed" size="medium" />
      </TestWrapper>
    );

    expect(screen.getByText('已完成')).toBeInTheDocument();
  });
});
