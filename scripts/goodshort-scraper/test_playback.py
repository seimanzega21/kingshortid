#!/usr/bin/env python3
"""
LOCAL HLS SERVER - Test video playback
========================================

Simple HTTP server to test captured HLS videos locally.
"""

from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
import json
import os

PORT = 8888
CAPTURED_DIR = Path(__file__).parent / "captured_complete"

class HLSHandler(SimpleHTTPRequestHandler):
    """Custom handler with CORS and proper MIME types"""
    
    def end_headers(self):
        # Enable CORS
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        
        # Cache control
        self.send_header('Cache-Control', 'no-cache')
        
        super().end_headers()
    
    def guess_type(self, path):
        """Override MIME type guessing"""
        if path.endswith('.m3u8'):
            return 'application/vnd.apple.mpegurl'
        elif path.endswith('.ts'):
            return 'video/mp2t'
        return super().guess_type(path)

def create_playlists():
    """Create HLS playlists for all episodes"""
    
    print("\nCreating playlists...")
    
    for episode_folder in CAPTURED_DIR.glob("episode_*"):
        segments = sorted(episode_folder.glob("segment_*.ts"))
        
        if not segments:
            continue
        
        playlist_file = episode_folder / "playlist.m3u8"
        
        with open(playlist_file, 'w') as f:
            f.write("#EXTM3U\n")
            f.write("#EXT-X-VERSION:3\n")
            f.write("#EXT-X-TARGETDURATION:10\n")
            f.write("#EXT-X-MEDIA-SEQUENCE:0\n")
            
            for seg in segments:
                f.write("#EXTINF:10.0,\n")
                f.write(f"{seg.name}\n")
            
            f.write("#EXT-X-ENDLIST\n")
        
        print(f"  ✅ {episode_folder.name}/playlist.m3u8 ({len(segments)} segments)")

