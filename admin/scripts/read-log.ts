import fs from 'fs';
import path from 'path';

const logPath = path.join(__dirname, '../segments.txt');

try {
    // Try reading as utf-8 first, if it looks garbled, might need different handling but usually fs handles BOM
    let content = fs.readFileSync(logPath, 'utf8');
    // Sanitize null bytes if powershell UTF-16
    content = content.replace(/\0/g, '');
    console.log('--- LOG CONTENT ---');
    console.log(content);
    console.log('--- END LOG ---');
} catch (e) {
    console.error(e);
}
