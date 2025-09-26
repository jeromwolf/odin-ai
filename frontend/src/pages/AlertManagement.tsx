import React from 'react';
import {
  Container,
  Typography,
  Box,
  Paper,
  Button
} from '@mui/material';

const AlertManagement: React.FC = () => {
  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" gutterBottom>
        알림 관리
      </Typography>

      <Paper sx={{ p: 3, mt: 2 }}>
        <Typography variant="h6" gutterBottom>
          알림 규칙 설정
        </Typography>
        <Typography variant="body1" color="text.secondary">
          알림 관리 기능은 개발 중입니다.
        </Typography>
        <Box sx={{ mt: 2 }}>
          <Button variant="contained" color="primary" disabled>
            알림 규칙 추가
          </Button>
        </Box>
      </Paper>
    </Container>
  );
};

export default AlertManagement;