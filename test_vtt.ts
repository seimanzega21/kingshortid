import { parseVtt } from './mobile/utils/vttParser';

const sample = `1
00:00:02,426 --> 00:00:03,320
Nara,

2
00:00:03,320 --> 00:00:04,400
jangan keterlaluan.`;

const cues = parseVtt(sample);
console.log(JSON.stringify(cues, null, 2));
