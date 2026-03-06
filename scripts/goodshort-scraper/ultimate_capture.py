#!/usr/bin/env python3
"""
GOODSHORT ULTIMATE CAPTURE SYSTEM
==================================

Complete automation untuk capture semua GoodShort content dengan:
- HTTP Toolkit integration  
- Smart retry & anti-blocking
- Progress tracking & resume capability
- Error handling & logging

ANTI-BLOCKING FEATURES:
- Random delays between requests
- Rate limiting
- Connection pooling
- Retry with exponential backoff
- Session rotation
- Progress save (resume on failure)
"""

import subprocess
import time
import json
import requests
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import random
from urllib.parse import urlparse
import logging

# ============================================================================
# CONFIGURATION
# ============================================================================

# Paths
SCRIPT_DIR = Path(__file__).parent
OUTPUT_DIR = SCRIPT_DIR / "captured_complete"
LOG_DIR = SCRIPT_DIR / "capture_logs"
OUTPUT_DIR.mkdir(exist_ok=True)
LOG_DIR.mkdir(exist_ok=True)

# Emulator
DEVICE = "emulator-5554"

# Anti-blocking settings
MIN_DELAY = 0.5  # Min seconds between requests
MAX_DELAY = 2.0  # Max seconds between requests
MAX_RETRIES = 5  # Max retry attempts
RETRY_BACKOFF = 2  # Exponential backoff multiplier
RATE_LIMIT = 10  # Max requests per second
SESSION_ROTATE_AFTER = 50  # Rotate session after N requests

# Headers (from successful HTTP Toolkit test)
BASE_HEADERS = {
    'User-Agent': 'com.newreading.goodreels/2.7.8.2078 (Linux;Android 11) ExoPlayerLib/2.18.2',
    'Accept-Encoding': 'identity',
    'Connection': 'Keep-Alive',
    'Accept': '*/*'
}

# ============================================================================
# LOGGING SETUP
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / f'capture_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ============================================================================
# SMART DOWNLOADER WITH ANTI-BLOCKING
# ============================================================================

class SmartDownloader:
    """Smart downloader with anti-blocking features"""
    
    def __init__(self):
        self.session = None
        self.request_count = 0
        self.total_downloaded = 0
        self.total_failed = 0
        self.last_request_time = 0
        self._init_session()
    
    def _init_session(self):
        """Initialize new session"""
        self.session = requests.Session()
        self.session.headers.update(BASE_HEADERS)
        # Connection pooling
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=10,
            pool_maxsize=20,
            max_retries=0  # We handle retries manually
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        logger.info("New session initialized")
    
    def _rotate_session(self):
        """Rotate session for anti-blocking"""
        self.session.close()
        self._init_session()
        self.request_count = 0
        logger.info("Session rotated")
    
    def _smart_delay(self):
        """Smart delay with rate limiting"""
        # Random delay
        delay = random.uniform(MIN_DELAY, MAX_DELAY)
        
        # Rate limiting
        time_since_last = time.time() - self.last_request_time
        min_interval = 1.0 / RATE_LIMIT
        if time_since_last < min_interval:
            additional_delay = min_interval - time_since_last
            delay += additional_delay
        
        time.sleep(delay)
        self.last_request_time = time.time()
    
    def download_segment(self, url: str, output_path: Path, attempt: int = 1) -> bool:
        """Download segment with retry and anti-blocking"""
        
        # Check session rotation
        if self.request_count >= SESSION_ROTATE_AFTER:
            self._rotate_session()
        
        # Smart delay before request
        self._smart_delay()
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # Save file
            with open(output_path, 'wb') as f:
                f.write(response.content)
            
            size_kb = len(response.content) / 1024
            logger.info(f"✅ Downloaded: {output_path.name} ({size_kb:.1f} KB)")
            
            self.request_count += 1
            self.total_downloaded += 1
            return True
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 403:
                logger.warning(f"⚠️  403 Forbidden - Attempt {attempt}/{MAX_RETRIES}")
                
                # Retry with exponential backoff
                if attempt < MAX_RETRIES:
                    backoff = RETRY_BACKOFF ** attempt
                    logger.info(f"Retrying in {backoff}s...")
                    time.sleep(backoff)
                    return self.download_segment(url, output_path, attempt + 1)
                else:
                    logger.error(f"❌ Max retries exceeded: {url}")
                    self.total_failed += 1
                    return False
            else:
                logger.error(f"❌ HTTP {e.response.status_code}: {url}")
                self.total_failed += 1
                return False
                
        except Exception as e:
            logger.error(f"❌ Error: {e}")
            
            # Retry on network errors
            if attempt < MAX_RETRIES:
                backoff = RETRY_BACKOFF ** attempt
                logger.info(f"Retrying in {backoff}s...")
                time.sleep(backoff)
                return self.download_segment(url, output_path, attempt + 1)
            else:
                self.total_failed += 1
                return False

