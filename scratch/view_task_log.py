log_path = r"C:\Users\Seiman\.gemini\antigravity\brain\49e43ccf-1c06-4078-9a5a-257a4fd0640f\.system_generated\tasks\task-3736.log"

try:
    with open(log_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    print(f"Total lines in log: {len(lines)}")
    print("\nFiltered log lines:")
    for line in lines:
        if "[*] Processing" in line or "Transcode finished" in line or "Upload complete!" in line or "Updating DB" in line or "failed" in line.lower() or "error" in line.lower():
            # Skip ffmpeg warnings/errors in lower case
            if "nal unit" in line.lower() or "splitting" in line.lower() or "packet to decoder" in line.lower() or "aac-lc" in line.lower() or "not allocated" in line.lower() or "exceeds limit" in line.lower():
                continue
            print(line.strip())
except Exception as e:
    print("Error reading log:", e)
