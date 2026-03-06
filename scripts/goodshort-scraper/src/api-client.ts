import axios, { AxiosInstance, AxiosResponse } from 'axios';
import { config } from './config';

// Headers captured from Frida hook - 2026-01-31
const CAPTURED_HEADERS = {
    'sign': '', // Will be set per-request from Frida capture
    'scWidth': '1080',
    'appVersion': '2782078',
    'language': 'en',
    'mcc': '310',
    'ramSize': '2077077504',
    'deviceId': '3a527bd0-4a98-47e7-ac47-f592c165d870',
    'model': 'sdk_gphone_x86_64',
    'variableChannelCode': '',
    'brand': 'google',
    'apn': '2',
    'androidId': 'ffffffffcf4ce71dcf4ce71d00000000',
    'deviceType': 'phone',
    'pname': 'com.newreading.goodreels',
    'timeZone': '+0700',
    'bigdataSession': '09807052-229f-45d2-8048-e5ece2a443b3',
    'afid': '1769846366998-4462332118971079286',
    'gender': 'UNKNOWN',
    'variableBid': '',
    'platform': 'ANDROID',
    'Authorization': 'Bearer ZXlKMGVYQWlPaUpLVjFRaUxDSmhiR2NpT2lKSVV6STFOaUo5LmV5SnlaV2RwYzNSbGNsUjVjR1VpT2lKUVJWSk5RVTVGVGxRaUxDSjFjMlZ5U1dRaU9qRTJNREExT0RReE4zMC5XYzA4LXpEOUxuaHBCREJkRENrMDBPQWxiLUtCa3ZKek9jbmg2Ump6MENF',
    'scDesc': '1080P',
    'currentLanguage': 'in',
    'originalChid': 'GRA00001',
    'scHeight': '2072',
    'channelCode': 'GRA00001',
    'hardWare': 'goldfish_x86_64',
    'os': '11',
    'romSize': '6228115456',
    'userId': '160058417',
    'adjustAdid': '',
    'p': '189',
    'lqb': '0',
    'lqa': '0',
    'currencyCode': '-1',
    'Content-Type': 'application/json; charset=UTF-8',
    'User-Agent': 'okhttp/4.10.0',
    'Accept-Encoding': 'gzip',
    'Connection': 'Keep-Alive'
};

// Sign headers captured from Frida for different endpoints
const CAPTURED_SIGNS: Record<string, { sign: string; timestamp: string }> = {
    'home/index': {
        sign: 'VTHYJWUtBYS5e0k4w/UuC3/uQnIHzRPrm7dMhdEWBnt5Uxm9DV4qxG/92PNTr6bfFTY8MiqjBmcV6gf6Bjm4xnCHEun1PU7bfROwwbGh08TiL3CjIefWBp27Uhit/gquZXk+pTn9XgyKVHtFYHGJBRgUg7Ps/etgAzVcmUdnXNP5uAg6demZORtW3Qv9iHv5Uctas4s0eV1idPafxnHGI7/FcdKItQf6ziWu4/WRQi+aM/+JF9sUO7yqD0KLTM76TIEkq8QTyGbksYHtXFA9enM3jWbaMjhts5jpI4Jb3yQQPpewMDbnbLqcKhGfvXIk4tppoYi4wx/21BIpBFW5cQ==',
        timestamp: '1769855063192'
    },
    'chapter/list': {
        sign: 'ntI35IwaKbKthKuOrMfV2CBkBl16Lxuv5lp1ehCiFpRD8joGiqe85Q0E+8ltdqiFVGuiIXhFeCOF/EPbuGFQdmvCmo56vcZvS1wH0/8bDrsjF8N6JQy7syjUu+mhyRTytHW+MoKB/6P1pTXZwCezqY7500W9wTw6MPzsI5LlpBcjGjjKcYg4OW4XZCCGnV/5qaZolzo0ciSvmZq4/2OOPCaOf+B+evGJipZoiNj5HMThwQHsAY9fqUyX5sZ8tCJXE/jV8dQ35XwhOK1hoSV5fgyvz9N2jxmAVMjK/QgCSCIvKZXRbKsNLdr5ixMtA2QSpoxEOAa2S7Sm6KTihzoiww==',
        timestamp: '1769855073446'
    },
    'reader/init': {
        sign: 'dCs6vFgsUqZyjxQ+snrbfGNYpU/H9WiNSQxSgKpEcxBuHV27JLkxfCxXHQWL/sEhNp1Um1gxL9UdqcAsNbjF0z96Pa5Gv4ZAZTwo+SNW5dJfZP2IykDosVRU27eT/Z/msXYFyydWcA/bXnqFtQpgzrWWFRpHALaJ5C3qiwUeGb6akocKv/nG59bAjIU+ERC2Gwt38hZ+AWEnSSOh9CSWO18jVTT0bTaEhiuMsEjsRR7B3WqUMDSzCvzJLud9zp7j3dJjm1j8DnH1RilLra8FJEN8O1K1CTuSVWIipOdL8fGQ6lSoLTV+U6yhsoMQSm1e14uyq5Vaep2e8LUEO5LNWQ==',
        timestamp: '1769855072775'
    },
    'book/quick/open': {
        sign: 'WeXjMJuxrQT2OyUxDdSazw5CBtVKIi02F104cEehUCeMuoP0f8DMIo5pd0EOo5wzW4uidE6ghUek+C0VUlQgd+jWvTB/91hWXb5Rm++AsrOSWsCQHFHFkRp+yTo7HcODPmpZd1e+ayDKkzWcpaND+s7yWKHW9KCuZ6i8Cm8KH3esWKFQSmTA+wkvZVL8FAk9O0JcOVNUd++md25XKvn21//SiMQf15aPt+1B3myxBD8UZ2fkb8f2MmD09zjRsoxpdue/XOXnuZJqnujU+ecRZSR2WEWb49sDYjkObpVuAd509h8rWE6OeYOd90d59JL5+QOZNNQrlKjhKrakdJvxpw==',
        timestamp: '1769855072790'
    }
};

