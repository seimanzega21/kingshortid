import fetch from 'node-fetch';

async function testClaim() {
  try {
    // Generate an artificial user payload or just see what a bad token does
    const res = await fetch('https://api.shortlovers.id/api/rewards/claim-ad', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ type: 'checkin_bonus', amount: 40 })
    });
    console.log(res.status, await res.text());
  } catch (e) {
    console.error(e);
  }
}
testClaim();
