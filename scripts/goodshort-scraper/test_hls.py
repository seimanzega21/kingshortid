#!/usr/bin/env python3
"""Test HLS URL access"""
import requests

url = "https://v2-akm.goodreels.com/mts/books/963/31001221963/614590/t5hgdagimt/720p/viisdqecsr_720p.m3u8"

headers = {
    'User-Agent': 'GoodShort/2.5.1 (Linux; Android 11; Vivo S1 Pro)',
    'Accept': '*/*',
    'Accept-Encoding': 'identity',
    'Connection': 'keep-alive',
    'Referer': 'https://www.goodshort.com/'
}

print(f"Testing URL: {url}\n")

try:
    response = requests.get(url, headers=headers, timeout=10)
    print(f"Status: {response.status_code}")
    print(f"Headers: {dict(response.headers)}")
    print(f"\nContent ({len(response.text)} bytes):")
    print(response.text[:500])
except Exception as e:
    print(f"Error: {e}")
