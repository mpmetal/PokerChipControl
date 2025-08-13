import React from 'react';
import { SafeAreaView, StyleSheet } from 'react-native';
import HistoryScreen from './screens/HistoryScreen';
import GameProvider from './context/GameContext';

export default function History() {
  return (
    <SafeAreaView style={styles.container}>
      <GameProvider>
        <HistoryScreen />
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