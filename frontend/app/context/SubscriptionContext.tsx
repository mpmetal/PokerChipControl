import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Platform, Alert } from 'react-native';
import Constants from 'expo-constants';

interface SubscriptionContextType {
  isPremium: boolean;
  isLoading: boolean;
  isTrialActive: boolean;
  daysRemaining: number;
  canStartTrial: boolean;
  // Functions
  startFreeTrial: () => Promise<boolean>;
  refreshSubscriptionStatus: () => Promise<void>;
}

const SubscriptionContext = createContext<SubscriptionContextType>({
  isPremium: false,
  isLoading: true,
  isTrialActive: false,
  daysRemaining: 0,
  canStartTrial: true,
  startFreeTrial: async () => false,
  refreshSubscriptionStatus: async () => {},
});

interface SubscriptionProviderProps {
  children: ReactNode;
}

export const SubscriptionProvider: React.FC<SubscriptionProviderProps> = ({ children }) => {
  const [isPremium, setIsPremium] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [isTrialActive, setIsTrialActive] = useState(false);
  const [daysRemaining, setDaysRemaining] = useState(0);
  const [canStartTrial, setCanStartTrial] = useState(true);

  const BACKEND_URL = Constants.expoConfig?.extra?.backendUrl || process.env.EXPO_PUBLIC_BACKEND_URL;

  const refreshSubscriptionStatus = async () => {
    try {
      // Get current player ID from storage
      const playerId = await AsyncStorage.getItem('current_player_id') || 'demo_user';
      
      const response = await fetch(`${BACKEND_URL}/api/subscription/status/${playerId}`);
      if (response.ok) {
        const status = await response.json();
        setIsPremium(status.is_premium);
        setIsTrialActive(status.is_trial);
        setDaysRemaining(status.days_remaining);
        setCanStartTrial(status.can_start_trial);
      }
    } catch (error) {
      console.error('Failed to refresh subscription status:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const startFreeTrial = async (): Promise<boolean> => {
    try {
      const playerId = await AsyncStorage.getItem('current_player_id') || 'demo_user';
      
      const response = await fetch(`${BACKEND_URL}/api/subscription/start-trial/${playerId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const result = await response.json();
        console.log('Trial started:', result);
        
        // Update local state
        setIsPremium(true);
        setIsTrialActive(true);
        setDaysRemaining(7);
        setCanStartTrial(false);
        
        Alert.alert(
          '¡Prueba Gratuita Iniciada! 🎉',
          'Tienes 7 días gratis para disfrutar de todas las funciones premium.'
        );
        return true;
      } else {
        const error = await response.json();
        Alert.alert('Error', error.detail || 'Failed to start trial');
        return false;
      }
    } catch (error) {
      console.error('Error starting trial:', error);
      Alert.alert('Error', 'Network error occurred');
      return false;
    }
  };

  useEffect(() => {
    refreshSubscriptionStatus();
  }, []);

  const contextValue: SubscriptionContextType = {
    isPremium,
    isLoading,
    isTrialActive,
    daysRemaining,
    canStartTrial,
    startFreeTrial,
    refreshSubscriptionStatus,
  };

  return (
    <SubscriptionContext.Provider value={contextValue}>
      {children}
    </SubscriptionContext.Provider>
  );
};

export const useSubscription = (): SubscriptionContextType => {
  const context = useContext(SubscriptionContext);
  if (!context) {
    throw new Error('useSubscription must be used within a SubscriptionProvider');
  }
  return context;
};