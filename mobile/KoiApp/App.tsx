import React, { useEffect } from 'react';
import { StatusBar } from 'expo-status-bar';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { useAuthStore } from './src/stores/authStore';
import { supabase } from './src/services/supabase';
import { LoadingScreen } from './src/components/LoadingScreen';
import { OnboardingScreen } from './src/screens/OnboardingScreen';
import { HomeScreen } from './src/screens/HomeScreen';
import { ConversationScreen } from './src/screens/ConversationScreen';
import { HistoryScreen } from './src/screens/HistoryScreen';
import { SettingsScreen } from './src/screens/SettingsScreen';
import { colors } from './src/theme/colors';

export type RootStackParamList = {
  Onboarding: undefined;
  Home: undefined;
  Conversation: undefined;
  History: { conversationId?: string } | undefined;
  Settings: undefined;
};

const Stack = createNativeStackNavigator<RootStackParamList>();

const navigationTheme = {
  dark: true,
  colors: {
    primary: colors.accent.primary,
    background: colors.bg.primary,
    card: colors.bg.secondary,
    text: colors.text.primary,
    border: colors.surface.border,
    notification: colors.accent.primary,
  },
  fonts: {
    regular: { fontFamily: 'System', fontWeight: '400' as const },
    medium: { fontFamily: 'System', fontWeight: '500' as const },
    bold: { fontFamily: 'System', fontWeight: '700' as const },
    heavy: { fontFamily: 'System', fontWeight: '900' as const },
  },
};

export default function App() {
  const { session, isLoading, isOnboarded, initialize, setSession, fetchProfile } =
    useAuthStore();

  useEffect(() => {
    initialize();

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, newSession) => {
      setSession(newSession);
      if (newSession) {
        fetchProfile();
      }
    });

    return () => {
      subscription.unsubscribe();
    };
  }, []);

  if (isLoading) {
    return (
      <SafeAreaProvider>
        <StatusBar style="light" />
        <LoadingScreen message="Starting Koi..." />
      </SafeAreaProvider>
    );
  }

  const isAuthenticated = !!session;
  const needsOnboarding = !isAuthenticated || !isOnboarded;

  return (
    <SafeAreaProvider>
      <StatusBar style="light" />
      <NavigationContainer theme={navigationTheme}>
        <Stack.Navigator
          screenOptions={{
            headerShown: false,
            animation: 'fade',
            contentStyle: { backgroundColor: colors.bg.primary },
          }}
        >
          {needsOnboarding ? (
            <Stack.Screen name="Onboarding" component={OnboardingScreen} />
          ) : (
            <>
              <Stack.Screen name="Home" component={HomeScreen} />
              <Stack.Screen
                name="Conversation"
                component={ConversationScreen}
                options={{ gestureEnabled: false, animation: 'fade_from_bottom' }}
              />
              <Stack.Screen name="History" component={HistoryScreen} />
              <Stack.Screen name="Settings" component={SettingsScreen} />
            </>
          )}
        </Stack.Navigator>
      </NavigationContainer>
    </SafeAreaProvider>
  );
}
