import React from 'react';
import { Box } from '@mui/material';
import { AppProviders } from './providers';
import { AppRouter } from './router';
import { AppLayout } from './AppLayout';

const App: React.FC = () => {
  return (
    <AppProviders>
      <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
        <AppLayout>
          <AppRouter />
        </AppLayout>
      </Box>
    </AppProviders>
  );
};

export default App;
