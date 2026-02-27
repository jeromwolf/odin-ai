import React, { useState, useCallback } from 'react';
import {
  Box,
  Typography,
  Paper,
  Grid,
  TextField,
  CircularProgress,
  Alert,
  Card,
  CardContent,
  Chip,
  Tabs,
  Tab,
  Divider,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  IconButton,
  Tooltip,
  InputAdornment,
  LinearProgress,
} from '@mui/material';
import {
  Search as SearchIcon,
  Hub,
  AccountBalance,
  LocalOffer,
  LocationOn,
  TrendingUp,
  Lightbulb,
  Groups,
  Category,
  Send,
} from '@mui/icons-material';
import graphService, {
  GlobalAskResponse,
  GraphStatus,
} from '../services/graphService';
import { PageHeader } from '../components/common';
import { ENTITY_TYPE_COLORS } from '../utils/colors';

// ─── TabPanel ───────────────────────────────────────────────────────────────

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel({ children, value, index }: TabPanelProps) {
  return (
    <div role="tabpanel" hidden={value !== index}>
      {value === index && <Box sx={{ pt: 2 }}>{children}</Box>}
    </div>
  );
}

// ─── Constants ───────────────────────────────────────────────────────────────

const entityTypeColors = ENTITY_TYPE_COLORS;

const entityTypeIcons: Record<string, React.ReactElement> = {
  Organization: <AccountBalance fontSize="small" />,
  Project: <Category fontSize="small" />,
  Technology: <Hub fontSize="small" />,
  Region: <LocationOn fontSize="small" />,
  Regulation: <Lightbulb fontSize="small" />,
  Material: <LocalOffer fontSize="small" />,
};

const quickSearches = [
  { label: '충남 공주시', icon: <LocationOn fontSize="small" /> },
  { label: '재해복구', icon: <Category fontSize="small" /> },
  { label: '소하천 공사', icon: <TrendingUp fontSize="small" /> },
  { label: '건설 트렌드', icon: <TrendingUp fontSize="small" /> },
  { label: '도로공사', icon: <Category fontSize="small" /> },
];

// ─── GraphExplorer Component ─────────────────────────────────────────────────

