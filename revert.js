const dramaId = 'y8o6b5ff5tm1h1cq11wy81o7';
const apiKey = '00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14';

async function revertUrls() {
  const epRes = await fetch('https://api.shortlovers.id/api/dramas/' + dramaId + '/episodes?includeInactive=true', {
    headers: { 'X-Admin-Key': apiKey }
  });
  const epData = await epRes.json();
  
  let count = 0;
  for (const episode of epData) {
    if (episode.videoUrl && episode.videoUrl.includes('stream.shortlovers.id')) {
      await fetch('https://api.shortlovers.id/api/episodes/' + episode.id, {
        method: 'PATCH',
        headers: { 'X-Admin-Key': apiKey, 'Content-Type': 'application/json' },
        body: JSON.stringify({ videoUrl: '' })
      });
      count++;
    }
  }
  console.log('Reverted ' + count + ' episodes.');
}
revertUrls();
