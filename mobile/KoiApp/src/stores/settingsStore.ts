import { create } from 'zustand';
import { createJSONStorage, persist } from 'zustand/middleware';
import AsyncStorage from '@react-native-async-storage/async-storage';

interface SettingsState {
  hasConsented: boolean;
  language: string;
  voiceId: string;
  hapticEnabled: boolean;
  notificationsEnabled: boolean;

  setConsented: (value: boolean) => void;
  setLanguage: (lang: string) => void;
  setVoiceId: (id: string) => void;
  setHapticEnabled: (value: boolean) => void;
  setNotificationsEnabled: (value: boolean) => void;
  resetSettings: () => void;
}

const defaultSettings = {
  hasConsented: false,
  language: 'hi-IN',
  voiceId: 'meera',
  hapticEnabled: true,
  notificationsEnabled: true,
};

export const useSettingsStore = create<SettingsState>()(
  persist(
    (set) => ({
      ...defaultSettings,

      setConsented: (value) => set({ hasConsented: value }),
      setLanguage: (lang) => set({ language: lang }),
      setVoiceId: (id) => set({ voiceId: id }),
      setHapticEnabled: (value) => set({ hapticEnabled: value }),
      setNotificationsEnabled: (value) => set({ notificationsEnabled: value }),
      resetSettings: () => set(defaultSettings),
    }),
    {
      name: 'koi-settings',
      storage: createJSONStorage(() => AsyncStorage),
    }
  )
);
