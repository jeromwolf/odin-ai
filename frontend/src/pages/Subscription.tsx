import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  CardActions,
  Button,
  Grid,
  Chip,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  LinearProgress,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  AccountBalance,
  CheckCircle,
  Star,
  Download,
  Upgrade,
} from '@mui/icons-material';
import apiClient from '../services/api';

interface PlanFeature {
  name: string;
  included: boolean;
  limit?: string;
}

interface Plan {
  id: string;
  name: string;
  price: number;
  period: string;
  popular?: boolean;
  features: PlanFeature[];
  description: string;
  color: string;
}

interface BillingHistory {
  id: string;
  date: string;
  amount: number;
  plan: string;
  status: 'paid' | 'pending' | 'failed';
  invoice?: string;
}

const Subscription: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [currentPlan, setCurrentPlan] = useState('basic');
  const [cancelDialogOpen, setCancelDialogOpen] = useState(false);
  const [upgradeDialogOpen, setUpgradeDialogOpen] = useState(false);
  const [selectedPlan, setSelectedPlan] = useState<string | null>(null);
  const [billingHistory, setBillingHistory] = useState<BillingHistory[]>([]);

  // 현재 사용량
  const [usage, setUsage] = useState({
    searches: { current: 0, limit: 100 },
    bookmarks: { current: 0, limit: 50 },
    notifications: { current: 0, limit: 20 },
  });

  // 구독 정보 불러오기
  useEffect(() => {
    loadSubscriptionData();
  }, []);

  const loadSubscriptionData = async () => {
    try {
      setLoading(true);

      // 현재 구독 정보 불러오기
      const subscription = await apiClient.getSubscription();
      if (subscription) {
        setCurrentPlan(subscription.plan_type || 'basic');
      }

      // 사용량 통계 불러오기
      const usageStats = await apiClient.getUsageStatistics();
      if (usageStats) {
        setUsage({
          searches: {
            current: usageStats.searches_used || 0,
            limit: usageStats.searches_limit || 100
          },
          bookmarks: {
            current: usageStats.bookmarks_used || 0,
            limit: usageStats.bookmarks_limit || 50
          },
          notifications: {
            current: usageStats.notifications_used || 0,
            limit: usageStats.notifications_limit || 20
          },
        });
      }

      // 결제 내역 불러오기
      const paymentHistory = await apiClient.getPaymentHistory();
      if (paymentHistory && Array.isArray(paymentHistory)) {
        setBillingHistory(paymentHistory.map((payment: any) => ({
          id: payment.id,
          date: payment.date,
          amount: payment.amount,
          plan: payment.plan_name,
          status: payment.status,
          invoice: payment.invoice_id,
        })));
      }
    } catch (error) {
      console.error('구독 정보 로드 실패:', error);
    } finally {
      setLoading(false);
    }
  };

  // 요금제 정보
  const plans: Plan[] = [
    {
      id: 'basic',
      name: '베이직',
      price: 0,
      period: '무료',
      description: '기본적인 입찰 정보 검색',
      color: '#6c757d',
      features: [
        { name: '일일 검색', included: true, limit: '100회' },
        { name: '북마크', included: true, limit: '50개' },
        { name: '기본 알림', included: true, limit: '20개' },
        { name: '이메일 지원', included: true },
        { name: '고급 필터', included: false },
        { name: 'API 접근', included: false },
        { name: '우선 지원', included: false },
      ],
    },
    {
      id: 'pro',
      name: '프로',
      price: 29000,
      period: '월',
      popular: true,
      description: '전문가를 위한 고급 기능',
      color: '#007bff',
      features: [
        { name: '일일 검색', included: true, limit: '무제한' },
        { name: '북마크', included: true, limit: '무제한' },
        { name: '고급 알림', included: true, limit: '무제한' },
        { name: '이메일 지원', included: true },
        { name: '고급 필터', included: true },
        { name: 'AI 분석', included: true },
        { name: '데이터 내보내기', included: true },
        { name: 'API 접근', included: false },
        { name: '우선 지원', included: true },
      ],
    },
    {
      id: 'enterprise',
      name: '엔터프라이즈',
      price: 99000,
      period: '월',
      description: '기업용 종합 솔루션',
      color: '#28a745',
      features: [
        { name: '모든 프로 기능', included: true },
        { name: 'API 접근', included: true, limit: '무제한' },
        { name: '팀 관리', included: true },
        { name: '사용자 지정 대시보드', included: true },
        { name: '전용 계정 매니저', included: true },
        { name: '24/7 우선 지원', included: true },
        { name: '온사이트 교육', included: true },
        { name: 'SLA 보장', included: true },
      ],
    },
  ];

  // 구독 업그레이드 API 호출을 위한 학들러들 업데이트

  const getCurrentPlan = () => plans.find(plan => plan.id === currentPlan);
  const currentPlanInfo = getCurrentPlan();

  const handleUpgrade = (planId: string) => {
    setSelectedPlan(planId);
    setUpgradeDialogOpen(true);
  };

  const confirmUpgrade = async () => {
    if (selectedPlan) {
      try {
        await apiClient.updateSubscription(selectedPlan);
        setCurrentPlan(selectedPlan);
        setUpgradeDialogOpen(false);
        alert(`${plans.find(p => p.id === selectedPlan)?.name} 플랜으로 업그레이드되었습니다.`);

        // 새로고침하여 새 데이터 불러오기
        await loadSubscriptionData();
      } catch (error) {
        console.error('업그레이드 실패:', error);
        alert('업그레이드에 실패했습니다.');
      }
    }
  };

  const handleCancelSubscription = async () => {
    try {
      await apiClient.cancelSubscription();
      setCancelDialogOpen(false);
      alert('구독이 취소되었습니다. 현재 결제 기간이 끝날 때까지 서비스를 이용할 수 있습니다.');

      // 새로고침하여 새 데이터 불러오기
      await loadSubscriptionData();
    } catch (error) {
      console.error('구독 취소 실패:', error);
      alert('구독 취소에 실패했습니다.');
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'paid': return 'success';
      case 'pending': return 'warning';
      case 'failed': return 'error';
      default: return 'default';
    }
  };

  const getUsagePercentage = (current: number, limit: number) => (current / limit) * 100;

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <Typography>구독 정보를 불러오는 중...</Typography>
      </Box>
    );
  }

  return (
    <Box>
      <Typography variant="h4" sx={{ mb: 3, display: 'flex', alignItems: 'center' }}>
        <AccountBalance sx={{ mr: 1 }} />
        구독 관리
      </Typography>

      {/* 현재 구독 상태 */}
      <Card sx={{ mb: 4 }}>
        <CardContent>
          <Grid container spacing={3} alignItems="center">
            <Grid item xs={12} md={8}>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Typography variant="h5" sx={{ mr: 2 }}>
                  현재 플랜: {currentPlanInfo?.name}
                </Typography>
                <Chip
                  label={currentPlanInfo?.price === 0 ? '무료' : '유료'}
                  color={currentPlanInfo?.price === 0 ? 'default' : 'primary'}
                />
                {currentPlanInfo?.popular && (
                  <Chip label="인기" color="secondary" sx={{ ml: 1 }} icon={<Star />} />
                )}
              </Box>
              <Typography variant="body1" color="text.secondary">
                {currentPlanInfo?.description}
              </Typography>
              {currentPlanInfo && currentPlanInfo.price > 0 && (
                <Typography variant="h6" sx={{ mt: 2 }}>
                  월 {currentPlanInfo.price.toLocaleString()}원
                </Typography>
              )}
            </Grid>
            <Grid item xs={12} md={4}>
              {currentPlan !== 'enterprise' && (
                <Button
                  variant="contained"
                  fullWidth
                  startIcon={<Upgrade />}
                  onClick={() => handleUpgrade(currentPlan === 'basic' ? 'pro' : 'enterprise')}
                >
                  업그레이드
                </Button>
              )}
              {currentPlan !== 'basic' && (
                <Button
                  variant="outlined"
                  color="error"
                  fullWidth
                  sx={{ mt: 1 }}
                  onClick={() => setCancelDialogOpen(true)}
                >
                  구독 취소
                </Button>
              )}
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* 사용량 현황 */}
      <Card sx={{ mb: 4 }}>
        <CardContent>
          <Typography variant="h6" sx={{ mb: 3 }}>
            이번 달 사용량
          </Typography>
          <Grid container spacing={3}>
            <Grid item xs={12} md={4}>
              <Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                  <Typography variant="body2">일일 검색</Typography>
                  <Typography variant="body2">
                    {usage.searches.current}/{usage.searches.limit}
                  </Typography>
                </Box>
                <LinearProgress
                  variant="determinate"
                  value={getUsagePercentage(usage.searches.current, usage.searches.limit)}
                  sx={{ height: 8, borderRadius: 4 }}
                />
              </Box>
            </Grid>
            <Grid item xs={12} md={4}>
              <Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                  <Typography variant="body2">북마크</Typography>
                  <Typography variant="body2">
                    {usage.bookmarks.current}/{usage.bookmarks.limit}
                  </Typography>
                </Box>
                <LinearProgress
                  variant="determinate"
                  value={getUsagePercentage(usage.bookmarks.current, usage.bookmarks.limit)}
                  color="secondary"
                  sx={{ height: 8, borderRadius: 4 }}
                />
              </Box>
            </Grid>
            <Grid item xs={12} md={4}>
              <Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                  <Typography variant="body2">알림 설정</Typography>
                  <Typography variant="body2">
                    {usage.notifications.current}/{usage.notifications.limit}
                  </Typography>
                </Box>
                <LinearProgress
                  variant="determinate"
                  value={getUsagePercentage(usage.notifications.current, usage.notifications.limit)}
                  color="warning"
                  sx={{ height: 8, borderRadius: 4 }}
                />
              </Box>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* 요금제 비교 */}
      <Typography variant="h5" sx={{ mb: 3 }}>
        요금제 비교
      </Typography>
      <Grid container spacing={3} sx={{ mb: 4 }}>
        {plans.map((plan) => (
          <Grid item xs={12} md={4} key={plan.id}>
            <Card
              sx={{
                height: '100%',
                position: 'relative',
                border: currentPlan === plan.id ? 2 : 1,
                borderColor: currentPlan === plan.id ? plan.color : 'divider',
              }}
            >
              {plan.popular && (
                <Chip
                  label="인기"
                  color="secondary"
                  size="small"
                  sx={{ position: 'absolute', top: 16, right: 16 }}
                />
              )}
              <CardContent>
                <Typography variant="h5" sx={{ mb: 1 }}>
                  {plan.name}
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  {plan.description}
                </Typography>
                <Box sx={{ mb: 3 }}>
                  <Typography variant="h3" component="span">
                    {plan.price === 0 ? '무료' : `₩${plan.price.toLocaleString()}`}
                  </Typography>
                  {plan.price > 0 && (
                    <Typography variant="body1" component="span" color="text.secondary">
                      /{plan.period}
                    </Typography>
                  )}
                </Box>
                <List dense>
                  {plan.features.map((feature, index) => (
                    <ListItem key={index} sx={{ px: 0 }}>
                      <ListItemIcon sx={{ minWidth: 32 }}>
                        <CheckCircle
                          fontSize="small"
                          color={feature.included ? 'success' : 'disabled'}
                        />
                      </ListItemIcon>
                      <ListItemText
                        primary={feature.name}
                        secondary={feature.limit}
                        sx={{
                          color: feature.included ? 'text.primary' : 'text.disabled',
                        }}
                      />
                    </ListItem>
                  ))}
                </List>
              </CardContent>
              <CardActions sx={{ p: 2, pt: 0 }}>
                {currentPlan === plan.id ? (
                  <Button fullWidth disabled>
                    현재 플랜
                  </Button>
                ) : (
                  <Button
                    fullWidth
                    variant="contained"
                    onClick={() => handleUpgrade(plan.id)}
                    sx={{ bgcolor: plan.color }}
                  >
                    {currentPlan === 'basic' ? '시작하기' : '업그레이드'}
                  </Button>
                )}
              </CardActions>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* 결제 내역 */}
      <Card>
        <CardContent>
          <Typography variant="h6" sx={{ mb: 3 }}>
            결제 내역
          </Typography>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>날짜</TableCell>
                  <TableCell>플랜</TableCell>
                  <TableCell>금액</TableCell>
                  <TableCell>상태</TableCell>
                  <TableCell>영수증</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {billingHistory.map((bill) => (
                  <TableRow key={bill.id}>
                    <TableCell>{bill.date}</TableCell>
                    <TableCell>{bill.plan}</TableCell>
                    <TableCell>₩{bill.amount.toLocaleString()}</TableCell>
                    <TableCell>
                      <Chip
                        label={bill.status === 'paid' ? '결제완료' : bill.status === 'pending' ? '대기중' : '실패'}
                        color={getStatusColor(bill.status)}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>
                      {bill.invoice && (
                        <Tooltip title="영수증 다운로드">
                          <IconButton size="small">
                            <Download />
                          </IconButton>
                        </Tooltip>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>

      {/* 업그레이드 확인 다이얼로그 */}
      <Dialog open={upgradeDialogOpen} onClose={() => setUpgradeDialogOpen(false)}>
        <DialogTitle>플랜 업그레이드</DialogTitle>
        <DialogContent>
          {selectedPlan && (
            <Box>
              <Alert severity="info" sx={{ mb: 2 }}>
                <Typography variant="body2">
                  {plans.find(p => p.id === selectedPlan)?.name} 플랜으로 업그레이드하시겠습니까?
                </Typography>
              </Alert>
              <Typography variant="body1">
                • 즉시 모든 기능에 액세스할 수 있습니다
              </Typography>
              <Typography variant="body1">
                • 다음 결제일부터 새로운 요금이 적용됩니다
              </Typography>
              <Typography variant="body1">
                • 언제든지 플랜을 변경하거나 취소할 수 있습니다
              </Typography>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setUpgradeDialogOpen(false)}>취소</Button>
          <Button onClick={confirmUpgrade} variant="contained">
            업그레이드
          </Button>
        </DialogActions>
      </Dialog>

      {/* 구독 취소 확인 다이얼로그 */}
      <Dialog open={cancelDialogOpen} onClose={() => setCancelDialogOpen(false)}>
        <DialogTitle>구독 취소</DialogTitle>
        <DialogContent>
          <Alert severity="warning" sx={{ mb: 2 }}>
            구독을 취소하면 현재 결제 기간이 끝날 때까지만 프리미엄 기능을 사용할 수 있습니다.
          </Alert>
          <Typography variant="body1">
            정말로 구독을 취소하시겠습니까?
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCancelDialogOpen(false)}>유지</Button>
          <Button onClick={handleCancelSubscription} color="error" variant="contained">
            취소
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Subscription;
