import React from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  Button,
  TextField,
  Box,
  Alert,
  Typography,
} from '@mui/material';
import { WarningAmberOutlined } from '@mui/icons-material';

interface DeleteExperimentDialogProps {
  open: boolean;
  experimentName: string;
  experimentId: string;
  isRunning: boolean;
  deleting: boolean;
  onClose: () => void;
  onConfirm: () => void;
}

export const DeleteExperimentDialog: React.FC<DeleteExperimentDialogProps> = ({
  open,
  experimentName,
  experimentId,
  isRunning,
  deleting,
  onClose,
  onConfirm,
}) => {
  const [confirmText, setConfirmText] = React.useState('');
  const isConfirmValid = confirmText === experimentName;

  const handleClose = () => {
    setConfirmText('');
    onClose();
  };

  const handleConfirm = () => {
    if (isConfirmValid) {
      onConfirm();
    }
  };

  React.useEffect(() => {
    if (!open) {
      setConfirmText('');
    }
  }, [open]);

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
      <DialogTitle>
        <Box display="flex" alignItems="center" gap={1}>
          <WarningAmberOutlined color="warning" />
          删除实验
        </Box>
      </DialogTitle>
      
      <DialogContent>
        {isRunning ? (
          <Alert severity="error" sx={{ mb: 2 }}>
            <Typography variant="body2">
              实验正在运行中，无法删除。请先停止实验后再尝试删除。
            </Typography>
          </Alert>
        ) : (
          <>
            <DialogContentText sx={{ mb: 2 }}>
              您即将删除实验 <strong>"{experimentName}"</strong>。
              此操作将永久删除实验数据和所有相关结果，且无法恢复。
            </DialogContentText>
            
            <Alert severity="warning" sx={{ mb: 2 }}>
              <Typography variant="body2">
                <strong>警告：</strong>删除后将无法恢复实验数据、配置和结果文件。
              </Typography>
            </Alert>

            <Typography variant="body2" sx={{ mb: 1 }}>
              请输入实验名称 <strong>"{experimentName}"</strong> 以确认删除：
            </Typography>
            
            <TextField
              fullWidth
              variant="outlined"
              placeholder={experimentName}
              value={confirmText}
              onChange={(e) => setConfirmText(e.target.value)}
              disabled={deleting}
              error={confirmText.length > 0 && !isConfirmValid}
              helperText={
                confirmText.length > 0 && !isConfirmValid
                  ? '输入的实验名称不匹配'
                  : ''
              }
            />

            <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
              实验ID: {experimentId}
            </Typography>
          </>
        )}
      </DialogContent>
      
      <DialogActions>
        <Button onClick={handleClose} disabled={deleting}>
          取消
        </Button>
        {!isRunning && (
          <Button
            variant="contained"
            color="error"
            onClick={handleConfirm}
            disabled={!isConfirmValid || deleting}
          >
            {deleting ? '删除中...' : '确认删除'}
          </Button>
        )}
      </DialogActions>
    </Dialog>
  );
};
