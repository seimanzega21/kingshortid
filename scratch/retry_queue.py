import subprocess
import time

ids = [
    "6a72ac7e1f385f32860cdabf", # Tidur Dengan Putra Mantan Suamiku
    "6a857e5003bc5a7c460a35f0", # Tuan Kini Aku Mantan Istrimu
]

for movie_id in ids:
    print(f"\\n=======================================================")
    print(f"Starting REELSHORT scrape for movie_id: {movie_id}")
    print(f"=======================================================\\n")
    
    cmd = ['python', 'scripts/scrape_reelshort_provider.py', movie_id]
    subprocess.run(cmd)
    
    print(f"\\n[QUEUE] Sleeping for 15 seconds before next drama to prevent rate limiting...\\n")
    time.sleep(15)

print("\\nAll retry processing completed successfully!")
