import React from 'react';
import { StyleSheet, SafeAreaView } from 'react-native';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import HomeScreen from './screens/HomeScreen';
import PlayersScreen from './screens/PlayersScreen';
import GameScreen from './screens/GameScreen';
import HistoryScreen from './screens/HistoryScreen';
import GameProvider from './context/GameContext';

const Stack = createNativeStackNavigator();

export default function Index() {
  return (
    <SafeAreaView style={styles.container}>
      <GameProvider>
        <NavigationContainer independent={true}>
          <Stack.Navigator
            initialRouteName="Home"
            screenOptions={{
              headerStyle: {
                backgroundColor: '#2E7D32',
              },
              headerTintColor: '#fff',
              headerTitleStyle: {
                fontWeight: 'bold',
              },
            }}
          >
            <Stack.Screen 
              name="Home" 
              component={HomeScreen} 
              options={{ title: 'Poker Chip Manager' }}
            />
            <Stack.Screen 
              name="Players" 
              component={PlayersScreen} 
              options={{ title: 'Manage Players' }}
            />
            <Stack.Screen 
              name="Game" 
              component={GameScreen} 
              options={{ title: 'Active Game' }}
            />
            <Stack.Screen 
              name="History" 
              component={HistoryScreen} 
              options={{ title: 'Game History' }}
            />
          </Stack.Navigator>
        </NavigationContainer>
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