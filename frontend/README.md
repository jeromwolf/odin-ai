# Odin-AI Frontend

공공조달 AI 플랫폼의 React 프론트엔드 애플리케이션입니다.

## 기술 스택

- **React 18** - UI 라이브러리
- **TypeScript** - 타입 안전성
- **Material-UI (MUI)** - UI 컴포넌트 라이브러리
- **Redux Toolkit** - 상태 관리
- **React Query** - 서버 상태 관리
- **React Router** - 라우팅
- **React Hook Form** - 폼 관리
- **Recharts** - 차트 라이브러리
- **Axios** - HTTP 클라이언트

## 프로젝트 구조

```
src/
├── components/          # 재사용 가능한 컴포넌트
│   ├── auth/           # 인증 관련 컴포넌트
│   └── layout/         # 레이아웃 컴포넌트
├── contexts/           # React Context
├── hooks/              # 커스텀 훅
├── pages/              # 페이지 컴포넌트
├── services/           # API 서비스
├── store/              # Redux 스토어
│   └── slices/         # Redux 슬라이스
├── styles/             # 스타일 파일
├── types/              # TypeScript 타입 정의
└── utils/              # 유틸리티 함수
```

## 주요 기능

### 인증 시스템
- JWT 기반 토큰 인증
- 자동 토큰 갱신
- 로그인/로그아웃/회원가입

### 대시보드
- 실시간 통계 대시보드
- 차트 및 그래프 시각화
- AI 추천 입찰
- 마감 임박 알림

### 입찰 관리
- 입찰 검색 및 필터링
- 북마크 기능
- 상세 정보 조회

### 구독 관리
- 구독 플랜 변경
- 사용량 모니터링
- 결제 이력 조회

## 환경 설정

### 환경 변수

`.env` 파일을 생성하고 다음 변수들을 설정하세요:

```bash
REACT_APP_API_BASE_URL=http://localhost:8000/api
REACT_APP_WEBSOCKET_URL=ws://localhost:8000/ws
REACT_APP_TOKEN_KEY=odin_ai_token
REACT_APP_REFRESH_TOKEN_KEY=odin_ai_refresh_token
REACT_APP_ENV=development
REACT_APP_DEBUG=true
```

## 개발 환경 실행

### 의존성 설치

```bash
npm install
# 또는
yarn install
```

### 개발 서버 시작

```bash
npm start
# 또는
yarn start
```

브라우저에서 [http://localhost:3000](http://localhost:3000)으로 접속하세요.

### 빌드

```bash
npm run build
# 또는
yarn build
```

### 테스트

```bash
npm test
# 또는
yarn test
```

### 린트 및 포맷팅

```bash
# 린트 검사
npm run lint

# 코드 포맷팅
npm run format
```

## API 연동

### API 클라이언트

`src/services/api.ts`에서 모든 API 호출을 관리합니다.

- 자동 인증 토큰 첨부
- 토큰 만료 시 자동 갱신
- 에러 처리 및 재시도 로직

### 주요 API 엔드포인트

- `/auth/*` - 인증 관련
- `/dashboard/*` - 대시보드 데이터
- `/bids/*` - 입찰 정보
- `/search/*` - 검색
- `/subscription/*` - 구독 관리
- `/bookmarks/*` - 북마크

## 상태 관리

### Redux Store

- `authSlice` - 사용자 인증 상태
- `bidSlice` - 입찰 데이터 및 필터
- `subscriptionSlice` - 구독 정보
- `notificationSlice` - 알림 관리

### React Query

서버 데이터 캐싱 및 동기화에 사용:

- 자동 캐싱
- 백그라운드 업데이트
- 낙관적 업데이트

## 컴포넌트 가이드

### 페이지 컴포넌트

모든 페이지는 `src/pages/`에 위치하며 React.lazy로 지연 로딩됩니다.

### 레이아웃

- `MainLayout` - 인증된 사용자용 메인 레이아웃
- `AuthLayout` - 로그인/회원가입용 레이아웃

### 라우팅

- `PrivateRoute` - 인증 필요 페이지 보호
- 중첩 라우팅으로 레이아웃 분리

## 테마 및 스타일링

### Material-UI 테마

`src/styles/theme.ts`에서 전역 테마를 관리합니다.

- 컬러 팔레트
- 타이포그래피
- 컴포넌트 기본 스타일

### 반응형 디자인

 Material-UI의 브레이크포인트 시스템을 활용한 반응형 레이아웃

## 배포

### 프로덕션 빌드

```bash
npm run build
```

빌드된 파일은 `build/` 폴더에 생성됩니다.

### Docker 배포

```dockerfile
FROM node:18-alpine as build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

## 개발 가이드

### 코딩 규칙

- TypeScript 엄격 모드 사용
- ESLint + Prettier 규칙 준수
- 컴포넌트명은 PascalCase
- 파일명은 컴포넌트명과 동일

### 폴더 구조 규칙

- 각 기능별로 폴더 분리
- 재사용 가능한 컴포넌트는 `components/`
- 페이지별 컴포넌트는 `pages/`
- 비즈니스 로직은 `services/`

### 성능 최적화

- React.memo 사용
- useCallback, useMemo 적절히 활용
- 이미지 최적화
- 코드 스플리팅

## 트러블슈팅

### 자주 발생하는 문제

1. **CORS 에러**
   - 백엔드 CORS 설정 확인
   - proxy 설정 확인

2. **토큰 만료**
   - 자동 갱신 로직 확인
   - localStorage 확인

3. **빌드 에러**
   - TypeScript 타입 에러 해결
   - 미사용 import 제거

## 라이센스

MIT License