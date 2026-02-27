import React, { useState, useEffect } from 'react';
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
  Paper,
  Snackbar,
} from '@mui/material';
import apiClient from '../services/api';
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
  TrendingUp,
  Bookmark,
  Search,
} from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext';
import { FullscreenLoading, PageHeader } from '../components/common';

const Profile: React.FC = () => {
  useAuth();
  const [editMode, setEditMode] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [profileData, setProfileData] = useState({
    name: '',
    email: '',
    phone: '',
    company: '',
    position: '',
    address: '',
    bio: '',
  });

  const [tempData, setTempData] = useState(profileData);
  const [changePasswordOpen, setChangePasswordOpen] = useState(false);
  const [passwords, setPasswords] = useState({
    current: '',
    new: '',
    confirm: '',
  });

  // 사용자 활동 통계
  const [userStats, setUserStats] = useState({
    totalSearches: 0,
    totalBookmarks: 0,
    recentActivity: 0,
    joinDate: '',
  });

  // 최근 활동 내역
  const [recentActivities, setRecentActivities] = useState<any[]>([]);

  const handleEdit = () => {
    setTempData(profileData);
    setEditMode(true);
  };

  const handleSave = async () => {
    try {
      const updateData = {
        name: tempData.name,
        email: tempData.email,
        phone: tempData.phone,
        company: tempData.company,
        department: tempData.address,  // address를 department로 저장
        position: tempData.position,
      };

      await apiClient.updateProfile(updateData);
      setProfileData(tempData);
      setEditMode(false);
      setSuccess('프로필이 업데이트되었습니다.');

      // 3초 후 성공 메시지 제거
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      console.error('프로필 업데이트 실패:', err);
      setError('프로필 업데이트에 실패했습니다.');
      setTimeout(() => setError(null), 3000);
    }
  };

  const handleCancel = () => {
    setTempData(profileData);
    setEditMode(false);
  };

  const handleInputChange = (field: string, value: string) => {
    setTempData(prev => ({ ...prev, [field]: value }));
  };

  // 프로필 데이터 로드
  useEffect(() => {
    loadProfile();
    loadActivity();
  }, []);

  const loadProfile = async () => {
    try {
      setLoading(true);
      const data = await apiClient.getProfile();
      if (data) {
        setProfileData({
          name: data.name || '',
          email: data.email || '',
          phone: data.phone || '',
          company: data.company || '',
          position: data.position || '',
          address: data.department || '',  // department를 임시로 address로 사용
          bio: '',  // bio는 DB에 없음
        });
        setUserStats({
          totalSearches: data.activity?.total_searches || 0,
          totalBookmarks: data.activity?.total_bookmarks || 0,
          recentActivity: data.activity?.recent_activity || 0,
          joinDate: data.created_at ? new Date(data.created_at).toLocaleDateString() : '',
        });
      }
    } catch (err) {
      console.error('프로필 로드 실패:', err);
      setError('프로필을 불러오는데 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const loadActivity = async () => {
    try {
      const data = await apiClient.getUserActivity();
      if (data && data.activities) {
        const formattedActivities = data.activities.map((act: any, index: number) => ({
          id: index + 1,
          action: act.type === 'bookmark' ? '북마크' : '입찰검색',
          keyword: act.type === 'bookmark' ? '' : act.description,
          title: act.type === 'bookmark' ? act.description : '',
          date: act.timestamp ? new Date(act.timestamp).toLocaleDateString() : '',
        }));
        setRecentActivities(formattedActivities);
      }
    } catch (err) {
      console.error('활동 내역 로드 실패:', err);
    }
  };

  const handlePasswordChange = async () => {
    try {
      await apiClient.changePassword(passwords.current, passwords.new);
      setPasswords({ current: '', new: '', confirm: '' });
      setChangePasswordOpen(false);
      setSuccess('비밀번호가 변경되었습니다.');
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      console.error('비밀번호 변경 실패:', err);
      setError('비밀번호 변경에 실패했습니다.');
      setTimeout(() => setError(null), 3000);
    }
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

  // Loading state
  if (loading) {
    return <FullscreenLoading />;
  }

  return (
    <Box>
      <PageHeader title="프로필" icon={<Person />} />

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

      {/* Success/Error Messages */}
      <Snackbar
        open={!!success}
        autoHideDuration={3000}
        onClose={() => setSuccess(null)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert onClose={() => setSuccess(null)} severity="success">
          {success}
        </Alert>
      </Snackbar>

      <Snackbar
        open={!!error}
        autoHideDuration={3000}
        onClose={() => setError(null)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert onClose={() => setError(null)} severity="error">
          {error}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default Profile;