# ============================================================================
# PROGRESS TRACKER
# ============================================================================

class ProgressTracker:
    """Track and save progress for resume capability"""
    
    def __init__(self, progress_file: Path):
        self.progress_file = progress_file
        self.data = self._load()
    
    def _load(self) -> Dict:
        """Load progress from file"""
        if self.progress_file.exists():
            with open(self.progress_file, 'r') as f:
                return json.load(f)
        return {
            'completed_episodes': [],
            'failed_episodes': [],
            'last_update': None,
            'total_segments': 0
        }
    
    def save(self):
        """Save progress to file"""
        self.data['last_update'] = datetime.now().isoformat()
        with open(self.progress_file, 'w') as f:
            json.dump(self.data, f, indent=2)
    
    def mark_completed(self, episode_id: str, segment_count: int):
        """Mark episode as completed"""
        self.data['completed_episodes'].append({
            'id': episode_id,
            'segments': segment_count,
            'timestamp': datetime.now().isoformat()
        })
        self.data['total_segments'] += segment_count
        self.save()
    
    def mark_failed(self, episode_id: str, reason: str):
        """Mark episode as failed"""
        self.data['failed_episodes'].append({
            'id': episode_id,
            'reason': reason,
            'timestamp': datetime.now().isoformat()
        })
        self.save()
    
    def is_completed(self, episode_id: str) -> bool:
        """Check if episode already completed"""
        return any(ep['id'] == episode_id for ep in self.data['completed_episodes'])

# ============================================================================
# HTTP TOOLKIT INTEGRATION
# ============================================================================

