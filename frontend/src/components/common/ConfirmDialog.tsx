import React from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  Button,
  Box,
  CircularProgress,
} from '@mui/material';
import { Warning, ErrorOutline, InfoOutlined } from '@mui/icons-material';

export interface ConfirmDialogProps {
  open: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  message: string;
  confirmText?: string;
  cancelText?: string;
  severity?: 'warning' | 'error' | 'info';
  loading?: boolean;
}

const severityConfig = {
  warning: {
    color: '#D97706',
    icon: <Warning sx={{ fontSize: 22 }} />,
  },
  error: {
    color: '#DC2626',
    icon: <ErrorOutline sx={{ fontSize: 22 }} />,
  },
  info: {
    color: '#2563EB',
    icon: <InfoOutlined sx={{ fontSize: 22 }} />,
  },
};

export const ConfirmDialog: React.FC<ConfirmDialogProps> = ({
  open,
  onClose,
  onConfirm,
  title,
  message,
  confirmText = '확인',
  cancelText = '취소',
  severity = 'warning',
  loading = false,
}) => {
  const config = severityConfig[severity];

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="xs"
      fullWidth
      PaperProps={{
        sx: {
          borderRadius: '16px',
          boxShadow: '0 20px 60px rgba(0,0,0,0.15)',
        },
      }}
    >
      <DialogTitle sx={{ pb: 1 }}>
        <Box display="flex" alignItems="center" gap={1.5}>
          <Box
            sx={{
              color: config.color,
              display: 'flex',
              alignItems: 'center',
              flexShrink: 0,
            }}
          >
            {config.icon}
          </Box>
          <Box
            component="span"
            sx={{ fontSize: '1rem', fontWeight: 700, lineHeight: 1.3 }}
          >
            {title}
          </Box>
        </Box>
      </DialogTitle>

      <DialogContent sx={{ pt: 0.5 }}>
        <DialogContentText sx={{ fontSize: '0.875rem', color: 'text.secondary', lineHeight: 1.6 }}>
          {message}
        </DialogContentText>
      </DialogContent>

      <DialogActions sx={{ px: 3, pb: 3, pt: 1, gap: 1 }}>
        <Button
          onClick={onClose}
          variant="text"
          disabled={loading}
          sx={{
            textTransform: 'none',
            fontWeight: 600,
            color: 'text.secondary',
            borderRadius: '8px',
          }}
        >
          {cancelText}
        </Button>
        <Button
          onClick={onConfirm}
          variant="contained"
          disabled={loading}
          sx={{
            textTransform: 'none',
            fontWeight: 600,
            borderRadius: '8px',
            bgcolor: config.color,
            '&:hover': {
              bgcolor: config.color,
              filter: 'brightness(0.9)',
            },
            minWidth: 80,
          }}
        >
          {loading ? (
            <CircularProgress size={18} sx={{ color: '#fff' }} />
          ) : (
            confirmText
          )}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default ConfirmDialog;
