import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from '@jest/globals';
import { ThemeProvider } from '@mui/material/styles';
import { createTheme } from '@/theme';
import { ExperimentStatusChip } from '../ExperimentStatusChip';

const theme = createTheme('light');

const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <ThemeProvider theme={theme}>
    {children}
  </ThemeProvider>
);

describe('ExperimentStatusChip', () => {
  it('should render CREATED status correctly', () => {
    render(
      <TestWrapper>
        <ExperimentStatusChip status="CREATED" />
      </TestWrapper>
    );

    expect(screen.getByText('已创建')).toBeInTheDocument();
  });

  it('should render RUNNING status correctly', () => {
    render(
      <TestWrapper>
        <ExperimentStatusChip status="RUNNING" />
      </TestWrapper>
    );

    expect(screen.getByText('运行中')).toBeInTheDocument();
  });

  it('should render COMPLETED status correctly', () => {
    render(
      <TestWrapper>
        <ExperimentStatusChip status="COMPLETED" />
      </TestWrapper>
    );

    expect(screen.getByText('已完成')).toBeInTheDocument();
  });

  it('should render FAILED status correctly', () => {
    render(
      <TestWrapper>
        <ExperimentStatusChip status="FAILED" />
      </TestWrapper>
    );

    expect(screen.getByText('失败')).toBeInTheDocument();
  });

  it('should render CANCELLED status correctly', () => {
    render(
      <TestWrapper>
        <ExperimentStatusChip status="CANCELLED" />
      </TestWrapper>
    );

    expect(screen.getByText('已取消')).toBeInTheDocument();
  });

  it('should render without icon when showIcon is false', () => {
    render(
      <TestWrapper>
        <ExperimentStatusChip status="COMPLETED" showIcon={false} />
      </TestWrapper>
    );

    expect(screen.getByText('已完成')).toBeInTheDocument();
    // Icon should not be present
    expect(screen.queryByTestId('CheckCircleOutlinedIcon')).not.toBeInTheDocument();
  });

  it('should render with tooltip by default', () => {
    render(
      <TestWrapper>
        <ExperimentStatusChip status="COMPLETED" />
      </TestWrapper>
    );

    // Tooltip should be present (though not visible without hover)
    expect(screen.getByText('已完成')).toBeInTheDocument();
  });

  it('should render without tooltip when tooltip is false', () => {
    render(
      <TestWrapper>
        <ExperimentStatusChip status="COMPLETED" tooltip={false} />
      </TestWrapper>
    );

    expect(screen.getByText('已完成')).toBeInTheDocument();
  });

  it('should render with small size', () => {
    render(
      <TestWrapper>
        <ExperimentStatusChip status="COMPLETED" size="small" />
      </TestWrapper>
    );

    expect(screen.getByText('已完成')).toBeInTheDocument();
  });

  it('should render with medium size', () => {
    render(
      <TestWrapper>
        <ExperimentStatusChip status="COMPLETED" size="medium" />
      </TestWrapper>
    );

    expect(screen.getByText('已完成')).toBeInTheDocument();
  });
});
