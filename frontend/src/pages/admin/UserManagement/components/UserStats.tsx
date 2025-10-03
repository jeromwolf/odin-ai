/**
 * 사용자 통계 카드 컴포넌트
 */

import React from 'react';
import { Grid, Card, CardContent, Box, Typography } from '@mui/material';
import { Person, CheckCircle, Email, Business } from '@mui/icons-material';

interface UserStatsProps {
  userStats: {
    total_users: number;
    active_users: number;
    verified_users?: number;
    paid_users?: number;
  } | null;
}

export const UserStats: React.FC<UserStatsProps> = ({ userStats }) => {
  if (!userStats) return null;

  return (
    <Grid container spacing={3} sx={{ mb: 3 }}>
      <Grid item xs={12} md={3}>
        <Card>
          <CardContent>
            <Box display="flex" alignItems="center">
              <Person sx={{ fontSize: 40, mr: 2, color: '#2196f3' }} />
              <Box>
                <Typography variant="body2" color="textSecondary">
                  전체 사용자
                </Typography>
                <Typography variant="h5">{userStats.total_users}</Typography>
              </Box>
            </Box>
          </CardContent>
        </Card>
      </Grid>
      <Grid item xs={12} md={3}>
        <Card>
          <CardContent>
            <Box display="flex" alignItems="center">
              <CheckCircle sx={{ fontSize: 40, mr: 2, color: '#4caf50' }} />
              <Box>
                <Typography variant="body2" color="textSecondary">
                  활성 사용자
                </Typography>
                <Typography variant="h5">{userStats.active_users}</Typography>
              </Box>
            </Box>
          </CardContent>
        </Card>
      </Grid>
      <Grid item xs={12} md={3}>
        <Card>
          <CardContent>
            <Box display="flex" alignItems="center">
              <Email sx={{ fontSize: 40, mr: 2, color: '#ff9800' }} />
              <Box>
                <Typography variant="body2" color="textSecondary">
                  이메일 인증
                </Typography>
                <Typography variant="h5">{userStats.verified_users || 0}</Typography>
              </Box>
            </Box>
          </CardContent>
        </Card>
      </Grid>
      <Grid item xs={12} md={3}>
        <Card>
          <CardContent>
            <Box display="flex" alignItems="center">
              <Business sx={{ fontSize: 40, mr: 2, color: '#9c27b0' }} />
              <Box>
                <Typography variant="body2" color="textSecondary">
                  유료 구독자
                </Typography>
                <Typography variant="h5">{userStats.paid_users || 0}</Typography>
              </Box>
            </Box>
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  );
};
