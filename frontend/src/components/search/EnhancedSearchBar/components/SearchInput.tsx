/**
 * SearchInput component
 * The styled search text field with adornments
 */

import React from 'react';
import {
  TextField,
  InputAdornment,
  IconButton,
  CircularProgress,
  Stack,
  Tooltip,
  alpha
} from '@mui/material';
import {
  Search as SearchIcon,
  Clear as ClearIcon
} from '@mui/icons-material';
import { styled, keyframes } from '@mui/material/styles';

// 애니메이션
const pulse = keyframes`
  0% {
    box-shadow: 0 0 0 0 rgba(25, 118, 210, 0.4);
  }
  70% {
    box-shadow: 0 0 0 10px rgba(25, 118, 210, 0);
  }
  100% {
    box-shadow: 0 0 0 0 rgba(25, 118, 210, 0);
  }
`;

export const StyledTextField = styled(TextField)(({ theme }) => ({
  '& .MuiOutlinedInput-root': {
    borderRadius: theme.shape.borderRadius * 3,
    backgroundColor: theme.palette.background.paper,
    transition: 'all 0.3s ease',
    '&:hover': {
      backgroundColor: alpha(theme.palette.primary.main, 0.02),
      '& fieldset': {
        borderColor: theme.palette.primary.main,
        borderWidth: 2
      }
    },
    '&.Mui-focused': {
      backgroundColor: theme.palette.background.paper,
      boxShadow: `0 0 0 4px ${alpha(theme.palette.primary.main, 0.1)}`,
      animation: `${pulse} 2s infinite`,
      '& fieldset': {
        borderColor: theme.palette.primary.main,
        borderWidth: 2
      }
    }
  },
  '& .MuiInputBase-input': {
    fontSize: '1.1rem',
    fontWeight: 500,
    '&::placeholder': {
      opacity: 0.6
    }
  }
}));

interface SearchInputProps {
  inputRef: React.RefObject<HTMLInputElement>;
  query: string;
  loading: boolean;
  placeholder: string;
  onQueryChange: (value: string) => void;
  onFocus: (e: React.FocusEvent<HTMLInputElement>) => void;
  onKeyDown: (e: React.KeyboardEvent) => void;
  onClear: () => void;
  onSearch: () => void;
}

const SearchInput: React.FC<SearchInputProps> = ({
  inputRef,
  query,
  loading,
  placeholder,
  onQueryChange,
  onFocus,
  onKeyDown,
  onClear,
  onSearch
}) => {
  return (
    <StyledTextField
      ref={inputRef}
      fullWidth
      variant="outlined"
      placeholder={placeholder}
      value={query}
      onChange={(e) => onQueryChange(e.target.value)}
      onFocus={onFocus}
      onKeyDown={onKeyDown}
      InputProps={{
        startAdornment: (
          <InputAdornment position="start">
            <SearchIcon color="action" />
          </InputAdornment>
        ),
        endAdornment: (
          <InputAdornment position="end">
            <Stack direction="row" spacing={0.5} alignItems="center">
              {loading && <CircularProgress size={20} />}
              {query && !loading && (
                <Tooltip title="지우기">
                  <IconButton size="small" onClick={onClear}>
                    <ClearIcon />
                  </IconButton>
                </Tooltip>
              )}
              <Tooltip title="검색">
                <IconButton
                  onClick={onSearch}
                  color="primary"
                  disabled={!query.trim()}
                  sx={{
                    bgcolor: query ? 'primary.main' : 'transparent',
                    color: query ? 'primary.contrastText' : 'action.active',
                    '&:hover': {
                      bgcolor: query ? 'primary.dark' : 'action.hover'
                    }
                  }}
                >
                  <SearchIcon />
                </IconButton>
              </Tooltip>
            </Stack>
          </InputAdornment>
        )
      }}
    />
  );
};

export default SearchInput;
