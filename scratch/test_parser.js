function parseVttTime(timeStr) {
    if (!timeStr) return 0;
    const parts = timeStr.trim().split(':');
    let seconds = 0;
    if (parts.length === 3) {
        seconds += parseInt(parts[0], 10) * 3600;
        seconds += parseInt(parts[1], 10) * 60;
        seconds += parseFloat(parts[2].replace(',', '.'));
    } else if (parts.length === 2) {
        seconds += parseInt(parts[0], 10) * 60;
        seconds += parseFloat(parts[1].replace(',', '.'));
    }
    return seconds;
}

function parseVtt(vttContent) {
    const cues = [];
    const blocks = vttContent.replace(/\r\n/g, '\n').replace(/\r/g, '\n').split(/\n\s*\n/);
    
    for (const block of blocks) {
        if (!block.trim() || block.includes('WEBVTT') || block.includes('Kind:') || block.includes('Language:')) {
            continue;
        }

        const lines = block.split('\n');
        let timeLineIndex = -1;
        
        for (let i = 0; i < lines.length; i++) {
            if (lines[i].includes('-->')) {
                timeLineIndex = i;
                break;
            }
        }

        if (timeLineIndex === -1) continue;

        const timeParts = lines[timeLineIndex].split('-->');
        if (timeParts.length < 2) continue;

        const startTime = parseVttTime(timeParts[0]);
        let endTimeStr = timeParts[1].trim();
        endTimeStr = endTimeStr.split(' ')[0]; 
        const endTime = parseVttTime(endTimeStr);

        let text = lines.slice(timeLineIndex + 1).join('\n').trim();
        text = text.replace(/<[^>]+>/g, '');

        cues.push({
            startTime,
            endTime,
            text
        });
    }

    return cues;
}

const srtText = `1
00:00:04,688 --> 00:00:06,690
Nomor yang kamu tuju

2
00:00:06,690 --> 00:00:08,458
tidak aktif.

3
00:00:15,932 --> 00:00:16,733
Masuk.`;

const parsed = parseVtt(srtText);
console.log("Parsed Cues:");
console.log(JSON.stringify(parsed, null, 2));
