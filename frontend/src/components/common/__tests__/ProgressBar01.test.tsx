import React from 'react';
import { render, screen } from '@testing-library/react';
import { ThemeProvider } from '@mui/material/styles';
import { createTheme } from '@/theme';
import { ProgressBar01 } from '../ProgressBar01';

const theme = createTheme();

const renderWithTheme = (component: React.ReactElement) => {
  return render(
    <ThemeProvider theme={theme}>
      {component}
    </ThemeProvider>
  );
};

describe('ProgressBar01', () => {
  it('renders with 0% progress', () => {
    renderWithTheme(<ProgressBar01 value01={0} />);
    
    expect(screen.getByText('0%')).toBeInTheDocument();
  });

  it('renders with 50% progress', () => {
    renderWithTheme(<ProgressBar01 value01={0.5} />);
    
    expect(screen.getByText('50%')).toBeInTheDocument();
  });

  it('renders with 100% progress', () => {
    renderWithTheme(<ProgressBar01 value01={1.0} />);
    
    expect(screen.getByText('100%')).toBeInTheDocument();
  });

  it('clamps values above 1.0 to 100%', () => {
    renderWithTheme(<ProgressBar01 value01={1.5} />);
    
    expect(screen.getByText('100%')).toBeInTheDocument();
  });

  it('clamps negative values to 0%', () => {
    renderWithTheme(<ProgressBar01 value01={-0.5} />);
    
    expect(screen.getByText('0%')).toBeInTheDocument();
  });

  it('rounds decimal values correctly', () => {
    renderWithTheme(<ProgressBar01 value01={0.426} />);
    
    expect(screen.getByText('43%')).toBeInTheDocument();
  });

  it('hides label when showLabel is false', () => {
    renderWithTheme(<ProgressBar01 value01={0.5} showLabel={false} />);
    
    expect(screen.queryByText('50%')).not.toBeInTheDocument();
  });

  it('applies custom height', () => {
    const { container } = renderWithTheme(
      <ProgressBar01 value01={0.5} height={10} />
    );
    
    const progressBar = container.querySelector('.MuiLinearProgress-root');
    expect(progressBar).toHaveStyle({ height: '10px' });
  });

  it('applies custom styles', () => {
    const customSx = { marginTop: '16px' };
    const { container } = renderWithTheme(
      <ProgressBar01 value01={0.5} sx={customSx} />
    );
    
    const wrapper = container.firstChild as HTMLElement;
    expect(wrapper).toHaveStyle({ marginTop: '16px' });
  });
});
