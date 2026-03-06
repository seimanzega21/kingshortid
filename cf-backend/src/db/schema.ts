import { pgTable, text, integer, real, boolean, timestamp, jsonb, uniqueIndex, index } from 'drizzle-orm/pg-core';
import { createId } from '@paralleldrive/cuid2';
import { sql } from 'drizzle-orm';

// Helper for default CUID
const cuid = () => text('id').primaryKey().$defaultFn(() => createId());
const timestampNow = (name: string) => timestamp(name, { withTimezone: true }).notNull().$defaultFn(() => new Date());
const timestampOpt = (name: string) => timestamp(name, { withTimezone: true });

// ==================== USERS ====================
export const users = pgTable('users', {
    id: text('id').primaryKey().$defaultFn(() => createId()),
    email: text('email').notNull().unique(),
    password: text('password'),
    name: text('name').notNull(),
    avatar: text('avatar'),
    provider: text('provider').notNull().default('local'),
    providerId: text('provider_id'),
    role: text('role').notNull().default('user'),

    isGuest: boolean('is_guest').notNull().default(false),
    guestId: text('guest_id').unique(),

    coins: integer('coins').notNull().default(100),
    vipStatus: boolean('vip_status').notNull().default(false),
    vipExpiry: timestampOpt('vip_expiry'),

    lastCheckIn: timestampOpt('last_check_in'),
    checkInStreak: integer('check_in_streak').notNull().default(0),

    preferences: text('preferences'),
    totalWatchTime: integer('total_watch_time').notNull().default(0),

    pushToken: text('push_token'),
    notifyEpisodes: boolean('notify_episodes').notNull().default(true),
    notifyCoins: boolean('notify_coins').notNull().default(true),
    notifySystem: boolean('notify_system').notNull().default(true),

    isActive: boolean('is_active').notNull().default(true),
    createdAt: timestampNow('created_at'),
    updatedAt: timestampNow('updated_at'),
});

// ==================== DRAMAS ====================
export const dramas = pgTable('dramas', {
    id: text('id').primaryKey().$defaultFn(() => createId()),
    title: text('title').notNull(),
    description: text('description').notNull(),
    cover: text('cover').notNull(),
    banner: text('banner'),

    genres: jsonb('genres').notNull().default([]),
    tagList: jsonb('tag_list').notNull().default([]),

    totalEpisodes: integer('total_episodes').notNull().default(0),
    rating: real('rating').notNull().default(0),
    views: integer('views').notNull().default(0),
    likes: integer('likes').notNull().default(0),

    reviewCount: integer('review_count').notNull().default(0),
    averageRating: real('average_rating').notNull().default(0),

    status: text('status').notNull().default('ongoing'),
    isVip: boolean('is_vip').notNull().default(false),
    isFeatured: boolean('is_featured').notNull().default(false),
    isActive: boolean('is_active').notNull().default(true),
    ageRating: text('age_rating').notNull().default('all'),

    releaseDate: timestampOpt('release_date'),
    director: text('director'),
    cast: jsonb('cast').notNull().default([]),
    country: text('country').notNull().default('China'),
    language: text('language').notNull().default('Mandarin'),

    createdAt: timestampNow('created_at'),
    updatedAt: timestampNow('updated_at'),
});

// ==================== EPISODES ====================
export const episodes = pgTable('episodes', {
    id: text('id').primaryKey().$defaultFn(() => createId()),
    dramaId: text('drama_id').notNull().references(() => dramas.id, { onDelete: 'cascade' }),

    episodeNumber: integer('episode_number').notNull(),
    title: text('title').notNull(),
    description: text('description'),
    thumbnail: text('thumbnail'),
    videoUrl: text('video_url').notNull(),
    duration: integer('duration').notNull().default(0),

    isVip: boolean('is_vip').notNull().default(false),
    coinPrice: integer('coin_price').notNull().default(0),
    views: integer('views').notNull().default(0),

    isActive: boolean('is_active').notNull().default(true),
    releaseDate: timestampNow('release_date'),

    createdAt: timestampNow('created_at'),
    updatedAt: timestampNow('updated_at'),

    seasonId: text('season_id'),
}, (table) => ({
    dramaEpUnique: uniqueIndex('episodes_drama_ep_unique').on(table.dramaId, table.episodeNumber),
    dramaIdx: index('episodes_drama_idx').on(table.dramaId),
}));

