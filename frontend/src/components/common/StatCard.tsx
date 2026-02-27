import React, { ReactNode } from 'react';
import { Card, CardContent, Box, Typography, Skeleton } from '@mui/material';
import { TrendingUp, TrendingDown } from '@mui/icons-material';

export interface StatCardProps {
  title: string;
  value: string | number;
  change?: number;
  changeLabel?: string;
  icon?: ReactNode;
  iconBg?: string;
  iconColor?: string;
  loading?: boolean;
  onClick?: () => void;
}

export const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  change,
  changeLabel,
  icon,
  iconBg = 'rgba(37, 99, 235, 0.08)',
  iconColor = '#2563EB',
  loading = false,
  onClick,
}) => {
  const isPositive = change !== undefined && change >= 0;
  const isClickable = Boolean(onClick);

  return (
    <Card
      onClick={onClick}
      sx={{
        borderRadius: '12px',
        border: '1px solid',
        borderColor: 'divider',
        boxShadow: 'none',
        cursor: isClickable ? 'pointer' : 'default',
        transition: 'transform 200ms ease, box-shadow 200ms ease',
        '&:hover': isClickable
          ? {
              transform: 'translateY(-2px)',
              boxShadow: '0 4px 16px rgba(0,0,0,0.08)',
            }
          : {},
      }}
    >
      <CardContent sx={{ p: 3, '&:last-child': { pb: 3 } }}>
        <Box display="flex" alignItems="flex-start" justifyContent="space-between" gap={2}>
          <Box flex={1} minWidth={0}>
            {loading ? (
              <Skeleton variant="text" width="60%" height={20} />
            ) : (
              <Typography variant="body2" color="text.secondary" fontWeight={500} noWrap>
                {title}
              </Typography>
            )}

            {loading ? (
              <Skeleton variant="text" width="80%" height={44} sx={{ mt: 0.5 }} />
            ) : (
              <Typography variant="h4" fontWeight={700} mt={0.5} lineHeight={1.2}>
                {value}
              </Typography>
            )}

            {!loading && change !== undefined && (
              <Box display="flex" alignItems="center" gap={0.5} mt={1}>
                {isPositive ? (
                  <TrendingUp sx={{ fontSize: 16, color: '#16A34A' }} />
                ) : (
                  <TrendingDown sx={{ fontSize: 16, color: '#DC2626' }} />
                )}
                <Typography
                  variant="caption"
                  fontWeight={600}
                  color={isPositive ? '#16A34A' : '#DC2626'}
                >
                  {isPositive ? '+' : ''}
                  {change}%
                </Typography>
                {changeLabel && (
                  <Typography variant="caption" color="text.disabled">
                    {changeLabel}
                  </Typography>
                )}
              </Box>
            )}
          </Box>

          {icon && (
            <Box
              sx={{
                width: 48,
                height: 48,
                borderRadius: 2,
                bgcolor: loading ? 'action.hover' : iconBg,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexShrink: 0,
                color: iconColor,
                '& .MuiSvgIcon-root': {
                  fontSize: 24,
                },
              }}
            >
              {loading ? (
                <Skeleton variant="rounded" width={48} height={48} sx={{ borderRadius: 2 }} />
              ) : (
                icon
              )}
            </Box>
          )}
        </Box>
      </CardContent>
    </Card>
  );
};

export default StatCard;
