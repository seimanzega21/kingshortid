const API = 'https://kingshortid-api.toonplay-seiman.workers.dev/api';

async function run() {
  console.log('Fetching all dramas...');
  const res = await fetch(API + '/dramas?limit=9999');
  const dList = await res.json();
  const dramas = dList.dramas || dList || [];
  
  let totalActiveEps = 0;
  let total540pEps = 0;
  let total720pEps = 0;
  
  console.log(`Checking ${dramas.length} dramas...`);
  
  for (let i = 0; i < dramas.length; i++) {
    const drama = dramas[i];
    try {
        const dRes = await fetch(API + `/dramas/${drama.id}/seasons`);
        const seasons = await dRes.json();
        const eps = seasons?.[0]?.episodes || [];
        
        for (const ep of eps) {
            totalActiveEps++;
            if (ep.videoUrl540p) total540pEps++;
            if (ep.videoUrl && ep.videoUrl.includes('720p')) total720pEps++;
        }
    } catch(e) { /* ignore */ }
    
    // progress
    if ((i+1) % 50 === 0) console.log(`Processed ${i+1}/${dramas.length}`);
  }
  
  console.log('--- RESULT ---');
  console.log('Total ACTIVE Episodes:', totalActiveEps);
  console.log('Total with 540p:', total540pEps);
  console.log('Total with 720p:', total720pEps);
  
  if (total540pEps < totalActiveEps) {
      console.log('⚠️ Not all episodes have 540p resolution!');
  } else {
      console.log('✅ All episodes have 540p resolution!');
  }
}

run();
