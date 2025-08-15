import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from '@jest/globals';
import { ThemeProvider } from '@mui/material/styles';
import { createTheme } from '@/theme';
import { HealthStatusCard, HealthStatusIndicator } from '../HealthStatusCard';

const theme = createTheme('light');

const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <ThemeProvider theme={theme}>
    {children}
  </ThemeProvider>
);

describe('HealthStatusIndicator', () => {
  it('should render healthy status correctly', () => {
    render(
      <TestWrapper>
        <HealthStatusIndicator status="healthy" />
      </TestWrapper>
    );

    expect(screen.getByText('健康')).toBeInTheDocument();
  });

  it('should render degraded status correctly', () => {
    render(
      <TestWrapper>
        <HealthStatusIndicator status="degraded" />
      </TestWrapper>
    );

    expect(screen.getByText('降级')).toBeInTheDocument();
  });

  it('should render unhealthy status correctly', () => {
    render(
      <TestWrapper>
        <HealthStatusIndicator status="unhealthy" />
      </TestWrapper>
    );

    expect(screen.getByText('异常')).toBeInTheDocument();
  });
});

describe('HealthStatusCard', () => {
  const mockProps = {
    status: 'healthy' as const,
    version: '1.0.0',
    uptime: 7200, // 2 hours
    timestamp: '2025-01-13T12:00:00Z',
  };

  it('should render health status card with all information', () => {
    render(
      <TestWrapper>
        <HealthStatusCard {...mockProps} />
      </TestWrapper>
    );

    expect(screen.getByText('系统状态')).toBeInTheDocument();
    expect(screen.getByText('健康')).toBeInTheDocument();
    expect(screen.getByText('1.0.0')).toBeInTheDocument();
    expect(screen.getByText('2小时 0分钟')).toBeInTheDocument();
  });

  it('should format uptime correctly for days', () => {
    render(
      <TestWrapper>
        <HealthStatusCard {...mockProps} uptime={90000} />
      </TestWrapper>
    );

    expect(screen.getByText('1天 1小时 0分钟')).toBeInTheDocument();
  });

  it('should format uptime correctly for minutes only', () => {
    render(
      <TestWrapper>
        <HealthStatusCard {...mockProps} uptime={1800} />
      </TestWrapper>
    );

    expect(screen.getByText('30分钟')).toBeInTheDocument();
  });

  it('should show loading progress when loading', () => {
    render(
      <TestWrapper>
        <HealthStatusCard {...mockProps} loading />
      </TestWrapper>
    );

    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });

  it('should format timestamp correctly', () => {
    render(
      <TestWrapper>
        <HealthStatusCard {...mockProps} />
      </TestWrapper>
    );

    // Should show formatted Chinese date
    expect(screen.getByText(/2025/)).toBeInTheDocument();
  });
});
