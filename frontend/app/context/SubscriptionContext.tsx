import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import Purchases, { CustomerInfo, PurchasesOffering } from 'react-native-purchases';
import { Platform, Alert } from 'react-native';
import Constants from 'expo-constants';

interface SubscriptionContextType {
  isPremium: boolean;
  isLoading: boolean;
  isTrialActive: boolean;
  daysRemaining: number;
  customerInfo: CustomerInfo | null;
  currentOffering: PurchasesOffering | null;
  canStartTrial: boolean;
  // Functions
  initializePurchases: () => Promise<void>;
  startFreeTrial: () => Promise<boolean>;
  purchaseSubscription: () => Promise<boolean>;
  restorePurchases: () => Promise<boolean>;
  refreshSubscriptionStatus: () => Promise<void>;
}

const SubscriptionContext = createContext<SubscriptionContextType>({
  isPremium: false,
  isLoading: true,
  isTrialActive: false,
  daysRemaining: 0,
  customerInfo: null,
  currentOffering: null,
  canStartTrial: true,
  initializePurchases: async () => {},
  startFreeTrial: async () => false,
  purchaseSubscription: async () => false,
  restorePurchases: async () => false,
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
  const [customerInfo, setCustomerInfo] = useState<CustomerInfo | null>(null);
  const [currentOffering, setCurrentOffering] = useState<PurchasesOffering | null>(null);
  const [canStartTrial, setCanStartTrial] = useState(true);

  const BACKEND_URL = Constants.expoConfig?.extra?.backendUrl || process.env.EXPO_PUBLIC_BACKEND_URL;
  const REVENUECAT_ANDROID_API_KEY = Constants.expoConfig?.extra?.revenueCatAndroidApiKey || process.env.EXPO_PUBLIC_REVENUECAT_ANDROID_API_KEY;

  const initializePurchases = async () => {
    try {
      console.log('Initializing RevenueCat...');
      
      if (Platform.OS === 'android' && REVENUECAT_ANDROID_API_KEY) {
        await Purchases.configure({
          apiKey: REVENUECAT_ANDROID_API_KEY,
        });
      } else {
        throw new Error('RevenueCat API key not found for Android');
      }

      // Set user ID (use stored player ID if available)
      const playerId = await AsyncStorage.getItem('current_player_id');
      if (playerId) {
        await Purchases.logIn(`player_${playerId}`);
      }

      // Set up listener for purchase updates
      Purchases.addCustomerInfoUpdateListener(async (info) => {
        console.log('Customer info updated:', info);
        setCustomerInfo(info);
        await updateSubscriptionStatus(info);
      });

      console.log('RevenueCat initialized successfully');
      await loadOfferings();
      await refreshSubscriptionStatus();
      
    } catch (error) {
      console.error('Failed to initialize RevenueCat:', error);
      setIsLoading(false);
    }
  };

  const loadOfferings = async () => {
    try {
      const offerings = await Purchases.getOfferings();
      if (offerings.current && offerings.current.availablePackages.length > 0) {
        setCurrentOffering(offerings.current);
        console.log('Loaded offerings:', offerings.current.availablePackages.length);
      } else {
        console.warn('No offerings available');
      }
    } catch (error) {
      console.error('Failed to load offerings:', error);
    }
  };

  const updateSubscriptionStatus = async (info: CustomerInfo) => {
    try {
      // Check if user has premium entitlement
      const premiumEntitlement = info.entitlements.active['premium'];
      const hasPremium = premiumEntitlement !== undefined;
      
      setIsPremium(hasPremium);

      if (hasPremium && premiumEntitlement) {
        // Calculate days remaining
        const expirationDate = new Date(premiumEntitlement.expirationDate);
        const now = new Date();
        const diffTime = expirationDate.getTime() - now.getTime();
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
        setDaysRemaining(Math.max(0, diffDays));

        // Check if it's a trial
        const isInTrial = diffDays <= 7; // Simple trial detection
        setIsTrialActive(isInTrial);
        setCanStartTrial(false);
      } else {
        setDaysRemaining(0);
        setIsTrialActive(false);
        // Check if user can start trial (this would need backend check)
        setCanStartTrial(true);
      }
    } catch (error) {
      console.error('Error updating subscription status:', error);
    }
  };

  const refreshSubscriptionStatus = async () => {
    try {
      const info = await Purchases.getCustomerInfo();
      setCustomerInfo(info);
      await updateSubscriptionStatus(info);
    } catch (error) {
      console.error('Failed to refresh subscription status:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const startFreeTrial = async (): Promise<boolean> => {
    try {
      // For now, simulate starting a free trial via backend
      const playerId = await AsyncStorage.getItem('current_player_id');
      if (!playerId) {
        Alert.alert('Error', 'No player selected');
        return false;
      }

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

  const purchaseSubscription = async (): Promise<boolean> => {
    try {
      if (!currentOffering || currentOffering.availablePackages.length === 0) {
        Alert.alert('Error', 'No subscription packages available');
        return false;
      }

      const packageToPurchase = currentOffering.availablePackages[0]; // Monthly subscription
      
      const purchaseResult = await Purchases.purchasePackage(packageToPurchase);
      
      if (purchaseResult.customerInfo.entitlements.active['premium']) {
        Alert.alert(
          '¡Suscripción Exitosa! 🎉',
          'Ahora tienes acceso completo a todas las funciones premium.'
        );
        await refreshSubscriptionStatus();
        return true;
      }
      
      return false;
    } catch (error: any) {
      if (!error.userCancelled) {
        console.error('Purchase failed:', error);
        Alert.alert('Purchase Failed', error.message || 'An error occurred during purchase.');
      }
      return false;
    }
  };

  const restorePurchases = async (): Promise<boolean> => {
    try {
      const customerInfo = await Purchases.restorePurchases();
      setCustomerInfo(customerInfo);
      await updateSubscriptionStatus(customerInfo);
      
      if (customerInfo.entitlements.active['premium']) {
        Alert.alert('Success', 'Your purchases have been restored!');
        return true;
      } else {
        Alert.alert('No Purchases', 'No active purchases found to restore.');
        return false;
      }
    } catch (error) {
      console.error('Failed to restore purchases:', error);
      Alert.alert('Error', 'Failed to restore purchases');
      return false;
    }
  };

  useEffect(() => {
    initializePurchases();
  }, []);

  const contextValue: SubscriptionContextType = {
    isPremium,
    isLoading,
    isTrialActive,
    daysRemaining,
    customerInfo,
    currentOffering,
    canStartTrial,
    initializePurchases,
    startFreeTrial,
    purchaseSubscription,
    restorePurchases,
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