import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Card,
  CardContent,
  Chip,
  Button,
  Tabs,
  Tab,
  Pagination,
  Typography,
  Divider,
  Collapse,
  IconButton,
} from '@mui/material';
import {
  Notifications,
  DoneAll,
  ExpandMore,
  ExpandLess,
  Circle,
} from '@mui/icons-material';
import apiClient from '../services/api';
import { FullscreenLoading, EmptyState, PageHeader } from '../components/common';
import { getRelativeTime } from '../utils/formatters';

interface NotificationItem {
  id: string;
  title: string;
  message: string;
  type: string;
  status: string;
  priority: string;
  metadata: Record<string, any>;
  created_at: string;
  read_at: string | null;
}

const getTypeLabel = (type: string): string => {
  const map: Record<string, string> = {
    bid_alert: '입찰 알림',
    system: '시스템',
    deadline: '마감 임박',
    new_bid: '신규 공고',
  };
  return map[type] || type;
};

const getTypeColor = (type: string): 'primary' | 'warning' | 'error' | 'default' => {
  const map: Record<string, 'primary' | 'warning' | 'error' | 'default'> = {
    bid_alert: 'primary',
    deadline: 'warning',
    new_bid: 'primary',
    system: 'default',
  };
  return map[type] || 'default';
};

const statusMap = ['all', 'unread', 'read'];

const NotificationInbox: React.FC = () => {
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState(0); // 0=전체, 1=안읽음, 2=읽음
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [markingAll, setMarkingAll] = useState(false);
  const limit = 20;

  const loadNotifications = useCallback(async () => {
    setLoading(true);
    try {
      const status = statusMap[tab];
      const response = await apiClient.getNotifications(status === 'unread');
      const data = response?.data || response || [];
      const items = Array.isArray(data) ? data : [];
      const filtered = status === 'all' ? items :
        status === 'unread' ? items.filter((n: NotificationItem) => n.status !== 'read') :
        items.filter((n: NotificationItem) => n.status === 'read');
      setTotal(response?.total || filtered.length);
      const start = (page - 1) * limit;
      setNotifications(filtered.slice(start, start + limit));
    } catch {
      setNotifications([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  }, [tab, page]);

  useEffect(() => {
    loadNotifications();
  }, [loadNotifications]);

  const handleTabChange = (_: React.SyntheticEvent, newValue: number) => {
    setTab(newValue);
    setPage(1);
    setExpandedId(null);
  };

  const handleExpand = async (item: NotificationItem) => {
    const isOpening = expandedId !== item.id;
    setExpandedId(isOpening ? item.id : null);
    if (isOpening && item.status !== 'read') {
      try {
        await apiClient.markNotificationAsRead(item.id);
        setNotifications((prev) =>
          prev.map((n) =>
            n.id === item.id ? { ...n, status: 'read', read_at: new Date().toISOString() } : n
          )
        );
      } catch {
        // 읽음 처리 실패 시 무시
      }
    }
  };

  const handleMarkAllRead = async () => {
    setMarkingAll(true);
    try {
      await apiClient.markAllNotificationsAsRead();
      setNotifications((prev) => prev.map((n) => ({ ...n, status: 'read', read_at: new Date().toISOString() })));
    } catch {
      // 실패 시 무시
    } finally {
      setMarkingAll(false);
    }
  };

  const unreadCount = notifications.filter((n) => n.status !== 'read').length;

  if (loading) {
    return <FullscreenLoading message="알림을 불러오는 중..." />;
  }

  return (
    <Box>
      <PageHeader
        title="알림 센터"
        icon={<Notifications />}
        action={
          <Button
            variant="outlined"
            startIcon={<DoneAll />}
            onClick={handleMarkAllRead}
            disabled={markingAll || unreadCount === 0}
          >
            {markingAll ? '처리 중...' : '모두 읽음 처리'}
          </Button>
        }
      />

      <Tabs value={tab} onChange={handleTabChange} sx={{ mb: 2, borderBottom: 1, borderColor: 'divider' }}>
        <Tab label="전체" />
        <Tab label="안읽음" />
        <Tab label="읽음" />
      </Tabs>

      {notifications.length === 0 ? (
        <EmptyState
          title="알림이 없습니다"
          description="새로운 알림이 도착하면 여기에 표시됩니다"
        />
      ) : (
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
          {notifications.map((item) => {
            const isUnread = item.status !== 'read';
            const isExpanded = expandedId === item.id;
            return (
              <Card
                key={item.id}
                sx={{
                  borderLeft: isUnread ? '4px solid' : '4px solid transparent',
                  borderLeftColor: isUnread ? 'primary.main' : 'transparent',
                  cursor: 'pointer',
                  '&:hover': { boxShadow: 2 },
                }}
                onClick={() => handleExpand(item)}
              >
                <CardContent sx={{ pb: '12px !important' }}>
                  <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 1 }}>
                    {isUnread && (
                      <Circle sx={{ fontSize: 10, color: 'primary.main', mt: 0.8, flexShrink: 0 }} />
                    )}
                    <Box sx={{ flexGrow: 1, minWidth: 0 }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 0.5 }}>
                        <Typography
                          variant="subtitle1"
                          fontWeight={isUnread ? 700 : 400}
                          noWrap
                          sx={{ flex: 1, mr: 1 }}
                        >
                          {item.title}
                        </Typography>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexShrink: 0 }}>
                          <Chip
                            label={getTypeLabel(item.type)}
                            size="small"
                            color={getTypeColor(item.type)}
                            variant="outlined"
                          />
                          <Typography variant="caption" color="text.secondary">
                            {getRelativeTime(item.created_at)}
                          </Typography>
                          <IconButton size="small" onClick={(e) => { e.stopPropagation(); handleExpand(item); }}>
                            {isExpanded ? <ExpandLess /> : <ExpandMore />}
                          </IconButton>
                        </Box>
                      </Box>
                      <Typography variant="body2" color="text.secondary" noWrap={!isExpanded}>
                        {item.message}
                      </Typography>
                    </Box>
                  </Box>

                  <Collapse in={isExpanded} timeout="auto" unmountOnExit>
                    <Divider sx={{ my: 1.5 }} />
                    <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap', mb: 1 }}>
                      {item.message}
                    </Typography>
                    {item.metadata?.bid_notice_no && (
                      <Typography variant="caption" color="text.secondary">
                        공고번호: {item.metadata.bid_notice_no}
                      </Typography>
                    )}
                    {item.read_at && (
                      <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.5 }}>
                        읽은 시간: {getRelativeTime(item.read_at)}
                      </Typography>
                    )}
                  </Collapse>
                </CardContent>
              </Card>
            );
          })}
        </Box>
      )}

      {total > limit && (
        <Box sx={{ display: 'flex', justifyContent: 'center', mt: 3 }}>
          <Pagination
            count={Math.ceil(total / limit)}
            page={page}
            onChange={(_, value) => setPage(value)}
            color="primary"
          />
        </Box>
      )}
    </Box>
  );
};

export default NotificationInbox;
