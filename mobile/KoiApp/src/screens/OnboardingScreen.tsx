import React, { useRef, useState } from 'react';
import {
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import Animated, {
  Easing,
  FadeIn,
  FadeInDown,
  FadeOut,
} from 'react-native-reanimated';
import { LinearGradient } from 'expo-linear-gradient';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import { colors } from '../theme/colors';
import { typography } from '../theme/typography';
import { spacing, borderRadius } from '../theme/spacing';
import { haptic } from '../utils/haptics';
import { useAuthStore } from '../stores/authStore';
import { supabase } from '../services/supabase';
import type { RootStackParamList } from '../../App';

type Props = NativeStackScreenProps<RootStackParamList, 'Onboarding'>;

type Step = 'welcome' | 'phone' | 'personalize';

export function OnboardingScreen({ navigation }: Props) {
  const [step, setStep] = useState<Step>('welcome');
  const [phone, setPhone] = useState('');
  const [otp, setOtp] = useState('');
  const [name, setName] = useState('');
  const [companionName, setCompanionName] = useState('Koi');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [otpSent, setOtpSent] = useState(false);

  const otpRef = useRef<TextInput>(null);
  const { fetchProfile, updateProfile } = useAuthStore();

  const handleGetStarted = () => {
    haptic.light();
    setStep('phone');
  };

  const handleSendOtp = async () => {
    if (phone.length < 10) {
      setError('Please enter a valid 10-digit phone number');
      return;
    }
    haptic.light();
    setIsLoading(true);
    setError(null);

    try {
      const fullPhone = `+91${phone.replace(/\D/g, '').slice(-10)}`;
      const { error: authError } = await supabase.auth.signInWithOtp({ phone: fullPhone });
      if (authError) throw authError;
      setOtpSent(true);
      setTimeout(() => otpRef.current?.focus(), 300);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to send OTP. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleVerifyOtp = async () => {
    if (otp.length !== 6) {
      setError('Please enter the 6-digit code');
      return;
    }
    haptic.light();
    setIsLoading(true);
    setError(null);

    try {
      const fullPhone = `+91${phone.replace(/\D/g, '').slice(-10)}`;
      const { error: authError } = await supabase.auth.verifyOtp({
        phone: fullPhone,
        token: otp,
        type: 'sms',
      });
      if (authError) throw authError;

      await fetchProfile();
      haptic.success();
      setStep('personalize');
    } catch (err) {
      haptic.error();
      setError(err instanceof Error ? err.message : 'Invalid code. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleComplete = async () => {
    if (!name.trim()) {
      setError('Please tell us your name');
      return;
    }
    haptic.light();
    setIsLoading(true);
    setError(null);

    try {
      await updateProfile({
        name: name.trim(),
        companion_name: companionName.trim() || 'Koi',
      });
      haptic.success();
      navigation.replace('Home');
    } catch (err) {
      haptic.error();
      setError(err instanceof Error ? err.message : 'Something went wrong. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <LinearGradient
      colors={[colors.bg.primary, colors.bg.secondary, colors.bg.primary]}
      style={styles.container}
    >
      <KeyboardAvoidingView
        style={styles.content}
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      >
        {step === 'welcome' && (
          <Animated.View
            entering={FadeIn.duration(800)}
            exiting={FadeOut.duration(300)}
            style={styles.stepContainer}
          >
            <View style={styles.logoArea}>
              <Text style={styles.logoText}>Koi</Text>
              <Text style={styles.tagline}>Someone who's always there</Text>
            </View>
            <Pressable
              style={({ pressed }) => [
                styles.primaryButton,
                pressed && styles.pressed,
              ]}
              onPress={handleGetStarted}
            >
              <LinearGradient
                colors={[...colors.accent.gradient]}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 0 }}
                style={styles.gradientButton}
              >
                <Text style={styles.primaryButtonText}>Get Started</Text>
              </LinearGradient>
            </Pressable>
          </Animated.View>
        )}

        {step === 'phone' && (
          <Animated.View
            entering={FadeInDown.duration(400)}
            exiting={FadeOut.duration(200)}
            style={styles.stepContainer}
          >
            <Text style={styles.stepTitle}>
              {otpSent ? 'Enter the code' : 'What\'s your number?'}
            </Text>
            <Text style={styles.stepSubtitle}>
              {otpSent
                ? `We sent a 6-digit code to +91 ${phone}`
                : 'We\'ll send you a verification code'}
            </Text>

            {!otpSent ? (
              <View style={styles.inputRow}>
                <View style={styles.prefixBox}>
                  <Text style={styles.prefixText}>+91</Text>
                </View>
                <TextInput
                  style={styles.phoneInput}
                  value={phone}
                  onChangeText={(text) => {
                    setPhone(text.replace(/\D/g, '').slice(0, 10));
                    setError(null);
                  }}
                  placeholder="10-digit mobile number"
                  placeholderTextColor={colors.text.muted}
                  keyboardType="phone-pad"
                  maxLength={10}
                  autoFocus
                />
              </View>
            ) : (
              <TextInput
                ref={otpRef}
                style={styles.otpInput}
                value={otp}
                onChangeText={(text) => {
                  setOtp(text.replace(/\D/g, '').slice(0, 6));
                  setError(null);
                }}
                placeholder="------"
                placeholderTextColor={colors.text.muted}
                keyboardType="number-pad"
                maxLength={6}
                textAlign="center"
              />
            )}

            {error && <Text style={styles.errorText}>{error}</Text>}

            <Pressable
              style={({ pressed }) => [
                styles.primaryButton,
                pressed && styles.pressed,
                isLoading && styles.disabled,
              ]}
              onPress={otpSent ? handleVerifyOtp : handleSendOtp}
              disabled={isLoading}
            >
              <LinearGradient
                colors={[...colors.accent.gradient]}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 0 }}
                style={styles.gradientButton}
              >
                {isLoading ? (
                  <ActivityIndicator color={colors.text.primary} />
                ) : (
                  <Text style={styles.primaryButtonText}>
                    {otpSent ? 'Verify' : 'Send Code'}
                  </Text>
                )}
              </LinearGradient>
            </Pressable>

            {otpSent && (
              <Pressable
                onPress={() => {
                  setOtpSent(false);
                  setOtp('');
                  setError(null);
                }}
              >
                <Text style={styles.linkText}>Change number</Text>
              </Pressable>
            )}
          </Animated.View>
        )}

        {step === 'personalize' && (
          <Animated.View
            entering={FadeInDown.duration(400)}
            exiting={FadeOut.duration(200)}
            style={styles.stepContainer}
          >
            <Text style={styles.stepTitle}>Almost there</Text>

            <View style={styles.inputGroup}>
              <Text style={styles.inputLabel}>What should I call you?</Text>
              <TextInput
                style={styles.textInput}
                value={name}
                onChangeText={(text) => {
                  setName(text);
                  setError(null);
                }}
                placeholder="Your name"
                placeholderTextColor={colors.text.muted}
                autoFocus
                autoCapitalize="words"
              />
            </View>

            <View style={styles.inputGroup}>
              <Text style={styles.inputLabel}>And what would you like to call me?</Text>
              <TextInput
                style={styles.textInput}
                value={companionName}
                onChangeText={setCompanionName}
                placeholder="Koi"
                placeholderTextColor={colors.text.muted}
                autoCapitalize="words"
              />
              <Text style={styles.hint}>You can always change this later</Text>
            </View>

            {error && <Text style={styles.errorText}>{error}</Text>}

            <Pressable
              style={({ pressed }) => [
                styles.primaryButton,
                pressed && styles.pressed,
                isLoading && styles.disabled,
              ]}
              onPress={handleComplete}
              disabled={isLoading}
            >
              <LinearGradient
                colors={[...colors.accent.gradient]}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 0 }}
                style={styles.gradientButton}
              >
                {isLoading ? (
                  <ActivityIndicator color={colors.text.primary} />
                ) : (
                  <Text style={styles.primaryButtonText}>Start Talking</Text>
                )}
              </LinearGradient>
            </Pressable>
          </Animated.View>
        )}
      </KeyboardAvoidingView>
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  content: {
    flex: 1,
    justifyContent: 'center',
    paddingHorizontal: spacing.lg,
  },
  stepContainer: {
    alignItems: 'center',
    gap: spacing.lg,
  },
  logoArea: {
    alignItems: 'center',
    marginBottom: spacing.xxl,
  },
  logoText: {
    ...typography.hero,
    color: colors.accent.primary,
    letterSpacing: 4,
  },
  tagline: {
    ...typography.body,
    color: colors.text.secondary,
    marginTop: spacing.sm,
  },
  stepTitle: {
    ...typography.h1,
    color: colors.text.primary,
    textAlign: 'center',
  },
  stepSubtitle: {
    ...typography.body,
    color: colors.text.secondary,
    textAlign: 'center',
    marginTop: -spacing.sm,
  },
  inputRow: {
    flexDirection: 'row',
    width: '100%',
    gap: spacing.sm,
  },
  prefixBox: {
    backgroundColor: colors.bg.card,
    borderRadius: borderRadius.md,
    paddingHorizontal: spacing.md,
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: colors.surface.border,
  },
  prefixText: {
    ...typography.body,
    color: colors.text.secondary,
    fontWeight: '600',
  },
  phoneInput: {
    flex: 1,
    backgroundColor: colors.bg.card,
    borderRadius: borderRadius.md,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.md,
    ...typography.body,
    color: colors.text.primary,
    borderWidth: 1,
    borderColor: colors.surface.border,
    letterSpacing: 2,
    fontSize: 20,
  },
  otpInput: {
    width: '80%',
    backgroundColor: colors.bg.card,
    borderRadius: borderRadius.md,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.md,
    ...typography.h1,
    color: colors.text.primary,
    borderWidth: 1,
    borderColor: colors.surface.border,
    letterSpacing: 12,
    textAlign: 'center',
  },
  inputGroup: {
    width: '100%',
    gap: spacing.sm,
  },
  inputLabel: {
    ...typography.body,
    color: colors.text.secondary,
  },
  textInput: {
    backgroundColor: colors.bg.card,
    borderRadius: borderRadius.md,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.md,
    ...typography.body,
    color: colors.text.primary,
    borderWidth: 1,
    borderColor: colors.surface.border,
  },
  hint: {
    ...typography.small,
    color: colors.text.muted,
  },
  primaryButton: {
    width: '100%',
    borderRadius: borderRadius.md,
    overflow: 'hidden',
  },
  gradientButton: {
    paddingVertical: spacing.md,
    alignItems: 'center',
    borderRadius: borderRadius.md,
  },
  primaryButtonText: {
    ...typography.body,
    fontWeight: '700',
    color: colors.text.primary,
  },
  pressed: {
    opacity: 0.8,
    transform: [{ scale: 0.98 }],
  },
  disabled: {
    opacity: 0.6,
  },
  errorText: {
    ...typography.caption,
    color: colors.status.error,
    textAlign: 'center',
  },
  linkText: {
    ...typography.caption,
    color: colors.accent.secondary,
    textDecorationLine: 'underline',
  },
});
