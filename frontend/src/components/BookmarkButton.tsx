import React, { useState, useEffect } from 'react';
import { IconButton, Tooltip, CircularProgress } from '@mui/material';
import BookmarkIcon from '@mui/icons-material/Bookmark';
import BookmarkBorderIcon from '@mui/icons-material/BookmarkBorder';
import { useSnackbar } from 'notistack';
import apiClient from '../services/apiClient';

interface BookmarkButtonProps {
  bidId: string;
  bidTitle?: string;
  organization?: string;
  price?: number;
  endDate?: string;
  size?: 'small' | 'medium' | 'large';
  onToggle?: (isBookmarked: boolean) => void;
}

const BookmarkButton: React.FC<BookmarkButtonProps> = ({
  bidId,
  bidTitle,
  organization,
  price,
  endDate,
  size = 'medium',
  onToggle
}) => {
  const [isBookmarked, setIsBookmarked] = useState(false);
  const [loading, setLoading] = useState(false);
  const { enqueueSnackbar } = useSnackbar();

  // 북마크 상태 확인
  useEffect(() => {
    checkBookmarkStatus();
  }, [bidId]);

  const checkBookmarkStatus = async () => {
    try {
      const response = await apiClient.get(`/bookmarks/check/${bidId}`);
      setIsBookmarked(response.data.is_bookmarked);
    } catch (error) {
      console.error('북마크 상태 확인 실패:', error);
    }
  };

  const handleToggle = async () => {
    setLoading(true);
    try {
      const response = await apiClient.post('/bookmarks/toggle', {
        bid_id: bidId,
        title: bidTitle,
        organization_name: organization,
        estimated_price: price,
        bid_end_date: endDate
      });

      const action = response.data.action;
      const newStatus = action === 'added';
      setIsBookmarked(newStatus);

      enqueueSnackbar(
        newStatus ? '북마크에 추가되었습니다' : '북마크가 제거되었습니다',
        { variant: newStatus ? 'success' : 'info' }
      );

      if (onToggle) {
        onToggle(newStatus);
      }
    } catch (error: any) {
      console.error('북마크 토글 실패:', error);
      enqueueSnackbar(
        error.response?.data?.detail || '북마크 처리 중 오류가 발생했습니다',
        { variant: 'error' }
      );
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <IconButton size={size} disabled>
        <CircularProgress size={size === 'small' ? 16 : 24} />
      </IconButton>
    );
  }

  return (
    <Tooltip title={isBookmarked ? '북마크 제거' : '북마크 추가'}>
      <IconButton
        onClick={handleToggle}
        size={size}
        sx={{
          color: isBookmarked ? 'primary.main' : 'action.active',
          '&:hover': {
            backgroundColor: isBookmarked ? 'primary.light' : 'action.hover'
          }
        }}
      >
        {isBookmarked ? <BookmarkIcon /> : <BookmarkBorderIcon />}
      </IconButton>
    </Tooltip>
  );
};

export default BookmarkButton;