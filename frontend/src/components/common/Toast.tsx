import * as React from 'react';
import {
  Snackbar,
  Alert,
  AlertTitle,
  Slide,
} from '@mui/material';
import type { TransitionProps } from '@mui/material/transitions';
import { create } from 'zustand';

// Toast types
export type ToastSeverity = 'success' | 'error' | 'warning' | 'info';

export interface ToastMessage {
  id: string;
  message: string;
  severity: ToastSeverity;
  title?: string;
  duration?: number;
  action?: React.ReactNode;
}

// Toast store
interface ToastState {
  toasts: ToastMessage[];
  addToast: (toast: Omit<ToastMessage, 'id'>) => void;
  removeToast: (id: string) => void;
  clearToasts: () => void;
}

export const useToastStore = create<ToastState>((set) => ({
  toasts: [],
  addToast: (toast) =>
    set((state) => ({
      toasts: [
        ...state.toasts,
        {
          ...toast,
          id: `toast-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
        },
      ],
    })),
  removeToast: (id) =>
    set((state) => ({
      toasts: state.toasts.filter((toast) => toast.id !== id),
    })),
  clearToasts: () => set({ toasts: [] }),
}));

// Toast hook for easy usage
export const useToast = () => {
  const { addToast, removeToast, clearToasts } = useToastStore();

  const toast = {
    success: (message: string, options?: Partial<Omit<ToastMessage, 'id' | 'message' | 'severity'>>) =>
      addToast({ message, severity: 'success', ...options }),
    error: (message: string, options?: Partial<Omit<ToastMessage, 'id' | 'message' | 'severity'>>) =>
      addToast({ message, severity: 'error', duration: 6000, ...options }),
    warning: (message: string, options?: Partial<Omit<ToastMessage, 'id' | 'message' | 'severity'>>) =>
      addToast({ message, severity: 'warning', ...options }),
    info: (message: string, options?: Partial<Omit<ToastMessage, 'id' | 'message' | 'severity'>>) =>
      addToast({ message, severity: 'info', ...options }),
  };

  return {
    toast,
    removeToast,
    clearToasts,
  };
};

// Slide transition component
const SlideTransition = React.forwardRef<
  unknown,
  TransitionProps & { children: React.ReactElement<any, any> }
>((props, ref) => {
  const slideProps = {
    ...props,
    direction: 'left' as const,
    appear: props.appear ?? true,
  };
  return <Slide ref={ref} {...slideProps} />;
});

// Individual toast component
interface ToastItemProps {
  toast: ToastMessage;
  onClose: (id: string) => void;
}

const ToastItem: React.FC<ToastItemProps> = ({ toast, onClose }) => {
  const handleClose = (_event?: React.SyntheticEvent | Event, reason?: string) => {
    if (reason === 'clickaway') {
      return;
    }
    onClose(toast.id);
  };

  return (
    <Snackbar
      open={true}
      autoHideDuration={toast.duration ?? 4000}
      onClose={handleClose}
      TransitionComponent={SlideTransition}
      anchorOrigin={{ vertical: 'top', horizontal: 'right' }}
      sx={{
        position: 'relative',
        '& .MuiSnackbar-root': {
          position: 'static',
          transform: 'none',
        },
      }}
    >
      <Alert
        onClose={handleClose}
        severity={toast.severity}
        variant="filled"
        action={toast.action}
        sx={{
          width: '100%',
          minWidth: 300,
          maxWidth: 500,
        }}
      >
        {toast.title && <AlertTitle>{toast.title}</AlertTitle>}
        {toast.message}
      </Alert>
    </Snackbar>
  );
};

// Toast container component
export const ToastContainer: React.FC = () => {
  const { toasts, removeToast } = useToastStore();

  if (toasts.length === 0) {
    return null;
  }

  return (
    <div
      style={{
        position: 'fixed',
        top: 24,
        right: 24,
        zIndex: 1700, // Higher than modal
        display: 'flex',
        flexDirection: 'column',
        gap: 8,
        pointerEvents: 'none',
      }}
    >
      {toasts.map((toast) => (
        <div key={toast.id} style={{ pointerEvents: 'auto' }}>
          <ToastItem toast={toast} onClose={removeToast} />
        </div>
      ))}
    </div>
  );
};
