import React, { Suspense } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { Box, CircularProgress } from '@mui/material';

// Lazy load pages for better performance
const ExperimentsPage = React.lazy(() => import('@/features/experiments/pages/ExperimentsPage'));
const ExperimentDetailPage = React.lazy(() => import('@/features/experiments/pages/ExperimentDetailPage'));
const ResultsPage = React.lazy(() => import('@/features/results/pages/ResultsPageNew'));
const TasksPage = React.lazy(() => import('@/features/tasks/pages/TasksPage'));
const TaskDetailPage = React.lazy(() => import('@/features/tasks/pages/TaskDetailPage'));
const HealthPage = React.lazy(() => import('@/features/health/pages/HealthPage'));
const ConfigPage = React.lazy(() => import('@/features/config/pages/ConfigPage'));

// Loading component
const PageLoader: React.FC = () => (
  <Box
    display="flex"
    justifyContent="center"
    alignItems="center"
    minHeight="200px"
    role="status"
    aria-label="页面加载中"
  >
    <CircularProgress size={40} />
  </Box>
);

// Not Found component
const NotFoundPage: React.FC = () => (
  <Box
    display="flex"
    flexDirection="column"
    justifyContent="center"
    alignItems="center"
    minHeight="400px"
    textAlign="center"
  >
    <h1>404 - 页面未找到</h1>
    <p>您访问的页面不存在</p>
  </Box>
);

// App Router Component
export const AppRouter: React.FC = () => {
  return (
    <Suspense fallback={<PageLoader />}>
      <Routes>
        {/* Default redirect to experiments */}
        <Route path="/" element={<Navigate to="/experiments" replace />} />
        
        {/* Experiments routes */}
        <Route path="/experiments" element={<ExperimentsPage />} />
        <Route path="/experiments/:id" element={<ExperimentDetailPage />} />
        
        {/* Results routes */}
        <Route path="/results" element={<ResultsPage />} />
        <Route path="/results/:experimentId" element={<ResultsPage />} />
        <Route path="/results/:experimentId/:algorithmKey" element={<ResultsPage />} />
        
        {/* Tasks routes */}
        <Route path="/tasks" element={<TasksPage />} />
        <Route path="/tasks/:id" element={<TaskDetailPage />} />
        
        {/* Health routes */}
        <Route path="/health" element={<HealthPage />} />
        
        {/* Config routes */}
        <Route path="/config" element={<ConfigPage />} />
        
        {/* 404 Not Found */}
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </Suspense>
  );
};
