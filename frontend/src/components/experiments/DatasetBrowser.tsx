/**
 * 数据集浏览器组件
 * 让用户可视化选择数据集和序列，而不是手动输入路径
 */

import { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  List,
  ListItem,
  ListItemButton,
  ListItemText,
  ListItemIcon,
  Checkbox,
  Typography,
  Box,
  Chip,
  Alert
} from '@mui/material';
import {
  Folder as FolderIcon,
  VideoFile as SequenceIcon,
  Info as InfoIcon
} from '@mui/icons-material';

import type { Dataset, Sequence } from '@/api/services/datasets';
import { listDatasets } from '@/api/services/datasets';

interface DatasetBrowserProps {
  open: boolean;
  onClose: () => void;
  onSelect: (dataset: Dataset, selectedSequences: string[]) => void;
  selectedDataset?: string;
  selectedSequences?: string[];
}

export function DatasetBrowser({
  open,
  onClose,
  onSelect,
  selectedDataset,
  selectedSequences = []
}: DatasetBrowserProps) {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [loading, setLoading] = useState(false);
  const [currentDataset, setCurrentDataset] = useState<Dataset | null>(null);
  const [checkedSequences, setCheckedSequences] = useState<string[]>([]);

  // 从API获取真实数据集 - 只在对话框打开时触发一次
  useEffect(() => {
    if (!open) {
      // 对话框关闭时重置状态
      setDatasets([]);
      setCurrentDataset(null);
      setCheckedSequences([]);
      setLoading(false);
      return;
    }

    setLoading(true);
    // 使用API客户端获取数据集（services层）
    listDatasets()
      .then(data => {
        const formattedDatasets: Dataset[] = (data.datasets || []) as unknown as Dataset[];
        setDatasets(formattedDatasets);

        // 如果有预选的数据集，设置为当前数据集
        if (selectedDataset && formattedDatasets.length > 0) {
          const match = formattedDatasets.find(d => d.path === selectedDataset) || null;
          setCurrentDataset(match);
        }

        // 设置预选的序列
        setCheckedSequences(selectedSequences || []);
      })
      .catch(error => {
        console.error('获取数据集失败:', error);
        setDatasets([]);
      })
      .finally(() => {
        setLoading(false);
      });
  }, [open]); // 只依赖 open 状态

  const handleDatasetSelect = (dataset: Dataset) => {
    // 若后端返回 sequences_info，优先使用
    const sequences = Array.isArray((dataset as any).sequences_info) && (dataset as any).sequences_info.length > 0
      ? (dataset as any).sequences_info
      : dataset.sequences;
    setCurrentDataset({ ...dataset, sequences } as Dataset);
    setCheckedSequences([]); // 重置序列选择
  };

  const handleSequenceToggle = (sequenceName: string) => {
    setCheckedSequences(prev => {
      const newChecked = prev.includes(sequenceName)
        ? prev.filter(s => s !== sequenceName)
        : [...prev, sequenceName];
      console.log('Sequence toggle:', sequenceName, 'New checked:', newChecked);
      return newChecked;
    });
  };

  const handleSelectAll = () => {
    if (!currentDataset) return;
    
    if (checkedSequences.length === currentDataset.sequences.length) {
      setCheckedSequences([]);
    } else {
      setCheckedSequences(currentDataset.sequences.map(s => s.name));
    }
  };

  const handleConfirm = () => {
    if (!currentDataset) return;
    // 即使未选择具体序列，也允许回传数据集路径以便表单展示与后续选择
    onSelect(currentDataset, checkedSequences);
    onClose();
  };

  const getDatasetTypeColor = (format?: string) => {
    const f = (format || '').toUpperCase();
    if (f.includes('TUM')) return 'primary';
    if (f.includes('KITTI')) return 'secondary';
    if (f.includes('EUROC')) return 'success';
    return 'default';
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>
        <Box display="flex" alignItems="center" gap={1}>
          <FolderIcon />
          选择数据集和序列
        </Box>
      </DialogTitle>
      
      <DialogContent>
        {loading ? (
          <Box textAlign="center" py={4}>
            <Typography>加载数据集...</Typography>
          </Box>
        ) : (
          <Box display="flex" gap={2} height="500px">
            {/* 数据集列表 */}
            <Box flex={1} borderRight={1} borderColor="divider" pr={2}>
              <Typography variant="h6" gutterBottom>
                可用数据集
              </Typography>
              <List>
                {datasets.map((dataset) => (
                  <ListItem key={dataset.name} disablePadding>
                    <ListItemButton
                      selected={currentDataset?.name === dataset.name}
                      onClick={() => handleDatasetSelect(dataset)}
                    >
                      <ListItemIcon>
                        <FolderIcon />
                      </ListItemIcon>
                      <ListItemText
                        primary={
                          <Box display="flex" alignItems="center" gap={1}>
                            {dataset.name}
                            <Chip
                              label={dataset.format}
                              size="small"
                              color={getDatasetTypeColor(dataset.format)}
                            />
                            {dataset.has_groundtruth && (
                              <Chip
                                label="GT"
                                size="small"
                                color="success"
                                variant="outlined"
                              />
                            )}
                          </Box>
                        }
                        secondary={
                          <Box>
                            <Typography variant="body2" color="textSecondary">
                              {dataset.description}
                            </Typography>
                            <Typography variant="caption" color="textSecondary">
                              {dataset.sequences.length} 个序列 • {dataset.total_frames} 帧
                            </Typography>
                          </Box>
                        }
                      />
                    </ListItemButton>
                  </ListItem>
                ))}
              </List>
            </Box>

            {/* 序列列表 */}
            <Box flex={1} pl={2}>
              {currentDataset ? (
                <>
                  <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                    <Typography variant="h6">
                      序列选择
                    </Typography>
                    <Button size="small" onClick={handleSelectAll}>
                      {checkedSequences.length === currentDataset.sequences.length ? '取消全选' : '全选'}
                    </Button>
                  </Box>

                  <Alert severity="info" sx={{ mb: 2 }}>
                    <Typography variant="body2">
                      已选择 {checkedSequences.length} / {currentDataset.sequences.length} 个序列
                    </Typography>
                  </Alert>

                  <List>
                    {currentDataset.sequences.map((sequence: Sequence) => (
                      <ListItem key={sequence.name} dense>
                        <ListItemIcon>
                          <Checkbox
                            checked={checkedSequences.includes(sequence.name)}
                            onChange={() => handleSequenceToggle(sequence.name)}
                          />
                        </ListItemIcon>
                        <ListItemText
                          primary={
                            <Box display="flex" alignItems="center" gap={1}>
                              <SequenceIcon fontSize="small" />
                              {sequence.name}
                            </Box>
                          }
                          secondary={
                            <Box>
                              <Typography variant="caption" color="textSecondary">
                                {sequence.frames} 帧
                              </Typography>
                            </Box>
                          }
                        />
                      </ListItem>
                    ))}
                  </List>
                </>
              ) : (
                <Box textAlign="center" py={4}>
                  <InfoIcon color="disabled" sx={{ fontSize: 48, mb: 2 }} />
                  <Typography color="textSecondary">
                    请选择一个数据集查看可用序列
                  </Typography>
                </Box>
              )}
            </Box>
          </Box>
        )}
      </DialogContent>

      <DialogActions>
        <Button onClick={onClose}>
          取消
        </Button>
        <Button
          onClick={handleConfirm}
          variant="contained"
          disabled={!currentDataset}
        >
          确认选择 ({checkedSequences.length})
        </Button>
      </DialogActions>
    </Dialog>
  );
}
