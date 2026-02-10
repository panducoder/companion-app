import { TextStyle } from 'react-native';

export const typography: Record<string, TextStyle> = {
  hero: {
    fontSize: 48,
    fontWeight: '700',
    lineHeight: 56,
  },
  h1: {
    fontSize: 28,
    fontWeight: '600',
    lineHeight: 34,
  },
  h2: {
    fontSize: 22,
    fontWeight: '600',
    lineHeight: 28,
  },
  body: {
    fontSize: 16,
    fontWeight: '400',
    lineHeight: 24,
  },
  caption: {
    fontSize: 14,
    fontWeight: '400',
    lineHeight: 20,
  },
  small: {
    fontSize: 12,
    fontWeight: '400',
    lineHeight: 16,
  },
};
