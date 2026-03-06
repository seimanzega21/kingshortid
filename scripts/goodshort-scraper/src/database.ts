/**
 * Database Module
 * Saves scraped data to PostgreSQL (optional, can also output to JSON)
 */

import fs from 'fs';
import path from 'path';
import { ScrapedDrama, ScrapeResult } from './types';

/**
 * Save scraped data to JSON file
 */
export function saveToJson(data: ScrapeResult, filename: string = 'scraped-data.json'): string {
    const outputDir = path.join(__dirname, '..', 'output');

    // Create output directory if it doesn't exist
    if (!fs.existsSync(outputDir)) {
        fs.mkdirSync(outputDir, { recursive: true });
    }

    const filepath = path.join(outputDir, filename);

    fs.writeFileSync(filepath, JSON.stringify(data, null, 2), 'utf-8');

    console.log(`💾 Data saved to: ${filepath}`);

    return filepath;
}

/**
 * Generate SQL insert statements for the scraped data
 * Compatible with KingShortID database schema
 */
export function generateSqlStatements(data: ScrapedDrama[]): string {
    const statements: string[] = [];

    statements.push('-- GoodShort Scraped Data Import');
    statements.push(`-- Generated at: ${new Date().toISOString()}`);
    statements.push('-- Run this in your PostgreSQL database\n');

    for (const drama of data) {
        // Insert drama
        const genres = drama.genres.join(', ');
        statements.push(`
-- Drama: ${drama.title}
INSERT INTO "Drama" (
  "title", "synopsis", "coverUrl", "genres", "episodeCount", "status", "createdAt", "updatedAt"
) VALUES (
  '${escapeSql(drama.title)}',
  '${escapeSql(drama.synopsis)}',
  '${drama.coverUrl}',
  ARRAY[${drama.genres.map(g => `'${escapeSql(g)}'`).join(', ')}],
  ${drama.episodeCount},
  '${drama.status}',
  NOW(),
  NOW()
) ON CONFLICT DO NOTHING;
`);

        // Insert episodes
        for (const episode of drama.episodes) {
            statements.push(`
INSERT INTO "Episode" (
  "dramaId", "episodeNumber", "title", "duration", "thumbnailUrl", "videoUrl", "createdAt", "updatedAt"
) VALUES (
  (SELECT id FROM "Drama" WHERE title = '${escapeSql(drama.title)}' LIMIT 1),
  ${episode.episodeNumber},
  '${escapeSql(episode.title)}',
  ${episode.duration},
  '${episode.thumbnailUrl}',
  '${episode.videoUrl720p || ''}',
  NOW(),
  NOW()
) ON CONFLICT DO NOTHING;
`);
        }
    }

    return statements.join('\n');
}

/**
 * Save SQL statements to file
 */
export function saveSqlToFile(data: ScrapedDrama[], filename: string = 'import.sql'): string {
    const outputDir = path.join(__dirname, '..', 'output');

    if (!fs.existsSync(outputDir)) {
        fs.mkdirSync(outputDir, { recursive: true });
    }

    const filepath = path.join(outputDir, filename);
    const sql = generateSqlStatements(data);

    fs.writeFileSync(filepath, sql, 'utf-8');

    console.log(`📄 SQL file saved to: ${filepath}`);

    return filepath;
}

/**
 * Escape single quotes in SQL strings
 */
function escapeSql(str: string): string {
    return str.replace(/'/g, "''");
}

export default { saveToJson, saveSqlToFile, generateSqlStatements };