def create_index_html():
    """Create index.html with video player"""
    
    episodes = []
    
    for episode_folder in CAPTURED_DIR.glob("episode_*"):
        playlist = episode_folder / "playlist.m3u8"
        if playlist.exists():
            episode_id = episode_folder.name.replace("episode_", "")
            segments = len(list(episode_folder.glob("segment_*.ts")))
            size_mb = sum(s.stat().st_size for s in episode_folder.glob("segment_*.ts")) / 1024 / 1024
            
            episodes.append({
                'id': episode_id,
                'segments': segments,
                'size': f"{size_mb:.2f} MB",
                'url': f"captured_complete/{episode_folder.name}/playlist.m3u8"
            })
    
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GoodShort Local Player - Test</title>
    <script src="https://cdn.jsdelivr.net/npm/hls.js@latest"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        
        h1 {{
            color: white;
            text-align: center;
            margin-bottom: 30px;
            font-size: 2.5rem;
            text-shadow: 0 2px 10px rgba(0,0,0,0.3);
        }}
        
        .stats {{
            background: rgba(255,255,255,0.1);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 30px;
            color: white;
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
        }}
        
        .stat {{
            text-align: center;
        }}
        
        .stat-value {{
            font-size: 2rem;
            font-weight: bold;
            margin-bottom: 5px;
        }}
        
        .stat-label {{
            opacity: 0.8;
            font-size: 0.9rem;
        }}
        
        .player-container {{
            background: rgba(0,0,0,0.5);
            backdrop-filter: blur(20px);
            border-radius: 20px;
            padding: 30px;
            margin-bottom: 30px;
        }}
        
        video {{
            width: 100%;
            max-width: 800px;
            display: block;
            margin: 0 auto 20px;
            border-radius: 10px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.5);
        }}
        
        .episode-info {{
            text-align: center;
            color: white;
            margin-bottom: 20px;
        }}
        
        .episode-info h2 {{
            font-size: 1.5rem;
            margin-bottom: 10px;
        }}
        
        .episode-details {{
            opacity: 0.8;
            font-size: 0.9rem;
        }}
        
        .episodes {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 20px;
        }}
        
        .episode-card {{
            background: rgba(255,255,255,0.1);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 20px;
            cursor: pointer;
            transition: all 0.3s ease;
            border: 2px solid transparent;
        }}
        
        .episode-card:hover {{
            transform: translateY(-5px);
            border-color: rgba(255,255,255,0.3);
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        }}
        
        .episode-card.active {{
            border-color: #4ade80;
            background: rgba(74, 222, 128, 0.2);
        }}
        
        .episode-title {{
            color: white;
            font-size: 1.2rem;
            font-weight: bold;
            margin-bottom: 10px;
        }}
        
        .episode-meta {{
            color: rgba(255,255,255,0.7);
            font-size: 0.9rem;
            display: flex;
            justify-content: space-between;
        }}
        
        .badge {{
            display: inline-block;
            background: rgba(255,255,255,0.2);
            padding: 5px 10px;
            border-radius: 20px;
            font-size: 0.8rem;
            margin-top: 10px;
        }}
        
        .success {{
            background: rgba(74, 222, 128, 0.3);
            color: #4ade80;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🎬 GoodShort Local Player</h1>
        
        <div class="stats">
            <div class="stat">
                <div class="stat-value">{len(episodes)}</div>
                <div class="stat-label">Episodes</div>
            </div>
            <div class="stat">
                <div class="stat-value">{sum(ep['segments'] for ep in episodes)}</div>
                <div class="stat-label">Total Segments</div>
            </div>
            <div class="stat">
                <div class="stat-value">{sum(float(ep['size'].split()[0]) for ep in episodes):.1f} MB</div>
                <div class="stat-label">Total Size</div>
            </div>
        </div>
        
        <div class="player-container">
            <div class="episode-info">
                <h2 id="current-episode">Select an episode to play</h2>
                <div class="episode-details" id="current-details"></div>
            </div>
            <video id="video" controls></video>
        </div>
        
        <div class="episodes" id="episodes">
            <!-- Episodes will be loaded here -->
        </div>
    </div>
    
    <script>
        const episodes = {json.dumps(episodes)};
        const video = document.getElementById('video');
        let hls = null;
        
        function playEpisode(episode) {{
            // Update UI
            document.querySelectorAll('.episode-card').forEach(card => {{
                card.classList.remove('active');
            }});
            event.currentTarget.classList.add('active');
            
            // Update info
            document.getElementById('current-episode').textContent = `Episode ${{episode.id}}`;
            document.getElementById('current-details').textContent = 
                `${{episode.segments}} segments • ${{episode.size}}`;
            
            // Load video
            const url = `http://localhost:{PORT}/${{episode.url}}`;
            
            if (Hls.isSupported()) {{
                if (hls) {{
                    hls.destroy();
                }}
                
                hls = new Hls({{
                    debug: false,
                    enableWorker: true,
                    lowLatencyMode: false,
                }});
                
                hls.loadSource(url);
                hls.attachMedia(video);
                
                hls.on(Hls.Events.MANIFEST_PARSED, function() {{
                    video.play();
                }});
                
                hls.on(Hls.Events.ERROR, function(event, data) {{
                    console.error('HLS Error:', data);
                }});
            }} else if (video.canPlayType('application/vnd.apple.mpegurl')) {{
                video.src = url;
                video.addEventListener('loadedmetadata', function() {{
                    video.play();
                }});
            }}
        }}
        
        // Render episodes
        const episodesContainer = document.getElementById('episodes');
        
        episodes.forEach(episode => {{
            const card = document.createElement('div');
            card.className = 'episode-card';
            card.onclick = () => playEpisode(episode);
            
            card.innerHTML = `
                <div class="episode-title">Episode ${{episode.id}}</div>
                <div class="episode-meta">
                    <span>📹 ${{episode.segments}} segments</span>
                    <span>💾 ${{episode.size}}</span>
                </div>
                <span class="badge success">✅ Ready</span>
            `;
            
            episodesContainer.appendChild(card);
        }});
        
        // Auto-play first episode
        if (episodes.length > 0) {{
            setTimeout(() => {{
                document.querySelector('.episode-card').click();
            }}, 500);
        }}
    </script>
</body>
</html>
"""
    
    with open(CAPTURED_DIR.parent / "index.html", 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"  ✅ index.html created")

def main():
    """Start local HLS server"""
    
    print("\n" + "="*70)
    print("LOCAL HLS SERVER - Test Playback")
    print("="*70)
    print()
    
    if not CAPTURED_DIR.exists():
        print("❌ No captured videos found!")
        print(f"Expected: {CAPTURED_DIR}")
        return
    
    # Create playlists
    create_playlists()
    
    # Create index
    create_index_html()
    
    print()
    print("="*70)
    print("SERVER READY!")
    print("="*70)
    print()
    print(f"🌐 Open in browser:")
    print(f"   http://localhost:{PORT}")
    print()
    print("📺 Video Player:")
    print(f"   - Select episode to play")
    print(f"   - HLS streaming from local files")
    print(f"   - Test quality and playback")
    print()
    print("Press Ctrl+C to stop server")
    print()
    print("="*70)
    print()
    
    # Change to script directory
    os.chdir(CAPTURED_DIR.parent)
    
    # Start server
    server = HTTPServer(('', PORT), HLSHandler)
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\n✅ Server stopped!")
        print()

if __name__ == "__main__":
    main()
