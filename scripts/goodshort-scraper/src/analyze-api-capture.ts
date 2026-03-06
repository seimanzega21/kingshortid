/**
 * API Capture Analyzer
 * Analyzes captured API traffic to find sign generation patterns
 */

import * as fs from 'fs';
import * as crypto from 'crypto';

interface CapturedRequest {
    id: number;
    timestamp: string;
    method: string;
    url: string;
    requestHeaders: Record<string, string>;
    requestBody: string | null;
    responseHeaders: Record<string, string>;
    responseBody: string | null;
    statusCode: number;
}

interface CaptureData {
    totalRequests: number;
    capturedAt: string;
    requests: CapturedRequest[];
}

class APIAnalyzer {
    private data: CaptureData;

    constructor(filePath: string) {
        const rawData = fs.readFileSync(filePath, 'utf-8');
        this.data = JSON.parse(rawData);
        console.log(`✅ Loaded ${this.data.totalRequests} requests from ${filePath}\n`);
    }

    // Analyze sign patterns
    analyzeSignPatterns() {
        console.log('🔍 ANALYZING SIGN PATTERNS\n');
        console.log('='.repeat(80));

        const signedRequests = this.data.requests.filter(r => r.requestHeaders.sign);

        console.log(`Found ${signedRequests.length} requests with 'sign' header\n`);

        signedRequests.forEach((req, idx) => {
            const sign = req.requestHeaders.sign;
            const timestamp = req.requestHeaders.timestamp || req.requestHeaders['x-timestamp'];
            const url = new URL(req.url);
            const path = url.pathname;
            const params = url.searchParams.toString();

            console.log(`\n[${idx + 1}] Request #${req.id}`);
            console.log(`    URL: ${path}`);
            console.log(`    Sign: ${sign}`);
            console.log(`    Timestamp: ${timestamp}`);
            console.log(`    Params: ${params || '(none)'}`);
            console.log(`    Body: ${req.requestBody ? req.requestBody.substring(0, 100) : '(none)'}`);

            // Try common hashing algorithms
            if (timestamp) {
                this.testHashCombinations(sign, timestamp, path, params, req.requestBody);
            }
        });

        console.log('\n' + '='.repeat(80));
    }

    // Test common hash combinations to find the pattern
    testHashCombinations(
        actualSign: string,
        timestamp: string,
        path: string,
        params: string,
        body: string | null
    ) {
        const secretKeys = [
            'goodshort',
            'goodreels',
            'hwyclientreels',
            'newreading',
            '123456',
            'secret',
            ''
        ];

        const inputs = [
            timestamp,
            `${timestamp}${path}`,
            `${timestamp}${params}`,
            `${timestamp}${path}${params}`,
            `${path}${timestamp}`,
            body || ''
        ];

        const hashTypes = ['md5', 'sha1', 'sha256'];

        for (const secret of secretKeys) {
            for (const input of inputs) {
                for (const hashType of hashTypes) {
                    // Simple hash
                    const simpleHash = crypto.createHash(hashType).update(input + secret).digest('hex');

                    // HMAC
                    if (secret) {
                        const hmac = crypto.createHmac(hashType, secret).update(input).digest('hex');

                        if (hmac === actualSign || hmac.toLowerCase() === actualSign.toLowerCase()) {
                            console.log(`    ✅ MATCH FOUND!`);
                            console.log(`       Type: HMAC-${hashType.toUpperCase()}`);
                            console.log(`       Secret: "${secret}"`);
                            console.log(`       Input: "${input}"`);
                            return true;
                        }
                    }

                    if (simpleHash === actualSign || simpleHash.toLowerCase() === actualSign.toLowerCase()) {
                        console.log(`    ✅ MATCH FOUND!`);
                        console.log(`       Type: ${hashType.toUpperCase()}`);
                        console.log(`       Input: "${input}${secret}"`);
                        return true;
                    }
                }
            }
        }

        return false;
    }

