import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Switch,
  FormControlLabel,
  FormGroup,
  Card,
  CardContent,
  Chip,
  TextField,
  Button,
  Alert,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
} from '@mui/material';
import {
  ExpandMore,
  NotificationsActive,
  Email,
  Add,
  Delete,
  Schedule,
  TrendingUp,
  Settings,
  Bookmark,
} from '@mui/icons-material';
import apiClient from '../services/api';
import { FullscreenLoading, PageHeader } from '../components/common';
import { useNotification } from '../contexts/NotificationContext';
import { formatKRW } from '../utils/formatters';

interface NotificationSettings {
  email: boolean;
  push: boolean;
}

interface KeywordAlert {
  id: number;
  keyword: string;
  category: string;
  priceRange?: {
    min: number;
    max: number;
  };
  workTypes?: string;
  enabled: boolean;
}

const Notifications: React.FC = () => {
  const { showSuccess, showError } = useNotification();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [generalSettings, setGeneralSettings] = useState<NotificationSettings>({
    email: true,
    push: true,
  });

  const [bidAlerts, setBidAlerts] = useState<NotificationSettings>({
    email: true,
    push: true,
  });

  const [deadlineAlerts, setDeadlineAlerts] = useState<NotificationSettings>({
    email: true,
    push: true,
  });

  const [keywordAlerts, setKeywordAlerts] = useState<KeywordAlert[]>([]);

  const [openAddDialog, setOpenAddDialog] = useState(false);
  const [newKeyword, setNewKeyword] = useState({
    keyword: '',
    category: '',
    minPrice: '',
    maxPrice: '',
    workTypes: '',
  });

  const categories = ['건설', '소프트웨어', '토목', '전기', '통신', '용역', '물품', '기계'];

  // 알림 설정 불러오기
  useEffect(() => {
    loadNotificationSettings();
  }, []);

  const loadNotificationSettings = async () => {
    try {
      setLoading(true);
      const settings = await apiClient.getNotificationSettings();
      if (settings) {
        // 일반 설정
        if (settings.general) {
          setGeneralSettings({
            email: settings.general.email !== false,
            push: settings.general.push !== false,
          });
        }
        // 입찰 알림
        if (settings.bid_alerts) {
          setBidAlerts({
            email: settings.bid_alerts.email !== false,
            push: settings.bid_alerts.push !== false,
          });
        }
        // 마감 알림
        if (settings.deadline_alerts) {
          setDeadlineAlerts({
            email: settings.deadline_alerts.email !== false,
            push: settings.deadline_alerts.push !== false,
          });
        }
        // 키워드 알림
        if (settings.keyword_alerts) {
          setKeywordAlerts(settings.keyword_alerts.map((alert: any) => ({
            id: alert.id,
            keyword: alert.keyword,
            category: alert.category || '기타',
            priceRange: alert.min_price && alert.max_price ? {
              min: alert.min_price,
              max: alert.max_price
            } : undefined,
            enabled: alert.is_active !== false,
          })));
        }
      }
    } catch (error) {
      console.error('알림 설정 로드 실패:', error);
    } finally {
      setLoading(false);
    }
  };

  const saveNotificationSettings = async () => {
    try {
      setSaving(true);
      const settings = {
        general: generalSettings,
        bid_alerts: bidAlerts,
        deadline_alerts: deadlineAlerts,
        keyword_alerts: keywordAlerts.map(alert => ({
          keyword: alert.keyword,
          category: alert.category,
          min_price: alert.priceRange?.min,
          max_price: alert.priceRange?.max,
          is_active: alert.enabled,
        })),
      };

      await apiClient.updateNotificationSettings(settings);
      showSuccess('알림 설정이 저장되었습니다.');
    } catch (error) {
      console.error('알림 설정 저장 실패:', error);
      showError('설정 저장에 실패했습니다.');
    } finally {
      setSaving(false);
    }
  };

  const handleGeneralSettingChange = (key: keyof NotificationSettings, value: boolean) => {
    setGeneralSettings(prev => ({ ...prev, [key]: value }));
  };

  const handleBidAlertChange = (key: keyof NotificationSettings, value: boolean) => {
    setBidAlerts(prev => ({ ...prev, [key]: value }));
  };

  const handleDeadlineAlertChange = (key: keyof NotificationSettings, value: boolean) => {
    setDeadlineAlerts(prev => ({ ...prev, [key]: value }));
  };

  const handleKeywordToggle = (id: number) => {
    setKeywordAlerts(prev =>
      prev.map(alert =>
        alert.id === id ? { ...alert, enabled: !alert.enabled } : alert
      )
    );
  };

  const handleDeleteKeyword = async (id: number) => {
    try {
      // API 호출하여 삭제 (ID가 문자열인 경우 대비)
      if (id > 1000000000) { // 새로 추가된 항목 (Date.now()로 생성)
        setKeywordAlerts(prev => prev.filter(alert => alert.id !== id));
      } else {
        await apiClient.deleteNotificationRule(String(id));
        setKeywordAlerts(prev => prev.filter(alert => alert.id !== id));
      }
    } catch (error) {
      console.error('키워드 삭제 실패:', error);
      showError('키워드 삭제에 실패했습니다.');
    }
  };

  const handleAddKeyword = async () => {
    if (newKeyword.keyword && newKeyword.category) {
      try {
        // 백엔드 API로 알림 규칙 생성
        const ruleData = {
          rule_name: `${newKeyword.keyword} (${newKeyword.category})`,
          description: `${newKeyword.category} 카테고리의 ${newKeyword.keyword} 키워드 알림`,
          conditions: {
            keywords: [newKeyword.keyword],
            category: newKeyword.category,
            min_price: newKeyword.minPrice ? parseInt(newKeyword.minPrice) : undefined,
            max_price: newKeyword.maxPrice ? parseInt(newKeyword.maxPrice) : undefined,
            work_types: newKeyword.workTypes ? newKeyword.workTypes.split(',').map(s => s.trim()).filter(Boolean) : undefined,
          },
          notification_channels: ["email", "web"],
          notification_timing: "immediate"
        };

        const createdRule = await apiClient.addNotificationRule(ruleData);

        // 생성된 규칙을 로컬 상태에 추가
        const newAlert: KeywordAlert = {
          id: createdRule.id,
          keyword: newKeyword.keyword,
          category: newKeyword.category,
          enabled: true,
        };

        if (newKeyword.minPrice && newKeyword.maxPrice) {
          newAlert.priceRange = {
            min: parseInt(newKeyword.minPrice),
            max: parseInt(newKeyword.maxPrice),
          };
        }

        setKeywordAlerts(prev => [...prev, newAlert]);
        setNewKeyword({ keyword: '', category: '', minPrice: '', maxPrice: '', workTypes: '' });
        setOpenAddDialog(false);
        showSuccess('알림 규칙이 저장되었습니다.');
      } catch (error) {
        console.error('알림 규칙 생성 실패:', error);
        showError('알림 규칙 생성에 실패했습니다.');
      }
    }
  };

  if (loading) {
    return <FullscreenLoading />;
  }

  return (
    <Box>
      <PageHeader title="알림 설정" icon={<NotificationsActive />} />

      <Alert severity="info" sx={{ mb: 3 }}>
        원하는 입찰 정보를 놓치지 않도록 알림을 설정하세요. 이메일과 푸시 알림을 통해 실시간으로 정보를 받을 수 있습니다.
      </Alert>

      {/* 전체 알림 설정 */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" sx={{ mb: 2, display: 'flex', alignItems: 'center' }}>
            <Settings sx={{ mr: 1 }} />
            전체 알림 설정
          </Typography>
          <FormGroup row>
            <FormControlLabel
              control={
                <Switch
                  checked={generalSettings.email}
                  onChange={(e) => handleGeneralSettingChange('email', e.target.checked)}
                />
              }
              label={
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  <Email sx={{ mr: 0.5, fontSize: 18 }} />
                  이메일 알림
                </Box>
              }
            />
            <FormControlLabel
              control={
                <Switch
                  checked={generalSettings.push}
                  onChange={(e) => handleGeneralSettingChange('push', e.target.checked)}
                />
              }
              label={
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  <NotificationsActive sx={{ mr: 0.5, fontSize: 18 }} />
                  푸시 알림
                </Box>
              }
            />
          </FormGroup>
        </CardContent>
      </Card>

      {/* 세부 알림 설정 */}
      <Accordion defaultExpanded>
        <AccordionSummary expandIcon={<ExpandMore />}>
          <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center' }}>
            <TrendingUp sx={{ mr: 1 }} />
            신규 입찰 알림
          </Typography>
        </AccordionSummary>
        <AccordionDetails>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            새로운 입찰 공고가 등록될 때 알림을 받습니다.
          </Typography>
          <FormGroup row>
            <FormControlLabel
              control={
                <Switch
                  checked={bidAlerts.email}
                  onChange={(e) => handleBidAlertChange('email', e.target.checked)}
                />
              }
              label="이메일"
            />
            <FormControlLabel
              control={
                <Switch
                  checked={bidAlerts.push}
                  onChange={(e) => handleBidAlertChange('push', e.target.checked)}
                />
              }
              label="푸시"
            />
          </FormGroup>
        </AccordionDetails>
      </Accordion>

      <Accordion>
        <AccordionSummary expandIcon={<ExpandMore />}>
          <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center' }}>
            <Schedule sx={{ mr: 1 }} />
            마감 임박 알림
          </Typography>
        </AccordionSummary>
        <AccordionDetails>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            관심 입찰의 마감일이 임박할 때 알림을 받습니다. (24시간, 3일 전)
          </Typography>
          <FormGroup row>
            <FormControlLabel
              control={
                <Switch
                  checked={deadlineAlerts.email}
                  onChange={(e) => handleDeadlineAlertChange('email', e.target.checked)}
                />
              }
              label="이메일"
            />
            <FormControlLabel
              control={
                <Switch
                  checked={deadlineAlerts.push}
                  onChange={(e) => handleDeadlineAlertChange('push', e.target.checked)}
                />
              }
              label="푸시"
            />
          </FormGroup>
        </AccordionDetails>
      </Accordion>

      {/* 키워드 알림 설정 */}
      <Card sx={{ mt: 3 }}>
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center' }}>
              <Bookmark sx={{ mr: 1 }} />
              키워드 알림
            </Typography>
            <Button
              variant="contained"
              startIcon={<Add />}
              onClick={() => setOpenAddDialog(true)}
            >
              키워드 추가
            </Button>
          </Box>

          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            설정한 키워드가 포함된 입찰 공고가 등록될 때 알림을 받습니다.
          </Typography>

          <List>
            {keywordAlerts.map((alert) => (
              <ListItem key={alert.id} divider>
                <ListItemText
                  primary={
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Typography variant="subtitle1">{alert.keyword}</Typography>
                      <Chip label={alert.category} size="small" color="primary" />
                      {!alert.enabled && (
                        <Chip label="비활성" size="small" color="default" />
                      )}
                    </Box>
                  }
                  secondary={
                    alert.priceRange && (
                      <Typography variant="body2" color="text.secondary">
                        가격 범위: {formatKRW(alert.priceRange.min)} ~ {formatKRW(alert.priceRange.max)}
                      </Typography>
                    )
                  }
                />
                <ListItemSecondaryAction>
                  <Box sx={{ display: 'flex', gap: 1 }}>
                    <Switch
                      checked={alert.enabled}
                      onChange={() => handleKeywordToggle(alert.id)}
                      size="small"
                    />
                    <IconButton
                      size="small"
                      onClick={() => handleDeleteKeyword(alert.id)}
                      color="error"
                    >
                      <Delete />
                    </IconButton>
                  </Box>
                </ListItemSecondaryAction>
              </ListItem>
            ))}
            {keywordAlerts.length === 0 && (
              <ListItem>
                <ListItemText
                  primary="설정된 키워드가 없습니다"
                  secondary="키워드를 추가하여 맞춤 알림을 받아보세요"
                />
              </ListItem>
            )}
          </List>
        </CardContent>
      </Card>

      {/* 키워드 추가 다이얼로그 */}
      <Dialog open={openAddDialog} onClose={() => setOpenAddDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>키워드 알림 추가</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 1 }}>
            <TextField
              fullWidth
              label="키워드"
              value={newKeyword.keyword}
              onChange={(e) => setNewKeyword(prev => ({ ...prev, keyword: e.target.value }))}
              placeholder="예: IT 시스템, 도로 포장"
              helperText="입찰 공고에서 찾을 키워드를 입력하세요"
            />

            <FormControl fullWidth>
              <InputLabel>카테고리</InputLabel>
              <Select
                value={newKeyword.category}
                label="카테고리"
                onChange={(e) => setNewKeyword(prev => ({ ...prev, category: e.target.value }))}
              >
                {categories.map((category) => (
                  <MenuItem key={category} value={category}>
                    {category}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            <Box sx={{ display: 'flex', gap: 2 }}>
              <TextField
                fullWidth
                label="최소 금액 (원)"
                type="number"
                value={newKeyword.minPrice}
                onChange={(e) => setNewKeyword(prev => ({ ...prev, minPrice: e.target.value }))}
                placeholder="1000000"
              />
              <TextField
                fullWidth
                label="최대 금액 (원)"
                type="number"
                value={newKeyword.maxPrice}
                onChange={(e) => setNewKeyword(prev => ({ ...prev, maxPrice: e.target.value }))}
                placeholder="50000000"
              />
            </Box>

            <Typography variant="caption" color="text.secondary">
              가격 범위는 선택사항입니다. 설정하지 않으면 모든 가격대의 입찰을 알립니다.
            </Typography>

            <TextField
              fullWidth
              label="업종 필터"
              placeholder="예: 종합공사, 전문공사, 실내건축공사업 (쉼표 구분)"
              value={newKeyword.workTypes || ''}
              onChange={(e) => setNewKeyword({ ...newKeyword, workTypes: e.target.value })}
              size="small"
              sx={{ mt: 2 }}
              helperText="알림 받을 업종을 쉼표로 구분하여 입력하세요"
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenAddDialog(false)}>취소</Button>
          <Button
            onClick={handleAddKeyword}
            variant="contained"
            disabled={!newKeyword.keyword || !newKeyword.category}
          >
            추가
          </Button>
        </DialogActions>
      </Dialog>

      {/* 저장 버튼 */}
      <Box sx={{ mt: 4, display: 'flex', justifyContent: 'center' }}>
        <Button
          variant="contained"
          size="large"
          sx={{ px: 4 }}
          onClick={saveNotificationSettings}
          disabled={saving}
        >
          설정 저장
        </Button>
      </Box>
    </Box>
  );
};

export default Notifications;