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
import { useRouter } from 'expo-router';

interface HistoryGame {
  id: string;
  name: string;
  date: string;
  players: Array<{
    player_id: string;
    player_name: string;
    starting_balance: number;
  }>;
  status: 'active' | 'closed';
  final_balances: Record<string, number>;
  created_date: string;
}

export default function HistoryScreen() {
  const router = useRouter();
  const { games, fetchGames, isLoading, setCurrentGame } = useGame();
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    fetchGames();
  }, []);

  const onRefresh = async () => {
    setRefreshing(true);
    await fetchGames();
    setRefreshing(false);
  };

  const handleGamePress = (game: any) => {
    if (game.status === 'active') {
      setCurrentGame(game);
      navigation.navigate('Game' as never);
    } else {
      // Show game details for closed games
      showGameDetails(game);
    }
  };

  const showGameDetails = (game: any) => {
    const playerDetails = game.players.map((p: any) => {
      const finalBalance = game.final_balances[p.player_id] || 0;
      const change = finalBalance - p.starting_balance;
      return `${p.player_name}: ${formatBalance(p.starting_balance)} → ${formatBalance(finalBalance)} (${change >= 0 ? '+' : ''}${change.toFixed(2)})`;
    }).join('\n');

    Alert.alert(
      `${game.name} - Details`,
      `Date: ${new Date(game.date).toLocaleDateString()}\nStatus: ${game.status}\n\nPlayer Results:\n${playerDetails}`,
      [{ text: 'OK' }]
    );
  };

  const exportGameData = (game: any) => {
    // This would implement CSV export functionality
    Alert.alert('Export', 'Export functionality coming soon!');
  };

  const formatBalance = (balance: number) => {
    const absBalance = Math.abs(balance);
    return balance >= 0 ? `+$${absBalance.toFixed(2)}` : `-$${absBalance.toFixed(2)}`;
  };

  const getGameStatusColor = (status: string) => {
    return status === 'active' ? '#4CAF50' : '#666';
  };

  const getGameStatusIcon = (status: string) => {
    return status === 'active' ? 'play-circle' : 'checkmark-circle';
  };

  const calculateGameTotals = (game: any) => {
    if (game.status === 'closed') {
      const totalWinnings = Object.values(game.final_balances).reduce((sum: number, balance: any) => {
        return sum + Math.max(0, balance);
      }, 0);
      const totalLosses = Object.values(game.final_balances).reduce((sum: number, balance: any) => {
        return sum + Math.abs(Math.min(0, balance));
      }, 0);
      return { totalWinnings, totalLosses };
    }
    return { totalWinnings: 0, totalLosses: 0 };
  };

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()}>
          <Ionicons name="arrow-back" size={24} color="#fff" />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Game History</Text>
        <TouchableOpacity onPress={() => Alert.alert('Export', 'Export all data coming soon!')}>
          <Ionicons name="download" size={24} color="#fff" />
        </TouchableOpacity>
      </View>

      {/* Games List */}
      <ScrollView 
        style={styles.gamesList}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
      >
        {games.map((game: any) => {
          const totals = calculateGameTotals(game);
          return (
            <TouchableOpacity
              key={game.id}
              style={[
                styles.gameCard,
                game.status === 'active' && styles.activeGameCard
              ]}
              onPress={() => handleGamePress(game)}
            >
              <View style={styles.gameHeader}>
                <View style={styles.gameTitle}>
                  <Text style={styles.gameName}>{game.name}</Text>
                  <Text style={styles.gameDate}>
                    {new Date(game.date).toLocaleDateString()}
                  </Text>
                </View>
                
                <View style={styles.gameStatus}>
                  <Ionicons 
                    name={getGameStatusIcon(game.status) as any} 
                    size={20} 
                    color={getGameStatusColor(game.status)} 
                  />
                  <Text style={[styles.statusText, { color: getGameStatusColor(game.status) }]}>
                    {game.status.charAt(0).toUpperCase() + game.status.slice(1)}
                  </Text>
                </View>
              </View>

              <View style={styles.gameDetails}>
                <Text style={styles.playersCount}>
                  {game.players.length} players
                </Text>
                
                {game.status === 'closed' && (
                  <View style={styles.gameTotals}>
                    <View style={styles.totalItem}>
                      <Ionicons name="trending-up" size={16} color="#4CAF50" />
                      <Text style={styles.totalWinnings}>
                        +${totals.totalWinnings.toFixed(2)}
                      </Text>
                    </View>
                    <View style={styles.totalItem}>
                      <Ionicons name="trending-down" size={16} color="#f44336" />
                      <Text style={styles.totalLosses}>
                        -${totals.totalLosses.toFixed(2)}
                      </Text>
                    </View>
                  </View>
                )}
              </View>

              {/* Player Summary */}
              <View style={styles.playerSummary}>
                {game.players.slice(0, 3).map((player: any, index: number) => {
                  const finalBalance = game.final_balances[player.player_id] || player.starting_balance;
                  return (
                    <View key={player.player_id} style={styles.playerItem}>
                      <Text style={styles.playerName}>{player.player_name}</Text>
                      <Text style={[
                        styles.playerBalance,
                        { color: finalBalance >= 0 ? '#4CAF50' : '#f44336' }
                      ]}>
                        {formatBalance(finalBalance)}
                      </Text>
                    </View>
                  );
                })}
                {game.players.length > 3 && (
                  <Text style={styles.morePlayersText}>
                    +{game.players.length - 3} more
                  </Text>
                )}
              </View>

              {/* Actions */}
              <View style={styles.gameActions}>
                <TouchableOpacity 
                  style={styles.actionButton}
                  onPress={() => showGameDetails(game)}
                >
                  <Ionicons name="eye" size={16} color="#2E7D32" />
                  <Text style={styles.actionButtonText}>Details</Text>
                </TouchableOpacity>
                
                {game.status === 'closed' && (
                  <TouchableOpacity 
                    style={styles.actionButton}
                    onPress={() => exportGameData(game)}
                  >
                    <Ionicons name="share" size={16} color="#2E7D32" />
                    <Text style={styles.actionButtonText}>Export</Text>
                  </TouchableOpacity>
                )}
              </View>
            </TouchableOpacity>
          );
        })}

        {games.length === 0 && !isLoading && (
          <View style={styles.emptyState}>
            <Ionicons name="time-outline" size={64} color="#ccc" />
            <Text style={styles.emptyText}>No games yet</Text>
            <Text style={styles.emptySubtext}>Start your first game to see history here</Text>
          </View>
        )}
      </ScrollView>
    </View>
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
    padding: 16,
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#fff',
  },
  gamesList: {
    flex: 1,
    padding: 16,
  },
  gameCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
  },
  activeGameCard: {
    borderColor: '#4CAF50',
    borderWidth: 2,
    backgroundColor: '#F1F8E9',
  },
  gameHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  gameTitle: {
    flex: 1,
  },
  gameName: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
  },
  gameDate: {
    fontSize: 14,
    color: '#666',
    marginTop: 2,
  },
  gameStatus: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  statusText: {
    fontSize: 14,
    fontWeight: '600',
  },
  gameDetails: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  playersCount: {
    fontSize: 14,
    color: '#666',
  },
  gameTotals: {
    flexDirection: 'row',
    gap: 16,
  },
  totalItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  totalWinnings: {
    fontSize: 14,
    fontWeight: '600',
    color: '#4CAF50',
  },
  totalLosses: {
    fontSize: 14,
    fontWeight: '600',
    color: '#f44336',
  },
  playerSummary: {
    marginBottom: 12,
  },
  playerItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 2,
  },
  playerName: {
    fontSize: 14,
    color: '#333',
  },
  playerBalance: {
    fontSize: 14,
    fontWeight: '600',
  },
  morePlayersText: {
    fontSize: 12,
    color: '#666',
    fontStyle: 'italic',
    textAlign: 'center',
    marginTop: 4,
  },
  gameActions: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    borderTopWidth: 1,
    borderTopColor: '#f0f0f0',
    paddingTop: 12,
  },
  actionButton: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 8,
    gap: 4,
  },
  actionButtonText: {
    fontSize: 14,
    color: '#2E7D32',
    fontWeight: '600',
  },
  emptyState: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingTop: 64,
  },
  emptyText: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#999',
    marginTop: 16,
  },
  emptySubtext: {
    fontSize: 16,
    color: '#ccc',
    textAlign: 'center',
    marginTop: 8,
  },
});