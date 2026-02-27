import React from 'react';
import { Box, CircularProgress, Typography } from '@mui/material';

export interface FullscreenLoadingProps {
  message?: string;
  overlay?: boolean;
  size?: number;
}

export const FullscreenLoading: React.FC<FullscreenLoadingProps> = ({
  message,
  overlay = false,
  size = 40,
}) => {
  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: overlay ? '100vh' : '60vh',
        gap: 2,
        ...(overlay && {
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          zIndex: 1300,
          bgcolor: 'rgba(255, 255, 255, 0.80)',
          backdropFilter: 'blur(2px)',
        }),
      }}
    >
      <CircularProgress size={size} thickness={3} />
      {message && (
        <Typography variant="body2" color="text.secondary" fontWeight={500}>
          {message}
        </Typography>
      )}
    </Box>
  );
};

export default FullscreenLoading;
