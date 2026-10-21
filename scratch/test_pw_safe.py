import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('141.11.160.187', username='root', password='Surya123!', timeout=10)

sftp = ssh.open_sftp()
with sftp.file('/tmp/check_pw.js', 'w') as f:
    f.write("""
const bcrypt = require('bcryptjs');

const candidates = ['Surya123!', 'admin123', 'admin', 'password', '123456', 'kingshort123', 'KingShort123!', 'seimanzega', 'seiman123', 'admin123456'];
const hashes = {
  'admin@kingshort.com': '$2b$10$P5Qo03ZhfPCcF6HNdPsQiOCtQykU58eKvDsxgZSsI0.4coYbJirva',
  'admin@kingshort.app': '$2b$10$u431DhAlws/P/Bt5fgADFuTOj1jwDcS2rvJYazviKBLS6zlQVQQau',
  'dhikacreative25@gmail.com': '$2b$10$KQasr8cgau01MfGA5BbHBOdy3uFH4yySvtX49ZMWZGSkp.xdTQc9y'
};

for (const [email, hash] of Object.entries(hashes)) {
  for (const cand of candidates) {
    if (bcrypt.compareSync(cand, hash)) {
      console.log(`MATCH FOUND: ${email} -> ${cand}`);
    }
  }
}
console.log('Done checking.');
""")
sftp.close()

stdin, stdout, stderr = ssh.exec_command('docker cp /tmp/check_pw.js kingshortid-api:/tmp/check_pw.js && docker exec kingshortid-api bun /tmp/check_pw.js')
print(stdout.read().decode())

ssh.close()
