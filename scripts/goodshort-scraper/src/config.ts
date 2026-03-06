/**
 * GoodShort API Configuration
 * Based on reverse-engineered API from HTTP Toolkit capture
 */

import dotenv from 'dotenv';
dotenv.config();

export const config = {
    // API Base URL
    apiBase: process.env.GOODSHORT_API_BASE || 'https://api-akm.goodreels.com/hwyclientreels',

    // Bearer token from HTTP Toolkit capture
    authToken: process.env.GOODSHORT_AUTH_TOKEN || '',

    // Database URL
    databaseUrl: process.env.DATABASE_URL || '',

    // Default headers required by GoodShort API
    defaultHeaders: {
        'Accept-Encoding': 'gzip',
        'Content-Type': 'application/json; charset=UTF-8',
        'appVersion': '2782078',
        'channelCode': 'GRA00001',
        'deviceType': 'phone',
        'platform': 'ANDROID',
        'language': 'en',
        'currentLanguage': 'in',
        'currencyCode': '-1',
        'os': '11',
        'brand': 'google',
        'model': 'sdk_gphone_x86_64',
        'pname': 'com.newreading.goodreels',
    },

    // Scraping settings
    scraping: {
        // Limit number of dramas to scrape (for testing)
        dramaLimit: 5,
        // Delay between requests (ms) to avoid rate limiting
        requestDelay: 1000,
        // Video quality preference
        videoQuality: '720p', // 720p, 540p, or 1080p
    }
};

export default config;