// ==================== SUBTITLES ====================
export const subtitles = pgTable('subtitles', {
    id: text('id').primaryKey().$defaultFn(() => createId()),
    episodeId: text('episode_id').notNull().references(() => episodes.id, { onDelete: 'cascade' }),

    language: text('language').notNull(),
    label: text('label').notNull(),
    url: text('url').notNull(),
    isDefault: boolean('is_default').notNull().default(false),

    createdAt: timestampNow('created_at'),
}, (table) => ({
    epLangUnique: uniqueIndex('subtitles_ep_lang_unique').on(table.episodeId, table.language),
    episodeIdx: index('subtitles_episode_idx').on(table.episodeId),
}));

// ==================== WATCHLIST ====================
export const watchlist = pgTable('watchlist', {
    id: text('id').primaryKey().$defaultFn(() => createId()),
    userId: text('user_id').notNull().references(() => users.id, { onDelete: 'cascade' }),
    dramaId: text('drama_id').notNull().references(() => dramas.id, { onDelete: 'cascade' }),
    addedAt: timestampNow('added_at'),
}, (table) => ({
    userDramaUnique: uniqueIndex('watchlist_user_drama_unique').on(table.userId, table.dramaId),
}));

// ==================== FAVORITES ====================
export const favorites = pgTable('favorites', {
    id: text('id').primaryKey().$defaultFn(() => createId()),
    userId: text('user_id').notNull().references(() => users.id, { onDelete: 'cascade' }),
    dramaId: text('drama_id').notNull().references(() => dramas.id, { onDelete: 'cascade' }),
    addedAt: timestampNow('added_at'),
}, (table) => ({
    userDramaUnique: uniqueIndex('favorites_user_drama_unique').on(table.userId, table.dramaId),
}));

// ==================== COLLECTION ====================
export const collections = pgTable('collections', {
    id: text('id').primaryKey().$defaultFn(() => createId()),
    userId: text('user_id').notNull().references(() => users.id, { onDelete: 'cascade' }),
    dramaId: text('drama_id').notNull().references(() => dramas.id, { onDelete: 'cascade' }),
    notifyNewEpisode: boolean('notify_new_episode').notNull().default(true),
    addedAt: timestampNow('added_at'),
}, (table) => ({
    userDramaUnique: uniqueIndex('collections_user_drama_unique').on(table.userId, table.dramaId),
}));

// ==================== WATCH HISTORY ====================
export const watchHistory = pgTable('watch_history', {
    id: text('id').primaryKey().$defaultFn(() => createId()),
    userId: text('user_id').notNull().references(() => users.id, { onDelete: 'cascade' }),
    dramaId: text('drama_id').notNull().references(() => dramas.id, { onDelete: 'cascade' }),
    episodeId: text('episode_id').notNull().references(() => episodes.id, { onDelete: 'cascade' }),

    episodeNumber: integer('episode_number').notNull(),
    progress: integer('progress').notNull().default(0),
    watchedAt: timestampNow('watched_at'),
}, (table) => ({
    userDramaUnique: uniqueIndex('watch_history_user_drama_unique').on(table.userId, table.dramaId),
    userWatchedIdx: index('watch_history_user_watched_idx').on(table.userId, table.watchedAt),
}));

