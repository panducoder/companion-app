import { supabase } from './supabase';

export interface RoomTokenResponse {
  token: string;
  url: string;
  roomName: string;
  conversationId: string | null;
}

export interface Conversation {
  id: string;
  user_id: string;
  started_at: string;
  ended_at: string | null;
  duration_seconds: number | null;
  summary: string | null;
  emotional_tone: string | null;
}

export interface Message {
  id: string;
  conversation_id: string;
  user_id: string;
  role: 'user' | 'assistant';
  content: string;
  created_at: string;
}

class AppError extends Error {
  originalError: unknown;
  constructor(message: string, originalError?: unknown) {
    super(message);
    this.name = 'AppError';
    this.originalError = originalError;
  }
}

export const api = {
  async getRoomToken(): Promise<RoomTokenResponse> {
    try {
      const { data, error } = await supabase.functions.invoke('generate-room-token');
      if (error) throw error;
      return data as RoomTokenResponse;
    } catch (err) {
      throw new AppError(
        'Unable to start conversation. Please check your connection and try again.',
        err
      );
    }
  },

  async getConversations(limit = 20): Promise<Conversation[]> {
    try {
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) throw new Error('Not authenticated');

      const { data, error } = await supabase
        .from('conversations')
        .select('*')
        .eq('user_id', user.id)
        .order('started_at', { ascending: false })
        .limit(limit);

      if (error) throw error;
      return (data ?? []) as Conversation[];
    } catch (err) {
      throw new AppError('Unable to load conversations. Please try again.', err);
    }
  },

  async getMessages(conversationId: string): Promise<Message[]> {
    try {
      const { data, error } = await supabase
        .from('messages')
        .select('*')
        .eq('conversation_id', conversationId)
        .order('created_at', { ascending: true });

      if (error) throw error;
      return (data ?? []) as Message[];
    } catch (err) {
      throw new AppError('Unable to load messages. Please try again.', err);
    }
  },

  async deleteUserData(): Promise<void> {
    try {
      const { error } = await supabase.functions.invoke('delete-user-data');
      if (error) throw error;
    } catch (err) {
      throw new AppError(
        'Unable to delete your data right now. Please try again later.',
        err
      );
    }
  },
};
