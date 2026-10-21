import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('141.11.160.187', username='root', password='Surya123!', timeout=10)

config_content = """http:
  routers:
    kingshort-admin-http:
      rule: "Host(`admin.shortlovers.id`)"
      entryPoints:
        - http
      service: kingshort-admin-svc
    kingshort-admin-https:
      rule: "Host(`admin.shortlovers.id`)"
      entryPoints:
        - https
      service: kingshort-admin-svc
      tls:
        certResolver: letsencrypt
  services:
    kingshort-admin-svc:
      loadBalancer:
        servers:
          - url: "http://kingshort-admin-app:3000"
"""

sftp = ssh.open_sftp()
with sftp.file('/data/coolify/proxy/dynamic/kingshort-admin.yaml', 'w') as f:
    f.write(config_content)
sftp.close()

print("Traefik dynamic config created for admin.shortlovers.id!")
ssh.close()
