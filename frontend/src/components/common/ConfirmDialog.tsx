import React from 'react';
import { Dialog, DialogTitle, DialogContent, DialogContentText, DialogActions, Button } from '@mui/material';

export interface ConfirmDialogProps {
  open: boolean;
  title?: string;
  description?: string;
  confirmText?: string;
  cancelText?: string;
  confirming?: boolean;
  onClose: () => void;
  onConfirm: () => void;
}

export const ConfirmDialog: React.FC<ConfirmDialogProps> = ({
  open,
  title = '确认操作',
  description,
  confirmText = '确认',
  cancelText = '取消',
  confirming = false,
  onClose,
  onConfirm,
}) => {
  return (
    <Dialog open={open} onClose={onClose} maxWidth="xs" fullWidth>
      {title && <DialogTitle>{title}</DialogTitle>}
      {description && (
        <DialogContent>
          <DialogContentText>{description}</DialogContentText>
        </DialogContent>
      )}
      <DialogActions>
        <Button onClick={onClose} disabled={confirming}>
          {cancelText}
        </Button>
        <Button variant="contained" color="warning" onClick={onConfirm} disabled={confirming}>
          {confirming ? '处理中...' : confirmText}
        </Button>
      </DialogActions>
    </Dialog>
  );
};
