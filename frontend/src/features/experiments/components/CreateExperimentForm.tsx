import React from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,

  Grid,
  Typography,
  Box,
  Chip,
  OutlinedInput,
  LinearProgress,
} from '@mui/material';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useClientConfig, useCreateExperiment, usePreviewOutputPath } from '@/api/services';
import { LoadingSpinner, ErrorState } from '@/components/common';
import { DatasetBrowser } from '@/components/experiments/DatasetBrowser';
import type { CreateExperimentRequest } from '@/types/api';

// =============================================================================
// FORM SCHEMA
// =============================================================================

const createExperimentSchema = z.object({
  name: z.string().min(1, '实验名称不能为空').max(100, '实验名称不能超过100个字符'),
  dataset_path: z.string().min(1, '数据集路径不能为空'),
  output_dir: z.string().optional(),
  feature_types: z.array(z.string()).min(1, '至少选择一种特征类型'),
  ransac_types: z.array(z.string()).min(1, '至少选择一种RANSAC类型'),
  sequences: z.array(z.string()).min(1, '至少输入一个序列'),
  num_runs: z.number().int().min(1, '运行次数至少为1').max(100, '运行次数不能超过100'),
  parallel_jobs: z.number().int().min(1, '并行任务数至少为1').max(32, '并行任务数不能超过32'),
  random_seed: z.number().int().min(0),
  save_frame_data: z.boolean(),
  save_descriptors: z.boolean(),
  compute_pr_curves: z.boolean(),
  analyze_ransac: z.boolean(),
  ransac_success_threshold: z.number().min(0).max(1),
  max_features: z.number().int().min(100).max(10000),
  feature_params: z.record(z.unknown()),
  ransac_threshold: z.number().positive(),
  ransac_confidence: z.number().min(0).max(1),
  ransac_max_iters: z.number().int().min(100),
});

type CreateExperimentFormData = z.infer<typeof createExperimentSchema>;

// =============================================================================
// CREATE EXPERIMENT FORM
// =============================================================================

interface CreateExperimentFormProps {
  open: boolean;
  onClose: () => void;
  onSuccess?: (experimentId: string) => void;
}

