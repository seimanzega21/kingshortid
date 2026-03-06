import { ImageResponse } from 'next/og';
import { NextRequest } from 'next/server';
import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

export const runtime = 'edge';

// GET /api/og/drama/[dramaId] - Generate Open Graph image for social sharing
export async function GET(
    req: NextRequest,
    context: { params: Promise<{ dramaId: string }> }
) {
    try {
        const { dramaId } = await context.params;

        const drama = await prisma.drama.findUnique({
            where: { id: dramaId },
            select: {
                title: true,
                description: true,
                genres: true,
                rating: true,
                views: true,
                totalEpisodes: true,
            },
        });

        if (!drama) {
            return new Response('Drama not found', { status: 404 });
        }

        return new ImageResponse(
            (
                <div
                    style={{
                        height: '100%',
                        width: '100%',
                        display: 'flex',
                        flexDirection: 'column',
                        alignItems: 'stretch',
                        justifyContent: 'space-between',
                        backgroundColor: '#0F172A',
                        padding: '60px',
                        fontFamily: 'system-ui, sans-serif',
                    }}
                >
                    {/* Background gradient */}
                    <div
                        style={{
                            position: 'absolute',
                            top: 0,
                            left: 0,
                            right: 0,
                            bottom: 0,
                            background: 'linear-gradient(135deg, #1E293B 0%, #0F172A 100%)',
                            opacity: 0.9,
                        }}
                    />

                    {/* Logo/Brand */}
                    <div
                        style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: '16px',
                            zIndex: 1,
                        }}
                    >
                        <div
                            style={{
                                fontSize: '48px',
                                fontWeight: 'bold',
                                background: 'linear-gradient(90deg, #FFD700, #FFA500)',
                                backgroundClip: 'text',
                                color: 'transparent',
                            }}
                        >
                            KingShort
                        </div>
                    </div>

                    {/* Main Content */}
                    <div
                        style={{
                            display: 'flex',
                            flexDirection: 'column',
                            zIndex: 1,
                            gap: '24px',
                        }}
                    >
                        {/* Title */}
                        <div
                            style={{
                                fontSize: '64px',
                                fontWeight: 'bold',
                                color: 'white',
                                lineHeight: 1.2,
                                maxWidth: '900px',
                            }}
                        >
                            {drama.title}
                        </div>

                        {/* Description */}
                        <div
                            style={{
                                fontSize: '28px',
                                color: '#94A3B8',
                                lineHeight: 1.4,
                                maxWidth: '800px',
                                display: '-webkit-box',
                                WebkitLineClamp: 2,
                                WebkitBoxOrient: 'vertical',
                                overflow: 'hidden',
                            }}
                        >
                            {drama.description}
                        </div>

                        {/* Genres */}
                        <div
                            style={{
                                display: 'flex',
                                gap: '12px',
                                flexWrap: 'wrap',
                            }}
                        >
                            {drama.genres.slice(0, 3).map((genre) => (
                                <div
                                    key={genre}
                                    style={{
                                        padding: '8px 20px',
                                        background: 'rgba(255, 215, 0, 0.15)',
                                        border: '2px solid #FFD700',
                                        borderRadius: '24px',
                                        color: '#FFD700',
                                        fontSize: '20px',
                                        fontWeight: '600',
                                    }}
                                >
                                    {genre}
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Stats Footer */}
                    <div
                        style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: '48px',
                            zIndex: 1,
                            fontSize: '24px',
                            color: '#CBD5E1',
                        }}
                    >
                        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                            <span>⭐</span>
                            <span style={{ fontWeight: 'bold', color: 'white' }}>
                                {drama.rating.toFixed(1)}
                            </span>
                            <span>Rating</span>
                        </div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                            <span>👁️</span>
                            <span style={{ fontWeight: 'bold', color: 'white' }}>
                                {(drama.views / 1000).toFixed(1)}K
                            </span>
                            <span>Views</span>
                        </div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                            <span>📺</span>
                            <span style={{ fontWeight: 'bold', color: 'white' }}>
                                {drama.totalEpisodes}
                            </span>
                            <span>Episodes</span>
                        </div>
                    </div>

                    {/* Decorative accent */}
                    <div
                        style={{
                            position: 'absolute',
                            bottom: 0,
                            right: 0,
                            width: '400px',
                            height: '400px',
                            background: 'radial-gradient(circle, rgba(255,215,0,0.1) 0%, transparent 70%)',
                        }}
                    />
                </div>
            ),
            {
                width: 1200,
                height: 630,
            }
        );
    } catch (error) {
        console.error('OG image generation error:', error);
        return new Response('Failed to generate image', { status: 500 });
    }
}
