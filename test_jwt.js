
const { SignJWT } = require('jose');
const secret = new TextEncoder().encode('ksh0rt1D-pr0d-jwt-s3cr3t-2026-x9k7m2');
async function run() {
  const token = await new SignJWT({ id: 'admin', role: 'admin' })
    .setProtectedHeader({ alg: 'HS256' })
    .setIssuedAt()
    .setExpirationTime('2h')
    .sign(secret);
  
  const res = await fetch('http://141.11.160.187:3002/api/dramas/y8o6b5ff5tm1h1cq11wy81o7?includeInactive=true', {
    headers: { 'Cookie': 'admin_token=' + token }
  });
  const data = await res.json();
  console.log('Episodes length from Next.js Proxy:', data.episodes?.length);
  console.log(data.error);
}
run();

