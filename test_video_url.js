const API_URL = 'https://api.shortlovers.id';

async function run() {
  const res = await fetch(API_URL + '/api/dramas?limit=5');
  const data = await res.json();
  const dramas = data.dramas || [];
  
  for (const drama of dramas) {
    if (drama.id !== 'y8o6b5ff5tm1h1cq11wy81o7') {
      const epRes = await fetch(API_URL + '/api/dramas/' + drama.id);
      const epData = await epRes.json();
      if (epData.episodes && epData.episodes.length > 0) {
        console.log('Drama:', drama.title);
        console.log('Sample videoUrl:', epData.episodes[0].videoUrl);
        break;
      }
    }
  }
}
run();
