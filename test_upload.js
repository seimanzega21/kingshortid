const fs = require('fs');

async function testUpload() {
  const formData = new FormData();
  // Creating a tiny dummy image (1x1 transparent png)
  const dummyImg = Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=', 'base64');
  const blob = new Blob([dummyImg], { type: 'image/png' });
  formData.append('file', blob, 'test.png');
  
  try {
    const r = await fetch('http://141.11.160.187:3002/api/upload', {
      method: 'POST',
      body: formData
    });
    console.log("Status:", r.status);
    console.log("Response:", await r.text());
  } catch(e) {
    console.error(e);
  }
}
testUpload();
