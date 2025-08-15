import React from 'react';
import {
  AppBar,
  Toolbar,
  Typography,
  Box,
  IconButton,
  Tooltip,
  Container,
} from '@mui/material';
import {
  Brightness4Outlined,
  Brightness7Outlined,
  ScienceOutlined,
} from '@mui/icons-material';
import { useThemeStore } from '@/store';
import { AppNavigation } from './AppNavigation';

interface AppLayoutProps {
  children: React.ReactNode;
}

export const AppLayout: React.FC<AppLayoutProps> = ({ children }) => {
  const { mode, toggleMode } = useThemeStore();

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      {/* App Bar */}
      <AppBar position="static" elevation={1}>
        <Toolbar>
          {/* Logo and Title */}
          <Box display="flex" alignItems="center" sx={{ mr: 4 }}>
            <ScienceOutlined sx={{ mr: 1 }} />
            <Typography
              variant="h6"
              component="h1"
              sx={{
                fontWeight: 600,
                letterSpacing: '-0.025em',
              }}
            >
              VO Benchmark
            </Typography>
          </Box>

          {/* Navigation */}
          <Box sx={{ flexGrow: 1 }}>
            <AppNavigation />
          </Box>

          {/* Theme Toggle */}
          <Tooltip title={mode === 'light' ? '切换到暗黑模式' : '切换到明亮模式'}>
            <IconButton
              onClick={toggleMode}
              color="inherit"
              aria-label={mode === 'light' ? '切换到暗黑模式' : '切换到明亮模式'}
              sx={{ ml: 1 }}
            >
              {mode === 'light' ? <Brightness4Outlined /> : <Brightness7Outlined />}
            </IconButton>
          </Tooltip>
        </Toolbar>
      </AppBar>

      {/* Main Content */}
      <Box component="main" sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column' }}>
        <Container maxWidth="xl" sx={{ py: 3, flexGrow: 1 }}>
          {children}
        </Container>
      </Box>
    </Box>
  );
};
