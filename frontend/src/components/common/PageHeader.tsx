import React, { ReactNode } from 'react';
import { Box, Typography, Breadcrumbs, Link } from '@mui/material';
import { NavigateNext } from '@mui/icons-material';

export interface PageHeaderProps {
  title: string;
  subtitle?: string;
  icon?: ReactNode;
  action?: ReactNode;
  breadcrumbs?: Array<{ label: string; href?: string }>;
}

export const PageHeader: React.FC<PageHeaderProps> = ({
  title,
  subtitle,
  icon,
  action,
  breadcrumbs,
}) => {
  return (
    <Box mb={3}>
      {breadcrumbs && breadcrumbs.length > 0 && (
        <Breadcrumbs
          separator={<NavigateNext fontSize="small" />}
          sx={{ mb: 1.5 }}
        >
          {breadcrumbs.map((crumb, index) => {
            const isLast = index === breadcrumbs.length - 1;
            return isLast ? (
              <Typography
                key={crumb.label}
                variant="body2"
                color="text.primary"
                fontWeight={500}
              >
                {crumb.label}
              </Typography>
            ) : (
              <Link
                key={crumb.label}
                href={crumb.href ?? '#'}
                underline="hover"
                color="text.secondary"
                variant="body2"
                sx={{ cursor: 'pointer' }}
              >
                {crumb.label}
              </Link>
            );
          })}
        </Breadcrumbs>
      )}

      <Box display="flex" alignItems="flex-start" justifyContent="space-between" gap={2}>
        <Box display="flex" alignItems="center" gap={2}>
          {icon && (
            <Box
              sx={{
                width: 40,
                height: 40,
                borderRadius: 2,
                bgcolor: 'primary.main',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexShrink: 0,
                color: '#fff',
                '& .MuiSvgIcon-root': {
                  fontSize: 20,
                },
              }}
            >
              {icon}
            </Box>
          )}

          <Box>
            <Typography variant="h5" fontWeight={700} lineHeight={1.2}>
              {title}
            </Typography>
            {subtitle && (
              <Typography
                variant="body2"
                color="text.secondary"
                mt={0.5}
                lineHeight={1.4}
              >
                {subtitle}
              </Typography>
            )}
          </Box>
        </Box>

        {action && (
          <Box display="flex" alignItems="center" gap={1} flexShrink={0}>
            {action}
          </Box>
        )}
      </Box>
    </Box>
  );
};

export default PageHeader;
