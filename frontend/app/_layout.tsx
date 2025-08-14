import { Stack } from 'expo-router';
import React from 'react';
import { GameProvider } from './context/GameContext';
import { LanguageProvider } from './context/LanguageContext';

export default function RootLayout() {
  return (
    <LanguageProvider>
      <GameProvider>
        <Stack>
          <Stack.Screen name="index" options={{ headerShown: false }} />
          <Stack.Screen name="game" options={{ headerShown: false }} />
          <Stack.Screen name="history" options={{ headerShown: false }} />
          <Stack.Screen name="players" options={{ headerShown: false }} />
          <Stack.Screen name="reports" options={{ headerShown: false }} />
        </Stack>
      </GameProvider>
    </LanguageProvider>
  );
}