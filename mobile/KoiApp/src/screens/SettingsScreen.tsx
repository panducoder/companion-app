import React, { useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import { colors } from '../theme/colors';
import { typography } from '../theme/typography';
import { spacing, borderRadius } from '../theme/spacing';
import { haptic } from '../utils/haptics';
import { useAuthStore } from '../stores/authStore';
import { useSettingsStore } from '../stores/settingsStore';
import { api } from '../services/api';
import type { RootStackParamList } from '../../App';

type Props = NativeStackScreenProps<RootStackParamList, 'Settings'>;

export function SettingsScreen({ navigation }: Props) {
  const insets = useSafeAreaInsets();
  const { profile, updateProfile, signOut, user } = useAuthStore();
  const { resetSettings } = useSettingsStore();

  const [name, setName] = useState(profile?.name ?? '');
  const [companionName, setCompanionName] = useState(profile?.companion_name ?? 'Koi');
  const [isSaving, setIsSaving] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);

  const handleSave = async () => {
    if (!name.trim()) return;
    haptic.light();
    setIsSaving(true);

    try {
      await updateProfile({
        name: name.trim(),
        companion_name: companionName.trim() || 'Koi',
      });
      haptic.success();
      setHasChanges(false);
    } catch {
      haptic.error();
      Alert.alert('Error', 'Could not save your changes. Please try again.');
    } finally {
      setIsSaving(false);
    }
  };

  const handleDeleteData = () => {
    haptic.warning();
    Alert.alert(
      'Delete All My Data',
      'This will permanently delete your profile, all conversations, and all memories. This action cannot be undone.',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete Everything',
          style: 'destructive',
          onPress: async () => {
            setIsDeleting(true);
            try {
              await api.deleteUserData();
              resetSettings();
              await signOut();
            } catch {
              haptic.error();
              Alert.alert('Error', 'Could not delete your data. Please try again later.');
              setIsDeleting(false);
            }
          },
        },
      ]
    );
  };

  const handleLogout = () => {
    haptic.light();
    Alert.alert('Log Out', 'Are you sure you want to log out?', [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Log Out',
        style: 'destructive',
        onPress: async () => {
          await signOut();
        },
      },
    ]);
  };

  return (
    <View style={[styles.container, { paddingTop: insets.top, paddingBottom: insets.bottom }]}>
      {/* Header */}
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
        <Text style={styles.headerTitle}>Settings</Text>
        {hasChanges ? (
          <Pressable onPress={handleSave} disabled={isSaving} hitSlop={16}>
            {isSaving ? (
              <ActivityIndicator color={colors.accent.primary} size="small" />
            ) : (
              <Text style={styles.saveText}>Save</Text>
            )}
          </Pressable>
        ) : (
          <View style={{ width: 40 }} />
        )}
      </View>

      <ScrollView
        style={styles.scroll}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        {/* Profile Section */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Profile</Text>

          <View style={styles.field}>
            <Text style={styles.fieldLabel}>Your name</Text>
            <TextInput
              style={styles.fieldInput}
              value={name}
              onChangeText={(text) => {
                setName(text);
                setHasChanges(true);
              }}
              placeholder="Your name"
              placeholderTextColor={colors.text.muted}
              autoCapitalize="words"
            />
          </View>

          <View style={styles.field}>
            <Text style={styles.fieldLabel}>Companion name</Text>
            <TextInput
              style={styles.fieldInput}
              value={companionName}
              onChangeText={(text) => {
                setCompanionName(text);
                setHasChanges(true);
              }}
              placeholder="Koi"
              placeholderTextColor={colors.text.muted}
              autoCapitalize="words"
            />
          </View>
        </View>

        {/* Privacy Section */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Privacy</Text>

          <Text style={styles.privacyNote}>
            Your conversations are stored securely and are only accessible by you. Voice audio is processed in real-time and is not stored after the conversation ends.
          </Text>

          <Pressable
            style={({ pressed }) => [styles.actionButton, pressed && styles.actionPressed]}
            onPress={() => {
              haptic.light();
              Alert.alert(
                'Privacy Policy',
                'You can read our full privacy policy at koi.app/privacy. Your data is encrypted and stored in India. We never sell your information.'
              );
            }}
          >
            <Text style={styles.actionButtonText}>Privacy Policy</Text>
          </Pressable>

          <Pressable
            style={({ pressed }) => [
              styles.actionButton,
              styles.dangerButton,
              pressed && styles.actionPressed,
            ]}
            onPress={handleDeleteData}
            disabled={isDeleting}
          >
            {isDeleting ? (
              <ActivityIndicator color={colors.status.error} size="small" />
            ) : (
              <Text style={[styles.actionButtonText, styles.dangerText]}>
                Delete All My Data
              </Text>
            )}
          </Pressable>
        </View>

        {/* Account Section */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Account</Text>

          <View style={styles.infoRow}>
            <Text style={styles.infoLabel}>Phone</Text>
            <Text style={styles.infoValue}>{user?.phone ?? 'Not set'}</Text>
          </View>

          <View style={styles.infoRow}>
            <Text style={styles.infoLabel}>Status</Text>
            <Text style={styles.infoValue}>
              {profile?.subscription_status === 'free' ? 'Free' : 'Premium'}
            </Text>
          </View>

          <Pressable
            style={({ pressed }) => [
              styles.actionButton,
              styles.logoutButton,
              pressed && styles.actionPressed,
            ]}
            onPress={handleLogout}
          >
            <Text style={[styles.actionButtonText, styles.logoutText]}>Log Out</Text>
          </Pressable>
        </View>

        {/* About Section */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>About</Text>

          <View style={styles.infoRow}>
            <Text style={styles.infoLabel}>Version</Text>
            <Text style={styles.infoValue}>1.0.0</Text>
          </View>

          <Text style={styles.credits}>
            Made with care in India. Powered by Sarvam AI.
          </Text>
        </View>
      </ScrollView>
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
  saveText: {
    ...typography.caption,
    color: colors.accent.primary,
    fontWeight: '600',
  },
  scroll: {
    flex: 1,
  },
  scrollContent: {
    padding: spacing.lg,
    gap: spacing.lg,
    paddingBottom: spacing.xxxl,
  },
  section: {
    gap: spacing.md,
  },
  sectionTitle: {
    ...typography.caption,
    fontWeight: '600',
    color: colors.text.muted,
    textTransform: 'uppercase',
    letterSpacing: 1,
  },
  field: {
    gap: spacing.xs,
  },
  fieldLabel: {
    ...typography.caption,
    color: colors.text.secondary,
  },
  fieldInput: {
    backgroundColor: colors.bg.card,
    borderRadius: borderRadius.md,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    ...typography.body,
    color: colors.text.primary,
    borderWidth: 1,
    borderColor: colors.surface.border,
  },
  privacyNote: {
    ...typography.caption,
    color: colors.text.secondary,
    lineHeight: 20,
  },
  actionButton: {
    backgroundColor: colors.bg.card,
    borderRadius: borderRadius.md,
    paddingVertical: spacing.md,
    paddingHorizontal: spacing.md,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: colors.surface.border,
  },
  dangerButton: {
    borderColor: 'rgba(239, 68, 68, 0.2)',
    backgroundColor: 'rgba(239, 68, 68, 0.08)',
  },
  logoutButton: {
    borderColor: colors.surface.border,
  },
  actionPressed: {
    opacity: 0.7,
  },
  actionButtonText: {
    ...typography.body,
    fontWeight: '600',
    color: colors.text.secondary,
  },
  dangerText: {
    color: colors.status.error,
  },
  logoutText: {
    color: colors.text.secondary,
  },
  infoRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: colors.bg.card,
    borderRadius: borderRadius.md,
    paddingVertical: spacing.sm,
    paddingHorizontal: spacing.md,
    borderWidth: 1,
    borderColor: colors.surface.border,
  },
  infoLabel: {
    ...typography.body,
    color: colors.text.secondary,
  },
  infoValue: {
    ...typography.body,
    color: colors.text.primary,
    fontWeight: '500',
  },
  credits: {
    ...typography.small,
    color: colors.text.muted,
    textAlign: 'center',
    marginTop: spacing.sm,
  },
});
