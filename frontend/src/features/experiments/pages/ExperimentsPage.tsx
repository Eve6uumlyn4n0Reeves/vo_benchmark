import React from 'react';
import {
  Box,
  Typography,
  Button,
  Paper,
  Alert,
} from '@mui/material';
import {
  AddOutlined,
  RefreshOutlined,
} from '@mui/icons-material';
import { useExperiments, useDeleteExperiment } from '@/api/services';
import { usePagination } from '@/hooks';
import {
  LoadingSpinner,
  ErrorState,
  NoData,
  PaginationControls,
} from '@/components/common';
import {
  ExperimentsList,
  ExperimentsFilters,
  CreateExperimentForm,
  DeleteExperimentDialog,
} from '../components';
import type { ExperimentsListParams } from '@/types/api';

// =============================================================================
// EXPERIMENTS PAGE
// =============================================================================

const ExperimentsPage: React.FC = () => {
  const [createFormOpen, setCreateFormOpen] = React.useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = React.useState(false);
  const [experimentToDelete, setExperimentToDelete] = React.useState<{
    id: string;
    name: string;
    status: string;
  } | null>(null);
  const [filters, setFilters] = React.useState<ExperimentsListParams>({
    page: 1,
    per_page: 20,
  });

  const pagination = usePagination({
    initialPage: filters.page,
    initialPerPage: filters.per_page,
  });

  // Sync pagination with filters
  React.useEffect(() => {
    setFilters(prev => ({
      ...prev,
      page: pagination.page,
      per_page: pagination.per_page,
    }));
  }, [pagination.page, pagination.per_page]);

  const experimentsQuery = useExperiments(filters);
  const deleteExperimentMutation = useDeleteExperiment();

  const handleFiltersChange = (newFilters: ExperimentsListParams) => {
    setFilters(newFilters);
    if (newFilters.page !== pagination.page) {
      pagination.setPage(newFilters.page || 1);
    }
  };

  const handlePageChange = (page: number) => {
    pagination.setPage(page);
  };

  const handlePageSizeChange = (pageSize: number) => {
    pagination.setPerPage(pageSize);
  };

  const handleDeleteExperiment = (experimentId: string) => {
    const experiment = experiments.find(exp => exp.experiment_id === experimentId);
    if (experiment) {
      setExperimentToDelete({
        id: experiment.experiment_id,
        name: experiment.name,
        status: experiment.status,
      });
      setDeleteDialogOpen(true);
    }
  };

  const handleDeleteConfirm = () => {
    if (experimentToDelete) {
      deleteExperimentMutation.mutate(experimentToDelete.id, {
        onSuccess: () => {
          setDeleteDialogOpen(false);
          setExperimentToDelete(null);
        },
      });
    }
  };

  const handleDeleteCancel = () => {
    setDeleteDialogOpen(false);
    setExperimentToDelete(null);
  };

  const handleRefresh = () => {
    experimentsQuery.refetch();
  };

  const handleCreateSuccess = (experimentId: string) => {
    // Refresh the list and optionally navigate to the new experiment
    experimentsQuery.refetch();
    console.log('Created experiment:', experimentId);
  };

  // Loading state for initial load
  if (experimentsQuery.isLoading && !experimentsQuery.data) {
    return (
      <Box>
        <Typography variant="h4" component="h1" gutterBottom>
          实验管理
        </Typography>
        <LoadingSpinner message="加载实验列表..." fullHeight />
      </Box>
    );
  }

  // Error state
  if (experimentsQuery.error && !experimentsQuery.data) {
    return (
      <Box>
        <Typography variant="h4" component="h1" gutterBottom>
          实验管理
        </Typography>
        <ErrorState
          error={experimentsQuery.error}
          onRetry={handleRefresh}
          title="无法加载实验列表"
          description="请检查后端服务是否正常运行"
          fullHeight
        />
      </Box>
    );
  }

  const experiments = experimentsQuery.data?.experiments || [];
  const paginationData = experimentsQuery.data?.pagination;

  return (
    <Box>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" component="h1">
          实验管理
        </Typography>
        <Box display="flex" gap={2}>
          <Button
            variant="outlined"
            startIcon={<RefreshOutlined />}
            onClick={handleRefresh}
            disabled={experimentsQuery.isFetching}
          >
            刷新
          </Button>
          <Button
            variant="contained"
            startIcon={<AddOutlined />}
            onClick={() => setCreateFormOpen(true)}
          >
            创建实验
          </Button>
        </Box>
      </Box>

      {/* Error Alert */}
      {experimentsQuery.error && experimentsQuery.data && (
        <Alert severity="warning" sx={{ mb: 3 }}>
          数据可能不是最新的，请尝试刷新页面
        </Alert>
      )}

      {/* Filters */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <ExperimentsFilters
          filters={filters}
          onFiltersChange={handleFiltersChange}
          loading={experimentsQuery.isFetching}
        />
      </Paper>

      {/* Content */}
      {experiments.length === 0 ? (
        <NoData
          title="暂无实验"
          description='点击“创建实验”开始您的第一个实验'
          action={{
            label: '创建实验',
            onClick: () => setCreateFormOpen(true),
            variant: 'contained',
          }}
        />
      ) : (
        <>
          <ExperimentsList
            experiments={experiments}
            loading={experimentsQuery.isFetching}
            onDelete={handleDeleteExperiment}
          />

          {/* Pagination */}
          {paginationData && paginationData.total_pages > 1 && (
            <Paper sx={{ mt: 3 }}>
              <PaginationControls
                pagination={paginationData}
                onPageChange={handlePageChange}
                onPageSizeChange={handlePageSizeChange}
                loading={experimentsQuery.isFetching}
              />
            </Paper>
          )}
        </>
      )}

      {/* Create Form Dialog */}
      <CreateExperimentForm
        open={createFormOpen}
        onClose={() => setCreateFormOpen(false)}
        onSuccess={handleCreateSuccess}
      />

      {/* Delete Confirmation Dialog */}
      {experimentToDelete && (
        <DeleteExperimentDialog
          open={deleteDialogOpen}
          experimentName={experimentToDelete.name}
          experimentId={experimentToDelete.id}
          isRunning={experimentToDelete.status === 'running' || experimentToDelete.status === 'RUNNING'}
          deleting={deleteExperimentMutation.isPending}
          onClose={handleDeleteCancel}
          onConfirm={handleDeleteConfirm}
        />
      )}
    </Box>
  );
};

export default ExperimentsPage;
