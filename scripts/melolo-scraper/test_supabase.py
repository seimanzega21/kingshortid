import requests
import json

headers = {
    'apikey': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImdrY25ibmxmcWRsb3RuamFpenh4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njg0NjQ5ODEsImV4cCI6MjA4NDA0MDk4MX0.EFP6qcUAT_Dk0bV3ycjxpduZ1MBuhCWOTE0ArIsS9Xo',
    'authorization': 'Bearer eyJhbGciOiJFUzI1NiIsImtpZCI6ImY0NTAxYzU1LTY5ZmMtNDczNy05NzFkLTU1OTVjZmRmZDAwNSIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJodHRwczovL2drY25ibmxmcWRsb3RuamFpenh4LnN1cGFiYXNlLmNvL2F1dGgvdjEiLCJzdWIiOiI2ZjNlNWMxNS1hMjFjLTRkMTAtYjg2Yy1lODgxNzBlN2I3MmQiLCJhdWQiOiJhdXRoZW50aWNhdGVkIiwiZXhwIjoxNzc3MTkzMzg2LCJpYXQiOjE3NzcxODk3ODYsImVtYWlsIjoic2VpbWFuemVnYTIxQGdtYWlsLmNvbSIsInBob25lIjoiIiwiYXBwX21ldGFkYXRhIjp7InByb3ZpZGVyIjoiZ29vZ2xlIiwicHJvdmlkZXJzIjpbImdvb2dsZSJdfX0.Qc6T8rXG6XbZ5Q2sT8K2V6P_5Y5_s6-y5g3g7X5sXyqX4yv1_ZtqYk7L_2Vn1H9d5P0zZqUvJ5t0WbT4o1m0Zg'
}

# 1. Let's see what tables are available, or query 'episodes' table directly
url = "https://gkcnbnlfqdlotnjaizxx.supabase.co/rest/v1/"
r = requests.get(url, headers=headers)
print("Root:", r.text[:200])

url2 = "https://gkcnbnlfqdlotnjaizxx.supabase.co/rest/v1/episodes?limit=5"
r2 = requests.get(url2, headers=headers)
print("Episodes:", r2.text[:500])

url3 = "https://gkcnbnlfqdlotnjaizxx.supabase.co/rest/v1/shortmax_episodes?limit=5"
r3 = requests.get(url3, headers=headers)
print("Shortmax Episodes:", r3.text[:500])