export const CreateExperimentForm: React.FC<CreateExperimentFormProps> = ({
  open,
  onClose,
  onSuccess,
}) => {
  const clientConfigQuery = useClientConfig();
  const createExperimentMutation = useCreateExperiment();
  const previewOutputMutation = usePreviewOutputPath();

  const [openDatasetBrowser, setDatasetBrowserOpen] = React.useState(false);

  const {
    control,
    handleSubmit,
    reset,
    watch,
    setValue,
    formState: { errors, isValid },
  } = useForm<CreateExperimentFormData>({
    resolver: zodResolver(createExperimentSchema),
    mode: 'onChange',
    defaultValues: {
      name: '',
      dataset_path: '',
      output_dir: '',
      feature_types: [],
      ransac_types: [],
      sequences: [],
      num_runs: 3,
      parallel_jobs: 4,
      random_seed: 42,
      save_frame_data: true,
      save_descriptors: false,
      compute_pr_curves: true,
      analyze_ransac: true,
      ransac_success_threshold: 0.8,
      max_features: 1000,
      feature_params: {},
      ransac_threshold: 1.0,
      ransac_confidence: 0.99,
      ransac_max_iters: 2000,
    },
  });

  const watchedDatasetPath = watch('dataset_path');

  // Load defaults from client config
  React.useEffect(() => {
    if (clientConfigQuery.data && open) {
      const config = clientConfigQuery.data.experiment;
      setValue('num_runs', config.defaultRuns);
      setValue('parallel_jobs', config.defaultParallelJobs);
      setValue('max_features', config.defaultMaxFeatures);
      setValue('ransac_threshold', config.defaultRansacThreshold);
      setValue('ransac_confidence', config.defaultRansacConfidence);
      setValue('ransac_max_iters', config.defaultRansacMaxIters);
    }
  }, [clientConfigQuery.data, open, setValue]);

  // Preview output path when dataset path changes
  React.useEffect(() => {
    if (watchedDatasetPath && watchedDatasetPath.trim()) {
      previewOutputMutation.mutate(
        { dataset_path: watchedDatasetPath.trim() },
        {
          onSuccess: (data) => {
            setValue('output_dir', data.output_path);
          },
        }
      );
    }
  }, [watchedDatasetPath, setValue]); // 移除 previewOutputMutation 依赖

  const handleClose = () => {
    reset();
    onClose();
  };

  const onSubmit = (data: CreateExperimentFormData) => {
    const requestData: CreateExperimentRequest = {
      ...data,
      feature_params: data.feature_params || {},
    };

    createExperimentMutation.mutate(requestData, {
      onSuccess: (response) => {
        handleClose();
        onSuccess?.(response.experiment.experiment_id);
      },
    });
  };

  // Loading state
  if (clientConfigQuery.isLoading) {
    return (
      <Dialog open={open} onClose={handleClose} maxWidth="md" fullWidth>
        <DialogContent>
          <LoadingSpinner message="加载配置信息..." />
        </DialogContent>
      </Dialog>
    );
  }

  // Error state
  if (clientConfigQuery.error) {
    return (
      <Dialog open={open} onClose={handleClose} maxWidth="md" fullWidth>
        <DialogContent>
          <ErrorState
            error={clientConfigQuery.error}
            onRetry={() => clientConfigQuery.refetch()}
            title="无法加载配置"
            description="请检查网络连接后重试"
          />
        </DialogContent>
      </Dialog>
    );
  }

  const availableFeatureTypes = clientConfigQuery.data?.algorithms.featureTypes || [];
  const availableRansacTypes = clientConfigQuery.data?.algorithms.ransacTypes || [];

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="md" fullWidth>
      <form onSubmit={handleSubmit(onSubmit)}>
        <DialogTitle>创建新实验</DialogTitle>

        <DialogContent>
          {createExperimentMutation.isPending && (
            <LinearProgress sx={{ mb: 2 }} />
          )}

          <Grid container spacing={3}>
            {/* Basic Info */}
            <Grid item xs={12}>
              <Typography variant="h6" gutterBottom>
                基本信息
              </Typography>
            </Grid>

            <Grid item xs={12}>
              <Controller
                name="name"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    label="实验名称"
                    fullWidth
                    required
                    error={!!errors.name}
                    helperText={errors.name?.message}
                  />
                )}
              />
            </Grid>

            <Grid item xs={12}>
              <Controller
                name="dataset_path"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    label="数据集路径"
                    fullWidth
                    required
                    error={!!errors.dataset_path}
                    helperText={errors.dataset_path?.message}
                    placeholder="/path/to/dataset"
                  />
                )}
              />
            </Grid>

            {/* Dataset Browser Trigger */}
            <Grid item xs={12}>
              <Box display="flex" gap={1}>
                <Button variant="outlined" onClick={() => setDatasetBrowserOpen(true)}>
                  浏览数据集
                </Button>
              </Box>
            </Grid>

            <Grid item xs={12}>
              <Controller
                name="output_dir"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    label="输出目录"
                    fullWidth
                    error={!!errors.output_dir}
                    helperText={errors.output_dir?.message || '留空将自动生成'}
                    placeholder="自动生成"
                    InputProps={{
                      readOnly: previewOutputMutation.isPending,
                    }}
                  />
                )}
              />
            </Grid>

            {/* Algorithm Config */}
            <Grid item xs={12}>
              <Typography variant="h6" gutterBottom sx={{ mt: 2 }}>
                算法配置
              </Typography>
            </Grid>

            <Grid item xs={12} sm={6}>
              <Controller
                name="feature_types"
                control={control}
                render={({ field }) => (
                  <FormControl fullWidth error={!!errors.feature_types}>
                    <InputLabel>特征类型</InputLabel>
                    <Select
                      {...field}
                      multiple
                      input={<OutlinedInput label="特征类型" />}
                      renderValue={(selected) => (
                        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                          {(selected as string[]).map((value) => (
                            <Chip key={value} label={value} size="small" />
                          ))}
                        </Box>
                      )}
                    >
                      {availableFeatureTypes.map((type) => (
                        <MenuItem key={type} value={type}>
                          {type}
                        </MenuItem>
                      ))}
                    </Select>
                    {errors.feature_types && (
                      <Typography variant="caption" color="error">
                        {errors.feature_types.message}
                      </Typography>
                    )}
                  </FormControl>
                )}
              />
            </Grid>

            <Grid item xs={12} sm={6}>
              <Controller
                name="ransac_types"
                control={control}
                render={({ field }) => (
                  <FormControl fullWidth error={!!errors.ransac_types}>
                    <InputLabel>RANSAC类型</InputLabel>
                    <Select
                      {...field}
                      multiple
                      input={<OutlinedInput label="RANSAC类型" />}
                      renderValue={(selected) => (
                        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                          {(selected as string[]).map((value) => (
                            <Chip key={value} label={value} size="small" />
                          ))}
                        </Box>
                      )}
                    >
                      {availableRansacTypes.map((type) => (
                        <MenuItem key={type} value={type}>
                          {type}
                        </MenuItem>
                      ))}
                    </Select>
                    {errors.ransac_types && (
                      <Typography variant="caption" color="error">
                        {errors.ransac_types.message}
                      </Typography>
                    )}
                  </FormControl>
                )}
              />
            </Grid>
          </Grid>
        </DialogContent>

        <DialogActions>
          <Button onClick={handleClose}>
            取消
          </Button>
          <Button
            type="submit"
            variant="contained"
            disabled={!isValid || createExperimentMutation.isPending}
          >

          {/* Dataset Browser Dialog */}
          <DatasetBrowser
            open={openDatasetBrowser}
            onClose={() => setDatasetBrowserOpen(false)}
            onSelect={(dataset, selectedSequences) => {
              setValue('dataset_path', dataset.path, { shouldValidate: true });
              setValue('sequences', selectedSequences, { shouldValidate: true });
              setDatasetBrowserOpen(false);
            }}
          />

            {createExperimentMutation.isPending ? '创建中...' : '创建实验'}
          </Button>
        </DialogActions>
      </form>
    </Dialog>
  );
};
