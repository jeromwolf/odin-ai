import React from 'react';
import { Box, Typography } from '@mui/material';

const Settings: React.FC = () => {
  return (
    <Box>
      <Typography variant="h4">설정</Typography>
      <Typography variant="body1" sx={{ mt: 2 }}>
        설정 페이지는 현재 개발 중입니다.
      </Typography>
    </Box>
  );
};

export default Settings;
