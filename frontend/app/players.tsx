import React from 'react';
import { SafeAreaView, StyleSheet } from 'react-native';
import PlayersScreen from './screens/PlayersScreen';
import { GameProvider } from './context/GameContext';

export default function Players() {
  return (
    <SafeAreaView style={styles.container}>
      <GameProvider>
        <PlayersScreen />
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