import React from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import {
  Tabs,
  Tab,
  Box,
} from '@mui/material';
import {
  ScienceOutlined,
  AssessmentOutlined,
  TaskOutlined,
  HealthAndSafetyOutlined,
  SettingsOutlined,
} from '@mui/icons-material';

// Navigation items configuration
const navigationItems = [
  {
    label: '实验管理',
    value: '/experiments',
    icon: <ScienceOutlined />,
    ariaLabel: '实验管理',
  },
  {
    label: '结果分析',
    value: '/results',
    icon: <AssessmentOutlined />,
    ariaLabel: '结果分析',
  },
  {
    label: '任务管理',
    value: '/tasks',
    icon: <TaskOutlined />,
    ariaLabel: '任务管理',
  },
  {
    label: '系统健康',
    value: '/health',
    icon: <HealthAndSafetyOutlined />,
    ariaLabel: '系统健康',
  },
  {
    label: '系统配置',
    value: '/config',
    icon: <SettingsOutlined />,
    ariaLabel: '系统配置',
  },
] as const;

export const AppNavigation: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();

  // Determine current tab based on pathname
  const getCurrentTab = () => {
    const pathname = location.pathname;
    
    // Find matching navigation item
    const matchedItem = navigationItems.find(item => {
      if (item.value === '/results') {
        // Special handling for results routes
        return pathname.startsWith('/results');
      }
      return pathname.startsWith(item.value);
    });

    return matchedItem?.value || false;
  };

  const currentTab = getCurrentTab();

  const handleTabChange = (_event: React.SyntheticEvent, newValue: string) => {
    navigate(newValue);
  };

  return (
    <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
      <Tabs
        value={currentTab}
        onChange={handleTabChange}
        textColor="inherit"
        indicatorColor="secondary"
        variant="scrollable"
        scrollButtons="auto"
        allowScrollButtonsMobile
        sx={{
          '& .MuiTab-root': {
            minHeight: 48,
            textTransform: 'none',
            fontSize: '0.875rem',
            fontWeight: 500,
            color: 'inherit',
            opacity: 0.7,
            '&.Mui-selected': {
              opacity: 1,
            },
            '&:hover': {
              opacity: 1,
            },
          },
          '& .MuiTabs-indicator': {
            backgroundColor: 'secondary.main',
          },
        }}
      >
        {navigationItems.map((item) => (
          <Tab
            key={item.value}
            label={item.label}
            value={item.value}
            icon={item.icon}
            iconPosition="start"
            aria-label={item.ariaLabel}
            sx={{
              '& .MuiTab-iconWrapper': {
                marginBottom: '0 !important',
                marginRight: 1,
              },
            }}
          />
        ))}
      </Tabs>
    </Box>
  );
};
