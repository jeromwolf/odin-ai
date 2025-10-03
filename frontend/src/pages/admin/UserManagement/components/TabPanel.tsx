/**
 * Tab Panel 컴포넌트
 */

import React from 'react';
import { Box } from '@mui/material';
import { TabPanelProps } from '../types';

export const TabPanel: React.FC<TabPanelProps> = ({ children, value, index }) => {
  return (
    <div role="tabpanel" hidden={value !== index}>
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
};
