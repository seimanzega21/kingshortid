
const { SignJWT } = require('jose');
const secret = new TextEncoder().encode('MYt4Si3dPkRYUtR4EVyaXsnv/MCLmn3jJzJSKxTyClVdX2mxPmcfOY4/CPj1c3012c13');
async function run() {
  const token = await new SignJWT({ id: 'admin', role: 'admin' })
    .setProtectedHeader({ alg: 'HS256' })
    .setIssuedAt()
    .setExpirationTime('2h')
    .sign(secret);
  
  const res = await fetch('http://127.0.0.1:3000/api/dramas/y8o6b5ff5tm1h1cq11wy81o7?includeInactive=true', {
    headers: { 'Cookie': 'admin_token=' + token }
  });
  const data = await res.text();
  console.log('Response:', data.substring(0, 500));
}
run();

