import React from 'react';
import {
  LineChart, Line, BarChart, Bar, PieChart, Pie, AreaChart, Area,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  Cell, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar
} from 'recharts';
import { Card, CardContent, Typography, Box, useTheme } from '@mui/material';
import { styled } from '@mui/material/styles';

// 스타일 컴포넌트
const ChartCard = styled(Card)(({ theme }) => ({
  height: '100%',
  boxShadow: theme.shadows[2],
  borderRadius: 12,
  overflow: 'hidden',
  transition: 'transform 0.3s ease, box-shadow 0.3s ease',
  '&:hover': {
    transform: 'translateY(-4px)',
    boxShadow: theme.shadows[6],
  },
  [theme.breakpoints.down('sm')]: {
    borderRadius: 8,
  },
}));

const ChartTitle = styled(Typography)(({ theme }) => ({
  fontWeight: 600,
  marginBottom: theme.spacing(2),
  color: theme.palette.text.primary,
}));

// 색상 팔레트
const COLORS = {
  primary: ['#8884d8', '#82ca9d', '#ffc658', '#ff7c7c', '#8dd1e1', '#d084d0'],
  success: '#4caf50',
  warning: '#ff9800',
  error: '#f44336',
  info: '#2196f3',
};

interface ChartData {
  name: string;
  value: number;
  [key: string]: any;
}

// 라인 차트 컴포넌트
export const EnhancedLineChart: React.FC<{
  data: ChartData[];
  title: string;
  dataKey?: string;
  height?: number;
}> = ({ data, title, dataKey = 'value', height = 300 }) => {
  const theme = useTheme();

  return (
    <ChartCard>
      <CardContent>
        <ChartTitle variant="h6">{title}</ChartTitle>
        <ResponsiveContainer width="100%" height={height}>
          <LineChart data={data} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke={theme.palette.divider} />
            <XAxis
              dataKey="name"
              stroke={theme.palette.text.secondary}
              style={{ fontSize: '0.875rem' }}
            />
            <YAxis
              stroke={theme.palette.text.secondary}
              style={{ fontSize: '0.875rem' }}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: theme.palette.background.paper,
                border: `1px solid ${theme.palette.divider}`,
                borderRadius: 8
              }}
            />
            <Legend />
            <Line
              type="monotone"
              dataKey={dataKey}
              stroke={COLORS.primary[0]}
              strokeWidth={2}
              dot={{ r: 4 }}
              activeDot={{ r: 6 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </CardContent>
    </ChartCard>
  );
};

// 막대 차트 컴포넌트
export const EnhancedBarChart: React.FC<{
  data: ChartData[];
  title: string;
  dataKey?: string;
  height?: number;
}> = ({ data, title, dataKey = 'value', height = 300 }) => {
  const theme = useTheme();

  return (
    <ChartCard>
      <CardContent>
        <ChartTitle variant="h6">{title}</ChartTitle>
        <ResponsiveContainer width="100%" height={height}>
          <BarChart data={data} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke={theme.palette.divider} />
            <XAxis
              dataKey="name"
              stroke={theme.palette.text.secondary}
              style={{ fontSize: '0.875rem' }}
              angle={-45}
              textAnchor="end"
              height={80}
            />
            <YAxis
              stroke={theme.palette.text.secondary}
              style={{ fontSize: '0.875rem' }}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: theme.palette.background.paper,
                border: `1px solid ${theme.palette.divider}`,
                borderRadius: 8
              }}
            />
            <Bar dataKey={dataKey} fill={COLORS.primary[0]} radius={[8, 8, 0, 0]}>
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={COLORS.primary[index % COLORS.primary.length]} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </ChartCard>
  );
};

// 파이 차트 컴포넌트
export const EnhancedPieChart: React.FC<{
  data: ChartData[];
  title: string;
  height?: number;
}> = ({ data, title, height = 300 }) => {
  const theme = useTheme();

  return (
    <ChartCard>
      <CardContent>
        <ChartTitle variant="h6">{title}</ChartTitle>
        <ResponsiveContainer width="100%" height={height}>
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              labelLine={false}
              label={(entry) => `${entry.name}: ${entry.value}`}
              outerRadius={80}
              fill="#8884d8"
              dataKey="value"
            >
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={COLORS.primary[index % COLORS.primary.length]} />
              ))}
            </Pie>
            <Tooltip
              contentStyle={{
                backgroundColor: theme.palette.background.paper,
                border: `1px solid ${theme.palette.divider}`,
                borderRadius: 8
              }}
            />
            <Legend />
          </PieChart>
        </ResponsiveContainer>
      </CardContent>
    </ChartCard>
  );
};

