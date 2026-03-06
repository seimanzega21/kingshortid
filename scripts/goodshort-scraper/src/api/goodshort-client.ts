/**
 * GoodShort API Client
 * Implements complete API authentication using RSA-SHA256 sign generation
 */

import axios, { AxiosInstance } from 'axios';
import { generateSign, getH5HeaderData } from '../sign-generator';

export interface APIClientConfig {
    gaid?: string;
    androidId?: string;
    userToken?: string;
    appSignatureMD5?: string;
}

export class GoodShortAPIClient {
    private baseURL = 'https://api-akm.goodreels.com/hwycclientreels'; // Fixed: hwYCclientreels → hwYCClientreels
    private client: AxiosInstance;
    private config: APIClientConfig;

    constructor(config?: APIClientConfig) {
        this.config = config || {};

        this.client = axios.create({
            baseURL: this.baseURL,
            timeout: 30000,
            headers: {
                'User-Agent': 'GoodReels/2.7.8 (Android)',
                'Content-Type': 'application/json'
            }
        });
    }

    /**
     * Update client configuration (e.g., after login)
     */
    updateConfig(config: Partial<APIClientConfig>) {
        this.config = { ...this.config, ...config };
    }

    /**
     * Make authenticated API request
     */
    private async request(method: string, path: string, params?: any, data?: any) {
        const timestamp = Date.now().toString();

        // Generate authentication headers
        const authHeaders = getH5HeaderData({
            timestamp,
            path,
            gaid: this.config.gaid,
            androidId: this.config.androidId,
            userToken: this.config.userToken,
            appSignatureMD5: this.config.appSignatureMD5
        });

        try {
            const response = await this.client.request({
                method,
                url: `${path}?timestamp=${timestamp}`, // Add timestamp to URL!
                params,
                data,
                headers: authHeaders
            });

            return response.data;
        } catch (error: any) {
            if (error.response) {
                console.error('API Error:', error.message);
                console.error('Status:', error.response.status);
                console.error('Response:', error.response.data);
            }
            throw error;
        }
    }

    /**
     * Get drama details
     */
    async getDrama(bookId: string) {
        return this.request('POST', '/reader/init', {}, { bookId, priceCurrencyCode: -1 });
    }

    /**
     * Get chapter/episode list
     */
    async getChapterList(bookId: string, chapterCount: number = 500) {
        return this.request('POST', '/chapter/list', {}, { bookId, latestChapterId: 0, chapterCount, needBookInfo: false });
    }

    /**
     * Get specific chapter details
     */
    async getChapterDetail(chapterId: string) {
        return this.request('POST', '/chapter/detail', {}, { chapterId });
    }

    /**
     * Search dramas
     */
    async searchDramas(keyword: string, page: number = 1) {
        return this.request('POST', '/search', {}, { keyword, pageNo: page, pageSize: 20 });
    }

    /**
     * Get drama list by category
     */
    async getDramasByCategory(channelId: number = -3, page: number = 1) {
        return this.request('POST', '/home/index', {}, { pageNo: page, pageSize: 12, channelType: 3, vipBookEnable: true, channelId });
    }

    /**
     * Get home/discover page data
     */
    async getHomeData() {
        return this.request('POST', '/home/index', {}, { pageNo: 1, pageSize: 12, channelType: 3, vipBookEnable: true, channelId: -3 });
    }
}

// Helper to construct video CDN URL
export function buildVideoCDNUrl(
    bookId: string,
    chapterId: string,
    token: string,
    videoId: string,
    resolution: '540p' | '720p' = '720p'
): { m3u8: string; getSegment: (n: number) => string } {
    const xxx = bookId.slice(-3);
    const baseUrl = `https://v2-akm.goodreels.com/mts/books/${xxx}/${bookId}/${chapterId}/${token}/${resolution}`;

    return {
        m3u8: `${baseUrl}/${videoId}_${resolution}.m3u8`,
        getSegment: (segmentNumber: number) =>
            `${baseUrl}/${videoId}_${resolution}_${segmentNumber.toString().padStart(6, '0')}.ts`
    };
}

// Export default instance
export default new GoodShortAPIClient();
