import React, { useCallback, useEffect, useState } from 'react';
import {
  FlatList,
  Pressable,
  RefreshControl,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import Animated, { FadeIn, FadeInDown } from 'react-native-reanimated';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import { colors } from '../theme/colors';
import { typography } from '../theme/typography';
import { spacing, borderRadius } from '../theme/spacing';
import { haptic } from '../utils/haptics';
import { requestMicrophonePermission } from '../utils/permissions';
import { VoiceOrb } from '../components/VoiceOrb';
import { ConsentModal } from '../components/ConsentModal';
import { useAuthStore } from '../stores/authStore';
import { useSettingsStore } from '../stores/settingsStore';
import { api, Conversation } from '../services/api';
import type { RootStackParamList } from '../../App';

type Props = NativeStackScreenProps<RootStackParamList, 'Home'>;

function getGreeting(): string {
  const hour = new Date().getHours();
  if (hour < 5) return 'Late night?';
  if (hour < 12) return 'Good morning';
  if (hour < 17) return 'Good afternoon';
  if (hour < 21) return 'Good evening';
  return 'Hey there';
}

function formatDuration(seconds: number | null): string {
  if (!seconds) return '';
  const mins = Math.floor(seconds / 60);
  if (mins < 1) return 'Less than a minute';
  if (mins === 1) return '1 minute';
  return `${mins} minutes`;
}

function formatDate(dateStr: string): string {
  const date = new Date(dateStr);
  const now = new Date();
  const diffDays = Math.floor(
    (now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24)
  );

  if (diffDays === 0) return 'Today';
  if (diffDays === 1) return 'Yesterday';
  if (diffDays < 7) return `${diffDays} days ago`;
  return date.toLocaleDateString('en-IN', { month: 'short', day: 'numeric' });
}

export function HomeScreen({ navigation }: Props) {
  const insets = useSafeAreaInsets();
  const { profile } = useAuthStore();
  const { hasConsented, setConsented } = useSettingsStore();
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [showConsent, setShowConsent] = useState(false);

  const userName = profile?.name ?? 'there';
  const companionName = profile?.companion_name ?? 'Koi';

  const loadConversations = useCallback(async () => {
    try {
      const data = await api.getConversations(10);
      setConversations(data);
    } catch {
      // Silently fail - conversations are not critical
    }
  }, []);

  const onRefresh = useCallback(async () => {
    setIsRefreshing(true);
    await loadConversations();
    setIsRefreshing(false);
  }, [loadConversations]);

  useEffect(() => {
    loadConversations();
  }, [loadConversations]);

  const handleStartTalking = async () => {
    haptic.medium();

    if (!hasConsented) {
      setShowConsent(true);
      return;
    }

    const granted = await requestMicrophonePermission();
    if (granted) {
      navigation.navigate('Conversation');
    }
  };

  const handleConsentAccept = async () => {
    setConsented(true);
    setShowConsent(false);
    const granted = await requestMicrophonePermission();
    if (granted) {
      navigation.navigate('Conversation');
    }
  };

  const handleConsentDecline = () => {
    setShowConsent(false);
  };

  const renderConversation = ({ item, index }: { item: Conversation; index: number }) => (
    <Animated.View entering={FadeInDown.delay(index * 80).duration(300)}>
      <Pressable
        style={({ pressed }) => [
          styles.conversationCard,
          pressed && styles.cardPressed,
        ]}
        onPress={() => {
          haptic.light();
          navigation.navigate('History', { conversationId: item.id });
        }}
      >
        <View style={styles.cardLeft}>
          <Text style={styles.cardDate}>{formatDate(item.started_at)}</Text>
          {item.summary && (
            <Text style={styles.cardSummary} numberOfLines={1}>
              {item.summary}
            </Text>
          )}
        </View>
        {item.duration_seconds != null && item.duration_seconds > 0 && (
          <Text style={styles.cardDuration}>
            {formatDuration(item.duration_seconds)}
          </Text>
        )}
      </Pressable>
    </Animated.View>
  );

  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      <ConsentModal
        visible={showConsent}
        onAccept={handleConsentAccept}
        onDecline={handleConsentDecline}
      />

      {/* Header */}
      <View style={styles.header}>
        <Animated.Text
          entering={FadeIn.duration(600)}
          style={styles.greeting}
        >
          {getGreeting()}, {userName}
        </Animated.Text>
        <Pressable
          style={({ pressed }) => [
            styles.settingsButton,
            pressed && styles.settingsPressed,
          ]}
          onPress={() => {
            haptic.light();
            navigation.navigate('Settings');
          }}
          accessibilityLabel="Settings"
        >
          <Text style={styles.settingsIcon}>&#x2699;</Text>
        </Pressable>
      </View>

      {/* Center area with Orb */}
      <View style={styles.orbSection}>
        <Animated.View entering={FadeIn.delay(200).duration(800)}>
          <VoiceOrb state="idle" size={180} />
        </Animated.View>
        <Text style={styles.companionName}>{companionName}</Text>
        <Text style={styles.statusText}>Ready to talk</Text>

        <Pressable
          style={({ pressed }) => [
            styles.talkButton,
            pressed && styles.pressed,
          ]}
          onPress={handleStartTalking}
        >
          <LinearGradient
            colors={[...colors.accent.gradient]}
            start={{ x: 0, y: 0 }}
            end={{ x: 1, y: 0 }}
            style={styles.talkGradient}
          >
            <Text style={styles.talkButtonText}>Start Talking</Text>
          </LinearGradient>
        </Pressable>
      </View>

      {/* Recent conversations */}
      {conversations.length > 0 && (
        <View style={styles.recentSection}>
          <Text style={styles.recentTitle}>Recent</Text>
          <FlatList
            data={conversations}
            keyExtractor={(item) => item.id}
            renderItem={renderConversation}
            refreshControl={
              <RefreshControl
                refreshing={isRefreshing}
                onRefresh={onRefresh}
                tintColor={colors.accent.primary}
              />
            }
            showsVerticalScrollIndicator={false}
            contentContainerStyle={styles.listContent}
          />
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.bg.primary,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.md,
  },
  greeting: {
    ...typography.h2,
    color: colors.text.primary,
  },
  settingsButton: {
    width: 40,
    height: 40,
    borderRadius: borderRadius.full,
    backgroundColor: colors.bg.card,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: colors.surface.border,
  },
  settingsPressed: {
    opacity: 0.7,
  },
  settingsIcon: {
    fontSize: 20,
    color: colors.text.secondary,
  },
  orbSection: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: spacing.lg,
    gap: spacing.md,
  },
  companionName: {
    ...typography.h1,
    color: colors.text.primary,
    marginTop: -spacing.lg,
  },
  statusText: {
    ...typography.caption,
    color: colors.text.secondary,
    marginTop: -spacing.sm,
  },
  talkButton: {
    borderRadius: borderRadius.xl,
    overflow: 'hidden',
    marginTop: spacing.md,
  },
  talkGradient: {
    paddingVertical: spacing.md,
    paddingHorizontal: spacing.xxl,
    borderRadius: borderRadius.xl,
  },
  talkButtonText: {
    ...typography.body,
    fontWeight: '700',
    color: colors.text.primary,
  },
  pressed: {
    opacity: 0.8,
    transform: [{ scale: 0.97 }],
  },
  recentSection: {
    maxHeight: '30%',
    paddingHorizontal: spacing.lg,
    paddingBottom: spacing.md,
  },
  recentTitle: {
    ...typography.caption,
    fontWeight: '600',
    color: colors.text.muted,
    textTransform: 'uppercase',
    letterSpacing: 1,
    marginBottom: spacing.sm,
  },
  listContent: {
    gap: spacing.sm,
  },
  conversationCard: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: colors.bg.card,
    borderRadius: borderRadius.md,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    borderWidth: 1,
    borderColor: colors.surface.border,
  },
  cardPressed: {
    opacity: 0.7,
  },
  cardLeft: {
    flex: 1,
    gap: 2,
  },
  cardDate: {
    ...typography.caption,
    color: colors.text.secondary,
    fontWeight: '500',
  },
  cardSummary: {
    ...typography.small,
    color: colors.text.muted,
  },
  cardDuration: {
    ...typography.small,
    color: colors.text.muted,
    marginLeft: spacing.sm,
  },
});
