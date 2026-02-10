import React, { useEffect } from 'react';
import { StyleSheet, Text, View } from 'react-native';
import Animated, {
  Easing,
  useAnimatedStyle,
  useSharedValue,
  withDelay,
  withSequence,
  withTiming,
} from 'react-native-reanimated';
import { colors } from '../theme/colors';
import { typography } from '../theme/typography';
import { spacing, borderRadius } from '../theme/spacing';

interface TranscriptBubbleProps {
  text: string;
  role: 'user' | 'assistant';
  /** Auto-fade after this many ms (default 5000). Set 0 to disable. */
  fadeAfterMs?: number;
}

export function TranscriptBubble({
  text,
  role,
  fadeAfterMs = 5000,
}: TranscriptBubbleProps) {
  const opacity = useSharedValue(0);

  useEffect(() => {
    if (!text) {
      opacity.value = 0;
      return;
    }

    if (fadeAfterMs > 0) {
      opacity.value = withSequence(
        withTiming(1, { duration: 200, easing: Easing.out(Easing.ease) }),
        withDelay(
          fadeAfterMs,
          withTiming(0, { duration: 600, easing: Easing.in(Easing.ease) })
        )
      );
    } else {
      opacity.value = withTiming(1, { duration: 200, easing: Easing.out(Easing.ease) });
    }
  }, [text, fadeAfterMs]);

  const animatedStyle = useAnimatedStyle(() => ({
    opacity: opacity.value,
  }));

  if (!text) return null;

  const isUser = role === 'user';

  return (
    <Animated.View
      style={[
        styles.container,
        isUser ? styles.userContainer : styles.assistantContainer,
        animatedStyle,
      ]}
    >
      <View
        style={[
          styles.bubble,
          isUser ? styles.userBubble : styles.assistantBubble,
        ]}
      >
        <Text
          style={[
            styles.label,
            { color: isUser ? colors.status.listening : colors.accent.primary },
          ]}
        >
          {isUser ? 'You' : 'Koi'}
        </Text>
        <Text style={styles.text}>{text}</Text>
      </View>
    </Animated.View>
  );
}

const styles = StyleSheet.create({
  container: {
    paddingHorizontal: spacing.md,
    marginBottom: spacing.sm,
  },
  userContainer: {
    alignItems: 'flex-end',
  },
  assistantContainer: {
    alignItems: 'flex-start',
  },
  bubble: {
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
  label: {
    ...typography.small,
    fontWeight: '600',
    marginBottom: 2,
  },
  text: {
    ...typography.body,
    color: colors.text.primary,
  },
});
