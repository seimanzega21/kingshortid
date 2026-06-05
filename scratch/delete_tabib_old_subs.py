import paramiko

SSH_HOST = '141.11.160.187'
SSH_USER = 'root'
SSH_PASS = 'Surya123!'

def main():
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        print(f"Connecting to SSH {SSH_USER}@{SSH_HOST}...")
        ssh.connect(SSH_HOST, username=SSH_USER, password=SSH_PASS, timeout=10)
        print("Connected.")
        
        # Delete old id_ID subtitles for the drama
        query = (
            "DELETE FROM subtitles "
            "WHERE language = 'id_ID' "
            "AND episode_id IN (SELECT id FROM episodes WHERE drama_id = 'dm4pug3ppvsaqrbppinxvu9w');"
        )
        cmd = f'docker exec -i supabase-db-og8gwooogk480gcws0o84ssc psql -U postgres -d postgres -c "{query}"'
        stdin, stdout, stderr = ssh.exec_command(cmd)
        print("\n--- DELETE OLD SUBTITLES RESULT ---")
        print(stdout.read().decode('utf-8'))
        print("Errors:")
        print(stderr.read().decode('utf-8'))
        
        # Verify current status
        verify_query = (
            "SELECT language, count(*) FROM subtitles "
            "WHERE episode_id IN (SELECT id FROM episodes WHERE drama_id = 'dm4pug3ppvsaqrbppinxvu9w') "
            "GROUP BY language;"
        )
        cmd_verify = f'docker exec -i supabase-db-og8gwooogk480gcws0o84ssc psql -U postgres -d postgres -c "{verify_query}"'
        stdin, stdout, stderr = ssh.exec_command(cmd_verify)
        print("\n--- NEW SUBTITLES COUNT BY LANGUAGE FOR TABIB ---")
        print(stdout.read().decode('utf-8'))
        
        ssh.close()
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    main()
