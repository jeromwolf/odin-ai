import React, { useState } from 'react';
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
  IconButton,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Chip,
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
  Delete,
  ExpandMore,
  Download,
  Upload,
  RestoreFromTrash,
  DeleteForever,
  Info,
  Warning,
} from '@mui/icons-material';

const Settings: React.FC = () => {
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

  const handleExportData = () => {
    // TODO: 데이터 내보내기 API 호출
    setExportDataOpen(false);
    alert('데이터 내보내기가 시작되었습니다. 완료되면 이메일로 다운로드 링크를 보내드립니다.');
  };

  const handleClearData = () => {
    // TODO: 사용자 데이터 삭제 API 호출
    setClearDataOpen(false);
    alert('검색 기록과 북마크가 삭제되었습니다.');
  };

  const handleDeleteAccount = () => {
    // TODO: 계정 삭제 API 호출
    setDeleteAccountOpen(false);
    alert('계정 삭제가 예약되었습니다. 30일 후 완전히 삭제됩니다.');
  };

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
                      onChange={(e) => setDarkMode(e.target.checked)}
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
                      onChange={(e) => setAutoSave(e.target.checked)}
                    />
                  }
                  label="자동 저장"
                />
                <FormControlLabel
                  control={
                    <Switch
                      checked={dataSync}
                      onChange={(e) => setDataSync(e.target.checked)}
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
                  onChange={(e) => setLanguage(e.target.value)}
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
                      onChange={(e) => setEmailNotifications(e.target.checked)}
                    />
                  }
                  label="이메일 알림"
                />
                <FormControlLabel
                  control={
                    <Switch
                      checked={pushNotifications}
                      onChange={(e) => setPushNotifications(e.target.checked)}
                    />
                  }
                  label="푸시 알림"
                />
                <FormControlLabel
                  control={
                    <Switch
                      checked={soundEnabled}
                      onChange={(e) => setSoundEnabled(e.target.checked)}
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
                      onChange={(e) => setPublicProfile(e.target.checked)}
                    />
                  }
                  label="프로필 공개"
                />
                <FormControlLabel
                  control={
                    <Switch
                      checked={analyticsEnabled}
                      onChange={(e) => setAnalyticsEnabled(e.target.checked)}
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
