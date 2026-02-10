import React, { useCallback, useEffect, useRef, useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import Animated, { FadeIn, FadeInUp } from 'react-native-reanimated';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import { colors } from '../theme/colors';
import { typography } from '../theme/typography';
import { spacing } from '../theme/spacing';
import { haptic } from '../utils/haptics';
import { configureAudioSession } from '../utils/permissions';
import { VoiceOrb } from '../components/VoiceOrb';
import { TranscriptBubble } from '../components/TranscriptBubble';
import { CallControls } from '../components/CallControls';
import { useAuthStore } from '../stores/authStore';
import { createSession, type OrbState } from '../services/livekit';
import type { RootStackParamList } from '../../App';

type Props = NativeStackScreenProps<RootStackParamList, 'Conversation'>;

const STATUS_LABELS: Record<OrbState, string> = {
  idle: 'Ready',
  connecting: 'Connecting...',
  listening: 'Listening...',
  speaking: '',
  error: 'Connection lost. Reconnecting...',
};

export function ConversationScreen({ navigation }: Props) {
  const insets = useSafeAreaInsets();
  const { profile } = useAuthStore();
  const companionName = profile?.companion_name ?? 'Koi';

  const [orbState, setOrbState] = useState<OrbState>('connecting');
  const [isMuted, setIsMuted] = useState(false);
  const [lastTranscript, setLastTranscript] = useState('');
  const [lastTranscriptRole, setLastTranscriptRole] = useState<'user' | 'assistant'>('assistant');
  const [sessionInfo, setSessionInfo] = useState<{
    token: string;
    url: string;
    roomName: string;
    conversationId: string;
  } | null>(null);

  const isDisconnecting = useRef(false);

  const connectToRoom = useCallback(async () => {
    try {
      setOrbState('connecting');
      await configureAudioSession();

      const session = await createSession();
      setSessionInfo(session);

      // In a real integration, here we would connect to the LiveKit room
      // using the LiveKitRoom component. For now, we simulate the flow:
      // After getting the token, transition to listening state.
      haptic.success();
      setOrbState('listening');

      // Simulated agent join after a delay
      // In production, this is driven by LiveKit participant events
      setTimeout(() => {
        if (!isDisconnecting.current) {
          setOrbState('speaking');
          setLastTranscript(`Hey! Good to hear from you.`);
          setLastTranscriptRole('assistant');

          setTimeout(() => {
            if (!isDisconnecting.current) {
              setOrbState('listening');
            }
          }, 3000);
        }
      }, 2000);
    } catch (err) {
      haptic.error();
      setOrbState('error');

      // Retry after 3 seconds
      setTimeout(() => {
        if (!isDisconnecting.current) {
          connectToRoom();
        }
      }, 3000);
    }
  }, []);

  useEffect(() => {
    connectToRoom();

    return () => {
      isDisconnecting.current = true;
    };
  }, [connectToRoom]);

  const handleToggleMute = () => {
    setIsMuted((prev) => !prev);
    // In production: toggle microphone track publication
    // room.localParticipant.setMicrophoneEnabled(!isMuted);
  };

  const handleEndCall = () => {
    isDisconnecting.current = true;
    haptic.heavy();
    // In production: disconnect from LiveKit room, end conversation in DB
    navigation.goBack();
  };

  const statusLabel = orbState === 'speaking' ? companionName : STATUS_LABELS[orbState];

  return (
    <View style={[styles.container, { paddingTop: insets.top, paddingBottom: insets.bottom }]}>
      {/* Top bar */}
      <View style={styles.topBar}>
        <Pressable
          onPress={() => {
            haptic.light();
            handleEndCall();
          }}
          hitSlop={16}
        >
          <Text style={styles.backText}>Back</Text>
        </Pressable>
        {sessionInfo && (
          <Text style={styles.roomIndicator}>
            {orbState === 'error' ? 'Reconnecting' : 'Connected'}
          </Text>
        )}
      </View>

      {/* Center orb area */}
      <View style={styles.orbArea}>
        <Animated.View entering={FadeIn.duration(600)}>
          <VoiceOrb state={orbState} size={220} />
        </Animated.View>

        <Animated.View entering={FadeInUp.delay(300).duration(400)} style={styles.statusArea}>
          <Text style={styles.companionName}>{statusLabel}</Text>
          {orbState === 'listening' && !isMuted && (
            <Text style={styles.hint}>Say anything, I'm here</Text>
          )}
          {isMuted && (
            <Text style={[styles.hint, { color: colors.status.error }]}>Microphone is muted</Text>
          )}
        </Animated.View>
      </View>

      {/* Transcript bubble */}
      <View style={styles.transcriptArea}>
        <TranscriptBubble
          text={lastTranscript}
          role={lastTranscriptRole}
          fadeAfterMs={5000}
        />
      </View>

      {/* Call controls */}
      <CallControls
        isMuted={isMuted}
        onToggleMute={handleToggleMute}
        onEndCall={handleEndCall}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.bg.primary,
  },
  topBar: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.sm,
  },
  backText: {
    ...typography.caption,
    color: colors.text.secondary,
  },
  roomIndicator: {
    ...typography.small,
    color: colors.status.listening,
  },
  orbArea: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    gap: spacing.md,
  },
  statusArea: {
    alignItems: 'center',
    marginTop: -spacing.lg,
    gap: spacing.xs,
  },
  companionName: {
    ...typography.h2,
    color: colors.text.primary,
  },
  hint: {
    ...typography.caption,
    color: colors.text.muted,
  },
  transcriptArea: {
    minHeight: 80,
    justifyContent: 'flex-end',
    paddingBottom: spacing.sm,
  },
});
