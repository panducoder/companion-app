import { Audio } from 'expo-av';
import { Alert, Linking, Platform } from 'react-native';

export async function requestMicrophonePermission(): Promise<boolean> {
  const { status: existingStatus } = await Audio.getPermissionsAsync();

  if (existingStatus === 'granted') {
    return true;
  }

  const { status } = await Audio.requestPermissionsAsync();

  if (status === 'granted') {
    return true;
  }

  Alert.alert(
    'Microphone Access Required',
    'Koi needs access to your microphone to have voice conversations. Please enable it in your device settings.',
    [
      { text: 'Not Now', style: 'cancel' },
      {
        text: 'Open Settings',
        onPress: () => {
          if (Platform.OS === 'ios') {
            Linking.openURL('app-settings:');
          } else {
            Linking.openSettings();
          }
        },
      },
    ]
  );

  return false;
}

export async function configureAudioSession(): Promise<void> {
  await Audio.setAudioModeAsync({
    allowsRecordingIOS: true,
    playsInSilentModeIOS: true,
    staysActiveInBackground: true,
    shouldDuckAndroid: true,
    playThroughEarpieceAndroid: false,
  });
}
