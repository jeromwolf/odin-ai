/**
 * SearchPagination 컴포넌트
 * 검색 결과 페이지네이션 UI 제공
 */

import React, { useMemo } from 'react';
import {
  Box,
  Pagination,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Typography,
  Stack,
  IconButton,
  Tooltip,
  useTheme,
  useMediaQuery,
  SelectChangeEvent
} from '@mui/material';
import {
  FirstPage as FirstPageIcon,
  LastPage as LastPageIcon,
  NavigateBefore as PrevIcon,
  NavigateNext as NextIcon,
  ViewList as ViewListIcon,
  ViewModule as ViewModuleIcon
} from '@mui/icons-material';
import { styled } from '@mui/material/styles';
import { SearchPaginationProps } from '../../types/search.types';

// 페이지 크기 옵션
const PAGE_SIZE_OPTIONS = [10, 20, 30, 50, 100];

// 모바일에서 표시할 최대 페이지 버튼 수
const MOBILE_MAX_BUTTONS = 3;
// 데스크톱에서 표시할 최대 페이지 버튼 수
const DESKTOP_MAX_BUTTONS = 7;

// 스타일 컴포넌트
const PaginationContainer = styled(Box)(({ theme }) => ({
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'space-between',
  padding: theme.spacing(2),
  borderTop: `1px solid ${theme.palette.divider}`,
  flexWrap: 'wrap',
  gap: theme.spacing(2),
  [theme.breakpoints.down('sm')]: {
    flexDirection: 'column',
    alignItems: 'stretch'
  }
}));

const PageInfo = styled(Typography)(({ theme }) => ({
  color: theme.palette.text.secondary,
  fontSize: '0.875rem',
  minWidth: '150px',
  [theme.breakpoints.down('sm')]: {
    textAlign: 'center',
    minWidth: 'auto'
  }
}));

const ControlsContainer = styled(Stack)(({ theme }) => ({
  flexDirection: 'row',
  alignItems: 'center',
  gap: theme.spacing(2),
  [theme.breakpoints.down('sm')]: {
    justifyContent: 'center',
    width: '100%'
  }
}));

