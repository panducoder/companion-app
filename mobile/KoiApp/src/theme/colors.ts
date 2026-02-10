export const colors = {
  bg: {
    primary: '#0A0A1A',
    secondary: '#12122A',
    card: '#1A1A3E',
  },
  accent: {
    primary: '#7C5CFC',
    secondary: '#5B8DEF',
    gradient: ['#7C5CFC', '#5B8DEF'] as const,
  },
  status: {
    listening: '#34D399',
    speaking: '#A78BFA',
    error: '#EF4444',
    connecting: '#FBBF24',
  },
  text: {
    primary: '#FFFFFF',
    secondary: '#9CA3AF',
    muted: '#4B5563',
  },
  surface: {
    border: 'rgba(255,255,255,0.08)',
    overlay: 'rgba(0,0,0,0.5)',
  },
} as const;
