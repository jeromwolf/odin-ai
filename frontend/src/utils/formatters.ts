/**
 * 통합 포맷 유틸리티
 * Dashboard, Search, Bookmarks, BidDetail, Notifications 등에서 중복 사용되던 함수 통합
 */
import { format, parseISO, differenceInDays, differenceInMinutes, differenceInHours } from 'date-fns';

/**
 * 한국 원화 금액을 억/만 단위로 포맷
 * @example 150000000 → '1억 5,000만원'
 * @example 50000000  → '5,000만원'
 * @example 9000      → '9,000원'
 * @example null      → '미정'
 */
export function formatKRW(amount: number | null | undefined): string {
  if (amount == null) return '미정';

  const eok = Math.floor(amount / 100000000);
  const man = Math.floor((amount % 100000000) / 10000);
  const won = amount % 10000;

  if (eok > 0) {
    if (man > 0) {
      return `${eok.toLocaleString()}억 ${man.toLocaleString()}만원`;
    }
    return `${eok.toLocaleString()}억원`;
  }

  if (man > 0) {
    return `${man.toLocaleString()}만원`;
  }

  return `${won.toLocaleString()}원`;
}

/**
 * 날짜 문자열을 한국식 포맷으로 변환
 * @param dateStr ISO 날짜 문자열
 * @param fmt 포맷 문자열 (기본: 'yyyy.MM.dd')
 *   - 'yyyy.MM.dd'
 *   - 'yyyy.MM.dd HH:mm'
 *   - 'yyyy년 MM월 dd일'
 *   - 'MM.dd'
 */
export function formatKRDate(
  dateStr: string | null | undefined,
  fmt: string = 'yyyy.MM.dd'
): string {
  if (!dateStr) return '-';
  try {
    const date = parseISO(dateStr);
    return format(date, fmt);
  } catch {
    return '-';
  }
}

/**
 * 마감일까지 남은 일수 반환
 * @returns 남은 일수 (과거면 음수), null이면 입력이 없는 경우
 */
export function getDaysRemaining(endDateStr: string | null | undefined): number | null {
  if (!endDateStr) return null;
  try {
    const end = parseISO(endDateStr);
    const now = new Date();
    return differenceInDays(end, now);
  } catch {
    return null;
  }
}

/**
 * 상대적 시간 표현 반환
 * @example '방금 전', '5분 전', '3시간 전', '2일 전', '1주 전', '3개월 전'
 */
export function getRelativeTime(dateStr: string | null | undefined): string {
  if (!dateStr) return '-';
  try {
    const date = parseISO(dateStr);
    const now = new Date();

    const minutes = differenceInMinutes(now, date);
    if (minutes < 1) return '방금 전';
    if (minutes < 60) return `${minutes}분 전`;

    const hours = differenceInHours(now, date);
    if (hours < 24) return `${hours}시간 전`;

    const days = differenceInDays(now, date);
    if (days < 7) return `${days}일 전`;
    if (days < 30) return `${Math.floor(days / 7)}주 전`;

    const months = Math.floor(days / 30);
    return `${months}개월 전`;
  } catch {
    return '-';
  }
}

/**
 * 남은 시간을 'X일 Y시간 남음' 형태로 반환
 * @example '3일 5시간 남음', '마감됨'
 */
export function formatTimeRemaining(endDateStr: string | null | undefined): string {
  if (!endDateStr) return '-';
  try {
    const end = parseISO(endDateStr);
    const now = new Date();

    const totalMinutes = differenceInMinutes(end, now);
    if (totalMinutes <= 0) return '마감됨';

    const totalHours = differenceInHours(end, now);
    const days = Math.floor(totalHours / 24);
    const hours = totalHours % 24;

    if (days > 0) {
      return `${days}일 ${hours}시간 남음`;
    }
    return `${hours}시간 남음`;
  } catch {
    return '-';
  }
}

/**
 * 숫자를 천 단위 콤마 포맷으로 변환
 * @example 1234567 → '1,234,567'
 * @example null → '0'
 */
export function formatNumber(num: number | null | undefined): string {
  if (num == null) return '0';
  return num.toLocaleString();
}

/**
 * 텍스트를 지정 길이로 잘라 '...' 추가
 * @param text 원본 텍스트
 * @param maxLength 최대 길이 (기본: 50)
 */
export function truncateText(text: string, maxLength: number = 50): string {
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength) + '...';
}
