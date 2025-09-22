import React from 'react';
import { Box, Typography } from '@mui/material';

const Profile: React.FC = () => {
  return (
    <Box>
      <Typography variant="h4">프로필</Typography>
      <Typography variant="body1" sx={{ mt: 2 }}>
        프로필 페이지는 현재 개발 중입니다.
      </Typography>
    </Box>
  );
};

export default Profile;
