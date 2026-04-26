import os
from supabase import create_client

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(url, key)

user_id = "13765727560" # ID from screenshot could be short lovers ID or actual users.id?
# Actually the ID in the app is often the user id but let's query both
try:
    res = supabase.table("users").select("*").eq("id", user_id).execute()
    print("Users by ID:", res.data)
except Exception as e:
    print(e)

res2 = supabase.table("users").select("*").ilike("name", "%Fitri%").execute()
print("Users by Name:", len(res2.data))
if len(res2.data) > 0:
    print("Found:", res2.data[0])
