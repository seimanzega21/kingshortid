import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('141.11.160.187', username='root', password='Surya123!', timeout=10)

script = """
const { PrismaClient } = require('@prisma/client');
const prisma = new PrismaClient();
async function run() {
  try {
    const totalUsers = await prisma.user.count();
    console.log('Users:', totalUsers);
    
    // Exact same queries as route.ts
    const startDate = new Date();
    startDate.setDate(startDate.getDate() - 7);
    startDate.setHours(0, 0, 0, 0);
    
    const rawViews = await prisma.watchHistory.findMany({
        select: { watchedAt: true },
        where: { watchedAt: { gte: startDate } },
        orderBy: { watchedAt: 'asc' },
    });
    console.log('rawViews count:', rawViews.length);
    
    const totalViews = await prisma.drama.aggregate({ _sum: { views: true } });
    console.log('TotalViews:', totalViews._sum.views);
    
  } catch(e) {
    console.error('Error:', e);
  } finally {
    await prisma.$disconnect();
  }
}
run();
"""

cmd = f"""docker exec kingshort-admin-app sh -c 'cat << "EOF" > /tmp/test.js
{script}
EOF
node /tmp/test.js'"""

_, stdout, stderr = ssh.exec_command(cmd)
print(stdout.read().decode())
print("STDERR:", stderr.read().decode())
ssh.close()
