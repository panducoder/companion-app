import { create } from 'zustand';
import { Session, User } from '@supabase/supabase-js';
import { supabase } from '../services/supabase';

export interface UserProfile {
  id: string;
  name: string | null;
  companion_name: string;
  phone: string | null;
  relationship_stage: string;
  subscription_status: string;
  created_at: string;
  last_active_at: string | null;
}

interface AuthState {
  session: Session | null;
  user: User | null;
  profile: UserProfile | null;
  isLoading: boolean;
  isOnboarded: boolean;
  error: string | null;

  initialize: () => Promise<void>;
  setSession: (session: Session | null) => void;
  fetchProfile: () => Promise<void>;
  updateProfile: (updates: Partial<UserProfile>) => Promise<void>;
  signOut: () => Promise<void>;
  clearError: () => void;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  session: null,
  user: null,
  profile: null,
  isLoading: true,
  isOnboarded: false,
  error: null,

  initialize: async () => {
    try {
      set({ isLoading: true, error: null });
      const { data: { session } } = await supabase.auth.getSession();

      if (session) {
        set({ session, user: session.user });
        await get().fetchProfile();
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to initialize';
      set({ error: message });
    } finally {
      set({ isLoading: false });
    }
  },

  setSession: (session) => {
    set({
      session,
      user: session?.user ?? null,
      isOnboarded: false,
    });
  },

  fetchProfile: async () => {
    const { user } = get();
    if (!user) return;

    try {
      const { data, error } = await supabase
        .from('profiles')
        .select('*')
        .eq('id', user.id)
        .single();

      if (error) throw error;

      const profile = data as UserProfile;
      set({
        profile,
        isOnboarded: !!profile.name,
      });
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to fetch profile';
      set({ error: message });
    }
  },

  updateProfile: async (updates) => {
    const { user } = get();
    if (!user) return;

    try {
      set({ error: null });
      const { data, error } = await supabase
        .from('profiles')
        .update(updates)
        .eq('id', user.id)
        .select()
        .single();

      if (error) throw error;

      set({
        profile: data as UserProfile,
        isOnboarded: !!(data as UserProfile).name,
      });
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to update profile';
      set({ error: message });
      throw err;
    }
  },

  signOut: async () => {
    try {
      set({ isLoading: true });
      await supabase.auth.signOut();
      set({
        session: null,
        user: null,
        profile: null,
        isOnboarded: false,
        isLoading: false,
      });
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to sign out';
      set({ error: message, isLoading: false });
    }
  },

  clearError: () => set({ error: null }),
}));
