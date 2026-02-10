import * as Haptics from 'expo-haptics';

export const haptic = {
  /** Light tap - for button presses */
  light: () => Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light),

  /** Medium tap - for toggle actions */
  medium: () => Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium),

  /** Heavy tap - for important actions like ending a call */
  heavy: () => Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Heavy),

  /** Success feedback */
  success: () => Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success),

  /** Warning feedback */
  warning: () => Haptics.notificationAsync(Haptics.NotificationFeedbackType.Warning),

  /** Error feedback */
  error: () => Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error),

  /** Selection tick - for scrolling through options */
  selection: () => Haptics.selectionAsync(),
};