const GraphExplorer: React.FC = () => {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<GlobalAskResponse | null>(null);
  const [graphStatus, setGraphStatus] = useState<GraphStatus | null>(null);
  const [ragStatus, setRagStatus] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [tabValue, setTabValue] = useState(0);
  const [statusLoaded, setStatusLoaded] = useState(false);

  // Load status on first render
  React.useEffect(() => {
    if (!statusLoaded) {
      loadStatus();
      setStatusLoaded(true);
    }
  }, [statusLoaded]);

  const loadStatus = async () => {
    try {
      const [gs, rs] = await Promise.all([
        graphService.getStatus().catch(() => null),
        graphService.getRagStatus().catch(() => null),
      ]);
      setGraphStatus(gs);
      setRagStatus(rs);
    } catch (e) {
      console.error('Status load failed:', e);
    }
  };

  const handleSearch = useCallback(async () => {
    if (!query.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const data = await graphService.globalAsk(query.trim(), 5);
      setResult(data);
      setTabValue(0);
    } catch (e: any) {
      setError(
        e?.response?.data?.detail || '질의 처리 중 오류가 발생했습니다'
      );
    } finally {
      setLoading(false);
    }
  }, [query]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') handleSearch();
  };

  return (
    <Box>
      {/* ── Header ── */}
      <PageHeader title="지식 그래프 탐색기" icon={<Hub />} />

      {/* ── Status Cards ── */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={4}>
          <Card variant="outlined">
            <CardContent sx={{ py: 1.5, '&:last-child': { pb: 1.5 } }}>
              <Box
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                }}
              >
                <Box>
                  <Typography variant="caption" color="text.secondary">
                    Neo4j 그래프
                  </Typography>
                  <Typography variant="h6">
                    {graphStatus?.total_nodes?.toLocaleString() || '-'} 노드
                  </Typography>
                </Box>
                <Chip
                  size="small"
                  label={
                    graphStatus?.neo4j_connected ? '연결됨' : '미연결'
                  }
                  color={
                    graphStatus?.neo4j_connected ? 'success' : 'error'
                  }
                />
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={4}>
          <Card variant="outlined">
            <CardContent sx={{ py: 1.5, '&:last-child': { pb: 1.5 } }}>
              <Box
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                }}
              >
                <Box>
                  <Typography variant="caption" color="text.secondary">
                    GraphRAG 엔티티
                  </Typography>
                  <Typography variant="h6">
                    {ragStatus?.graphrag?.entities?.toLocaleString() || '-'} 개
                  </Typography>
                </Box>
                <Chip
                  size="small"
                  label={
                    ragStatus?.graphrag?.available ? '활성' : '비활성'
                  }
                  color={
                    ragStatus?.graphrag?.available ? 'success' : 'default'
                  }
                />
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={4}>
          <Card variant="outlined">
            <CardContent sx={{ py: 1.5, '&:last-child': { pb: 1.5 } }}>
              <Box
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                }}
              >
                <Box>
                  <Typography variant="caption" color="text.secondary">
                    커뮤니티
                  </Typography>
                  <Typography variant="h6">
                    {ragStatus?.graphrag?.communities?.toLocaleString() || '-'} 개
                  </Typography>
                </Box>
                <Groups color="primary" />
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* ── Search Bar ── */}
      <Paper sx={{ p: 2, mb: 2 }}>
        <TextField
          fullWidth
          placeholder="입찰 데이터에 대해 질문하세요 (예: 충청남도 건설 트렌드는?)"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={loading}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon />
              </InputAdornment>
            ),
            endAdornment: (
              <InputAdornment position="end">
                <IconButton
                  onClick={handleSearch}
                  disabled={loading || !query.trim()}
                  color="primary"
                >
                  {loading ? (
                    <CircularProgress size={20} />
                  ) : (
                    <Send />
                  )}
                </IconButton>
              </InputAdornment>
            ),
          }}
        />
        <Box
          sx={{ mt: 1.5, display: 'flex', gap: 1, flexWrap: 'wrap', alignItems: 'center' }}
        >
          <Typography
            variant="caption"
            color="text.secondary"
            sx={{ mr: 0.5 }}
          >
            빠른 검색:
          </Typography>
          {quickSearches.map((qs) => (
            <Chip
              key={qs.label}
              label={qs.label}
              icon={qs.icon}
              size="small"
              variant="outlined"
              clickable
              onClick={() => setQuery(qs.label)}
            />
          ))}
        </Box>
      </Paper>

      {loading && <LinearProgress sx={{ mb: 2 }} />}
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {/* ── Results ── */}
      {result && (
        <Grid container spacing={2}>
          {/* AI Answer */}
          <Grid item xs={12} md={7}>
            <Paper sx={{ p: 3, minHeight: 400 }}>
              <Typography variant="h6" gutterBottom>
                <Lightbulb
                  sx={{
                    mr: 1,
                    verticalAlign: 'middle',
                    color: '#ff9800',
                  }}
                />
                AI 분석 결과
              </Typography>
              <Divider sx={{ mb: 2 }} />
              <Typography
                variant="body1"
                sx={{ whiteSpace: 'pre-wrap', lineHeight: 1.8 }}
              >
                {result.answer}
              </Typography>
              {!result.has_llm_answer && (
                <Alert severity="info" sx={{ mt: 2 }}>
                  LLM이 비활성화되어 커뮤니티 요약만 표시됩니다.
                </Alert>
              )}
            </Paper>
          </Grid>

          {/* Side Panel */}
          <Grid item xs={12} md={5}>
            <Paper sx={{ minHeight: 400 }}>
              <Tabs
                value={tabValue}
                onChange={(_, v) => setTabValue(v)}
                variant="fullWidth"
                sx={{ borderBottom: 1, borderColor: 'divider' }}
              >
                <Tab
                  label={`커뮤니티 (${result.communities?.length ?? 0})`}
                />
                <Tab
                  label={`엔티티 (${result.related_entities?.length ?? 0})`}
                />
              </Tabs>

              {/* Communities Tab */}
              <TabPanel value={tabValue} index={0}>
                <Box
                  sx={{
                    px: 2,
                    pb: 2,
                    maxHeight: 500,
                    overflow: 'auto',
                  }}
                >
                  {result.communities?.length > 0 ? (
                    result.communities.map((comm) => (
                      <Card
                        key={comm.community_id}
                        variant="outlined"
                        sx={{ mb: 1.5 }}
                      >
                        <CardContent
                          sx={{ py: 1.5, '&:last-child': { pb: 1.5 } }}
                        >
                          <Typography
                            variant="subtitle2"
                            fontWeight="bold"
                            gutterBottom
                          >
                            #{comm.community_id}{' '}
                            {comm.title?.length > 60
                              ? `${comm.title.slice(0, 60)}...`
                              : comm.title}
                          </Typography>
                          <Typography
                            variant="body2"
                            color="text.secondary"
                            sx={{ mb: 1 }}
                          >
                            {comm.summary?.length > 120
                              ? `${comm.summary.slice(0, 120)}...`
                              : comm.summary}
                          </Typography>
                          <Box sx={{ display: 'flex', gap: 1 }}>
                            <Chip
                              size="small"
                              label={`엔티티 ${comm.entity_count}`}
                              color="primary"
                              variant="outlined"
                            />
                            <Chip
                              size="small"
                              label={`입찰 ${comm.bid_count}건`}
                              color="secondary"
                              variant="outlined"
                            />
                          </Box>
                          {comm.findings?.length > 0 && (
                            <Box
                              sx={{
                                mt: 1,
                                display: 'flex',
                                gap: 0.5,
                                flexWrap: 'wrap',
                              }}
                            >
                              {comm.findings.slice(0, 5).map((f, fi) => (
                                <Chip
                                  key={fi}
                                  size="small"
                                  label={
                                    f.entity?.length > 20
                                      ? `${f.entity.slice(0, 20)}...`
                                      : f.entity
                                  }
                                  sx={{
                                    bgcolor:
                                      entityTypeColors[f.type] || '#757575',
                                    color: 'white',
                                    fontSize: '0.7rem',
                                  }}
                                />
                              ))}
                            </Box>
                          )}
                        </CardContent>
                      </Card>
                    ))
                  ) : (
                    <Alert severity="info">커뮤니티 데이터가 없습니다</Alert>
                  )}
                </Box>
              </TabPanel>

              {/* Entities Tab */}
              <TabPanel value={tabValue} index={1}>
                <Box
                  sx={{
                    px: 2,
                    pb: 2,
                    maxHeight: 500,
                    overflow: 'auto',
                  }}
                >
                  {result.related_entities?.length > 0 ? (
                    <List dense>
                      {result.related_entities.map((entity, i) => (
                        <ListItem key={i} sx={{ px: 0 }}>
                          <ListItemIcon sx={{ minWidth: 36 }}>
                            <Tooltip title={entity.type}>
                              {entityTypeIcons[entity.type] ?? (
                                <Hub fontSize="small" />
                              )}
                            </Tooltip>
                          </ListItemIcon>
                          <ListItemText
                            primary={entity.name}
                            secondary={
                              entity.description?.length > 80
                                ? `${entity.description.slice(0, 80)}...`
                                : entity.description || entity.type
                            }
                            primaryTypographyProps={{
                              variant: 'body2',
                              fontWeight: 'medium',
                            }}
                            secondaryTypographyProps={{ variant: 'caption' }}
                          />
                        </ListItem>
                      ))}
                    </List>
                  ) : (
                    <Alert severity="info">관련 엔티티가 없습니다</Alert>
                  )}
                </Box>
              </TabPanel>
            </Paper>
          </Grid>
        </Grid>
      )}

      {/* ── Empty State ── */}
      {!result && !loading && (
        <Paper sx={{ p: 6, textAlign: 'center' }}>
          <Hub sx={{ fontSize: 64, color: 'text.disabled', mb: 2 }} />
          <Typography variant="h6" color="text.secondary" gutterBottom>
            지식 그래프에 질문해 보세요
          </Typography>
          <Typography variant="body2" color="text.disabled">
            GraphRAG 커뮤니티 분석을 기반으로 입찰 데이터의 패턴, 트렌드,
            인사이트를 제공합니다
          </Typography>
        </Paper>
      )}
    </Box>
  );
};

export default GraphExplorer;