class HTTPToolkitCapture:
    """Integrate with HTTP Toolkit for URL capture"""
    
    @staticmethod
    def extract_from_har(har_file: Path) -> Dict[str, List[str]]:
        """Extract .ts URLs from HAR file, grouped by episode"""
        
        if not har_file.exists():
            logger.error(f"HAR file not found: {har_file}")
            return {}
        
        with open(har_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        entries = data.get('log', {}).get('entries', [])
        
        # Group by episode
        episodes = {}
        
        for entry in entries:
            url = entry['request']['url']
            
            # Filter .ts segments
            if url.endswith('.ts') and 'goodreels.com' in url:
                # Extract episode ID from URL
                # Pattern: /books/260/31000762260/325922/...
                parts = urlparse(url).path.split('/')
                if len(parts) >= 6:
                    episode_id = parts[5]  # Episode ID from path
                    
                    if episode_id not in episodes:
                        episodes[episode_id] = []
                    
                    episodes[episode_id].append(url)
        
        logger.info(f"Extracted {len(episodes)} episodes from HAR")
        for ep_id, urls in episodes.items():
            logger.info(f"  Episode {ep_id}: {len(urls)} segments")
        
        return episodes

# ============================================================================
# MAIN CAPTURE ORCHESTRATOR
# ============================================================================

class GoodShortCaptureSystem:
    """Main orchestrator for complete capture"""
    
    def __init__(self):
        self.downloader = SmartDownloader()
        self.progress = ProgressTracker(SCRIPT_DIR / "capture_progress.json")
    
    def capture_from_har(self, har_file: Path):
        """Capture all segments from HAR file"""
        
        logger.info("="*70)
        logger.info("GOODSHORT ULTIMATE CAPTURE SYSTEM")
        logger.info("="*70)
        logger.info(f"HAR File: {har_file}")
        logger.info(f"Output: {OUTPUT_DIR}/")
        logger.info("")
        
        # Extract episodes
        episodes = HTTPToolkitCapture.extract_from_har(har_file)
        
        if not episodes:
            logger.error("No episodes found in HAR file!")
            return
        
        total_episodes = len(episodes)
        total_segments = sum(len(urls) for urls in episodes.values())
        
        logger.info(f"Total: {total_episodes} episodes, {total_segments} segments")
        logger.info("")
        
        # Download each episode
        for idx, (ep_id, urls) in enumerate(episodes.items(), 1):
            
            # Skip if already completed
            if self.progress.is_completed(ep_id):
                logger.info(f"[{idx}/{total_episodes}] Episode {ep_id}: ALREADY COMPLETED ✅")
                continue
            
            logger.info(f"[{idx}/{total_episodes}] Episode {ep_id}: {len(urls)} segments")
            
            # Create episode folder
            ep_folder = OUTPUT_DIR / f"episode_{ep_id}"
            ep_folder.mkdir(exist_ok=True)
            
            # Download segments
            success_count = 0
            for i, url in enumerate(urls):
                filename = f"segment_{i:06d}.ts"
                output_path = ep_folder / filename
                
                # Skip if already exists
                if output_path.exists():
                    logger.info(f"  [{i+1}/{len(urls)}] {filename}: SKIP (exists)")
                    success_count += 1
                    continue
                
                # Download with smart retry
                success = self.downloader.download_segment(url, output_path)
                if success:
                    success_count += 1
            
            # Mark progress
            if success_count == len(urls):
                self.progress.mark_completed(ep_id, len(urls))
                logger.info(f"  ✅ Episode {ep_id} COMPLETE ({success_count}/{len(urls)})")
            else:
                self.progress.mark_failed(ep_id, f"Only {success_count}/{len(urls)} segments")
                logger.warning(f"  ⚠️  Episode {ep_id} INCOMPLETE ({success_count}/{len(urls)})")
            
            logger.info("")
        
        # Final summary
        logger.info("="*70)
        logger.info("CAPTURE COMPLETE!")
        logger.info("="*70)
        logger.info(f"Total downloaded: {self.downloader.total_downloaded}")
        logger.info(f"Total failed: {self.downloader.total_failed}")
        logger.info(f"Completed episodes: {len(self.progress.data['completed_episodes'])}")
        logger.info(f"Failed episodes: {len(self.progress.data['failed_episodes'])}")
        logger.info(f"Output: {OUTPUT_DIR}/")
        logger.info("")

# ============================================================================
# CLI INTERFACE
# ============================================================================

def main():
    """Main entry point"""
    
    import sys
    
    print("\n" + "="*70)
    print("GOODSHORT ULTIMATE CAPTURE SYSTEM")
    print("="*70)
    print()
    
    # Check for HAR file
    har_file = SCRIPT_DIR / "goodshort_capture.har"
    
    if len(sys.argv) > 1:
        har_file = Path(sys.argv[1])
    
    if not har_file.exists():
        print("❌ HAR file not found!")
        print()
        print("USAGE:")
        print(f"  python {Path(__file__).name} [har_file.har]")
        print()
        print("OR:")
        print(f"  1. Export HAR from HTTP Toolkit")
        print(f"  2. Save as: {har_file}")
        print(f"  3. Run this script")
        print()
        return
    
    # Run capture
    system = GoodShortCaptureSystem()
    system.capture_from_har(har_file)

if __name__ == "__main__":
    main()
