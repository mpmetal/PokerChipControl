import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  Alert,
  RefreshControl,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useGame } from '../context/GameContext';
import { useLanguage } from '../context/LanguageContext';
import { useRouter } from 'expo-router';

interface DashboardData {
  active_games: number;
  total_players: number;
  total_credit_owed: number;
  total_debt_owed: number;
  recent_transactions: any[];
}

export default function HomeScreen() {
  const router = useRouter();
  const { currentGame, isLoading, fetchPlayers, fetchGames } = useGame();
  const { t, language, setLanguage } = useLanguage();
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  const fetchDashboard = async () => {
    try {
      const API_BASE_URL = process.env.EXPO_PUBLIC_BACKEND_URL;
      const response = await fetch(`${API_BASE_URL}/api/dashboard`);
      if (response.ok) {
        const data = await response.json();
        setDashboardData(data);
      }
    } catch (error) {
      console.error('Error fetching dashboard:', error);
    }
  };

  useEffect(() => {
    fetchDashboard();
  }, []);

  const onRefresh = async () => {
    setRefreshing(true);
    await Promise.all([
      fetchDashboard(),
      fetchPlayers(),
      fetchGames()
    ]);
    setRefreshing(false);
  };

  const handleNewGame = () => {
    if (currentGame) {
      Alert.alert(
        'Active Game Exists',
        'There is already an active game. Please close it before starting a new one.',
        [
          { text: 'Cancel', style: 'cancel' },
          { text: 'View Game', onPress: () => router.push('/game') }
        ]
      );
      return;
    }
    router.push('/players');
  };

  const handleContinueGame = () => {
    if (currentGame) {
      router.push('/game');
    }
  };

  return (
    <ScrollView 
      style={styles.container}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
      }
    >
      {/* Header */}
      <View style={styles.header}>
        <View style={styles.headerContent}>
          <Text style={styles.headerTitle}>{t.poker_club_manager}</Text>
          <Text style={styles.headerSubtitle}>{t.manage_chips_players_sessions}</Text>
        </View>
        
        {/* Language Toggle */}
        <TouchableOpacity 
          style={styles.languageToggle}
          onPress={() => setLanguage(language === 'en' ? 'es' : 'en')}
        >
          <Ionicons name="language" size={20} color="#fff" />
          <Text style={styles.languageText}>{language.toUpperCase()}</Text>
        </TouchableOpacity>
      </View>

      {/* Quick Stats */}
      {dashboardData && (
        <View style={styles.statsContainer}>
          <View style={styles.statCard}>
            <Ionicons name="people" size={32} color="#4CAF50" />
            <Text style={styles.statNumber}>{dashboardData.total_players}</Text>
            <Text style={styles.statLabel}>{t.players}</Text>
          </View>
          
          <View style={styles.statCard}>
            <Ionicons name="game-controller" size={32} color="#2196F3" />
            <Text style={styles.statNumber}>{dashboardData.active_games}</Text>
            <Text style={styles.statLabel}>{t.active_games}</Text>
          </View>
        </View>
      )}

      {/* Credit/Debt Summary */}
      {dashboardData && (
        <View style={styles.balanceContainer}>
          <View style={styles.balanceCard}>
            <View style={styles.balanceHeader}>
              <Ionicons name="trending-up" size={24} color="#4CAF50" />
              <Text style={styles.balanceTitle}>{t.credit_owed}</Text>
            </View>
            <Text style={styles.creditAmount}>${dashboardData.total_credit_owed.toFixed(2)}</Text>
            <Text style={styles.balanceSubtitle}>{t.money_owed_to_players}</Text>
          </View>

          <View style={styles.balanceCard}>
            <View style={styles.balanceHeader}>
              <Ionicons name="trending-down" size={24} color="#f44336" />
              <Text style={styles.balanceTitle}>{t.debt_owed}</Text>
            </View>
            <Text style={styles.debtAmount}>${dashboardData.total_debt_owed.toFixed(2)}</Text>
            <Text style={styles.balanceSubtitle}>{t.money_owed_by_players}</Text>
          </View>
        </View>
      )}

      {/* Game Actions */}
      <View style={styles.actionsContainer}>
        {currentGame ? (
          <TouchableOpacity style={styles.continueButton} onPress={handleContinueGame}>
            <Ionicons name="play" size={24} color="#fff" />
            <Text style={styles.buttonText}>Continue Game: {currentGame.name}</Text>
          </TouchableOpacity>
        ) : (
          <TouchableOpacity style={styles.newGameButton} onPress={handleNewGame}>
            <Ionicons name="add-circle" size={24} color="#fff" />
            <Text style={styles.buttonText}>New Game Session</Text>
          </TouchableOpacity>
        )}

        <TouchableOpacity 
          style={styles.secondaryButton} 
          onPress={() => router.push('/players')}
        >
          <Ionicons name="people" size={24} color="#2E7D32" />
          <Text style={styles.secondaryButtonText}>Manage Players</Text>
        </TouchableOpacity>

        <TouchableOpacity 
          style={styles.secondaryButton} 
          onPress={() => router.push('/history')}
        >
          <Ionicons name="time" size={24} color="#2E7D32" />
          <Text style={styles.secondaryButtonText}>Game History</Text>
        </TouchableOpacity>

        <TouchableOpacity 
          style={styles.secondaryButton} 
          onPress={() => router.push('/reports')}
        >
          <Ionicons name="bar-chart" size={24} color="#2E7D32" />
          <Text style={styles.secondaryButtonText}>Player Reports</Text>
        </TouchableOpacity>
      </View>

      {/* Recent Transactions */}
      {dashboardData && dashboardData.recent_transactions.length > 0 && (
        <View style={styles.recentContainer}>
          <Text style={styles.sectionTitle}>Recent Transactions</Text>
          {dashboardData.recent_transactions.slice(0, 5).map((transaction, index) => (
            <View key={index} style={styles.transactionItem}>
              <View style={styles.transactionLeft}>
                <Text style={styles.transactionPlayer}>{transaction.player_name}</Text>
                <Text style={styles.transactionType}>{transaction.transaction_type.replace('_', ' ')}</Text>
              </View>
              <Text style={styles.transactionAmount}>${transaction.amount}</Text>
            </View>
          ))}
        </View>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  header: {
    backgroundColor: '#2E7D32',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 24,
  },
  headerContent: {
    flex: 1,
  },
  languageToggle: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 20,
    gap: 4,
  },
  languageText: {
    color: '#fff',
    fontSize: 12,
    fontWeight: '600',
  },
  headerTitle: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#fff',
    textAlign: 'center',
  },
  headerSubtitle: {
    fontSize: 16,
    color: '#C8E6C9',
    textAlign: 'center',
    marginTop: 8,
  },
  statsContainer: {
    flexDirection: 'row',
    padding: 16,
    gap: 16,
  },
  statCard: {
    flex: 1,
    backgroundColor: '#fff',
    padding: 16,
    borderRadius: 12,
    alignItems: 'center',
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
  },
  statNumber: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#333',
    marginTop: 8,
  },
  statLabel: {
    fontSize: 14,
    color: '#666',
    marginTop: 4,
  },
  balanceContainer: {
    flexDirection: 'row',
    paddingHorizontal: 16,
    paddingBottom: 16,
    gap: 16,
  },
  balanceCard: {
    flex: 1,
    backgroundColor: '#fff',
    padding: 16,
    borderRadius: 12,
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
  },
  balanceHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  balanceTitle: {
    fontSize: 16,
    fontWeight: '600',
    marginLeft: 8,
    color: '#333',
  },
  creditAmount: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#4CAF50',
  },
  debtAmount: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#f44336',
  },
  balanceSubtitle: {
    fontSize: 12,
    color: '#666',
    marginTop: 4,
  },
  actionsContainer: {
    padding: 16,
    gap: 12,
  },
  newGameButton: {
    backgroundColor: '#4CAF50',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 16,
    borderRadius: 12,
    gap: 8,
  },
  continueButton: {
    backgroundColor: '#2196F3',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 16,
    borderRadius: 12,
    gap: 8,
  },
  secondaryButton: {
    backgroundColor: '#fff',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 16,
    borderRadius: 12,
    borderWidth: 2,
    borderColor: '#2E7D32',
    gap: 8,
  },
  buttonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  secondaryButtonText: {
    color: '#2E7D32',
    fontSize: 16,
    fontWeight: '600',
  },
  recentContainer: {
    margin: 16,
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 16,
  },
  transactionItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  transactionLeft: {
    flex: 1,
  },
  transactionPlayer: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
  },
  transactionType: {
    fontSize: 14,
    color: '#666',
    textTransform: 'capitalize',
  },
  transactionAmount: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#2E7D32',
  },
});