const SearchPagination: React.FC<SearchPaginationProps> = ({
  currentPage,
  totalPages,
  pageSize,
  totalItems,
  onPageChange,
  onPageSizeChange,
  loading = false,
  showFirstLast = true,
  showPageSizeSelector = true,
  showItemsInfo = true,
  pageSizeOptions = PAGE_SIZE_OPTIONS,
  viewMode,
  onViewModeChange
}) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const isTablet = useMediaQuery(theme.breakpoints.down('md'));

  /**
   * 현재 표시중인 아이템 범위 계산
   */
  const itemRange = useMemo(() => {
    const start = (currentPage - 1) * pageSize + 1;
    const end = Math.min(currentPage * pageSize, totalItems);
    return { start, end };
  }, [currentPage, pageSize, totalItems]);

  /**
   * 페이지 변경 처리
   */
  const handlePageChange = (event: React.ChangeEvent<unknown>, value: number) => {
    if (value !== currentPage && !loading) {
      onPageChange(value);
    }
  };

  /**
   * 페이지 크기 변경 처리
   */
  const handlePageSizeChange = (event: SelectChangeEvent<number>) => {
    const newSize = event.target.value as number;
    if (onPageSizeChange && newSize !== pageSize) {
      onPageSizeChange(newSize);
      // 페이지 크기 변경 시 첫 페이지로 이동
      if (currentPage !== 1) {
        onPageChange(1);
      }
    }
  };

  /**
   * 첫 페이지로 이동
   */
  const handleFirstPage = () => {
    if (currentPage !== 1 && !loading) {
      onPageChange(1);
    }
  };

  /**
   * 마지막 페이지로 이동
   */
  const handleLastPage = () => {
    if (currentPage !== totalPages && !loading) {
      onPageChange(totalPages);
    }
  };

  /**
   * 이전 페이지로 이동
   */
  const handlePreviousPage = () => {
    if (currentPage > 1 && !loading) {
      onPageChange(currentPage - 1);
    }
  };

  /**
   * 다음 페이지로 이동
   */
  const handleNextPage = () => {
    if (currentPage < totalPages && !loading) {
      onPageChange(currentPage + 1);
    }
  };

  /**
   * 빠른 페이지 이동 (10페이지 단위)
   */
  const handleJumpPages = (direction: 'forward' | 'backward') => {
    const jumpSize = 10;
    let targetPage: number;

    if (direction === 'forward') {
      targetPage = Math.min(currentPage + jumpSize, totalPages);
    } else {
      targetPage = Math.max(currentPage - jumpSize, 1);
    }

    if (targetPage !== currentPage && !loading) {
      onPageChange(targetPage);
    }
  };

  /**
   * 페이지 정보 텍스트 생성
   */
  const getPageInfoText = () => {
    if (totalItems === 0) {
      return '검색 결과 없음';
    }

    if (isMobile) {
      return `${currentPage} / ${totalPages}`;
    }

    return `${itemRange.start}-${itemRange.end} / 총 ${totalItems.toLocaleString()}개`;
  };

  // 결과가 없는 경우
  if (totalItems === 0) {
    return null;
  }

  // 페이지가 하나뿐인 경우
  if (totalPages === 1 && !showPageSizeSelector && !showItemsInfo) {
    return null;
  }

  return (
    <PaginationContainer>
      {/* 왼쪽: 아이템 정보 및 뷰 모드 */}
      <Stack direction="row" spacing={2} alignItems="center">
        {showItemsInfo && (
          <PageInfo>
            {getPageInfoText()}
          </PageInfo>
        )}

        {viewMode !== undefined && onViewModeChange && !isMobile && (
          <Stack direction="row" spacing={0.5}>
            <Tooltip title="리스트 뷰">
              <IconButton
                size="small"
                onClick={() => onViewModeChange('list')}
                color={viewMode === 'list' ? 'primary' : 'default'}
                disabled={loading}
              >
                <ViewListIcon />
              </IconButton>
            </Tooltip>
            <Tooltip title="그리드 뷰">
              <IconButton
                size="small"
                onClick={() => onViewModeChange('grid')}
                color={viewMode === 'grid' ? 'primary' : 'default'}
                disabled={loading}
              >
                <ViewModuleIcon />
              </IconButton>
            </Tooltip>
          </Stack>
        )}
      </Stack>

      {/* 중앙: 페이지네이션 컨트롤 */}
      <ControlsContainer>
        {/* 첫 페이지 / 이전 페이지 버튼 (데스크톱) */}
        {!isMobile && showFirstLast && (
          <>
            <Tooltip title="첫 페이지">
              <span>
                <IconButton
                  size="small"
                  onClick={handleFirstPage}
                  disabled={currentPage === 1 || loading}
                >
                  <FirstPageIcon />
                </IconButton>
              </span>
            </Tooltip>

            {totalPages > 20 && (
              <Tooltip title="10페이지 뒤로">
                <span>
                  <IconButton
                    size="small"
                    onClick={() => handleJumpPages('backward')}
                    disabled={currentPage <= 10 || loading}
                  >
                    <PrevIcon />
                    <Typography variant="caption">10</Typography>
                  </IconButton>
                </span>
              </Tooltip>
            )}
          </>
        )}

        {/* 메인 페이지네이션 */}
        <Pagination
          count={totalPages}
          page={currentPage}
          onChange={handlePageChange}
          disabled={loading}
          size={isMobile ? 'small' : 'medium'}
          siblingCount={isMobile ? 0 : isTablet ? 1 : 2}
          boundaryCount={isMobile ? 1 : 2}
          showFirstButton={isMobile && showFirstLast}
          showLastButton={isMobile && showFirstLast}
          color="primary"
          shape="rounded"
          sx={{
            '& .MuiPaginationItem-root': {
              fontWeight: 500
            },
            '& .Mui-selected': {
              fontWeight: 700
            }
          }}
        />

        {/* 다음 페이지 / 마지막 페이지 버튼 (데스크톱) */}
        {!isMobile && showFirstLast && (
          <>
            {totalPages > 20 && (
              <Tooltip title="10페이지 앞으로">
                <span>
                  <IconButton
                    size="small"
                    onClick={() => handleJumpPages('forward')}
                    disabled={currentPage > totalPages - 10 || loading}
                  >
                    <Typography variant="caption">10</Typography>
                    <NextIcon />
                  </IconButton>
                </span>
              </Tooltip>
            )}

            <Tooltip title="마지막 페이지">
              <span>
                <IconButton
                  size="small"
                  onClick={handleLastPage}
                  disabled={currentPage === totalPages || loading}
                >
                  <LastPageIcon />
                </IconButton>
              </span>
            </Tooltip>
          </>
        )}
      </ControlsContainer>

      {/* 오른쪽: 페이지 크기 선택 */}
      {showPageSizeSelector && onPageSizeChange && (
        <FormControl size="small" sx={{ minWidth: 120 }}>
          <InputLabel id="page-size-label">표시 개수</InputLabel>
          <Select
            labelId="page-size-label"
            value={pageSize}
            onChange={handlePageSizeChange}
            disabled={loading}
            label="표시 개수"
          >
            {pageSizeOptions.map(size => (
              <MenuItem key={size} value={size}>
                {size}개씩
              </MenuItem>
            ))}
          </Select>
        </FormControl>
      )}
    </PaginationContainer>
  );
};

