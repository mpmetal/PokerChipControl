import React from 'react';
import { SafeAreaView, StyleSheet } from 'react-native';
import ReportsScreen from './screens/ReportsScreen';
import { GameProvider } from './context/GameContext';

export default function Reports() {
  return (
    <SafeAreaView style={styles.container}>
      <GameProvider>
        <ReportsScreen />
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