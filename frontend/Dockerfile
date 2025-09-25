# Frontend Dockerfile
FROM node:18-alpine AS builder

# 작업 디렉토리
WORKDIR /app

# 패키지 파일 복사
COPY package*.json ./

# 의존성 설치
RUN npm ci --only=production

# 소스 코드 복사
COPY . .

# 프로덕션 빌드
RUN npm run build

# Production stage
FROM nginx:alpine

# Nginx 설정
COPY nginx/default.conf /etc/nginx/conf.d/default.conf

# 빌드된 파일 복사
COPY --from=builder /app/build /usr/share/nginx/html

# 헬스체크
HEALTHCHECK --interval=30s --timeout=3s \
  CMD wget --no-verbose --tries=1 --spider http://localhost || exit 1

# 포트 노출
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]