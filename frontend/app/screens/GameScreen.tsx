import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  Alert,
  Modal,
  TextInput,
  KeyboardAvoidingView,
  Platform,
  Image,
} from 'react-native';
import { Ionicons, MaterialIcons } from '@expo/vector-icons';
import { useGame } from '../context/GameContext';
import { useRouter } from 'expo-router';

const TRANSACTION_TYPES = [
  { key: 'cash', label: 'Cash', icon: 'cash', color: '#4CAF50' },
  { key: 'bank_transfer', label: 'Bank Transfer', icon: 'card', color: '#2196F3' },
  { key: 'credit', label: 'Credit', icon: 'trending-down', color: '#FF9800' },
  { key: 'cashed_out', label: 'Cashed Out', icon: 'trending-up', color: '#9C27B0' },
  { key: 'paid_with_chips', label: 'Paid with Chips', icon: 'swap-horizontal', color: '#607D8B' },
  { key: 'pay_credit', label: 'Pay Credit', icon: 'remove-circle', color: '#E91E63' },
];

export default function GameScreen() {
  const router = useRouter();
  const { currentGame, players, transactions, closeCurrentGame, createTransaction, fetchGameTransactions, addPlayerToGame } = useGame();
  const [showTransactionModal, setShowTransactionModal] = useState(false);
  const [showAddPlayerModal, setShowAddPlayerModal] = useState(false);
  const [selectedPlayer, setSelectedPlayer] = useState<any>(null);
  const [selectedTransactionType, setSelectedTransactionType] = useState('');
  const [amount, setAmount] = useState('');
  const [description, setDescription] = useState('');

  useEffect(() => {
    if (currentGame) {
      fetchGameTransactions(currentGame.id);
    }
  }, [currentGame]);

  const handleTransaction = (playerId: string, transactionType: string) => {
    const player = players.find(p => p.id === playerId);
    setSelectedPlayer(player);
    setSelectedTransactionType(transactionType);
    setShowTransactionModal(true);
  };

  const submitTransaction = async () => {
    if (!selectedPlayer || !selectedTransactionType || !currentGame) return;

    let transactionAmount = 0;
    
    // Handle cashed out - player enters amount they want to cash out
    if (selectedTransactionType === 'cashed_out') {
      if (!amount || parseFloat(amount) <= 0) {
        Alert.alert('Error', 'Please enter a valid cash out amount.');
        return;
      }
      transactionAmount = parseFloat(amount);
    } else if (selectedTransactionType === 'paid_with_chips') {
      // For paid with chips, validate amount against what they can actually pay
      if (!amount || parseFloat(amount) <= 0) {
        Alert.alert('Error', 'Please enter a valid amount.');
        return;
      }
      transactionAmount = parseFloat(amount);
      
      // Show confirmation for large payments
      const newBalance = selectedPlayer.current_balance + transactionAmount;
      if (transactionAmount > 1000) {
        const confirmed = await new Promise((resolve) => {
          Alert.alert(
            'Confirm Large Payment',
            `Player will pay $${transactionAmount.toFixed(2)} with chips.\nCurrent balance: ${formatBalance(selectedPlayer.current_balance)}\nNew balance: ${formatBalance(newBalance)}`,
            [
              { text: 'Cancel', onPress: () => resolve(false) },
              { text: 'Confirm', onPress: () => resolve(true) }
            ]
          );
        });
        if (!confirmed) return;
      }
    } else if (selectedTransactionType === 'pay_credit') {
      // For pay credit, validate amount and check if player has debt to pay
      if (!amount || parseFloat(amount) <= 0) {
        Alert.alert('Error', 'Please enter a valid payment amount.');
        return;
      }
      
      if (selectedPlayer.current_balance >= 0) {
        Alert.alert('Error', 'This player has no debt to pay. Current balance is not negative.');
        return;
      }
      
      transactionAmount = parseFloat(amount);
      const debt = Math.abs(selectedPlayer.current_balance);
      
      if (transactionAmount > debt) {
        Alert.alert('Error', `Payment amount ($${transactionAmount.toFixed(2)}) cannot exceed current debt ($${debt.toFixed(2)}).`);
        return;
      }
      
      // Show confirmation for payment
      const newBalance = selectedPlayer.current_balance + transactionAmount;
      const confirmed = await new Promise((resolve) => {
        Alert.alert(
          'Confirm Credit Payment',
          `Player will pay $${transactionAmount.toFixed(2)} to reduce their debt.\nCurrent debt: $${debt.toFixed(2)}\nRemaining debt after payment: $${Math.abs(newBalance).toFixed(2)}${newBalance >= 0 ? ' (Paid in full)' : ''}`,
          [
            { text: 'Cancel', onPress: () => resolve(false) },
            { text: 'Confirm Payment', onPress: () => resolve(true) }
          ]
        );
      });
      if (!confirmed) return;
    } else {
      // For other transactions, require amount
      if (!amount || parseFloat(amount) <= 0) {
        Alert.alert('Error', 'Please enter a valid amount.');
        return;
      }
      transactionAmount = parseFloat(amount);
    }

    try {
      await createTransaction(
        currentGame.id, 
        selectedPlayer.id, 
        selectedTransactionType, 
        transactionAmount,
        description || undefined
      );
      
      setShowTransactionModal(false);
      setAmount('');
      setDescription('');
      setSelectedPlayer(null);
      setSelectedTransactionType('');
    } catch (error) {
      Alert.alert('Error', 'Failed to create transaction. Please try again.');
      console.error('Transaction error:', error);
    }
  };

  const handleCloseGame = () => {
    if (!currentGame) {
      Alert.alert('Error', 'No active game to close.');
      return;
    }

    // Check if all players have cashed out (balance should be 0 or negative for debt)
    const playersWithBalance = currentGame.players.filter(gamePlayer => {
      const player = players.find(p => p.id === gamePlayer.player_id);
      return player && player.current_balance > 0; // Positive balance means they haven't cashed out
    });

    if (playersWithBalance.length > 0) {
      const playerNames = playersWithBalance.map(gamePlayer => {
        const player = players.find(p => p.id === gamePlayer.player_id);
        return player?.name;
      }).join(', ');
      
      Alert.alert(
        'Cannot Close Game',
        `The following players still have credits and must cash out first: ${playerNames}`,
        [{ text: 'OK' }]
      );
      return;
    }

    Alert.alert(
      'Close Game',
      'All players have cashed out. Are you sure you want to close this game? All balances will be finalized.',
      [
        { text: 'Cancel', style: 'cancel' },
        { 
          text: 'Close Game', 
          style: 'destructive',
          onPress: async () => {
            try {
              console.log('Closing game from UI:', currentGame.id);
              await closeCurrentGame();
              console.log('Game closed successfully, navigating home');
              router.push('/');
            } catch (error) {
              console.error('Error in handleCloseGame:', error);
              Alert.alert(
                'Error Closing Game', 
                error.message || 'Failed to close the game. Please try again.',
                [{ text: 'OK' }]
              );
            }
          }
        }
      ]
    );
  };

  const getBalanceColor = (balance: number) => {
    if (balance > 0) return '#4CAF50'; // Green for positive (credit owed to player)
    if (balance < 0) return '#f44336'; // Red for negative (debt from player)
    return '#666'; // Gray for zero
  };

  const formatBalance = (balance: number) => {
    const absBalance = Math.abs(balance);
    const formattedAmount = formatMoney(absBalance);
    return balance >= 0 ? `+$${formattedAmount}` : `-$${formattedAmount}`;
  };

  const formatMoney = (amount: number) => {
    // Remove .00 if the amount is a whole number, add commas for thousands
    if (amount % 1 === 0) {
      return amount.toLocaleString('en-US');
    } else {
      return amount.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    }
  };

  const getTransactionTypeInfo = (type: string) => {
    return TRANSACTION_TYPES.find(t => t.key === type) || TRANSACTION_TYPES[0];
  };

  if (!currentGame) {
    return (
      <View style={styles.noGameContainer}>
        <Ionicons name="game-controller-outline" size={64} color="#ccc" />
        <Text style={styles.noGameText}>No active game</Text>
        <TouchableOpacity 
          style={styles.startGameButton}
          onPress={() => router.push('/players')}
        >
          <Text style={styles.startGameButtonText}>Start New Game</Text>
        </TouchableOpacity>
      </View>
    );
  }

  // Calculate total chips in play (only for this game)
  const totalChipsInPlay = currentGame.players.reduce((total, gamePlayer) => {
    return total + (gamePlayer.chips_in_game || 0);
  }, 0);

  return (
    <View style={styles.container}>
      {/* Game Header */}
      <View style={styles.gameHeader}>
        <View style={styles.headerLeft}>
          <Text style={styles.gameTitle}>{currentGame.name}</Text>
          <Text style={styles.gameDate}>
            {new Date(currentGame.date).toLocaleDateString()}
          </Text>
          {/* Total Table Amount */}
          <Text style={styles.totalTableAmount}>
            Total Table: ${formatMoney(totalChipsInPlay)}
          </Text>
        </View>
        
        <View style={styles.headerActions}>
          <TouchableOpacity 
            style={styles.addPlayerButton} 
            onPress={() => setShowAddPlayerModal(true)}
          >
            <Ionicons name="person-add" size={20} color="#fff" />
            <Text style={styles.addPlayerText}>Add Player</Text>
          </TouchableOpacity>
          
          <TouchableOpacity style={styles.closeGameButton} onPress={handleCloseGame}>
            <Ionicons name="stop-circle" size={24} color="#fff" />
            <Text style={styles.closeGameText}>Close Game</Text>
          </TouchableOpacity>
        </View>
      </View>

      {/* Players Table */}
      <ScrollView style={styles.playersContainer}>
        {currentGame.players.map((gamePlayer) => {
          const player = players.find(p => p.id === gamePlayer.player_id);
          if (!player) return null;

          return (
            <View key={player.id} style={styles.playerRow}>
              {/* Player Photo */}
              <View style={styles.playerPhotoContainer}>
                {player.photo ? (
                  <Image 
                    source={{ uri: player.photo }} 
                    style={styles.playerPhoto}
                  />
                ) : (
                  <View style={styles.placeholderPhoto}>
                    <MaterialIcons name="person" size={24} color="#999" />
                  </View>
                )}
                {/* Cash Out Status Indicator */}
                {player.current_balance <= 0 && (
                  <View style={styles.cashedOutIndicator}>
                    <Ionicons name="checkmark-circle" size={16} color="#4CAF50" />
                  </View>
                )}
              </View>
              
              {/* Player Info and Balance */}
              <View style={styles.playerInfoWithBalance}>
                <View style={styles.playerInfoLeft}>
                  <Text style={styles.playerName}>{player.name}</Text>
                  {player.current_balance <= 0 && (
                    <Text style={styles.cashedOutLabel}>CASHED OUT</Text>
                  )}
                  <Text style={styles.startingBalance}>
                    Started: {formatBalance(gamePlayer.starting_balance)}
                  </Text>
                  <Text style={styles.totalPlayed}>
                    Chips in Game: ${formatMoney(Math.max(0, gamePlayer.chips_in_game || 0))}
                  </Text>
                </View>

                {/* Player Balance/Debt on the right */}
                <View style={styles.playerBalanceRight}>
                  <Text style={[styles.currentBalance, { color: getBalanceColor(player.current_balance) }]}>
                    {formatBalance(Math.abs(player.current_balance))}
                  </Text>
                  <Text style={styles.balanceLabel}>
                    {player.current_balance > 0 ? 'Owed to Player' : player.current_balance < 0 ? 'Player Owes' : 'Even'}
                  </Text>
                </View>
              </View>

              {/* Transaction Buttons */}
              <View style={styles.actionsContainer}>
                {TRANSACTION_TYPES.map((type, index) => (
                  <TouchableOpacity
                    key={type.key}
                    style={[styles.actionButton, { backgroundColor: type.color }]}
                    onPress={() => handleTransaction(player.id, type.key)}
                  >
                    <Ionicons name={type.icon as any} size={14} color="#fff" />
                    <Text style={styles.actionButtonText}>{type.label}</Text>
                  </TouchableOpacity>
                ))}
              </View>
            </View>
          );
        })}
      </ScrollView>

      {/* Recent Transactions */}
      <View style={styles.transactionsContainer}>
        <Text style={styles.sectionTitle}>Recent Transactions</Text>
        <ScrollView style={styles.transactionsList}>
          {transactions.slice(-10).reverse().map((transaction) => {
            const typeInfo = getTransactionTypeInfo(transaction.transaction_type);
            return (
              <View key={transaction.id} style={styles.transactionItem}>
                <View style={styles.transactionLeft}>
                  <View style={styles.transactionHeader}>
                    <Ionicons name={typeInfo.icon as any} size={16} color={typeInfo.color} />
                    <Text style={styles.transactionPlayer}>{transaction.player_name}</Text>
                  </View>
                  <Text style={styles.transactionType}>{typeInfo.label}</Text>
                  {transaction.description && (
                    <Text style={styles.transactionDescription}>{transaction.description}</Text>
                  )}
                </View>
                <View style={styles.transactionRight}>
                  <Text style={styles.transactionAmount}>${formatMoney(transaction.amount)}</Text>
                  <Text style={styles.transactionTime}>
                    {new Date(transaction.timestamp).toLocaleTimeString()}
                  </Text>
                </View>
              </View>
            );
          })}
        </ScrollView>
      </View>

      {/* Transaction Modal */}
      <Modal visible={showTransactionModal} transparent animationType="slide">
        <KeyboardAvoidingView 
          style={styles.modalOverlay}
          behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        >
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>Add Transaction</Text>
            
            {selectedPlayer && (
              <View style={styles.playerSummary}>
                <Text style={styles.playerSummaryName}>{selectedPlayer.name}</Text>
                <Text style={styles.playerSummaryBalance}>
                  Current Balance: {formatBalance(selectedPlayer.current_balance)}
                </Text>
              </View>
            )}

            {selectedTransactionType && (
              <View style={styles.transactionTypeSummary}>
                <Text style={styles.transactionTypeTitle}>
                  {getTransactionTypeInfo(selectedTransactionType).label}
                </Text>
                <Text style={styles.transactionTypeDescription}>
                  {selectedTransactionType === 'cash' && 'Player buys chips with cash (no balance change)'}
                  {selectedTransactionType === 'bank_transfer' && 'Player buys chips via bank transfer (no balance change)'}
                  {selectedTransactionType === 'credit' && 'Player receives chips on credit (creates debt)'}
                  {selectedTransactionType === 'cashed_out' && 'Player cashes out winnings (enter amount won)'}
                  {selectedTransactionType === 'paid_with_chips' && 'Player pays debt or creates credit with chips'}
                  {selectedTransactionType === 'pay_credit' && 'Player pays off existing debt with cash/transfer (not chips)'}
                </Text>
              </View>
            )}

            <TextInput
              style={styles.input}
              placeholder="Amount"
              value={amount}
              onChangeText={setAmount}
              keyboardType="numeric"
              autoFocus
            />

            <TextInput
              style={styles.input}
              placeholder="Description (optional)"
              value={description}
              onChangeText={setDescription}
              multiline
            />
            
            <View style={styles.modalButtons}>
              <TouchableOpacity 
                style={styles.cancelButton}
                onPress={() => {
                  setShowTransactionModal(false);
                  setAmount('');
                  setDescription('');
                }}
              >
                <Text style={styles.cancelButtonText}>Cancel</Text>
              </TouchableOpacity>
              
              <TouchableOpacity 
                style={styles.addButton}
                onPress={submitTransaction}
              >
                <Text style={styles.addButtonText}>ADD</Text>
              </TouchableOpacity>
            </View>
          </View>
        </KeyboardAvoidingView>
      </Modal>

      {/* Add Player Modal */}
      <Modal visible={showAddPlayerModal} transparent animationType="slide">
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>Add Player to Game</Text>
            
            <Text style={styles.instruction}>
              Select a player to add to the current game. They will join with their current balance.
            </Text>

            <ScrollView style={styles.availablePlayersList}>
              {players
                .filter(player => !currentGame?.players.some(p => p.player_id === player.id))
                .map((player) => (
                <TouchableOpacity
                  key={player.id}
                  style={styles.availablePlayerCard}
                  onPress={async () => {
                    try {
                      if (currentGame) {
                        await addPlayerToGame(currentGame.id, player.id);
                        setShowAddPlayerModal(false);
                        // Refresh the current game data
                        const updatedGames = await fetch(`${process.env.EXPO_PUBLIC_BACKEND_URL}/api/games`).then(r => r.json());
                        const updatedCurrentGame = updatedGames.find((g: any) => g.id === currentGame.id);
                        if (updatedCurrentGame) {
                          // This will be handled by the context automatically
                        }
                      }
                    } catch (error) {
                      Alert.alert('Error', 'Failed to add player to game. Please try again.');
                    }
                  }}
                >
                  <View style={styles.availablePlayerInfo}>
                    <Text style={styles.availablePlayerName}>{player.name}</Text>
                    <Text style={styles.availablePlayerBalance}>
                      Current Balance: {formatBalance(player.current_balance)}
                    </Text>
                  </View>
                  <Ionicons name="add-circle" size={24} color="#4CAF50" />
                </TouchableOpacity>
              ))}
              
              {players.filter(player => !currentGame?.players.some(p => p.player_id === player.id)).length === 0 && (
                <View style={styles.noPlayersAvailable}>
                  <Ionicons name="people-outline" size={48} color="#ccc" />
                  <Text style={styles.noPlayersText}>All players are already in the game</Text>
                </View>
              )}
            </ScrollView>
            
            <TouchableOpacity 
              style={styles.cancelButton}
              onPress={() => setShowAddPlayerModal(false)}
            >
              <Text style={styles.cancelButtonText}>Cancel</Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  noGameContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 32,
  },
  noGameText: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#999',
    marginTop: 16,
    marginBottom: 24,
  },
  startGameButton: {
    backgroundColor: '#2E7D32',
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 8,
  },
  startGameButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  gameHeader: {
    backgroundColor: '#2E7D32',
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
  },
  headerLeft: {
    flex: 1,
  },
  totalTableAmount: {
    color: '#A5D6A7',
    fontSize: 16,
    fontWeight: 'bold',
    marginTop: 4,
  },
  headerActions: {
    flexDirection: 'column',
    alignItems: 'flex-end',
    gap: 8,
  },
  addPlayerButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#4CAF50',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 6,
    gap: 4,
  },
  addPlayerText: {
    color: '#fff',
    fontSize: 12,
    fontWeight: '600',
  },
  gameTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#fff',
  },
  gameDate: {
    fontSize: 14,
    color: '#C8E6C9',
    marginTop: 4,
  },
  closeGameButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#f44336',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 8,
    gap: 4,
  },
  closeGameText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '600',
  },
  playersContainer: {
    flex: 1,
    padding: 16,
  },
  playerRow: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 12,
    marginBottom: 4,
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    gap: 12,
  },
  playerInfoWithBalance: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginLeft: 12,
  },
  playerInfoLeft: {
    flex: 1,
  },
  playerBalanceRight: {
    alignItems: 'flex-end',
    minWidth: 100,
    marginLeft: 8,
  },
  playerPhotoContainer: {
    width: 50,
    height: 50,
    borderRadius: 25,
    overflow: 'hidden',
    backgroundColor: '#f0f0f0',
    justifyContent: 'center',
    alignItems: 'center',
    position: 'relative',
  },
  cashedOutIndicator: {
    position: 'absolute',
    bottom: -2,
    right: -2,
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 2,
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.2,
    shadowRadius: 2,
  },
  playerPhoto: {
    width: 50,
    height: 50,
    borderRadius: 25,
  },
  placeholderPhoto: {
    width: 50,
    height: 50,
    borderRadius: 25,
    backgroundColor: '#e0e0e0',
    justifyContent: 'center',
    alignItems: 'center',
  },
  playerInfo: {
    marginBottom: 8,
  },
  playerNameRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 4,
  },
  playerName: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
  },
  cashedOutLabel: {
    fontSize: 10,
    color: '#4CAF50',
    fontWeight: 'bold',
    backgroundColor: '#E8F5E8',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
  },
  playerInfoRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  playerStatsRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  playerStat: {
    fontSize: 14,
    color: '#666',
  },
  startingBalance: {
    fontSize: 14,
    color: '#666',
    marginTop: 4,
  },
  totalPlayed: {
    fontSize: 14,
    color: '#4CAF50',
    marginTop: 2,
    fontWeight: '600',
  },
  currentBalanceContainer: {
    alignItems: 'center',
    marginBottom: 16,
  },
  currentBalance: {
    fontSize: 24,
    fontWeight: 'bold',
  },
  balanceLabel: {
    fontSize: 12,
    color: '#666',
    marginTop: 2,
  },
  actionsContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
    gap: 8,
  },
  actionButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 8,
    paddingVertical: 6,
    borderRadius: 6,
    minWidth: '30%',
    flex: 1,
    maxWidth: '32%',
    gap: 4,
    justifyContent: 'center',
  },
  actionButtonText: {
    color: '#fff',
    fontSize: 12,
    fontWeight: '600',
  },
  transactionsContainer: {
    backgroundColor: '#fff',
    maxHeight: 200,
    borderTopWidth: 1,
    borderTopColor: '#e0e0e0',
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
    padding: 16,
    paddingBottom: 8,
  },
  transactionsList: {
    paddingHorizontal: 16,
    paddingBottom: 16,
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
  transactionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  transactionPlayer: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
  },
  transactionType: {
    fontSize: 14,
    color: '#666',
    marginTop: 2,
  },
  transactionDescription: {
    fontSize: 12,
    color: '#999',
    marginTop: 2,
    fontStyle: 'italic',
  },
  transactionRight: {
    alignItems: 'flex-end',
  },
  transactionAmount: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#2E7D32',
  },
  transactionTime: {
    fontSize: 12,
    color: '#666',
    marginTop: 2,
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  modalContent: {
    backgroundColor: '#fff',
    width: '90%',
    borderRadius: 12,
    padding: 24,
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    textAlign: 'center',
    marginBottom: 16,
    color: '#333',
  },
  playerSummary: {
    backgroundColor: '#f5f5f5',
    padding: 16,
    borderRadius: 8,
    marginBottom: 16,
  },
  playerSummaryName: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
  },
  playerSummaryBalance: {
    fontSize: 14,
    color: '#666',
    marginTop: 4,
  },
  transactionTypeSummary: {
    marginBottom: 16,
  },
  transactionTypeTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 4,
  },
  transactionTypeDescription: {
    fontSize: 14,
    color: '#666',
    lineHeight: 20,
  },
  input: {
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
    marginBottom: 16,
  },
  modalButtons: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    gap: 12,
  },
  cancelButton: {
    flex: 1,
    padding: 12,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#ddd',
    alignItems: 'center',
  },
  cancelButtonText: {
    color: '#666',
    fontSize: 16,
    fontWeight: '600',
  },
  addButton: {
    flex: 1,
    backgroundColor: '#2E7D32',
    padding: 12,
    borderRadius: 8,
    alignItems: 'center',
  },
  addButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  availablePlayersList: {
    maxHeight: 300,
    marginVertical: 16,
  },
  availablePlayerCard: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: '#f9f9f9',
    padding: 12,
    borderRadius: 8,
    marginBottom: 8,
  },
  availablePlayerInfo: {
    flex: 1,
  },
  availablePlayerName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
  },
  availablePlayerBalance: {
    fontSize: 14,
    color: '#666',
    marginTop: 2,
  },
  noPlayersAvailable: {
    alignItems: 'center',
    padding: 32,
  },
  noPlayersText: {
    fontSize: 16,
    color: '#999',
    textAlign: 'center',
    marginTop: 8,
  },
  instruction: {
    fontSize: 14,
    color: '#666',
    textAlign: 'center',
    lineHeight: 20,
  },
});