import React, { useCallback, useEffect, useRef, useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import Animated, { FadeIn, FadeInUp } from 'react-native-reanimated';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import {
  LiveKitRoom,
  useConnectionState,
  useLocalParticipant,
  useVoiceAssistant,
} from '@livekit/react-native';
import { ConnectionState, Track } from 'livekit-client';
import { AudioSession } from '@livekit/react-native';
import { colors } from '../theme/colors';
import { typography } from '../theme/typography';
import { spacing } from '../theme/spacing';
import { haptic } from '../utils/haptics';
import { VoiceOrb } from '../components/VoiceOrb';
import { TranscriptBubble } from '../components/TranscriptBubble';
import { CallControls } from '../components/CallControls';
import { useAuthStore } from '../stores/authStore';
import { createSession, type LiveKitSession, type OrbState } from '../services/livekit';
import type { RootStackParamList } from '../../App';

type Props = NativeStackScreenProps<RootStackParamList, 'Conversation'>;

function mapAgentStateToOrb(
  agentState: string,
  connectionState: ConnectionState,
): OrbState {
  if (connectionState !== ConnectionState.Connected) {
    return 'connecting';
  }
  switch (agentState) {
    case 'speaking':
      return 'speaking';
    case 'listening':
      return 'listening';
    case 'thinking':
      return 'listening';
    case 'initializing':
    case 'connecting':
    case 'pre-connect-buffering':
      return 'connecting';
    case 'disconnected':
    case 'failed':
      return 'error';
    default:
      return 'idle';
  }
}

/** Inner component rendered inside LiveKitRoom context */
function ConversationContent({
  onEndCall,
  companionName,
}: {
  onEndCall: () => void;
  companionName: string;
}) {
  const insets = useSafeAreaInsets();
  const connectionState = useConnectionState();
  const { localParticipant, isMicrophoneEnabled } = useLocalParticipant();
  const voiceAssistant = useVoiceAssistant();

  const [lastTranscript, setLastTranscript] = useState('');
  const [lastTranscriptRole, setLastTranscriptRole] = useState<'user' | 'assistant'>('assistant');

  const orbState = mapAgentStateToOrb(voiceAssistant.state, connectionState);
  const isMuted = !isMicrophoneEnabled;

  // Track agent transcriptions
  useEffect(() => {
    if (voiceAssistant.agentTranscriptions.length > 0) {
      const latest = voiceAssistant.agentTranscriptions[voiceAssistant.agentTranscriptions.length - 1];
      if (latest?.text) {
        setLastTranscript(latest.text);
        setLastTranscriptRole('assistant');
      }
    }
  }, [voiceAssistant.agentTranscriptions]);

  // Haptic on connect
  useEffect(() => {
    if (connectionState === ConnectionState.Connected) {
      haptic.success();
    }
  }, [connectionState]);

  const handleToggleMute = useCallback(() => {
    localParticipant.setMicrophoneEnabled(isMicrophoneEnabled ? false : true);
  }, [localParticipant, isMicrophoneEnabled]);

  const handleEndCall = useCallback(() => {
    haptic.heavy();
    onEndCall();
  }, [onEndCall]);

  const statusLabel =
    orbState === 'speaking'
      ? companionName
      : orbState === 'connecting'
        ? 'Connecting...'
        : orbState === 'listening'
          ? 'Listening...'
          : orbState === 'error'
            ? 'Connection lost. Reconnecting...'
            : 'Ready';

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
        <Text style={styles.roomIndicator}>
          {connectionState === ConnectionState.Connected
            ? 'Connected'
            : connectionState === ConnectionState.Reconnecting
              ? 'Reconnecting'
              : 'Connecting'}
        </Text>
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

export function ConversationScreen({ navigation }: Props) {
  const { profile } = useAuthStore();
  const companionName = profile?.companion_name ?? 'Koi';

  const [session, setSession] = useState<LiveKitSession | null>(null);
  const [sessionError, setSessionError] = useState<string | null>(null);
  const isDisconnecting = useRef(false);

  // Configure audio session and fetch token on mount
  useEffect(() => {
    let cancelled = false;

    async function init() {
      try {
        // Configure iOS audio session for voice call
        await AudioSession.configureAudio({
          android: {
            audioTypeOptions: {
              manageAudioFocus: true,
              audioMode: 'inCommunication',
              audioStreamType: 'voiceCall',
              audioFocusMode: 'gain',
              audioAttributesUsageType: 'voiceCommunication',
              audioAttributesContentType: 'speech',
            },
          },
          ios: {
            defaultOutput: 'speaker',
          },
        });
        await AudioSession.startAudioSession();

        const lkSession = await createSession();
        if (!cancelled) {
          setSession(lkSession);
        }
      } catch (err) {
        if (!cancelled) {
          setSessionError(
            err instanceof Error ? err.message : 'Unable to start conversation. Please try again.',
          );
          haptic.error();
        }
      }
    }

    init();

    return () => {
      cancelled = true;
      isDisconnecting.current = true;
      AudioSession.stopAudioSession();
    };
  }, []);

  const handleEndCall = useCallback(() => {
    isDisconnecting.current = true;
    navigation.goBack();
  }, [navigation]);

  const handleRoomError = useCallback(
    (error: Error) => {
      if (!isDisconnecting.current) {
        setSessionError(error.message);
        haptic.error();
      }
    },
    [],
  );

  const handleDisconnected = useCallback(() => {
    if (!isDisconnecting.current) {
      // Unexpected disconnect -- go back
      haptic.warning();
      navigation.goBack();
    }
  }, [navigation]);

  // Show error state
  if (sessionError && !session) {
    return (
      <View style={[styles.container, styles.centerContent]}>
        <Text style={styles.errorText}>{sessionError}</Text>
        <Pressable
          onPress={() => {
            haptic.light();
            navigation.goBack();
          }}
        >
          <Text style={styles.backText}>Go Back</Text>
        </Pressable>
      </View>
    );
  }

  // Show loading state while getting token
  if (!session) {
    return (
      <View style={[styles.container, styles.centerContent]}>
        <VoiceOrb state="connecting" size={180} />
        <Text style={[styles.companionName, { marginTop: spacing.md }]}>Connecting...</Text>
      </View>
    );
  }

  return (
    <LiveKitRoom
      serverUrl={session.url}
      token={session.token}
      connect={true}
      audio={true}
      video={false}
      onError={handleRoomError}
      onDisconnected={handleDisconnected}
    >
      <ConversationContent
        onEndCall={handleEndCall}
        companionName={companionName}
      />
    </LiveKitRoom>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.bg.primary,
  },
  centerContent: {
    alignItems: 'center',
    justifyContent: 'center',
    gap: spacing.md,
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
  errorText: {
    ...typography.body,
    color: colors.status.error,
    textAlign: 'center',
    paddingHorizontal: spacing.lg,
  },
});
