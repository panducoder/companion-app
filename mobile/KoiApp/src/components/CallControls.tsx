import React from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { colors } from '../theme/colors';
import { typography } from '../theme/typography';
import { spacing, borderRadius } from '../theme/spacing';
import { haptic } from '../utils/haptics';

interface CallControlsProps {
  isMuted: boolean;
  onToggleMute: () => void;
  onEndCall: () => void;
}

export function CallControls({
  isMuted,
  onToggleMute,
  onEndCall,
}: CallControlsProps) {
  const handleMutePress = () => {
    haptic.light();
    onToggleMute();
  };

  const handleEndPress = () => {
    haptic.heavy();
    onEndCall();
  };

  return (
    <View style={styles.container}>
      <Pressable
        style={({ pressed }) => [
          styles.button,
          styles.muteButton,
          isMuted && styles.mutedButton,
          pressed && styles.pressed,
        ]}
        onPress={handleMutePress}
        accessibilityLabel={isMuted ? 'Unmute microphone' : 'Mute microphone'}
        accessibilityRole="button"
      >
        <Text style={styles.buttonIcon}>{isMuted ? '🔇' : '🎤'}</Text>
        <Text style={[styles.buttonLabel, isMuted && styles.mutedLabel]}>
          {isMuted ? 'Unmute' : 'Mute'}
        </Text>
      </Pressable>

      <Pressable
        style={({ pressed }) => [
          styles.button,
          styles.endButton,
          pressed && styles.pressed,
        ]}
        onPress={handleEndPress}
        accessibilityLabel="End call"
        accessibilityRole="button"
      >
        <Text style={styles.buttonIcon}>📞</Text>
        <Text style={[styles.buttonLabel, styles.endLabel]}>End</Text>
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    gap: spacing.xl,
    paddingVertical: spacing.lg,
    paddingHorizontal: spacing.md,
  },
  button: {
    width: 72,
    height: 72,
    borderRadius: borderRadius.full,
    alignItems: 'center',
    justifyContent: 'center',
    gap: 4,
  },
  muteButton: {
    backgroundColor: colors.bg.card,
    borderWidth: 1,
    borderColor: colors.surface.border,
  },
  mutedButton: {
    backgroundColor: 'rgba(239, 68, 68, 0.15)',
    borderColor: 'rgba(239, 68, 68, 0.3)',
  },
  endButton: {
    backgroundColor: colors.status.error,
  },
  pressed: {
    opacity: 0.7,
    transform: [{ scale: 0.95 }],
  },
  buttonIcon: {
    fontSize: 24,
  },
  buttonLabel: {
    ...typography.small,
    color: colors.text.secondary,
  },
  mutedLabel: {
    color: colors.status.error,
  },
  endLabel: {
    color: colors.text.primary,
  },
});