/**
 * 간단한 페이지네이션 컴포넌트
 * 모바일이나 공간이 제한된 곳에서 사용
 */
export const SimplePagination: React.FC<Omit<SearchPaginationProps, 'showFirstLast' | 'showPageSizeSelector' | 'showItemsInfo'>> = (props) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));

  return (
    <Box sx={{
      display: 'flex',
      justifyContent: 'center',
      py: 2,
      borderTop: 1,
      borderColor: 'divider'
    }}>
      <Stack direction="row" spacing={1} alignItems="center">
        <IconButton
          size="small"
          onClick={() => props.onPageChange(props.currentPage - 1)}
          disabled={props.currentPage === 1 || props.loading}
        >
          <PrevIcon />
        </IconButton>

        <Typography variant="body2" sx={{ px: 2 }}>
          {props.currentPage} / {props.totalPages}
        </Typography>

        <IconButton
          size="small"
          onClick={() => props.onPageChange(props.currentPage + 1)}
          disabled={props.currentPage === props.totalPages || props.loading}
        >
          <NextIcon />
        </IconButton>
      </Stack>
    </Box>
  );
};

/**
 * 로드 더 페이지네이션 컴포넌트
 * 무한 스크롤 대신 버튼 클릭으로 더 불러오기
 */
export const LoadMorePagination: React.FC<{
  hasMore: boolean;
  loading?: boolean;
  onLoadMore: () => void;
  itemsLoaded: number;
  totalItems?: number;
}> = ({ hasMore, loading, onLoadMore, itemsLoaded, totalItems }) => {
  if (!hasMore) {
    return null;
  }

  return (
    <Box sx={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      py: 3,
      gap: 1
    }}>
      {totalItems && (
        <Typography variant="caption" color="text.secondary">
          {itemsLoaded} / {totalItems} 항목 표시됨
        </Typography>
      )}
      <Box>
        <Box
          component="button"
          onClick={onLoadMore}
          disabled={loading}
          sx={{
            px: 3,
            py: 1.5,
            border: 1,
            borderColor: 'primary.main',
            borderRadius: 1,
            backgroundColor: 'background.paper',
            color: 'primary.main',
            fontWeight: 500,
            cursor: loading ? 'wait' : 'pointer',
            transition: 'all 0.2s',
            '&:hover': {
              backgroundColor: 'primary.main',
              color: 'primary.contrastText'
            },
            '&:disabled': {
              opacity: 0.5,
              cursor: 'not-allowed'
            }
          }}
        >
          {loading ? '불러오는 중...' : '더 보기'}
        </Box>
      </Box>
    </Box>
  );
};

export default SearchPagination;