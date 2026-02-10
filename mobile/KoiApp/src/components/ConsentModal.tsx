import React from 'react';
import { Modal, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { colors } from '../theme/colors';
import { typography } from '../theme/typography';
import { spacing, borderRadius } from '../theme/spacing';
import { haptic } from '../utils/haptics';

interface ConsentModalProps {
  visible: boolean;
  onAccept: () => void;
  onDecline: () => void;
}

export function ConsentModal({ visible, onAccept, onDecline }: ConsentModalProps) {
  const handleAccept = () => {
    haptic.success();
    onAccept();
  };

  const handleDecline = () => {
    haptic.light();
    onDecline();
  };

  return (
    <Modal
      visible={visible}
      transparent
      animationType="fade"
      statusBarTranslucent
    >
      <View style={styles.overlay}>
        <View style={styles.card}>
          <Text style={styles.title}>Before we start</Text>
          <ScrollView
            style={styles.scrollArea}
            showsVerticalScrollIndicator={false}
          >
            <Text style={styles.body}>
              Koi is here to be a good listener and a thoughtful companion. Here is what you should know:
            </Text>

            <Text style={styles.sectionTitle}>Voice Processing</Text>
            <Text style={styles.body}>
              Your voice is processed in real-time to understand what you say. Audio is not stored after the conversation ends.
            </Text>

            <Text style={styles.sectionTitle}>Conversation Memory</Text>
            <Text style={styles.body}>
              Koi remembers key points from your conversations to be a better companion over time. You can delete this data anytime from Settings.
            </Text>

            <Text style={styles.sectionTitle}>Not a Therapist</Text>
            <Text style={styles.body}>
              Koi is an AI companion, not a mental health professional. If you are in crisis, please reach out to a qualified professional or helpline.
            </Text>

            <Text style={styles.sectionTitle}>Your Privacy</Text>
            <Text style={styles.body}>
              Your conversations are private. We use Sarvam AI to process voice and generate responses. You can view and delete your data at any time.
            </Text>
          </ScrollView>

          <View style={styles.actions}>
            <Pressable
              style={({ pressed }) => [
                styles.button,
                styles.declineButton,
                pressed && styles.pressed,
              ]}
              onPress={handleDecline}
            >
              <Text style={styles.declineText}>Not Now</Text>
            </Pressable>
            <Pressable
              style={({ pressed }) => [
                styles.button,
                styles.acceptButton,
                pressed && styles.pressed,
              ]}
              onPress={handleAccept}
            >
              <Text style={styles.acceptText}>I Understand</Text>
            </Pressable>
          </View>
        </View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: colors.surface.overlay,
    justifyContent: 'center',
    alignItems: 'center',
    padding: spacing.lg,
  },
  card: {
    backgroundColor: colors.bg.secondary,
    borderRadius: borderRadius.xl,
    padding: spacing.lg,
    maxHeight: '80%',
    width: '100%',
    borderWidth: 1,
    borderColor: colors.surface.border,
  },
  title: {
    ...typography.h1,
    color: colors.text.primary,
    marginBottom: spacing.md,
    textAlign: 'center',
  },
  scrollArea: {
    marginBottom: spacing.md,
  },
  sectionTitle: {
    ...typography.caption,
    fontWeight: '600',
    color: colors.accent.primary,
    marginTop: spacing.md,
    marginBottom: spacing.xs,
    textTransform: 'uppercase',
    letterSpacing: 1,
  },
  body: {
    ...typography.body,
    color: colors.text.secondary,
    marginBottom: spacing.sm,
  },
  actions: {
    flexDirection: 'row',
    gap: spacing.sm,
  },
  button: {
    flex: 1,
    paddingVertical: spacing.md,
    borderRadius: borderRadius.md,
    alignItems: 'center',
  },
  declineButton: {
    backgroundColor: colors.bg.card,
    borderWidth: 1,
    borderColor: colors.surface.border,
  },
  acceptButton: {
    backgroundColor: colors.accent.primary,
  },
  pressed: {
    opacity: 0.7,
    transform: [{ scale: 0.98 }],
  },
  declineText: {
    ...typography.body,
    fontWeight: '600',
    color: colors.text.secondary,
  },
  acceptText: {
    ...typography.body,
    fontWeight: '600',
    color: colors.text.primary,
  },
});
