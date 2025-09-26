
// 브라우저에서 실행할 디버깅 스크립트
console.log('=== JWT 토큰 디버깅 ===');
console.log('Access Token:', localStorage.getItem('odin_ai_token'));
console.log('Refresh Token:', localStorage.getItem('odin_ai_refresh_token'));
console.log('Token 길이:', localStorage.getItem('odin_ai_token')?.length);

// JWT 토큰 디코드
const token = localStorage.getItem('odin_ai_token');
if (token) {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    console.log('토큰 페이로드:', payload);
    console.log('만료 시간:', new Date(payload.exp * 1000));
    console.log('현재 시간:', new Date());
    console.log('토큰 만료 여부:', payload.exp * 1000 < Date.now());
  } catch (e) {
    console.error('토큰 디코딩 실패:', e);
  }
}

