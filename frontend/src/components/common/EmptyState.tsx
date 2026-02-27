import React, { ReactNode } from 'react';
import { Box, Typography, Button } from '@mui/material';
import { SearchOff } from '@mui/icons-material';

export interface EmptyStateProps {
  icon?: ReactNode;
  title: string;
  description?: string;
  action?: {
    label: string;
    onClick: () => void;
  };
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  icon,
  title,
  description,
  action,
}) => {
  return (
    <Box
      display="flex"
      flexDirection="column"
      alignItems="center"
      justifyContent="center"
      py={8}
      px={3}
      textAlign="center"
    >
      <Box
        sx={{
          width: 64,
          height: 64,
          color: 'text.disabled',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          '& .MuiSvgIcon-root': {
            fontSize: 64,
          },
        }}
      >
        {icon ?? <SearchOff />}
      </Box>

      <Typography variant="h6" fontWeight={600} mt={2}>
        {title}
      </Typography>

      {description && (
        <Typography
          variant="body2"
          color="text.secondary"
          mt={1}
          maxWidth={360}
          lineHeight={1.6}
        >
          {description}
        </Typography>
      )}

      {action && (
        <Button
          variant="outlined"
          onClick={action.onClick}
          sx={{ mt: 2, borderRadius: '8px', textTransform: 'none', fontWeight: 600 }}
        >
          {action.label}
        </Button>
      )}
    </Box>
  );
};

export default EmptyState;
