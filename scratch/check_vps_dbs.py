import paramiko
import json

SSH_HOST = '141.11.160.187'
SSH_USER = 'root'
SSH_PASS = 'Surya123!'

def run_cmd(ssh, cmd):
    stdin, stdout, stderr = ssh.exec_command(cmd)
    return stdout.read().decode('utf-8').strip(), stderr.read().decode('utf-8').strip()

def main():
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        print(f"Connecting to SSH {SSH_USER}@{SSH_HOST}...")
        ssh.connect(SSH_HOST, username=SSH_USER, password=SSH_PASS, timeout=10)
        print("Connected.")
        
        # 1. Get docker ps
        print("\n--- RUNNING DOCKER CONTAINERS ---")
        out, err = run_cmd(ssh, 'docker ps --format "table {{.ID}}\\t{{.Names}}\\t{{.Image}}\\t{{.Ports}}\\t{{.Status}}"')
        print(out)
        
        # Find all containers with 'db' or 'postgres' in name
        containers_out, _ = run_cmd(ssh, 'docker ps --format "{{.Names}}"')
        containers = [c for c in containers_out.split('\n') if c.strip()]
        
        db_containers = [c for c in containers if 'db' in c or 'postgres' in c]
        print(f"\nFound DB containers: {db_containers}")
        
        for db in db_containers:
            print(f"\n================ INSPECTING CONTAINER: {db} ================")
            
            # Check schemas
            out_schema, _ = run_cmd(ssh, f'docker exec -t {db} psql -U postgres -d postgres -c "SELECT schema_name FROM information_schema.schemata;" 2>/dev/null')
            print(f"Schemas:")
            print(out_schema)
            
            # Check public tables
            out_tables, _ = run_cmd(ssh, f'docker exec -t {db} psql -U postgres -d postgres -P pager=off -c "SELECT table_name FROM information_schema.tables WHERE table_schema = \'public\';" 2>/dev/null')
            print(f"Public tables:")
            print(out_tables)
            
            # Check users/User tables in all schemas
            out_user_tables, _ = run_cmd(ssh, f'docker exec -t {db} psql -U postgres -d postgres -P pager=off -c "SELECT table_schema, table_name FROM information_schema.tables WHERE table_name ILIKE \'%user%\';" 2>/dev/null')
            print(f"User tables in all schemas:")
            print(out_user_tables)
            
            # Count users and admins if 'users' table exists
            if 'users' in out_tables or 'User' in out_tables:
                table_name = 'users' if 'users' in out_tables else '"User"'
                out_count, _ = run_cmd(ssh, f'docker exec -t {db} psql -U postgres -d postgres -P pager=off -c "SELECT count(*) FROM {table_name};" 2>/dev/null')
                print(f"Total user count in {table_name}: {out_count}")
                
                # Retrieve admins
                out_admins, _ = run_cmd(ssh, f'docker exec -t {db} psql -U postgres -d postgres -P pager=off -c "SELECT email, role, provider, created_at FROM {table_name} WHERE role = \'admin\' OR email LIKE \'%admin%\';" 2>/dev/null')
                print(f"Admins in {table_name}:")
                print(out_admins)
                
        ssh.close()
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    main()
