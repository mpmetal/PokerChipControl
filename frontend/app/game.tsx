import React from 'react';
import { SafeAreaView, StyleSheet } from 'react-native';
import GameScreen from './screens/GameScreen';
import { GameProvider } from './context/GameContext';

export default function Game() {
  return (
    <SafeAreaView style={styles.container}>
      <GameProvider>
        <GameScreen />
      </GameProvider>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
});