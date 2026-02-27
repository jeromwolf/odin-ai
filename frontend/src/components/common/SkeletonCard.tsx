import React from 'react';
import { Card, CardContent, Skeleton, Box } from '@mui/material';

export interface SkeletonCardProps {
  variant?: 'stat' | 'content' | 'list';
  count?: number;
}

const cardSx = {
  borderRadius: '12px',
  border: '1px solid',
  borderColor: 'divider',
  boxShadow: 'none',
};

const StatSkeleton: React.FC = () => (
  <Card sx={cardSx}>
    <CardContent sx={{ p: 3, '&:last-child': { pb: 3 } }}>
      <Box display="flex" alignItems="flex-start" justifyContent="space-between" gap={2}>
        <Box flex={1}>
          <Skeleton animation="wave" variant="text" width="55%" height={18} />
          <Skeleton animation="wave" variant="text" width="75%" height={44} sx={{ mt: 0.5 }} />
          <Box display="flex" gap={0.5} mt={1}>
            <Skeleton animation="wave" variant="rounded" width={16} height={16} />
            <Skeleton animation="wave" variant="text" width={60} height={16} />
          </Box>
        </Box>
        <Skeleton
          animation="wave"
          variant="rounded"
          width={48}
          height={48}
          sx={{ borderRadius: 2, flexShrink: 0 }}
        />
      </Box>
    </CardContent>
  </Card>
);

const ContentSkeleton: React.FC = () => (
  <Card sx={cardSx}>
    <CardContent sx={{ p: 3, '&:last-child': { pb: 3 } }}>
      <Skeleton animation="wave" variant="text" width="70%" height={24} />
      <Skeleton animation="wave" variant="text" width="100%" height={16} sx={{ mt: 1.5 }} />
      <Skeleton animation="wave" variant="text" width="90%" height={16} sx={{ mt: 0.5 }} />
      <Skeleton animation="wave" variant="text" width="60%" height={16} sx={{ mt: 0.5 }} />
      <Box display="flex" justifyContent="flex-end" mt={2}>
        <Skeleton animation="wave" variant="rounded" width={80} height={32} sx={{ borderRadius: '8px' }} />
      </Box>
    </CardContent>
  </Card>
);

const ListSkeleton: React.FC = () => (
  <Card sx={{ ...cardSx, borderRadius: '8px' }}>
    <CardContent sx={{ p: 2, '&:last-child': { pb: 2 } }}>
      <Box display="flex" alignItems="center" gap={1.5}>
        <Skeleton animation="wave" variant="circular" width={40} height={40} sx={{ flexShrink: 0 }} />
        <Box flex={1}>
          <Skeleton animation="wave" variant="text" width="50%" height={18} />
          <Skeleton animation="wave" variant="text" width="80%" height={14} sx={{ mt: 0.5 }} />
        </Box>
      </Box>
    </CardContent>
  </Card>
);

const SkeletonMap = {
  stat: StatSkeleton,
  content: ContentSkeleton,
  list: ListSkeleton,
};

export const SkeletonCard: React.FC<SkeletonCardProps> = ({
  variant = 'content',
  count = 1,
}) => {
  const SkeletonComponent = SkeletonMap[variant];
  const items = Array.from({ length: count }, (_, i) => i);

  return (
    <>
      {items.map((i) => (
        <SkeletonComponent key={i} />
      ))}
    </>
  );
};

export default SkeletonCard;
