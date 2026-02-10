import React, { useEffect, useState } from 'react';
import {
  ActivityIndicator,
  FlatList,
  Pressable,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import Animated, { FadeInDown } from 'react-native-reanimated';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import { colors } from '../theme/colors';
import { typography } from '../theme/typography';
import { spacing, borderRadius } from '../theme/spacing';
import { haptic } from '../utils/haptics';
import { api, Conversation, Message } from '../services/api';
import type { RootStackParamList } from '../../App';

type Props = NativeStackScreenProps<RootStackParamList, 'History'>;

export function HistoryScreen({ navigation, route }: Props) {
  const insets = useSafeAreaInsets();
  const { conversationId } = route.params ?? {};

  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [selectedConvo, setSelectedConvo] = useState<string | null>(conversationId ?? null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isLoadingMessages, setIsLoadingMessages] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadConversations();
  }, []);

  useEffect(() => {
    if (selectedConvo) {
      loadMessages(selectedConvo);
    }
  }, [selectedConvo]);

  const loadConversations = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const data = await api.getConversations();
      setConversations(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load conversations');
    } finally {
      setIsLoading(false);
    }
  };

  const loadMessages = async (convoId: string) => {
    try {
      setIsLoadingMessages(true);
      const data = await api.getMessages(convoId);
      setMessages(data);
    } catch {
      // Keep whatever messages we had
    } finally {
      setIsLoadingMessages(false);
    }
  };

  const formatTime = (dateStr: string) => {
    return new Date(dateStr).toLocaleTimeString('en-IN', {
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const formatConvoDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-IN', {
      weekday: 'short',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  if (selectedConvo) {
    return (
      <View style={[styles.container, { paddingTop: insets.top, paddingBottom: insets.bottom }]}>
        <View style={styles.header}>
          <Pressable
            onPress={() => {
              haptic.light();
              setSelectedConvo(null);
              setMessages([]);
            }}
            hitSlop={16}
          >
            <Text style={styles.backText}>All Conversations</Text>
          </Pressable>
        </View>

        {isLoadingMessages ? (
          <View style={styles.centerContent}>
            <ActivityIndicator color={colors.accent.primary} size="large" />
          </View>
        ) : messages.length === 0 ? (
          <View style={styles.centerContent}>
            <Text style={styles.emptyText}>No messages in this conversation</Text>
          </View>
        ) : (
          <FlatList
            data={messages}
            keyExtractor={(item) => item.id}
            renderItem={({ item, index }) => (
              <Animated.View
                entering={FadeInDown.delay(index * 50).duration(200)}
                style={[
                  styles.messageRow,
                  item.role === 'user' ? styles.userRow : styles.assistantRow,
                ]}
              >
                <View
                  style={[
                    styles.messageBubble,
                    item.role === 'user' ? styles.userBubble : styles.assistantBubble,
                  ]}
                >
                  <Text style={styles.messageText}>{item.content}</Text>
                  <Text style={styles.messageTime}>{formatTime(item.created_at)}</Text>
                </View>
              </Animated.View>
            )}
            contentContainerStyle={styles.messageList}
            showsVerticalScrollIndicator={false}
          />
        )}
      </View>
    );
  }

  return (
    <View style={[styles.container, { paddingTop: insets.top, paddingBottom: insets.bottom }]}>
      <View style={styles.header}>
        <Pressable
          onPress={() => {
            haptic.light();
            navigation.goBack();
          }}
          hitSlop={16}
        >
          <Text style={styles.backText}>Back</Text>
        </Pressable>
        <Text style={styles.headerTitle}>Conversations</Text>
        <View style={{ width: 60 }} />
      </View>

      {isLoading ? (
        <View style={styles.centerContent}>
          <ActivityIndicator color={colors.accent.primary} size="large" />
        </View>
      ) : error ? (
        <View style={styles.centerContent}>
          <Text style={styles.errorText}>{error}</Text>
          <Pressable
            style={styles.retryButton}
            onPress={() => {
              haptic.light();
              loadConversations();
            }}
          >
            <Text style={styles.retryText}>Try Again</Text>
          </Pressable>
        </View>
      ) : conversations.length === 0 ? (
        <View style={styles.centerContent}>
          <Text style={styles.emptyTitle}>No conversations yet</Text>
          <Text style={styles.emptyText}>
            Start a conversation with Koi and it will appear here
          </Text>
        </View>
      ) : (
        <FlatList
          data={conversations}
          keyExtractor={(item) => item.id}
          renderItem={({ item, index }) => (
            <Animated.View entering={FadeInDown.delay(index * 60).duration(300)}>
              <Pressable
                style={({ pressed }) => [
                  styles.convoCard,
                  pressed && styles.cardPressed,
                ]}
                onPress={() => {
                  haptic.light();
                  setSelectedConvo(item.id);
                }}
              >
                <Text style={styles.convoDate}>
                  {formatConvoDate(item.started_at)}
                </Text>
                {item.summary && (
                  <Text style={styles.convoSummary} numberOfLines={2}>
                    {item.summary}
                  </Text>
                )}
                <View style={styles.convoMeta}>
                  {item.duration_seconds != null && item.duration_seconds > 0 && (
                    <Text style={styles.convoMetaText}>
                      {Math.floor(item.duration_seconds / 60)} min
                    </Text>
                  )}
                  {item.emotional_tone && (
                    <Text style={styles.convoMetaText}>{item.emotional_tone}</Text>
                  )}
                </View>
              </Pressable>
            </Animated.View>
          )}
          contentContainerStyle={styles.listContent}
          showsVerticalScrollIndicator={false}
        />
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
  backText: {
    ...typography.caption,
    color: colors.accent.secondary,
  },
  headerTitle: {
    ...typography.h2,
    color: colors.text.primary,
  },
  centerContent: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: spacing.xl,
    gap: spacing.md,
  },
  emptyTitle: {
    ...typography.h2,
    color: colors.text.primary,
  },
  emptyText: {
    ...typography.body,
    color: colors.text.muted,
    textAlign: 'center',
  },
  errorText: {
    ...typography.body,
    color: colors.status.error,
    textAlign: 'center',
  },
  retryButton: {
    paddingVertical: spacing.sm,
    paddingHorizontal: spacing.lg,
    borderRadius: borderRadius.md,
    backgroundColor: colors.bg.card,
    borderWidth: 1,
    borderColor: colors.surface.border,
  },
  retryText: {
    ...typography.caption,
    color: colors.accent.primary,
    fontWeight: '600',
  },
  listContent: {
    padding: spacing.lg,
    gap: spacing.sm,
  },
  convoCard: {
    backgroundColor: colors.bg.card,
    borderRadius: borderRadius.md,
    padding: spacing.md,
    borderWidth: 1,
    borderColor: colors.surface.border,
    gap: spacing.xs,
  },
  cardPressed: {
    opacity: 0.7,
  },
  convoDate: {
    ...typography.caption,
    color: colors.text.secondary,
    fontWeight: '500',
  },
  convoSummary: {
    ...typography.body,
    color: colors.text.primary,
  },
  convoMeta: {
    flexDirection: 'row',
    gap: spacing.sm,
    marginTop: spacing.xs,
  },
  convoMetaText: {
    ...typography.small,
    color: colors.text.muted,
  },
  messageList: {
    padding: spacing.md,
    gap: spacing.sm,
  },
  messageRow: {
    marginBottom: spacing.sm,
  },
  userRow: {
    alignItems: 'flex-end',
  },
  assistantRow: {
    alignItems: 'flex-start',
  },
  messageBubble: {
    maxWidth: '85%',
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    borderRadius: borderRadius.lg,
  },
  userBubble: {
    backgroundColor: 'rgba(52, 211, 153, 0.12)',
    borderWidth: 1,
    borderColor: 'rgba(52, 211, 153, 0.2)',
  },
  assistantBubble: {
    backgroundColor: 'rgba(124, 92, 252, 0.12)',
    borderWidth: 1,
    borderColor: 'rgba(124, 92, 252, 0.2)',
  },
  messageText: {
    ...typography.body,
    color: colors.text.primary,
  },
  messageTime: {
    ...typography.small,
    color: colors.text.muted,
    marginTop: spacing.xs,
    alignSelf: 'flex-end',
  },
});
