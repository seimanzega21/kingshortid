const dramaId = 'y8o6b5ff5tm1h1cq11wy81o7';
const API_URL = 'https://api.shortlovers.id';

async function run() {
  const res = await fetch(API_URL + '/api/dramas/' + dramaId + '?includeInactive=true');
  const data = await res.json();
  const episodes = data.episodes || [];
  
  console.log('Found ' + episodes.length + ' episodes');

  for (const ep of episodes) {
    if (ep.videoUrl === null) {
      console.log('Updating episode ' + ep.episodeNumber + '...');
      let success = false;
      let retries = 3;
      while (!success && retries > 0) {
        try {
          const updateRes = await fetch(API_URL + '/api/episodes/' + ep.id, {
            method: 'PATCH',
            headers: {
              'Content-Type': 'application/json',
              'X-Admin-Key': '00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14'
            },
            body: JSON.stringify({ videoUrl: '' })
          });
          if (!updateRes.ok) {
            console.error('Failed to update:', await updateRes.text());
          } else {
            success = true;
          }
        } catch (e) {
          retries--;
          console.error('Network error, retries left:', retries);
        }
      }
    }
  }
  console.log('Done');
}
run();
