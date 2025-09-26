import React, { useState } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Avatar,
  TextField,
  Button,
  Grid,
  Divider,
  Alert,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  Chip,
  Paper,
} from '@mui/material';
import {
  Person,
  Edit,
  Save,
  Cancel,
  PhotoCamera,
  Business,
  Email,
  Phone,
  LocationOn,
  CalendarToday,
  TrendingUp,
  Bookmark,
  Search,
} from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext';

const Profile: React.FC = () => {
  const { user } = useAuth();
  const [editMode, setEditMode] = useState(false);
  const [profileData, setProfileData] = useState({
    name: '홍길동',
    email: 'hong@example.com',
    phone: '010-1234-5678',
    company: '한국건설(주)',
    position: '입찰담당자',
    address: '서울특별시 강남구 테헤란로 123',
    bio: '10년차 건설업계 입찰 전문가입니다. 주로 토목, 건축 분야의 공공입찰을 담당하고 있습니다.',
  });

  const [tempData, setTempData] = useState(profileData);
  const [changePasswordOpen, setChangePasswordOpen] = useState(false);
  const [passwords, setPasswords] = useState({
    current: '',
    new: '',
    confirm: '',
  });

  // 사용자 활동 통계 (예시 데이터)
  const userStats = {
    totalSearches: 156,
    totalBookmarks: 23,
    recentActivity: 7,
    joinDate: '2024-01-15',
  };

  // 최근 활동 내역 (예시 데이터)
  const recentActivities = [
    { id: 1, action: '입찰검색', keyword: 'IT 시스템 구축', date: '2025-09-26' },
    { id: 2, action: '북마크', title: '서울시청 본관 리모델링 공사', date: '2025-09-25' },
    { id: 3, action: '입찰검색', keyword: '도로 포장', date: '2025-09-24' },
    { id: 4, action: '북마크', title: '학교 건설 공사', date: '2025-09-23' },
  ];

  const handleEdit = () => {
    setTempData(profileData);
    setEditMode(true);
  };

  const handleSave = () => {
    setProfileData(tempData);
    setEditMode(false);
    // TODO: API 호출하여 프로필 업데이트
  };

  const handleCancel = () => {
    setTempData(profileData);
    setEditMode(false);
  };

  const handleInputChange = (field: string, value: string) => {
    setTempData(prev => ({ ...prev, [field]: value }));
  };

  const handlePasswordChange = () => {
    // TODO: 비밀번호 변경 API 호출
    setPasswords({ current: '', new: '', confirm: '' });
    setChangePasswordOpen(false);
    alert('비밀번호가 변경되었습니다.');
  };

  const getActionIcon = (action: string) => {
    switch (action) {
      case '입찰검색':
        return <Search fontSize="small" />;
      case '북마크':
        return <Bookmark fontSize="small" />;
      default:
        return <TrendingUp fontSize="small" />;
    }
  };

  return (
    <Box>
      <Typography variant="h4" sx={{ mb: 3, display: 'flex', alignItems: 'center' }}>
        <Person sx={{ mr: 1 }} />
        프로필
      </Typography>

      <Grid container spacing={3}>
        {/* 프로필 정보 */}
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
                <Avatar
                  sx={{
                    width: 80,
                    height: 80,
                    bgcolor: 'primary.main',
                    fontSize: '2rem',
                    mr: 3,
                  }}
                >
                  {profileData.name.charAt(0)}
                </Avatar>
                <Box sx={{ flexGrow: 1 }}>
                  <Typography variant="h5">{profileData.name}</Typography>
                  <Typography variant="body2" color="text.secondary">
                    {profileData.company} · {profileData.position}
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
                    가입일: {userStats.joinDate}
                  </Typography>
                </Box>
                <IconButton color="primary" sx={{ alignSelf: 'flex-start' }}>
                  <PhotoCamera />
                </IconButton>
                {!editMode && (
                  <Button
                    variant="outlined"
                    startIcon={<Edit />}
                    onClick={handleEdit}
                    sx={{ ml: 1 }}
                  >
                    수정
                  </Button>
                )}
              </Box>

              <Divider sx={{ mb: 3 }} />

              <Grid container spacing={3}>
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    label="이름"
                    value={editMode ? tempData.name : profileData.name}
                    onChange={(e) => handleInputChange('name', e.target.value)}
                    disabled={!editMode}
                    InputProps={{
                      startAdornment: <Person sx={{ mr: 1, color: 'text.secondary' }} />,
                    }}
                  />
                </Grid>
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    label="이메일"
                    value={editMode ? tempData.email : profileData.email}
                    onChange={(e) => handleInputChange('email', e.target.value)}
                    disabled={!editMode}
                    InputProps={{
                      startAdornment: <Email sx={{ mr: 1, color: 'text.secondary' }} />,
                    }}
                  />
                </Grid>
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    label="전화번호"
                    value={editMode ? tempData.phone : profileData.phone}
                    onChange={(e) => handleInputChange('phone', e.target.value)}
                    disabled={!editMode}
                    InputProps={{
                      startAdornment: <Phone sx={{ mr: 1, color: 'text.secondary' }} />,
                    }}
                  />
                </Grid>
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    label="회사명"
                    value={editMode ? tempData.company : profileData.company}
                    onChange={(e) => handleInputChange('company', e.target.value)}
                    disabled={!editMode}
                    InputProps={{
                      startAdornment: <Business sx={{ mr: 1, color: 'text.secondary' }} />,
                    }}
                  />
                </Grid>
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    label="직책"
                    value={editMode ? tempData.position : profileData.position}
                    onChange={(e) => handleInputChange('position', e.target.value)}
                    disabled={!editMode}
                  />
                </Grid>
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    label="주소"
                    value={editMode ? tempData.address : profileData.address}
                    onChange={(e) => handleInputChange('address', e.target.value)}
                    disabled={!editMode}
                    InputProps={{
                      startAdornment: <LocationOn sx={{ mr: 1, color: 'text.secondary' }} />,
                    }}
                  />
                </Grid>
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="소개"
                    value={editMode ? tempData.bio : profileData.bio}
                    onChange={(e) => handleInputChange('bio', e.target.value)}
                    disabled={!editMode}
                    multiline
                    rows={3}
                    helperText="본인과 업무에 대한 간단한 소개를 작성해주세요"
                  />
                </Grid>
              </Grid>

              {editMode && (
                <Box sx={{ display: 'flex', gap: 2, mt: 3, justifyContent: 'flex-end' }}>
                  <Button
                    variant="outlined"
                    startIcon={<Cancel />}
                    onClick={handleCancel}
                  >
                    취소
                  </Button>
                  <Button
                    variant="contained"
                    startIcon={<Save />}
                    onClick={handleSave}
                  >
                    저장
                  </Button>
                </Box>
              )}
            </CardContent>
          </Card>

          {/* 비밀번호 변경 */}
          <Card sx={{ mt: 3 }}>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2 }}>
                보안 설정
              </Typography>
              <Button
                variant="outlined"
                onClick={() => setChangePasswordOpen(true)}
              >
                비밀번호 변경
              </Button>
            </CardContent>
          </Card>
        </Grid>

        {/* 활동 통계 및 최근 활동 */}
        <Grid item xs={12} md={4}>
          {/* 활동 통계 */}
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2, display: 'flex', alignItems: 'center' }}>
                <TrendingUp sx={{ mr: 1 }} />
                활동 통계
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <Paper sx={{ p: 2, textAlign: 'center' }}>
                    <Typography variant="h4" color="primary">
                      {userStats.totalSearches}
                    </Typography>
                    <Typography variant="caption">총 검색 횟수</Typography>
                  </Paper>
                </Grid>
                <Grid item xs={6}>
                  <Paper sx={{ p: 2, textAlign: 'center' }}>
                    <Typography variant="h4" color="secondary">
                      {userStats.totalBookmarks}
                    </Typography>
                    <Typography variant="caption">북마크 수</Typography>
                  </Paper>
                </Grid>
                <Grid item xs={12}>
                  <Paper sx={{ p: 2, textAlign: 'center' }}>
                    <Typography variant="h4" color="success.main">
                      {userStats.recentActivity}
                    </Typography>
                    <Typography variant="caption">최근 7일 활동</Typography>
                  </Paper>
                </Grid>
              </Grid>
            </CardContent>
          </Card>

          {/* 최근 활동 */}
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2 }}>
                최근 활동
              </Typography>
              <List>
                {recentActivities.map((activity) => (
                  <ListItem key={activity.id} divider>
                    <ListItemText
                      primary={
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          {getActionIcon(activity.action)}
                          <Typography variant="body2">
                            {activity.action}
                          </Typography>
                        </Box>
                      }
                      secondary={
                        <>
                          <Typography variant="body2" noWrap>
                            {activity.keyword || activity.title}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {activity.date}
                          </Typography>
                        </>
                      }
                    />
                  </ListItem>
                ))}
              </List>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* 비밀번호 변경 다이얼로그 */}
      <Dialog
        open={changePasswordOpen}
        onClose={() => setChangePasswordOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>비밀번호 변경</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 1 }}>
            <TextField
              fullWidth
              type="password"
              label="현재 비밀번호"
              value={passwords.current}
              onChange={(e) => setPasswords(prev => ({ ...prev, current: e.target.value }))}
            />
            <TextField
              fullWidth
              type="password"
              label="새 비밀번호"
              value={passwords.new}
              onChange={(e) => setPasswords(prev => ({ ...prev, new: e.target.value }))}
              helperText="8자 이상, 영문/숫자/특수문자 조합"
            />
            <TextField
              fullWidth
              type="password"
              label="새 비밀번호 확인"
              value={passwords.confirm}
              onChange={(e) => setPasswords(prev => ({ ...prev, confirm: e.target.value }))}
              error={passwords.new !== passwords.confirm && passwords.confirm !== ''}
              helperText={
                passwords.new !== passwords.confirm && passwords.confirm !== ''
                  ? '비밀번호가 일치하지 않습니다'
                  : ''
              }
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setChangePasswordOpen(false)}>취소</Button>
          <Button
            onClick={handlePasswordChange}
            variant="contained"
            disabled={
              !passwords.current ||
              !passwords.new ||
              passwords.new !== passwords.confirm
            }
          >
            변경
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Profile;
