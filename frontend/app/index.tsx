import React from 'react';
import { StyleSheet, SafeAreaView } from 'react-native';
import HomeScreen from './screens/HomeScreen';
import GameProvider from './context/GameContext';

export default function Index() {
  return (
    <SafeAreaView style={styles.container}>
      <GameProvider>
        <HomeScreen />
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