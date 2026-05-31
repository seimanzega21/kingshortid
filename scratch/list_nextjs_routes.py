import os

def find_routes():
    api_dir = r"d:\kingshortid\admin\src\app\api"
    routes = []
    for root, dirs, files in os.walk(api_dir):
        for f in files:
            if f in ["route.ts", "route.js"]:
                rel_path = os.path.relpath(os.path.join(root, f), api_dir)
                routes.append(rel_path)
    
    print("\n--- Next.js API Routes ---")
    for r in sorted(routes):
        print(r)

if __name__ == "__main__":
    find_routes()