export interface ApiClientOptions {
    useSign?: string; // Use a specific captured sign
    timestamp?: string;
}

export class GoodShortApiClient {
    private client: AxiosInstance;
    private baseUrl = 'https://api-akm.goodreels.com';

    constructor() {
        this.client = axios.create({
            baseURL: this.baseUrl,
            timeout: 30000,
            headers: CAPTURED_HEADERS
        });
    }

    /**
     * Get local time string in the format used by the app
     */
    private getLocalTime(): string {
        const now = new Date();
        const offset = '+0700';
        const pad = (n: number) => n.toString().padStart(2, '0');
        const pad3 = (n: number) => n.toString().padStart(3, '0');

        return `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())} ` +
            `${pad(now.getHours())}:${pad(now.getMinutes())}:${pad(now.getSeconds())}.${pad3(now.getMilliseconds())} ${offset}`;
    }

    /**
     * Make request with captured sign header
     */
    private async makeRequest<T>(
        endpoint: string,
        body: any,
        signKey: string
    ): Promise<T> {
        const signData = CAPTURED_SIGNS[signKey];
        if (!signData) {
            throw new Error(`No captured sign for endpoint: ${signKey}. Run Frida to capture.`);
        }

        const url = `/hwycclientreels/${endpoint}?timestamp=${signData.timestamp}`;

        const response = await this.client.post<T>(url, body, {
            headers: {
                ...CAPTURED_HEADERS,
                'sign': signData.sign,
                'localTime': this.getLocalTime()
            }
        });

        return response.data;
    }

    /**
     * Get home/index drama list
     */
    async getHomeIndex(pageNo: number = 1, pageSize: number = 12): Promise<any> {
        return this.makeRequest('home/index', {
            pageNo,
            pageSize,
            channelType: 3,
            vipBookEnable: true,
            channelId: -3
        }, 'home/index');
    }

    /**
     * Get chapter list for a book
     */
    async getChapterList(bookId: string, chapterCount: number = 500): Promise<any> {
        return this.makeRequest('chapter/list', {
            latestChapterId: 0,
            chapterCount,
            needBookInfo: false,
            bookId
        }, 'chapter/list');
    }

    /**
     * Initialize reader for a book
     */
    async getReaderInit(bookId: string): Promise<any> {
        return this.makeRequest('reader/init', {
            priceCurrencyCode: -1,
            bookId
        }, 'reader/init');
    }

    /**
     * Quick open a book
     */
    async quickOpenBook(bookId: string, chapterId: number = -1): Promise<any> {
        return this.makeRequest('book/quick/open', {
            chapterId,
            bookId
        }, 'book/quick/open');
    }

    /**
     * Update captured sign from Frida output
     */
    updateSign(endpoint: string, sign: string, timestamp: string): void {
        CAPTURED_SIGNS[endpoint] = { sign, timestamp };
        console.log(`Updated sign for ${endpoint}`);
    }

    /**
     * Get all available sign keys
     */
    getAvailableEndpoints(): string[] {
        return Object.keys(CAPTURED_SIGNS);
    }
}

// Export singleton instance
export const apiClient = new GoodShortApiClient();
