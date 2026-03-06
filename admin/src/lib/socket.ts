import { Server as HTTPServer } from 'http';
import { Server as SocketIOServer, Socket } from 'socket.io';
import { prisma } from '@/lib/prisma';

interface WatchPartyState {
    currentTime: number;
    isPlaying: boolean;
    lastUpdate: number;
}

interface PartyParticipant {
    userId: string;
    userName: string;
    avatar?: string;
    socketId: string;
}

const watchPartyStates = new Map<string, WatchPartyState>();
const partyParticipants = new Map<string, Set<PartyParticipant>>();

export function initializeSocketIO(httpServer: HTTPServer) {
    const io = new SocketIOServer(httpServer, {
        cors: {
            origin: process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3000',
            methods: ['GET', 'POST'],
            credentials: true,
        },
    });

    io.on('connection', (socket: Socket) => {
        console.log(`User connected: ${socket.id}`);

        // Join Watch Party
        socket.on('join-party', async (data: {
            partyId: string;
            userId: string;
            userName: string;
            avatar?: string;
        }) => {
            const { partyId, userId, userName, avatar } = data;

            try {
                // Verify party exists
                const party = await prisma.watchParty.findUnique({
                    where: { id: partyId },
                });

                if (!party) {
                    socket.emit('error', { message: 'Watch party not found' });
                    return;
                }

                // Join socket room
                socket.join(partyId);

                // Add participant
                if (!partyParticipants.has(partyId)) {
                    partyParticipants.set(partyId, new Set());
                }

                const participant: PartyParticipant = {
                    userId,
                    userName,
                    avatar,
                    socketId: socket.id,
                };

                partyParticipants.get(partyId)?.add(participant);

                // Update database
                await prisma.watchPartyParticipant.upsert({
                    where: {
                        partyId_userId: { partyId, userId },
                    },
                    create: {
                        partyId,
                        userId,
                        isActive: true,
                    },
                    update: {
                        isActive: true,
                        leftAt: null,
                    },
                });

                // Get current party state
                const currentState = watchPartyStates.get(partyId) || {
                    currentTime: 0,
                    isPlaying: false,
                    lastUpdate: Date.now(),
                };

                // Send current state to new participant
                socket.emit('party-state', currentState);

                // Notify others
                const participants = Array.from(partyParticipants.get(partyId) || []);
                io.to(partyId).emit('participant-joined', {
                    participant,
                    participants,
                });

                console.log(`User ${userName} joined party ${partyId}`);
            } catch (error) {
                console.error('Error joining party:', error);
                socket.emit('error', { message: 'Failed to join party' });
            }
        });

        // Leave Watch Party
        socket.on('leave-party', async (data: { partyId: string; userId: string }) => {
            const { partyId, userId } = data;

            socket.leave(partyId);

            // Remove participant
            const participants = partyParticipants.get(partyId);
            if (participants) {
                const participant = Array.from(participants).find(
                    (p) => p.socketId === socket.id
                );
                if (participant) {
                    participants.delete(participant);

                    // Update database
                    await prisma.watchPartyParticipant.update({
                        where: {
                            partyId_userId: { partyId, userId },
                        },
                        data: {
                            isActive: false,
                            leftAt: new Date(),
                        },
                    });

                    // Notify others
                    io.to(partyId).emit('participant-left', {
                        participant,
                        participants: Array.from(participants),
                    });
                }
            }

            console.log(`User ${userId} left party ${partyId}`);
        });

        // Sync Video Playback
        socket.on('sync-video', (data: {
            partyId: string;
            currentTime: number;
            isPlaying: boolean;
        }) => {
            const { partyId, currentTime, isPlaying } = data;

            const state: WatchPartyState = {
                currentTime,
                isPlaying,
                lastUpdate: Date.now(),
            };

            watchPartyStates.set(partyId, state);

            // Broadcast to all participants except sender
            socket.to(partyId).emit('video-sync', {
                currentTime,
                isPlaying,
            });
        });

        // Play/Pause
        socket.on('play-pause', (data: { partyId: string; isPlaying: boolean }) => {
            const { partyId, isPlaying } = data;

            const state = watchPartyStates.get(partyId);
            if (state) {
                state.isPlaying = isPlaying;
                state.lastUpdate = Date.now();
            }

            socket.to(partyId).emit('video-play-pause', { isPlaying });
        });

        // Seek
        socket.on('seek', (data: { partyId: string; currentTime: number }) => {
            const { partyId, currentTime } = data;

            const state = watchPartyStates.get(partyId);
            if (state) {
                state.currentTime = currentTime;
                state.lastUpdate = Date.now();
            }

            socket.to(partyId).emit('video-seek', { currentTime });
        });

        // Chat Message
        socket.on('chat-message', (data: {
            partyId: string;
            userId: string;
            userName: string;
            avatar?: string;
            message: string;
        }) => {
            const { partyId, userId, userName, avatar, message } = data;

            const chatMessage = {
                id: `${Date.now()}-${userId}`,
                userId,
                userName,
                avatar,
                message,
                timestamp: Date.now(),
            };

            // Broadcast to all participants in room
            io.to(partyId).emit('chat-message', chatMessage);

            console.log(`Chat in ${partyId}: ${userName}: ${message}`);
        });

        // Disconnect
        socket.on('disconnect', async () => {
            console.log(`User disconnected: ${socket.id}`);

            // Find and remove from all parties
            for (const [partyId, participants] of partyParticipants.entries()) {
                const participant = Array.from(participants).find(
                    (p) => p.socketId === socket.id
                );

                if (participant) {
                    participants.delete(participant);

                    // Update database
                    await prisma.watchPartyParticipant.updateMany({
                        where: {
                            partyId,
                            userId: participant.userId,
                        },
                        data: {
                            isActive: false,
                            leftAt: new Date(),
                        },
                    });

                    // Notify others
                    io.to(partyId).emit('participant-left', {
                        participant,
                        participants: Array.from(participants),
                    });
                }
            }
        });
    });

    console.log('Socket.IO initialized');
    return io;
}