    // List all API endpoints
    listEndpoints() {
        console.log('\n📋 API ENDPOINTS DISCOVERED\n');
        console.log('='.repeat(80));

        const endpoints = new Map<string, number>();

        this.data.requests.forEach(req => {
            const url = new URL(req.url);
            const path = url.pathname;
            endpoints.set(path, (endpoints.get(path) || 0) + 1);
        });

        const sorted = Array.from(endpoints.entries()).sort((a, b) => b[1] - a[1]);

        sorted.forEach(([path, count]) => {
            console.log(`  ${count.toString().padStart(3)} × ${path}`);
        });

        console.log('\n' + '='.repeat(80));
    }

    // Extract drama metadata structure
    extractDramaMetadata() {
        console.log('\n📦 DRAMA METADATA STRUCTURE\n');
        console.log('='.repeat(80));

        const dramaRequests = this.data.requests.filter(r =>
            r.url.includes('/book') && r.responseBody
        );

        if (dramaRequests.length === 0) {
            console.log('No drama metadata found in captures');
            return;
        }

        const sample = dramaRequests[0];
        try {
            const json = JSON.parse(sample.responseBody);
            console.log('Sample drama response structure:');
            console.log(JSON.stringify(json, null, 2).substring(0, 1000));

            if (json.data) {
                console.log('\n📊 Available fields in drama data:');
                console.log(Object.keys(json.data).join(', '));
            }
        } catch (e) {
            console.log('Error parsing response:', e);
        }

        console.log('\n' + '='.repeat(80));
    }

    // Extract chapter/episode list structure
    extractChapterStructure() {
        console.log('\n📺 EPISODE/CHAPTER STRUCTURE\n');
        console.log('='.repeat(80));

        const chapterRequests = this.data.requests.filter(r =>
            (r.url.includes('/chapter') || r.url.includes('/episode')) && r.responseBody
        );

        if (chapterRequests.length === 0) {
            console.log('No chapter/episode data found in captures');
            return;
        }

        const sample = chapterRequests[0];
        try {
            const json = JSON.parse(sample.responseBody);
            console.log('Sample chapter list response:');
            console.log(JSON.stringify(json, null, 2).substring(0, 1000));

            if (json.data && Array.isArray(json.data)) {
                console.log(`\n📊 Found ${json.data.length} chapters`);
                if (json.data[0]) {
                    console.log('Chapter fields:', Object.keys(json.data[0]).join(', '));
                }
            }
        } catch (e) {
            console.log('Error parsing response:', e);
        }

        console.log('\n' + '='.repeat(80));
    }

    // Generate implementation hints
    generateImplementationHints() {
        console.log('\n💡 IMPLEMENTATION HINTS\n');
        console.log('='.repeat(80));

        const hasSign = this.data.requests.some(r => r.requestHeaders.sign);
        const hasTimestamp = this.data.requests.some(r => r.requestHeaders.timestamp);
        const hasAuth = this.data.requests.some(r =>
            r.requestHeaders.authorization || r.requestHeaders.token
        );

        if (hasSign) {
            console.log('✅ Requests use "sign" header for authentication');
        }
        if (hasTimestamp) {
            console.log('✅ Requests include timestamp');
        }
        if (hasAuth) {
            console.log('✅ Requests may require auth token');
        }

        console.log('\nRecommended next steps:');
        console.log('1. Run analyzeSignPatterns() to find sign algorithm');
        console.log('2. Check if secret key is hardcoded in app');
        console.log('3. Implement sign generator in TypeScript');
        console.log('4. Build API client with proper headers');

        console.log('\n' + '='.repeat(80));
    }

    // Run full analysis
    runFullAnalysis() {
        this.listEndpoints();
        this.analyzeSignPatterns();
        this.extractDramaMetadata();
        this.extractChapterStructure();
        this.generateImplementationHints();
    }
}

// CLI Usage
if (require.main === module) {
    const args = process.argv.slice(2);
    const filePath = args[0] || 'api-captured.json';

    if (!fs.existsSync(filePath)) {
        console.error(`❌ File not found: ${filePath}`);
        console.log('\nUsage: npm run analyze-api <json-file>');
        console.log('Example: npm run analyze-api api-captured.json');
        process.exit(1);
    }

    const analyzer = new APIAnalyzer(filePath);
    analyzer.runFullAnalysis();
}

export { APIAnalyzer };