// 영역 차트 컴포넌트
export const EnhancedAreaChart: React.FC<{
  data: ChartData[];
  title: string;
  dataKeys: string[];
  height?: number;
}> = ({ data, title, dataKeys, height = 300 }) => {
  const theme = useTheme();

  return (
    <ChartCard>
      <CardContent>
        <ChartTitle variant="h6">{title}</ChartTitle>
        <ResponsiveContainer width="100%" height={height}>
          <AreaChart data={data} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke={theme.palette.divider} />
            <XAxis
              dataKey="name"
              stroke={theme.palette.text.secondary}
              style={{ fontSize: '0.875rem' }}
            />
            <YAxis
              stroke={theme.palette.text.secondary}
              style={{ fontSize: '0.875rem' }}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: theme.palette.background.paper,
                border: `1px solid ${theme.palette.divider}`,
                borderRadius: 8
              }}
            />
            <Legend />
            {dataKeys.map((key, index) => (
              <Area
                key={key}
                type="monotone"
                dataKey={key}
                stackId="1"
                stroke={COLORS.primary[index % COLORS.primary.length]}
                fill={COLORS.primary[index % COLORS.primary.length]}
                fillOpacity={0.6}
              />
            ))}
          </AreaChart>
        </ResponsiveContainer>
      </CardContent>
    </ChartCard>
  );
};

// 레이더 차트 컴포넌트
export const EnhancedRadarChart: React.FC<{
  data: any[];
  title: string;
  dataKey: string;
  height?: number;
}> = ({ data, title, dataKey, height = 300 }) => {
  const theme = useTheme();

  return (
    <ChartCard>
      <CardContent>
        <ChartTitle variant="h6">{title}</ChartTitle>
        <ResponsiveContainer width="100%" height={height}>
          <RadarChart data={data}>
            <PolarGrid stroke={theme.palette.divider} />
            <PolarAngleAxis
              dataKey="category"
              stroke={theme.palette.text.secondary}
              style={{ fontSize: '0.875rem' }}
            />
            <PolarRadiusAxis
              angle={90}
              stroke={theme.palette.text.secondary}
              style={{ fontSize: '0.75rem' }}
            />
            <Radar
              name={dataKey}
              dataKey={dataKey}
              stroke={COLORS.primary[0]}
              fill={COLORS.primary[0]}
              fillOpacity={0.6}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: theme.palette.background.paper,
                border: `1px solid ${theme.palette.divider}`,
                borderRadius: 8
              }}
            />
          </RadarChart>
        </ResponsiveContainer>
      </CardContent>
    </ChartCard>
  );
};

// 통계 카드 컴포넌트
export const StatCard: React.FC<{
  title: string;
  value: string | number;
  change?: number;
  icon?: React.ReactNode;
  color?: 'primary' | 'success' | 'warning' | 'error' | 'info';
}> = ({ title, value, change, icon, color = 'primary' }) => {
  const isPositive = change && change > 0;

  return (
    <ChartCard>
      <CardContent>
        <Box display="flex" justifyContent="space-between" alignItems="center">
          <Box>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              {title}
            </Typography>
            <Typography variant="h4" fontWeight={600}>
              {value}
            </Typography>
            {change !== undefined && (
              <Typography
                variant="body2"
                color={isPositive ? 'success.main' : 'error.main'}
                sx={{ mt: 1 }}
              >
                {isPositive ? '▲' : '▼'} {Math.abs(change)}%
              </Typography>
            )}
          </Box>
          {icon && (
            <Box
              sx={{
                p: 2,
                borderRadius: 2,
                backgroundColor: `${color}.light`,
                color: `${color}.main`,
              }}
            >
              {icon}
            </Box>
          )}
        </Box>
      </CardContent>
    </ChartCard>
  );
};

const charts = {
  EnhancedLineChart,
  EnhancedBarChart,
  EnhancedPieChart,
  EnhancedAreaChart,
  EnhancedRadarChart,
  StatCard,
};

export default charts;