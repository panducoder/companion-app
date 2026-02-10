import { api, RoomTokenResponse } from './api';
import { config } from '../config';

export type OrbState = 'idle' | 'connecting' | 'listening' | 'speaking' | 'error';

export interface LiveKitSession {
  token: string;
  url: string;
  roomName: string;
  conversationId: string | null;
}

export async function createSession(): Promise<LiveKitSession> {
  const response: RoomTokenResponse = await api.getRoomToken();
  return {
    token: response.token,
    url: response.url || config.livekit.url,
    roomName: response.roomName,
    conversationId: response.conversationId,
  };
}

export function getLiveKitUrl(): string {
  return config.livekit.url;
}
