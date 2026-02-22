import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Switch,
  FormControlLabel,
  FormGroup,
  Divider,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Button,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  TextField,
} from '@mui/material';
import {
  Settings as SettingsIcon,
  DarkMode,
  LightMode,
  Language,
  Notifications,
  Security,
  Storage,
  ExpandMore,
  Download,
  RestoreFromTrash,
  DeleteForever,
  Info,
  Warning,
} from '@mui/icons-material';
import apiClient from '../services/api';

const Settings: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  // 앱 설정
  const [darkMode, setDarkMode] = useState(false);
  const [language, setLanguage] = useState('ko');
  const [autoSave, setAutoSave] = useState(true);
  const [dataSync, setDataSync] = useState(true);

  // 알림 설정
  const [emailNotifications, setEmailNotifications] = useState(true);
  const [pushNotifications, setPushNotifications] = useState(true);
  const [soundEnabled, setSoundEnabled] = useState(false);

  // 개인정보 설정
  const [publicProfile, setPublicProfile] = useState(false);
  const [analyticsEnabled, setAnalyticsEnabled] = useState(true);

  // 다이얼로그 상태
  const [deleteAccountOpen, setDeleteAccountOpen] = useState(false);
  const [exportDataOpen, setExportDataOpen] = useState(false);
  const [clearDataOpen, setClearDataOpen] = useState(false);
  const [deleteConfirmText, setDeleteConfirmText] = useState('');

  // 설정 불러오기
  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      setLoading(true);
      const settings = await apiClient.getSettings();
      if (settings) {
        // 앱 설정
        setDarkMode(settings.dark_mode || false);
        setLanguage(settings.language || 'ko');
        setAutoSave(settings.auto_save !== false);
        setDataSync(settings.data_sync !== false);

        // 알림 설정
        setEmailNotifications(settings.email_notifications !== false);
        setPushNotifications(settings.push_notifications !== false);
        setSoundEnabled(settings.sound_enabled || false);

        // 개인정보 설정
        setPublicProfile(settings.public_profile || false);
        setAnalyticsEnabled(settings.analytics_enabled !== false);
      }
    } catch (error) {
      console.error('설정 로드 실패:', error);
    } finally {
      setLoading(false);
    }
  };

  // 설정 저장 (자동 저장)
  const saveSettings = async (newSettings: any) => {
    try {
      setSaving(true);
      await apiClient.updateSettings(newSettings);
    } catch (error) {
      console.error('설정 저장 실패:', error);
      alert('설정 저장에 실패했습니다.');
    } finally {
      setSaving(false);
    }
  };

  // 설정 변경 핸들러들 (각 변경마다 자동 저장)
  const handleDarkModeChange = (checked: boolean) => {
    setDarkMode(checked);
    saveSettings({ dark_mode: checked });
  };

  const handleLanguageChange = (value: string) => {
    setLanguage(value);
    saveSettings({ language: value });
  };

  const handleAutoSaveChange = (checked: boolean) => {
    setAutoSave(checked);
    saveSettings({ auto_save: checked });
  };

  const handleDataSyncChange = (checked: boolean) => {
    setDataSync(checked);
    saveSettings({ data_sync: checked });
  };

  const handleEmailNotificationsChange = (checked: boolean) => {
    setEmailNotifications(checked);
    saveSettings({ email_notifications: checked });
  };

  const handlePushNotificationsChange = (checked: boolean) => {
    setPushNotifications(checked);
    saveSettings({ push_notifications: checked });
  };

  const handleSoundEnabledChange = (checked: boolean) => {
    setSoundEnabled(checked);
    saveSettings({ sound_enabled: checked });
  };

  const handlePublicProfileChange = (checked: boolean) => {
    setPublicProfile(checked);
    saveSettings({ public_profile: checked });
  };

  const handleAnalyticsEnabledChange = (checked: boolean) => {
    setAnalyticsEnabled(checked);
    saveSettings({ analytics_enabled: checked });
  };

  const handleExportData = async () => {
    try {
      const blob = await apiClient.exportData();
      // 다운로드 링크 생성
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `odin_data_export_${new Date().toISOString().split('T')[0]}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);

      setExportDataOpen(false);
      alert('데이터 내보내기가 완료되었습니다.');
    } catch (error) {
      console.error('데이터 내보내기 실패:', error);
      alert('데이터 내보내기에 실패했습니다.');
    }
  };

  const handleClearData = async () => {
    try {
      // API 호출하여 데이터 삭제 (가짜 API - 실제 구현 필요)
      // await apiClient.clearUserData();
      setClearDataOpen(false);
      alert('검색 기록과 북마크가 삭제되었습니다.');
    } catch (error) {
      console.error('데이터 삭제 실패:', error);
      alert('데이터 삭제에 실패했습니다.');
    }
  };

  const handleDeleteAccount = async () => {
    if (deleteConfirmText !== '계정삭제') {
      alert('입력값이 정확하지 않습니다.');
      return;
    }

    try {
      await apiClient.deleteAccount();
      setDeleteAccountOpen(false);
      alert('계정 삭제가 예약되었습니다. 30일 후 완전히 삭제됩니다.');
      // 로그아웃 및 홈페이지로 이동
      await apiClient.logout();
      window.location.href = '/';
    } catch (error) {
      console.error('계정 삭제 실패:', error);
      alert('계정 삭제에 실패했습니다.');
    }
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <Typography>설정을 불러오는 중...</Typography>
      </Box>
    );
  }

  return (
    <Box>
      <Typography variant="h4" sx={{ mb: 3, display: 'flex', alignItems: 'center' }}>
        <SettingsIcon sx={{ mr: 1 }} />
        설정
      </Typography>

      {/* 앱 설정 */}
      <Accordion defaultExpanded>
        <AccordionSummary expandIcon={<ExpandMore />}>
          <Typography variant="h6">앱 설정</Typography>
        </AccordionSummary>
        <AccordionDetails>
          <Card>
            <CardContent>
              <FormGroup>
                <FormControlLabel
                  control={
                    <Switch
                      checked={darkMode}
                      onChange={(e) => handleDarkModeChange(e.target.checked)}
                      disabled={saving}
                    />
                  }
                  label={
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      {darkMode ? <DarkMode sx={{ mr: 1 }} /> : <LightMode sx={{ mr: 1 }} />}
                      다크 모드
                    </Box>
                  }
                />
                <FormControlLabel
                  control={
                    <Switch
                      checked={autoSave}
                      onChange={(e) => handleAutoSaveChange(e.target.checked)}
                      disabled={saving}
                    />
                  }
                  label="자동 저장"
                />
                <FormControlLabel
                  control={
                    <Switch
                      checked={dataSync}
                      onChange={(e) => handleDataSyncChange(e.target.checked)}
                      disabled={saving}
                    />
                  }
                  label="데이터 동기화"
                />
              </FormGroup>

              <Divider sx={{ my: 3 }} />

              <FormControl fullWidth sx={{ mb: 2 }}>
                <InputLabel>언어</InputLabel>
                <Select
                  value={language}
                  label="언어"
                  onChange={(e) => handleLanguageChange(e.target.value)}
                  disabled={saving}
                  startAdornment={<Language sx={{ mr: 1 }} />}
                >
                  <MenuItem value="ko">한국어</MenuItem>
                  <MenuItem value="en">English</MenuItem>
                  <MenuItem value="ja">日本語</MenuItem>
                  <MenuItem value="zh">中文</MenuItem>
                </Select>
              </FormControl>

              <Alert severity="info" sx={{ mt: 2 }}>
                설정 변경사항은 즉시 적용되며 자동으로 저장됩니다.
              </Alert>
            </CardContent>
          </Card>
        </AccordionDetails>
      </Accordion>

      {/* 알림 설정 */}
      <Accordion>
        <AccordionSummary expandIcon={<ExpandMore />}>
          <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center' }}>
            <Notifications sx={{ mr: 1 }} />
            알림 설정
          </Typography>
        </AccordionSummary>
        <AccordionDetails>
          <Card>
            <CardContent>
              <FormGroup>
                <FormControlLabel
                  control={
                    <Switch
                      checked={emailNotifications}
                      onChange={(e) => handleEmailNotificationsChange(e.target.checked)}
                      disabled={saving}
                    />
                  }
                  label="이메일 알림"
                />
                <FormControlLabel
                  control={
                    <Switch
                      checked={pushNotifications}
                      onChange={(e) => handlePushNotificationsChange(e.target.checked)}
                      disabled={saving}
                    />
                  }
                  label="푸시 알림"
                />
                <FormControlLabel
                  control={
                    <Switch
                      checked={soundEnabled}
                      onChange={(e) => handleSoundEnabledChange(e.target.checked)}
                      disabled={saving}
                    />
                  }
                  label="알림 소리"
                />
              </FormGroup>

              <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
                상세한 알림 설정은 '알림 설정' 메뉴에서 관리할 수 있습니다.
              </Typography>
            </CardContent>
          </Card>
        </AccordionDetails>
      </Accordion>

      {/* 개인정보 설정 */}
      <Accordion>
        <AccordionSummary expandIcon={<ExpandMore />}>
          <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center' }}>
            <Security sx={{ mr: 1 }} />
            개인정보 및 보안
          </Typography>
        </AccordionSummary>
        <AccordionDetails>
          <Card>
            <CardContent>
              <FormGroup sx={{ mb: 3 }}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={publicProfile}
                      onChange={(e) => handlePublicProfileChange(e.target.checked)}
                      disabled={saving}
                    />
                  }
                  label="프로필 공개"
                />
                <FormControlLabel
                  control={
                    <Switch
                      checked={analyticsEnabled}
                      onChange={(e) => handleAnalyticsEnabledChange(e.target.checked)}
                      disabled={saving}
                    />
                  }
                  label="사용 통계 수집 동의"
                />
              </FormGroup>

              <Alert severity="info" icon={<Info />}>
                사용 통계는 서비스 개선을 위해 익명으로 수집되며, 개인정보는 포함되지 않습니다.
              </Alert>
            </CardContent>
          </Card>
        </AccordionDetails>
      </Accordion>

      {/* 데이터 관리 */}
      <Accordion>
        <AccordionSummary expandIcon={<ExpandMore />}>
          <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center' }}>
            <Storage sx={{ mr: 1 }} />
            데이터 관리
          </Typography>
        </AccordionSummary>
        <AccordionDetails>
          <Card>
            <CardContent>
              <Typography variant="subtitle1" sx={{ mb: 2 }}>
                데이터 백업 및 관리
              </Typography>

              <List>
                <ListItem>
                  <ListItemText
                    primary="데이터 내보내기"
                    secondary="검색 기록, 북마크, 설정 등을 JSON 파일로 내보냅니다"
                  />
                  <ListItemSecondaryAction>
                    <Button
                      variant="outlined"
                      startIcon={<Download />}
                      onClick={() => setExportDataOpen(true)}
                    >
                      내보내기
                    </Button>
                  </ListItemSecondaryAction>
                </ListItem>

                <Divider />

                <ListItem>
                  <ListItemText
                    primary="검색 기록 삭제"
                    secondary="모든 검색 기록과 북마크를 삭제합니다 (복구 불가능)"
                  />
                  <ListItemSecondaryAction>
                    <Button
                      variant="outlined"
                      color="warning"
                      startIcon={<RestoreFromTrash />}
                      onClick={() => setClearDataOpen(true)}
                    >
                      삭제
                    </Button>
                  </ListItemSecondaryAction>
                </ListItem>
              </List>
            </CardContent>
          </Card>
        </AccordionDetails>
      </Accordion>

      {/* 계정 관리 */}
      <Accordion>
        <AccordionSummary expandIcon={<ExpandMore />}>
          <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', color: 'error.main' }}>
            <Warning sx={{ mr: 1 }} />
            계정 관리
          </Typography>
        </AccordionSummary>
        <AccordionDetails>
          <Card>
            <CardContent>
              <Alert severity="error" sx={{ mb: 3 }}>
                계정을 삭제하면 모든 데이터가 영구적으로 삭제되며 복구할 수 없습니다.
              </Alert>

              <Button
                variant="contained"
                color="error"
                startIcon={<DeleteForever />}
                onClick={() => setDeleteAccountOpen(true)}
                fullWidth
              >
                계정 삭제
              </Button>
            </CardContent>
          </Card>
        </AccordionDetails>
      </Accordion>

      {/* 다이얼로그들 */}

      {/* 데이터 내보내기 다이얼로그 */}
      <Dialog open={exportDataOpen} onClose={() => setExportDataOpen(false)}>
        <DialogTitle>데이터 내보내기</DialogTitle>
        <DialogContent>
          <Typography variant="body1" sx={{ mb: 2 }}>
            다음 데이터가 내보내집니다:
          </Typography>
          <List>
            <ListItem>
              <ListItemText primary="• 검색 기록" />
            </ListItem>
            <ListItem>
              <ListItemText primary="• 북마크 목록" />
            </ListItem>
            <ListItem>
              <ListItemText primary="• 알림 설정" />
            </ListItem>
            <ListItem>
              <ListItemText primary="• 앱 설정" />
            </ListItem>
          </List>
          <Alert severity="info">
            내보낸 파일은 다른 계정으로 가져올 수 있습니다.
          </Alert>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setExportDataOpen(false)}>취소</Button>
          <Button onClick={handleExportData} variant="contained">
            내보내기
          </Button>
        </DialogActions>
      </Dialog>

      {/* 데이터 삭제 다이얼로그 */}
      <Dialog open={clearDataOpen} onClose={() => setClearDataOpen(false)}>
        <DialogTitle>데이터 삭제 확인</DialogTitle>
        <DialogContent>
          <Alert severity="warning" sx={{ mb: 2 }}>
            모든 검색 기록과 북마크가 삭제됩니다. 이 작업은 되돌릴 수 없습니다.
          </Alert>
          <Typography variant="body1">
            정말로 삭제하시겠습니까?
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setClearDataOpen(false)}>취소</Button>
          <Button onClick={handleClearData} variant="contained" color="warning">
            삭제
          </Button>
        </DialogActions>
      </Dialog>

      {/* 계정 삭제 다이얼로그 */}
      <Dialog open={deleteAccountOpen} onClose={() => setDeleteAccountOpen(false)}>
        <DialogTitle>계정 삭제 확인</DialogTitle>
        <DialogContent>
          <Alert severity="error" sx={{ mb: 2 }}>
            계정을 삭제하면 모든 데이터가 영구적으로 삭제됩니다.
          </Alert>
          <Typography variant="body1" sx={{ mb: 2 }}>
            정말로 계정을 삭제하시겠습니까? 삭제 후 30일 동안은 복구할 수 있습니다.
          </Typography>
          <TextField
            fullWidth
            label="삭제 확인을 위해 '계정삭제'를 입력하세요"
            variant="outlined"
            value={deleteConfirmText}
            onChange={(e) => setDeleteConfirmText(e.target.value)}
            helperText="이 필드에 '계정삭제'를 정확히 입력해야 삭제가 가능합니다"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteAccountOpen(false)}>취소</Button>
          <Button onClick={handleDeleteAccount} variant="contained" color="error">
            삭제
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Settings;
