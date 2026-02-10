import { api, RoomTokenResponse } from './api';

export type OrbState = 'idle' | 'connecting' | 'listening' | 'speaking' | 'error';

export interface LiveKitSession {
  token: string;
  url: string;
  roomName: string;
  conversationId: string;
}

export async function createSession(): Promise<LiveKitSession> {
  const response: RoomTokenResponse = await api.getRoomToken();
  return {
    token: response.token,
    url: response.url,
    roomName: response.roomName,
    conversationId: response.conversationId,
  };
}

export function getLiveKitUrl(): string {
  return process.env.EXPO_PUBLIC_LIVEKIT_URL ?? '';
}
