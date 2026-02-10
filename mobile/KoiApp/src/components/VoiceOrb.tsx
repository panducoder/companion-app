import React, { useEffect } from 'react';
import { StyleSheet, View } from 'react-native';
import Animated, {
  Easing,
  interpolateColor,
  SharedValue,
  useAnimatedStyle,
  useSharedValue,
  withDelay,
  withRepeat,
  withSequence,
  withTiming,
} from 'react-native-reanimated';
import { colors } from '../theme/colors';
import type { OrbState } from '../services/livekit';

interface VoiceOrbProps {
  state: OrbState;
  size?: number;
}

const ORB_DEFAULT_SIZE = 200;

export function VoiceOrb({ state, size = ORB_DEFAULT_SIZE }: VoiceOrbProps) {
  const scale = useSharedValue(1);
  const opacity = useSharedValue(1);
  const glowOpacity = useSharedValue(0);
  const ring1Scale = useSharedValue(1);
  const ring1Opacity = useSharedValue(0);
  const ring2Scale = useSharedValue(1);
  const ring2Opacity = useSharedValue(0);
  const ring3Scale = useSharedValue(1);
  const ring3Opacity = useSharedValue(0);
  const colorProgress = useSharedValue(0);

  useEffect(() => {
    // Reset all values before transitioning
    scale.value = 1;
    opacity.value = 1;
    glowOpacity.value = 0;
    ring1Scale.value = 1;
    ring1Opacity.value = 0;
    ring2Scale.value = 1;
    ring2Opacity.value = 0;
    ring3Scale.value = 1;
    ring3Opacity.value = 0;

    switch (state) {
      case 'idle':
        // Slow breathing: scale 1.0 -> 1.03 -> 1.0, 4s cycle
        scale.value = withRepeat(
          withSequence(
            withTiming(1.03, { duration: 2000, easing: Easing.inOut(Easing.ease) }),
            withTiming(1.0, { duration: 2000, easing: Easing.inOut(Easing.ease) })
          ),
          -1,
          false
        );
        // Subtle glow pulse
        glowOpacity.value = withRepeat(
          withSequence(
            withTiming(0.3, { duration: 2000, easing: Easing.inOut(Easing.ease) }),
            withTiming(0.1, { duration: 2000, easing: Easing.inOut(Easing.ease) })
          ),
          -1,
          false
        );
        colorProgress.value = 0;
        break;

      case 'connecting':
        // Gentle pulse: scale 1.0 -> 1.05, 1s cycle. Opacity 0.7 -> 0.9
        scale.value = withRepeat(
          withSequence(
            withTiming(1.05, { duration: 500, easing: Easing.inOut(Easing.ease) }),
            withTiming(1.0, { duration: 500, easing: Easing.inOut(Easing.ease) })
          ),
          -1,
          false
        );
        opacity.value = withRepeat(
          withSequence(
            withTiming(0.9, { duration: 500, easing: Easing.inOut(Easing.ease) }),
            withTiming(0.7, { duration: 500, easing: Easing.inOut(Easing.ease) })
          ),
          -1,
          false
        );
        colorProgress.value = withTiming(1, { duration: 300 });
        break;

      case 'listening':
        // Slight breathing: scale 1.0 -> 1.02, 2s cycle
        scale.value = withRepeat(
          withSequence(
            withTiming(1.02, { duration: 1000, easing: Easing.inOut(Easing.ease) }),
            withTiming(1.0, { duration: 1000, easing: Easing.inOut(Easing.ease) })
          ),
          -1,
          false
        );
        // Green glow ring pulsing
        glowOpacity.value = withRepeat(
          withSequence(
            withTiming(0.6, { duration: 1000, easing: Easing.inOut(Easing.ease) }),
            withTiming(0.2, { duration: 1000, easing: Easing.inOut(Easing.ease) })
          ),
          -1,
          false
        );
        colorProgress.value = withTiming(2, { duration: 300 });
        break;

      case 'speaking':
        // Active pulse: scale 1.0 -> 1.15 -> 1.0, ~300ms cycle
        scale.value = withRepeat(
          withSequence(
            withTiming(1.15, { duration: 150, easing: Easing.out(Easing.ease) }),
            withTiming(1.0, { duration: 150, easing: Easing.in(Easing.ease) })
          ),
          -1,
          false
        );
        // Concentric rings expanding outward
        ring1Scale.value = withRepeat(
          withSequence(
            withTiming(1, { duration: 0 }),
            withTiming(1.8, { duration: 1200, easing: Easing.out(Easing.ease) })
          ),
          -1,
          false
        );
        ring1Opacity.value = withRepeat(
          withSequence(
            withTiming(0.5, { duration: 0 }),
            withTiming(0, { duration: 1200, easing: Easing.out(Easing.ease) })
          ),
          -1,
          false
        );
        ring2Scale.value = withRepeat(
          withSequence(
            withTiming(1, { duration: 0 }),
            withDelay(
              400,
              withTiming(1.8, { duration: 1200, easing: Easing.out(Easing.ease) })
            )
          ),
          -1,
          false
        );
        ring2Opacity.value = withRepeat(
          withSequence(
            withTiming(0, { duration: 400 }),
            withTiming(0.4, { duration: 0 }),
            withTiming(0, { duration: 1200, easing: Easing.out(Easing.ease) })
          ),
          -1,
          false
        );
        ring3Scale.value = withRepeat(
          withSequence(
            withTiming(1, { duration: 0 }),
            withDelay(
              800,
              withTiming(1.8, { duration: 1200, easing: Easing.out(Easing.ease) })
            )
          ),
          -1,
          false
        );
        ring3Opacity.value = withRepeat(
          withSequence(
            withTiming(0, { duration: 800 }),
            withTiming(0.3, { duration: 0 }),
            withTiming(0, { duration: 1200, easing: Easing.out(Easing.ease) })
          ),
          -1,
          false
        );
        glowOpacity.value = withRepeat(
          withSequence(
            withTiming(0.7, { duration: 150, easing: Easing.out(Easing.ease) }),
            withTiming(0.3, { duration: 150, easing: Easing.in(Easing.ease) })
          ),
          -1,
          false
        );
        colorProgress.value = withTiming(3, { duration: 300 });
        break;

      case 'error':
        // Scale to 0.95, single pulse then static
        scale.value = withSequence(
          withTiming(0.9, { duration: 200, easing: Easing.out(Easing.ease) }),
          withTiming(0.95, { duration: 300, easing: Easing.inOut(Easing.ease) })
        );
        glowOpacity.value = withSequence(
          withTiming(0.8, { duration: 200 }),
          withTiming(0.4, { duration: 500 })
        );
        colorProgress.value = withTiming(4, { duration: 200 });
        break;
    }
  }, [state]);

  const orbStyle = useAnimatedStyle(() => {
    const bgColor = interpolateColor(
      colorProgress.value,
      [0, 1, 2, 3, 4],
      [
        colors.accent.primary,     // idle: purple
        colors.status.connecting,  // connecting: amber
        colors.status.listening,   // listening: green
        colors.status.speaking,    // speaking: light purple
        colors.status.error,       // error: red
      ]
    );

    return {
      transform: [{ scale: scale.value }],
      opacity: opacity.value,
      backgroundColor: bgColor,
    };
  });

  const glowStyle = useAnimatedStyle(() => {
    const glowColor = interpolateColor(
      colorProgress.value,
      [0, 1, 2, 3, 4],
      [
        colors.accent.primary,
        colors.status.connecting,
        colors.status.listening,
        colors.status.speaking,
        colors.status.error,
      ]
    );

    return {
      opacity: glowOpacity.value,
      shadowColor: glowColor,
      backgroundColor: glowColor,
    };
  });

  const makeRingStyle = (ringScale: SharedValue<number>, ringOpacity: SharedValue<number>) =>
    useAnimatedStyle(() => {
      const ringColor = interpolateColor(
        colorProgress.value,
        [0, 1, 2, 3, 4],
        [
          colors.accent.primary,
          colors.status.connecting,
          colors.status.listening,
          colors.status.speaking,
          colors.status.error,
        ]
      );

      return {
        transform: [{ scale: ringScale.value }],
        opacity: ringOpacity.value,
        borderColor: ringColor,
      };
    });

  const ring1AnimStyle = makeRingStyle(ring1Scale, ring1Opacity);
  const ring2AnimStyle = makeRingStyle(ring2Scale, ring2Opacity);
  const ring3AnimStyle = makeRingStyle(ring3Scale, ring3Opacity);

  const halfSize = size / 2;

  return (
    <View style={[styles.container, { width: size * 2, height: size * 2 }]}>
      {/* Expanding rings (visible during speaking) */}
      <Animated.View
        style={[
          styles.ring,
          ring1AnimStyle,
          {
            width: size,
            height: size,
            borderRadius: halfSize,
            top: halfSize,
            left: halfSize,
          },
        ]}
      />
      <Animated.View
        style={[
          styles.ring,
          ring2AnimStyle,
          {
            width: size,
            height: size,
            borderRadius: halfSize,
            top: halfSize,
            left: halfSize,
          },
        ]}
      />
      <Animated.View
        style={[
          styles.ring,
          ring3AnimStyle,
          {
            width: size,
            height: size,
            borderRadius: halfSize,
            top: halfSize,
            left: halfSize,
          },
        ]}
      />

      {/* Glow layer */}
      <Animated.View
        style={[
          styles.glow,
          glowStyle,
          {
            width: size * 1.4,
            height: size * 1.4,
            borderRadius: (size * 1.4) / 2,
            top: halfSize - size * 0.2,
            left: halfSize - size * 0.2,
          },
        ]}
      />

      {/* Core orb */}
      <Animated.View
        style={[
          styles.orb,
          orbStyle,
          {
            width: size,
            height: size,
            borderRadius: halfSize,
            top: halfSize,
            left: halfSize,
          },
        ]}
      />

      {/* Inner highlight */}
      <View
        style={[
          styles.highlight,
          {
            width: size * 0.6,
            height: size * 0.6,
            borderRadius: (size * 0.6) / 2,
            top: halfSize + size * 0.1,
            left: halfSize + size * 0.15,
          },
        ]}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    alignItems: 'center',
    justifyContent: 'center',
    position: 'relative',
  },
  orb: {
    position: 'absolute',
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.6,
    shadowRadius: 30,
    elevation: 20,
  },
  glow: {
    position: 'absolute',
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.5,
    shadowRadius: 40,
    elevation: 10,
  },
  ring: {
    position: 'absolute',
    borderWidth: 2,
    borderColor: 'transparent',
    backgroundColor: 'transparent',
  },
  highlight: {
    position: 'absolute',
    backgroundColor: 'rgba(255,255,255,0.08)',
  },
});
