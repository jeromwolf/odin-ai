import React from 'react';
import { Box, Typography } from '@mui/material';

const Bookmarks: React.FC = () => {
  return (
    <Box>
      <Typography variant="h4">북마크</Typography>
      <Typography variant="body1" sx={{ mt: 2 }}>
        북마크 페이지는 현재 개발 중입니다.
      </Typography>
    </Box>
  );
};

export default Bookmarks;
