import React from 'react';
import { StyleSheet, SafeAreaView } from 'react-native';
import HomeScreen from './screens/HomeScreen';
import GameProvider from './context/GameContext';
import LanguageProvider from './context/LanguageContext';

export default function Index() {
  return (
    <SafeAreaView style={styles.container}>
      <LanguageProvider>
        <GameProvider>
          <HomeScreen />
        </GameProvider>
      </LanguageProvider>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
});