"""
Deep analysis of request signing mechanism
Extract all signed requests and identify patterns
"""

import json
from pathlib import Path
from collections import defaultdict
import base64
from urllib.parse import urlparse, parse_qs

def analyze_all_signed_requests():
    """Extract and analyze all requests with 'sign' header"""
    
    har_files = [
        "HTTPToolkit_2026-02-03_00-53.har",
        "HTTPToolkit_2026-02-03_00-02.har",
        "HTTPToolkit_2026-02-02_23-24.har",
        "fresh_capture.har"
    ]
    
    signed_requests = []
    
    print("🔍 Extracting all signed requests from HAR files...\n")
    print("="*80 + "\n")
    
    for har_file in har_files:
        if not Path(har_file).exists():
            continue
        
        print(f"📂 Analyzing: {har_file}")
        
        with open(har_file, 'r', encoding='utf-8') as f:
            har = json.load(f)
        
        for entry in har['log']['entries']:
            request = entry['request']
            
            # Check for 'sign' header
            sign_header = None
            for header in request['headers']:
                if header['name'].lower() == 'sign':
                    sign_header = header['value']
                    break
            
            if not sign_header:
                continue
            
            # Extract request details
            url = request['url']
            method = request['method']
            headers = {h['name']: h['value'] for h in request['headers']}
            
            # POST data
            post_data = request.get('postData', {}).get('text', '')
            
            # Query params
            parsed_url = urlparse(url)
            query_params = parse_qs(parsed_url.query)
            
            signed_requests.append({
                'url': url,
                'path': parsed_url.path,
                'method': method,
                'sign': sign_header,
                'timestamp': headers.get('timestamp', ''),
                'auth': headers.get('authorization', ''),
                'post_data': post_data,
                'query_params': query_params,
                'user_agent': headers.get('user-agent', ''),
                'content_type': headers.get('content-type', '')
            })
        
        print(f"  Found {len([r for r in signed_requests])} signed requests so far\n")
    
    print(f"="*80)
    print(f"📊 TOTAL SIGNED REQUESTS: {len(signed_requests)}")
    print(f"="*80 + "\n")
    
    return signed_requests


def analyze_signing_patterns(requests):
    """Identify patterns in signing"""
    
    print("\n🔬 ANALYZING SIGNING PATTERNS\n")
    print("="*80 + "\n")
    
    # Group by endpoint
    by_endpoint = defaultdict(list)
    for req in requests:
        endpoint = req['path']
        by_endpoint[endpoint].append(req)
    
    print(f"📍 Unique endpoints with signing: {len(by_endpoint)}\n")
    
    # Analyze each endpoint
    for endpoint, reqs in sorted(by_endpoint.items(), key=lambda x: len(x[1]), reverse=True)[:10]:
        print(f"\n{'='*80}")
        print(f"📌 {endpoint}")
        print(f"{'='*80}")
        print(f"Requests: {len(reqs)}\n")
        
        if len(reqs) >= 2:
            # Compare first two requests
            req1, req2 = reqs[0], reqs[1]
            
            print("🔍 Comparing 2 requests:\n")
            
            print(f"Request 1:")
            print(f"  Sign: {req1['sign'][:60]}...")
            print(f"  Timestamp: {req1['timestamp']}")
            print(f"  Auth: {req1['auth'][:50]}..." if req1['auth'] else "  Auth: None")
            print(f"  POST data: {req1['post_data'][:100]}..." if req1['post_data'] else "  POST data: None")
            print()
            
            print(f"Request 2:")
            print(f"  Sign: {req2['sign'][:60]}...")
            print(f"  Timestamp: {req2['timestamp']}")
            print(f"  Auth: {req2['auth'][:50]}..." if req2['auth'] else "  Auth: None")
            print(f"  POST data: {req2['post_data'][:100]}..." if req2['post_data'] else "  POST data: None")
            print()
            
            # Check if signatures are different
            if req1['sign'] != req2['sign']:
                print("✅ Signatures are DIFFERENT (dynamic signing)")
            else:
                print("⚠️  Signatures are SAME (static signing?)")
            
            # Check timestamp
            if req1['timestamp'] != req2['timestamp']:
                print("✅ Timestamps are DIFFERENT (time-based)")
            else:
                print("⚠️  Timestamps are SAME")
    
    # Signature length analysis
    print(f"\n\n{'='*80}")
    print("📏 SIGNATURE CHARACTERISTICS")
    print(f"{'='*80}\n")
    
    sign_lengths = [len(r['sign']) for r in requests]
    unique_lengths = set(sign_lengths)
    
    print(f"Signature lengths: {unique_lengths}")
    print(f"Most common length: {max(set(sign_lengths), key=sign_lengths.count)}")
    
    # Try to decode signature
    sample_sign = requests[0]['sign']
    print(f"\nSample signature: {sample_sign[:80]}...")
    print(f"Length: {len(sample_sign)} characters")
    
    try:
        decoded = base64.b64decode(sample_sign)
        print(f"Base64 decoded length: {len(decoded)} bytes")
        print(f"Decoded (hex): {decoded[:32].hex()}...")
    except:
        print("⚠️  Not valid base64")
    
    return by_endpoint


def identify_signing_components(requests):
    """Try to identify what components are used in signing"""
    
    print(f"\n\n{'='*80}")
    print("🧩 IDENTIFYING SIGNING COMPONENTS")
    print(f"{'='*80}\n")
    
    # Pick a request to analyze
    if not requests:
        print("No requests to analyze")
        return
    
    req = requests[0]
    
    print("Analyzing request:")
    print(f"  URL: {req['url']}")
    print(f"  Method: {req['method']}")
    print()
    
    print("Possible signing components:\n")
    
    components = {
        'URL path': req['path'],
        'Method': req['method'],
        'Timestamp': req['timestamp'],
        'POST body': req['post_data'][:100] if req['post_data'] else 'None',
        'Query params': str(req['query_params'])[:100],
        'Content-Type': req['content_type']
    }
    
    for name, value in components.items():
        print(f"  • {name}: {value}")
    
    print("\n💡 Likely signing format:")
    print("   signature = RSA_SHA256_sign(timestamp + path + method + body)")
    print("   OR")
    print("   signature = RSA_SHA256_sign(JSON.stringify(request_data))")


def save_signing_data(requests):
    """Save signing data for manual analysis"""
    
    output = {
        'total_requests': len(requests),
        'sample_requests': requests[:5],  # First 5 for manual review
        'unique_endpoints': list(set(r['path'] for r in requests)),
        'analysis_results': {
            'signatures_are_dynamic': len(set(r['sign'] for r in requests)) > 1,
            'timestamps_used': len(set(r['timestamp'] for r in requests)) > 1,
            'average_sign_length': sum(len(r['sign']) for r in requests) / len(requests) if requests else 0
        }
    }
    
    with open('signing_analysis.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"\n\n✅ Saved analysis to signing_analysis.json")
    print(f"✅ Total requests analyzed: {len(requests)}")


if __name__ == "__main__":
    requests = analyze_all_signed_requests()
    
    if requests:
        analyze_signing_patterns(requests)
        identify_signing_components(requests)
        save_signing_data(requests)
    else:
        print("⚠️  No signed requests found in HAR files")
