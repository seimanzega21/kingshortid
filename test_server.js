
const http = require('http');
http.createServer((req, res) => {
  console.log('Received request:', req.url);
  res.end('Hello');
}).listen(8000);
console.log('Listening on 8000');