// ==================== COIN TRANSACTIONS ====================
export const coinTransactions = pgTable('coin_transactions', {
    id: text('id').primaryKey().$defaultFn(() => createId()),
    userId: text('user_id').notNull().references(() => users.id, { onDelete: 'cascade' }),

    type: text('type').notNull(),
    amount: integer('amount').notNull(),
    description: text('description').notNull(),
    reference: text('reference'),
    balanceAfter: integer('balance_after'),

    createdAt: timestampNow('created_at'),
}, (table) => ({
    userCreatedIdx: index('coin_tx_user_created_idx').on(table.userId, table.createdAt),
}));

// ==================== NOTIFICATIONS ====================
export const notifications = pgTable('notifications', {
    id: text('id').primaryKey().$defaultFn(() => createId()),
    userId: text('user_id').notNull().references(() => users.id, { onDelete: 'cascade' }),

    title: text('title').notNull(),
    body: text('body').notNull(),
    type: text('type').notNull(),
    data: text('data'),
    read: boolean('read').notNull().default(false),

    createdAt: timestampNow('created_at'),
}, (table) => ({
    userCreatedIdx: index('notif_user_created_idx').on(table.userId, table.createdAt),
}));

// ==================== CATEGORIES ====================
export const categories = pgTable('categories', {
    id: text('id').primaryKey().$defaultFn(() => createId()),
    name: text('name').notNull().unique(),
    slug: text('slug').notNull().unique(),
    icon: text('icon'),
    order: integer('order').notNull().default(0),
});

// ==================== ACHIEVEMENTS ====================
export const achievements = pgTable('achievements', {
    id: text('id').primaryKey().$defaultFn(() => createId()),
    name: text('name').notNull(),
    description: text('description').notNull(),
    icon: text('icon'),
    type: text('type').notNull(),
    requirement: integer('requirement').notNull(),
    reward: integer('reward').notNull().default(0),
    isActive: boolean('is_active').notNull().default(true),
    createdAt: timestampNow('created_at'),
});

export const userAchievements = pgTable('user_achievements', {
    id: text('id').primaryKey().$defaultFn(() => createId()),
    userId: text('user_id').notNull().references(() => users.id, { onDelete: 'cascade' }),
    achievementId: text('achievement_id').notNull().references(() => achievements.id, { onDelete: 'cascade' }),
    unlockedAt: timestampNow('unlocked_at'),
}, (table) => ({
    userAchUnique: uniqueIndex('user_ach_unique').on(table.userId, table.achievementId),
    userUnlockedIdx: index('user_ach_unlocked_idx').on(table.userId, table.unlockedAt),
}));

// ==================== DAILY REWARDS ====================
export const dailyRewards = pgTable('daily_rewards', {
    id: text('id').primaryKey().$defaultFn(() => createId()),
    userId: text('user_id').notNull().references(() => users.id, { onDelete: 'cascade' }),

    rewardType: text('reward_type').notNull(),
    amount: integer('amount').notNull(),
    claimedAt: timestampNow('claimed_at'),
}, (table) => ({
    userClaimedIdx: index('daily_rewards_user_claimed_idx').on(table.userId, table.claimedAt),
}));

// ==================== SEASONS ====================
export const seasons = pgTable('seasons', {
    id: text('id').primaryKey().$defaultFn(() => createId()),
    dramaId: text('drama_id').notNull().references(() => dramas.id, { onDelete: 'cascade' }),

    seasonNumber: integer('season_number').notNull(),
    title: text('title').notNull(),
    description: text('description'),
    poster: text('poster'),
    trailer: text('trailer'),

    episodeCount: integer('episode_count').notNull().default(0),
    releaseDate: timestampOpt('release_date'),

    createdAt: timestampNow('created_at'),
    updatedAt: timestampNow('updated_at'),
}, (table) => ({
    dramaSeasonUnique: uniqueIndex('seasons_drama_season_unique').on(table.dramaId, table.seasonNumber),
    dramaSeasonIdx: index('seasons_drama_season_idx').on(table.dramaId, table.seasonNumber),
}));
