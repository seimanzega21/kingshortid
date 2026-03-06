const fs = require('fs');
const lines = fs.readFileSync('d:/kingshortid/admin/diagnose_output.txt', 'utf8').split('\n');

// Show ep1_url lines (they contain the video URL pattern)
for (const l of lines) {
    if (l.startsWith('  ep1_url=')) {
        // Show just the path portion
        const url = l.replace('  ep1_url=', '');
        const path = url.replace('https://stream.shortlovers.id/melolo/', '');
        process.stdout.write('  ' + path + '\n');
    } else if (!l.startsWith('  ')) {
        process.stdout.write(l + '\n');
    }
}
