import React from 'react';
import { Box, Typography, Button } from '@mui/material';
import { useNavigate } from 'react-router-dom';

const NotFound: React.FC = () => {
  const navigate = useNavigate();

  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        height: '100vh',
      }}
    >
      <Typography variant="h1" sx={{ fontSize: '6rem', fontWeight: 'bold' }}>
        404
      </Typography>
      <Typography variant="h4" sx={{ mb: 2 }}>
        페이지를 찾을 수 없습니다
      </Typography>
      <Typography variant="body1" sx={{ mb: 4 }}>
        요청하신 페이지가 존재하지 않거나 이동되었습니다.
      </Typography>
      <Button
        variant="contained"
        onClick={() => navigate('/dashboard')}
      >
        대시보드로 돌아가기
      </Button>
    </Box>
  );
};

export default NotFound;
