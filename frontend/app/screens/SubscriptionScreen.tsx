import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
  ScrollView,
  Platform,
} from 'react-native';
import { router } from 'expo-router';
import { useSubscription } from '../context/SubscriptionContext';
import { useLanguage } from '../context/LanguageContext';
import { Button } from 'react-native-elements';
import { MaterialIcons } from '@expo/vector-icons';

const SubscriptionScreen: React.FC = () => {
  const [purchasing, setPurchasing] = useState(false);
  const { t } = useLanguage();
  const {
    isPremium,
    isLoading,
    isTrialActive,
    daysRemaining,
    canStartTrial,
    startFreeTrial,
  } = useSubscription();

  const handleStartTrial = async () => {
    setPurchasing(true);
    try {
      const success = await startFreeTrial();
      if (success) {
        // Navigate back to home after successful trial start
        setTimeout(() => {
          router.back();
        }, 2000);
      }
    } finally {
      setPurchasing(false);
    }
  };

  const handlePurchase = async () => {
    setPurchasing(true);
    try {
      // For demo, just show alert
      Alert.alert(
        'Demo Mode',
        'En producción, aquí se procesaría el pago real a través de Google Play Store o App Store.'
      );
    } finally {
      setPurchasing(false);
    }
  };

  const handleRestore = async () => {
    setPurchasing(true);
    try {
      // For demo, just show alert
      Alert.alert(
        'Demo Mode',
        'En producción, aquí se restaurarían las compras desde la store.'
      );
    } finally {
      setPurchasing(false);
    }
  };

  if (isLoading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#007AFF" />
        <Text style={styles.loadingText}>Cargando estado de suscripción...</Text>
      </View>
    );
  }

  if (isPremium) {
    return (
      <View style={styles.container}>
        <TouchableOpacity style={styles.backButton} onPress={() => router.back()}>
          <MaterialIcons name="arrow-back" size={24} color="#007AFF" />
        </TouchableOpacity>

        <ScrollView contentContainerStyle={styles.content}>
          <View style={styles.premiumContainer}>
            <MaterialIcons name="verified" size={80} color="#4CAF50" />
            <Text style={styles.premiumTitle}>¡Eres Premium! 🎉</Text>
            
            {isTrialActive ? (
              <View style={styles.trialInfo}>
                <Text style={styles.trialText}>Prueba Gratuita Activa</Text>
                <Text style={styles.daysText}>
                  {daysRemaining} {daysRemaining === 1 ? 'día restante' : 'días restantes'}
                </Text>
                <Text style={styles.trialNote}>
                  Después del período de prueba, se cobrará $2 USD mensuales.
                </Text>
              </View>
            ) : (
              <View style={styles.subscriptionInfo}>
                <Text style={styles.subscriptionText}>Suscripción Activa</Text>
                <Text style={styles.daysText}>
                  {daysRemaining} {daysRemaining === 1 ? 'día restante' : 'días restantes'}
                </Text>
              </View>
            )}

            <View style={styles.featuresContainer}>
              <Text style={styles.featuresTitle}>Funciones Premium:</Text>
              <View style={styles.feature}>
                <MaterialIcons name="check-circle" size={20} color="#4CAF50" />
                <Text style={styles.featureText}>Jugadores ilimitados</Text>
              </View>
              <View style={styles.feature}>
                <MaterialIcons name="check-circle" size={20} color="#4CAF50" />
                <Text style={styles.featureText}>Partidas ilimitadas</Text>
              </View>
              <View style={styles.feature}>
                <MaterialIcons name="check-circle" size={20} color="#4CAF50" />
                <Text style={styles.featureText}>Reportes avanzados</Text>
              </View>
              <View style={styles.feature}>
                <MaterialIcons name="check-circle" size={20} color="#4CAF50" />
                <Text style={styles.featureText}>Exportar datos</Text>
              </View>
              <View style={styles.feature}>
                <MaterialIcons name="check-circle" size={20} color="#4CAF50" />
                <Text style={styles.featureText}>Soporte prioritario</Text>
              </View>
            </View>

            <TouchableOpacity 
              style={styles.restoreButton}
              onPress={handleRestore}
              disabled={purchasing}
            >
              <Text style={styles.restoreButtonText}>Restaurar Compras</Text>
            </TouchableOpacity>
          </View>
        </ScrollView>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <TouchableOpacity style={styles.backButton} onPress={() => router.back()}>
        <MaterialIcons name="arrow-back" size={24} color="#007AFF" />
      </TouchableOpacity>

      <ScrollView contentContainerStyle={styles.content}>
        <View style={styles.headerContainer}>
          <MaterialIcons name="stars" size={60} color="#FFD700" />
          <Text style={styles.title}>Hazte Premium</Text>
          <Text style={styles.subtitle}>
            Desbloquea todas las funciones avanzadas
          </Text>
        </View>

        <View style={styles.planContainer}>
          <View style={styles.planHeader}>
            <Text style={styles.planTitle}>Plan Mensual</Text>
            <Text style={styles.planPrice}>$2 USD</Text>
            <Text style={styles.planPeriod}>por mes</Text>
          </View>

          {canStartTrial && (
            <View style={styles.trialBadge}>
              <Text style={styles.trialBadgeText}>✨ 7 días gratis</Text>
            </View>
          )}

          <View style={styles.featuresContainer}>
            <Text style={styles.featuresTitle}>Lo que obtienes:</Text>
            
            <View style={styles.feature}>
              <MaterialIcons name="people" size={20} color="#007AFF" />
              <Text style={styles.featureText}>Jugadores ilimitados</Text>
            </View>
            
            <View style={styles.feature}>
              <MaterialIcons name="casino" size={20} color="#007AFF" />
              <Text style={styles.featureText}>Partidas ilimitadas</Text>
            </View>
            
            <View style={styles.feature}>
              <MaterialIcons name="analytics" size={20} color="#007AFF" />
              <Text style={styles.featureText}>Reportes detallados</Text>
            </View>
            
            <View style={styles.feature}>
              <MaterialIcons name="file-download" size={20} color="#007AFF" />
              <Text style={styles.featureText}>Exportar a CSV/Excel</Text>
            </View>
            
            <View style={styles.feature}>
              <MaterialIcons name="support-agent" size={20} color="#007AFF" />
              <Text style={styles.featureText}>Soporte prioritario</Text>
            </View>
            
            <View style={styles.feature}>
              <MaterialIcons name="cloud-sync" size={20} color="#007AFF" />
              <Text style={styles.featureText}>Respaldo en la nube</Text>
            </View>
          </View>

          {canStartTrial ? (
            <TouchableOpacity
              style={[styles.subscribeButton, purchasing && styles.disabledButton]}
              onPress={handleStartTrial}
              disabled={purchasing}
            >
              {purchasing ? (
                <ActivityIndicator color="white" />
              ) : (
                <>
                  <MaterialIcons name="play-arrow" size={24} color="white" />
                  <Text style={styles.subscribeButtonText}>
                    Iniciar Prueba Gratis
                  </Text>
                </>
              )}
            </TouchableOpacity>
          ) : (
            <TouchableOpacity
              style={[styles.subscribeButton, purchasing && styles.disabledButton]}
              onPress={handlePurchase}
              disabled={purchasing}
            >
              {purchasing ? (
                <ActivityIndicator color="white" />
              ) : (
                <>
                  <MaterialIcons name="star" size={24} color="white" />
                  <Text style={styles.subscribeButtonText}>
                    Suscribirse Ahora
                  </Text>
                </>
              )}
            </TouchableOpacity>
          )}

          <TouchableOpacity 
            style={styles.restoreButton}
            onPress={handleRestore}
            disabled={purchasing}
          >
            <Text style={styles.restoreButtonText}>Restaurar Compras</Text>
          </TouchableOpacity>
        </View>

        <View style={styles.disclaimerContainer}>
          <Text style={styles.disclaimerText}>
            La suscripción se renueva automáticamente a menos que se cancele al menos 24 horas antes del final del período actual.
          </Text>
          <Text style={styles.disclaimerText}>
            Se puede cancelar en cualquier momento desde la configuración de tu cuenta.
          </Text>
        </View>
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#f5f5f5',
  },
  loadingText: {
    marginTop: 16,
    fontSize: 16,
    color: '#666',
  },
  backButton: {
    position: 'absolute',
    top: 50,
    left: 20,
    zIndex: 1,
    padding: 8,
  },
  content: {
    paddingTop: 80,
    paddingHorizontal: 20,
    paddingBottom: 40,
  },
  headerContainer: {
    alignItems: 'center',
    marginBottom: 40,
  },
  title: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#333',
    marginTop: 16,
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 18,
    color: '#666',
    textAlign: 'center',
  },
  planContainer: {
    backgroundColor: 'white',
    borderRadius: 16,
    padding: 24,
    marginBottom: 24,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 4,
  },
  planHeader: {
    alignItems: 'center',
    marginBottom: 24,
  },
  planTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 8,
  },
  planPrice: {
    fontSize: 48,
    fontWeight: 'bold',
    color: '#007AFF',
  },
  planPeriod: {
    fontSize: 16,
    color: '#666',
  },
  trialBadge: {
    backgroundColor: '#FFD700',
    borderRadius: 20,
    paddingHorizontal: 16,
    paddingVertical: 8,
    alignSelf: 'center',
    marginBottom: 24,
  },
  trialBadgeText: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
  },
  featuresContainer: {
    marginBottom: 32,
  },
  featuresTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 16,
  },
  feature: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  featureText: {
    fontSize: 16,
    color: '#333',
    marginLeft: 12,
    flex: 1,
  },
  subscribeButton: {
    backgroundColor: '#007AFF',
    borderRadius: 12,
    paddingVertical: 16,
    paddingHorizontal: 24,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 16,
  },
  disabledButton: {
    backgroundColor: '#ccc',
  },
  subscribeButtonText: {
    color: 'white',
    fontSize: 18,
    fontWeight: 'bold',
    marginLeft: 8,
  },
  restoreButton: {
    alignItems: 'center',
    paddingVertical: 12,
  },
  restoreButtonText: {
    color: '#007AFF',
    fontSize: 16,
  },
  disclaimerContainer: {
    paddingHorizontal: 16,
  },
  disclaimerText: {
    fontSize: 12,
    color: '#999',
    textAlign: 'center',
    marginBottom: 8,
  },
  premiumContainer: {
    alignItems: 'center',
    padding: 24,
  },
  premiumTitle: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#4CAF50',
    marginTop: 16,
    marginBottom: 24,
  },
  trialInfo: {
    backgroundColor: '#E3F2FD',
    borderRadius: 12,
    padding: 20,
    alignItems: 'center',
    marginBottom: 32,
    width: '100%',
  },
  subscriptionInfo: {
    backgroundColor: '#E8F5E8',
    borderRadius: 12,
    padding: 20,
    alignItems: 'center',
    marginBottom: 32,
    width: '100%',
  },
  trialText: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#2196F3',
    marginBottom: 8,
  },
  subscriptionText: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#4CAF50',
    marginBottom: 8,
  },
  daysText: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 8,
  },
  trialNote: {
    fontSize: 14,
    color: '#666',
    textAlign: 'center',
  },
});

export default SubscriptionScreen;