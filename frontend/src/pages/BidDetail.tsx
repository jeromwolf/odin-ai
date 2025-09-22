import React from 'react';
import { Box, Typography } from '@mui/material';
import { useParams } from 'react-router-dom';

const BidDetail: React.FC = () => {
  const { id } = useParams();
  
  return (
    <Box>
      <Typography variant="h4">입찰 상세</Typography>
      <Typography variant="body1" sx={{ mt: 2 }}>
        입찰 ID: {id}
      </Typography>
    </Box>
  );
};

export default BidDetail;