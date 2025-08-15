import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  Alert,
  TextInput,
  Modal,
  KeyboardAvoidingView,
  Platform,
  Image,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import * as ImagePicker from 'expo-image-picker';
import { useGame } from '../context/GameContext';
import { useRouter } from 'expo-router';

export default function PlayersScreen() {
  const router = useRouter();
  const { players, createPlayer, updatePlayer, deletePlayer, fetchPlayers, createGame, isLoading } = useGame();
  const [showAddPlayer, setShowAddPlayer] = useState(false);
  const [showEditPlayer, setShowEditPlayer] = useState(false);
  const [editingPlayer, setEditingPlayer] = useState<any>(null);
  const [newPlayerName, setNewPlayerName] = useState('');
  const [newPlayerPhoto, setNewPlayerPhoto] = useState<string | null>(null);
  const [editPlayerName, setEditPlayerName] = useState('');
  const [editPlayerBalance, setEditPlayerBalance] = useState('');
  const [editPlayerPhoto, setEditPlayerPhoto] = useState<string | null>(null);
  const [selectedPlayers, setSelectedPlayers] = useState<Set<string>>(new Set());
  const [showNewGame, setShowNewGame] = useState(false);
  const [gameName, setGameName] = useState('');

  const openAddPlayerModal = () => {
    // Reset all state when opening modal
    setNewPlayerName('');
    setNewPlayerPhoto(null);
    setShowAddPlayer(true);
  };

  const openEditPlayerModal = (player: any) => {
    // Debug logs to check player data and photo
    console.log('Opening edit modal for player:', player);
    console.log('Player photo:', player.photo);
    console.log('Player photo exists:', !!player.photo);
    
    // Reset and set proper state when opening edit modal
    setEditingPlayer(player);
    setEditPlayerName(player.name);
    setEditPlayerBalance(player.current_balance.toString());
    setEditPlayerPhoto(player.photo || null);
    
    // Debug log to check what was set
    console.log('Set editPlayerPhoto to:', player.photo || null);
    
    setShowEditPlayer(true);
  };

  const pickImage = async (isEditing = false) => {
    // Request permission
    const permissionResult = await ImagePicker.requestMediaLibraryPermissionsAsync();
    
    if (permissionResult.granted === false) {
      Alert.alert('Permission Required', 'Permission to access camera roll is required!');
      return;
    }

    // Open image picker
    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      allowsEditing: true,
      aspect: [1, 1], // Square aspect ratio for circular photos
      quality: 0.5, // Reduce quality to keep base64 size manageable
      base64: true,
    });

    if (!result.canceled && result.assets[0].base64) {
      const base64 = `data:image/jpeg;base64,${result.assets[0].base64}`;
      if (isEditing) {
        setEditPlayerPhoto(base64);
      } else {
        setNewPlayerPhoto(base64);
      }
    }
  };

  const handleAddPlayer = async () => {
    if (newPlayerName.trim()) {
      try {
        await createPlayer(newPlayerName.trim(), newPlayerPhoto || undefined);
        setNewPlayerName('');
        setNewPlayerPhoto(null);
        setShowAddPlayer(false);
      } catch (error) {
        Alert.alert('Error', 'Failed to create player. Please try again.');
      }
    }
  };

  const handleEditPlayer = openEditPlayerModal;

  const handleUpdatePlayer = async () => {
    if (!editingPlayer || !editPlayerName.trim()) {
      Alert.alert('Error', 'Please enter a valid name.');
      return;
    }

    try {
      const balance = parseFloat(editPlayerBalance) || editingPlayer.current_balance;
      await updatePlayer(editingPlayer.id, editPlayerName.trim(), balance, editPlayerPhoto || undefined);
      setShowEditPlayer(false);
      setEditingPlayer(null);
      setEditPlayerName('');
      setEditPlayerBalance('');
      setEditPlayerPhoto(null);
    } catch (error) {
      Alert.alert('Error', 'Failed to update player. Please try again.');
    }
  };

  const handleDeletePlayer = async (player: any) => {
    // Check if player.id exists
    if (!player.id) {
      const errorMessage = 'Invalid player data. Cannot delete player.';
      if (Platform.OS === 'web') {
        window.alert(errorMessage);
      } else {
        Alert.alert('Error', errorMessage);
      }
      return;
    }
    
    // Use platform-specific confirmation dialog
    let confirmed = false;
    
    try {
      console.log('Starting delete process for player:', player.name, 'ID:', player.id);
      
      if (Platform.OS === 'web') {
        confirmed = window.confirm(`Are you sure you want to delete ${player.name}?`);
      } else {
        confirmed = await new Promise<boolean>((resolve) => {
          Alert.alert(
            'Delete Player',
            `Are you sure you want to delete ${player.name}?`,
            [
              { text: 'Cancel', style: 'cancel', onPress: () => resolve(false) },
              { text: 'Delete', style: 'destructive', onPress: () => resolve(true) }
            ]
          );
        });
      }
      
      console.log('User confirmation result:', confirmed);
      
      if (!confirmed) {
        console.log('User cancelled deletion');
        return; // User cancelled
      }
      
      console.log('Proceeding with deletion...');
      await deletePlayer(player.id);
      console.log('Delete API call completed successfully');
      
      // Refresh the player list
      await fetchPlayers();
      console.log('Player list refreshed');
      
    } catch (error: any) {
      console.error('Delete player error:', error);
      const errorMessage = error.message || 'Failed to delete player. They may be in an active game.';
      
      if (Platform.OS === 'web') {
        window.alert(`Delete Failed: ${errorMessage}`);
      } else {
        Alert.alert('Delete Failed', errorMessage);
      }
    }
  };

  const togglePlayerSelection = (playerId: string) => {
    const newSelected = new Set(selectedPlayers);
    if (newSelected.has(playerId)) {
      newSelected.delete(playerId);
    } else {
      newSelected.add(playerId);
    }
    setSelectedPlayers(newSelected);
  };

  const handleStartGame = async () => {
    if (selectedPlayers.size < 2) {
      Alert.alert('Error', 'Please select at least 2 players to start a game.');
      return;
    }
    
    if (!gameName.trim()) {
      Alert.alert('Error', 'Please enter a game name.');
      return;
    }

    await createGame(gameName, Array.from(selectedPlayers));
    setShowNewGame(false);
    setSelectedPlayers(new Set());
    setGameName('');
    router.push('/game');
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

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity 
          style={styles.backButton}
          onPress={() => router.back()}
        >
          <Ionicons name="arrow-back" size={24} color="#fff" />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Players</Text>
        <TouchableOpacity onPress={openAddPlayerModal}>
          <Ionicons name="add" size={24} color="#fff" />
        </TouchableOpacity>
      </View>

      {/* Action Buttons */}
      <View style={styles.actionContainer}>
        {!showNewGame ? (
          <>
            <TouchableOpacity 
              style={styles.selectButton}
              onPress={() => setShowNewGame(true)}
            >
              <Ionicons name="game-controller" size={20} color="#fff" />
              <Text style={styles.buttonText}>Start New Game</Text>
            </TouchableOpacity>
            
            {/* Help Text */}
            <View style={styles.helpContainer}>
              <Text style={styles.helpText}>
                👆 Tap "Start New Game" to select players and begin!
              </Text>
            </View>
          </>
        ) : (
          <>
            {/* Game Name Input */}
            <View style={styles.gameSetupContainer}>
              <Text style={styles.setupTitle}>🎮 Create New Game</Text>
              <TextInput
                style={styles.gameNameInput}
                placeholder="Game name (e.g., Friday Night)"
                value={gameName}
                onChangeText={setGameName}
              />
              
              <Text style={styles.selectionTitle}>
                Select Players ({selectedPlayers.size} selected)
              </Text>
              <Text style={styles.selectionInstruction}>
                👇 Tap players below to select them for the game
              </Text>
            </View>

            {/* Action Buttons */}
            <View style={styles.gameActionButtons}>
              <TouchableOpacity 
                style={styles.cancelGameButton}
                onPress={() => {
                  setShowNewGame(false);
                  setSelectedPlayers(new Set());
                  setGameName('');
                }}
              >
                <Text style={styles.cancelGameButtonText}>Cancel</Text>
              </TouchableOpacity>
              
              <TouchableOpacity 
                style={[
                  styles.startGameButton,
                  { opacity: selectedPlayers.size < 2 || !gameName.trim() ? 0.5 : 1 }
                ]}
                onPress={handleStartGame}
                disabled={selectedPlayers.size < 2 || !gameName.trim()}
              >
                <Text style={styles.startGameButtonText}>Start Game</Text>
              </TouchableOpacity>
            </View>
          </>
        )}
      </View>

      {/* Players List */}
      <ScrollView style={styles.playersList}>
        {players.map((player) => (
          <View key={player.id} style={styles.playerCard}>
            <TouchableOpacity
              style={[
                styles.playerContent,
                selectedPlayers.has(player.id) && styles.selectedPlayer
              ]}
              onPress={() => showNewGame && togglePlayerSelection(player.id)}
            >
              {/* Circular Photo */}
              <View style={styles.photoContainer}>
                {player.photo ? (
                  <Image source={{ uri: player.photo }} style={styles.playerPhoto} />
                ) : (
                  <View style={styles.defaultPhoto}>
                    <Ionicons name="person" size={24} color="#1976D2" />
                  </View>
                )}
              </View>

              <View style={styles.playerInfo}>
                <Text style={styles.playerName}>{player.name}</Text>
                <Text style={styles.playerStats}>
                  Total Played: ${player.total_played.toFixed(2)}
                </Text>
              </View>
              
              <View style={styles.balanceContainer}>
                <Text style={[styles.balanceAmount, { color: getBalanceColor(player.current_balance) }]}>
                  {formatBalance(player.current_balance)}
                </Text>
                <Text style={styles.balanceLabel}>
                  {player.current_balance > 0 ? 'Credit' : player.current_balance < 0 ? 'Debt' : 'Even'}
                </Text>
              </View>

              {showNewGame && (
                <View style={styles.checkboxContainer}>
                  <Ionicons 
                    name={selectedPlayers.has(player.id) ? "checkbox" : "square-outline"} 
                    size={24} 
                    color="#1976D2" 
                  />
                </View>
              )}
            </TouchableOpacity>

            {/* Action Buttons - Always Visible when not in game selection mode */}
            {!showNewGame && (
              <View style={styles.playerActions}>
                <TouchableOpacity 
                  style={styles.editButton}
                  onPress={() => openEditPlayerModal(player)}
                >
                  <Ionicons name="pencil" size={16} color="#1976D2" />
                  <Text style={styles.editButtonText}>Edit</Text>
                </TouchableOpacity>
                
                <TouchableOpacity 
                  style={styles.deleteButton}
                  onPress={() => handleDeletePlayer(player)}
                >
                  <Ionicons name="trash" size={16} color="#f44336" />
                  <Text style={styles.deleteButtonText}>Delete</Text>
                </TouchableOpacity>
              </View>
            )}
          </View>
        ))}

        {players.length === 0 && (
          <View style={styles.emptyState}>
            <Ionicons name="people-outline" size={64} color="#ccc" />
            <Text style={styles.emptyText}>No players yet</Text>
            <Text style={styles.emptySubtext}>Add your first player to get started</Text>
          </View>
        )}
      </ScrollView>

      {/* Add Player Modal */}
      <Modal visible={showAddPlayer} transparent animationType="slide">
        <KeyboardAvoidingView 
          style={styles.modalOverlay}
          behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        >
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>Add New Player</Text>
            
            {/* Photo Selection */}
            <View style={styles.photoSelectionContainer}>
              <Text style={styles.photoLabel}>Player Photo</Text>
              <TouchableOpacity style={styles.photoButton} onPress={() => pickImage(false)}>
                {newPlayerPhoto ? (
                  <Image source={{ uri: newPlayerPhoto }} style={styles.photoPreview} />
                ) : (
                  <View style={styles.photoPlaceholder}>
                    <Ionicons name="camera" size={24} color="#1976D2" />
                    <Text style={styles.photoButtonText}>Add Photo</Text>
                  </View>
                )}
              </TouchableOpacity>
            </View>
            
            <TextInput
              style={styles.input}
              placeholder="Player name"
              value={newPlayerName}
              onChangeText={setNewPlayerName}
              autoFocus
            />
            
            <View style={styles.modalButtons}>
              <TouchableOpacity 
                style={styles.cancelButton}
                onPress={() => {
                  setShowAddPlayer(false);
                  setNewPlayerName('');
                  setNewPlayerPhoto(null); // CRITICAL FIX: Reset photo state
                }}
              >
                <Text style={styles.cancelButtonText}>Cancel</Text>
              </TouchableOpacity>
              
              <TouchableOpacity 
                style={styles.addButton}
                onPress={handleAddPlayer}
                disabled={!newPlayerName.trim()}
              >
                <Text style={styles.addButtonText}>Add Player</Text>
              </TouchableOpacity>
            </View>
          </View>
        </KeyboardAvoidingView>
      </Modal>

      {/* Edit Player Modal */}
      <Modal visible={showEditPlayer} transparent animationType="slide">
        <KeyboardAvoidingView 
          style={styles.modalOverlay}
          behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        >
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>Edit Player</Text>
            
            {/* Photo Selection */}
            <View style={styles.photoSelectionContainer}>
              <Text style={styles.photoLabel}>Player Photo</Text>
              <TouchableOpacity style={styles.photoButton} onPress={() => pickImage(true)}>
                {editPlayerPhoto ? (
                  <Image source={{ uri: editPlayerPhoto }} style={styles.photoPreview} />
                ) : (
                  <View style={styles.photoPlaceholder}>
                    <Ionicons name="camera" size={24} color="#1976D2" />
                    <Text style={styles.photoButtonText}>Add Photo</Text>
                  </View>
                )}
              </TouchableOpacity>
            </View>
            
            <TextInput
              style={styles.input}
              placeholder="Player name"
              value={editPlayerName}
              onChangeText={setEditPlayerName}
              autoFocus
            />

            <TextInput
              style={styles.input}
              placeholder="Current balance"
              value={editPlayerBalance}
              onChangeText={setEditPlayerBalance}
              keyboardType="numeric"
            />
            
            <View style={styles.modalButtons}>
              <TouchableOpacity 
                style={styles.cancelButton}
                onPress={() => {
                  setShowEditPlayer(false);
                  setEditingPlayer(null);
                  setEditPlayerName('');
                  setEditPlayerBalance('');
                  setEditPlayerPhoto(null); // CRITICAL FIX: Reset photo state
                }}
              >
                <Text style={styles.cancelButtonText}>Cancel</Text>
              </TouchableOpacity>
              
              <TouchableOpacity 
                style={styles.addButton}
                onPress={handleUpdatePlayer}
                disabled={!editPlayerName.trim()}
              >
                <Text style={styles.addButtonText}>Update Player</Text>
              </TouchableOpacity>
            </View>
          </View>
        </KeyboardAvoidingView>
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  header: {
    backgroundColor: '#1976D2',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 16,
  },
  backButton: {
    padding: 8,
    marginLeft: -8,
    borderRadius: 8,
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#fff',
  },
  actionContainer: {
    padding: 16,
  },
  selectButton: {
    backgroundColor: '#1976D2',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 12,
    borderRadius: 8,
    gap: 8,
  },
  helpContainer: {
    backgroundColor: '#E8F5E9',
    padding: 12,
    borderRadius: 8,
    marginTop: 8,
    alignItems: 'center',
  },
  helpText: {
    fontSize: 14,
    color: '#1976D2',
    textAlign: 'center',
    fontWeight: '500',
  },
  gameSetupContainer: {
    backgroundColor: '#E3F2FD',
    padding: 16,
    borderRadius: 12,
    marginBottom: 12,
  },
  setupTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#1976D2',
    textAlign: 'center',
    marginBottom: 12,
  },
  gameNameInput: {
    backgroundColor: '#fff',
    borderWidth: 1,
    borderColor: '#BBDEFB',
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
    marginBottom: 12,
  },
  selectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1976D2',
    marginBottom: 4,
  },
  selectionInstruction: {
    fontSize: 14,
    color: '#1976D2',
    textAlign: 'center',
  },
  gameActionButtons: {
    flexDirection: 'row',
    gap: 12,
  },
  cancelGameButton: {
    flex: 1,
    backgroundColor: '#fff',
    borderWidth: 2,
    borderColor: '#ddd',
    borderRadius: 8,
    padding: 12,
    alignItems: 'center',
  },
  cancelGameButtonText: {
    color: '#666',
    fontSize: 16,
    fontWeight: '600',
  },
  startGameButton: {
    flex: 1,
    backgroundColor: '#1976D2',
    borderRadius: 8,
    padding: 12,
    alignItems: 'center',
  },
  startGameButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  buttonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  playersList: {
    flex: 1,
    padding: 16,
  },
  playerCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    marginBottom: 8,
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
  },
  playerContent: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    gap: 12,
  },
  photoContainer: {
    width: 50,
    height: 50,
    borderRadius: 25,
    overflow: 'hidden',
  },
  playerPhoto: {
    width: 50,
    height: 50,
    borderRadius: 25,
  },
  defaultPhoto: {
    width: 50,
    height: 50,
    borderRadius: 25,
    backgroundColor: '#E3F2FD',
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 2,
    borderColor: '#1976D2',
  },
  playerActions: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    paddingHorizontal: 16,
    paddingBottom: 12,
    borderTopWidth: 1,
    borderTopColor: '#f0f0f0',
    gap: 12,
  },
  editButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#E3F2FD',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    flex: 1,
    justifyContent: 'center',
    gap: 4,
  },
  editButtonText: {
    color: '#1976D2',
    fontSize: 14,
    fontWeight: '600',
  },
  deleteButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFEBEE',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    flex: 1,
    justifyContent: 'center',
    gap: 4,
  },
  deleteButtonText: {
    color: '#f44336',
    fontSize: 14,
    fontWeight: '600',
  },
  selectedPlayer: {
    backgroundColor: '#E8F5E8',
    borderColor: '#2E7D32',
    borderWidth: 2,
  },
  playerInfo: {
    flex: 1,
  },
  playerName: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
  },
  playerStats: {
    fontSize: 14,
    color: '#666',
    marginTop: 4,
  },
  balanceContainer: {
    alignItems: 'flex-end',
    marginRight: 8,
  },
  balanceAmount: {
    fontSize: 18,
    fontWeight: 'bold',
  },
  balanceLabel: {
    fontSize: 12,
    color: '#666',
    marginTop: 2,
  },
  checkboxContainer: {
    marginLeft: 8,
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
  input: {
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 8,
    color: '#333',
  },
  instruction: {
    fontSize: 14,
    color: '#666',
    marginBottom: 16,
    textAlign: 'center',
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
    backgroundColor: '#1976D2',
    padding: 12,
    borderRadius: 8,
    alignItems: 'center',
  },
  addButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  photoSelectionContainer: {
    marginBottom: 16,
  },
  photoLabel: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
    marginBottom: 8,
  },
  photoButton: {
    width: 100,
    height: 100,
    borderRadius: 8,
    borderWidth: 2,
    borderColor: '#1976D2',
    borderStyle: 'dashed',
    alignItems: 'center',
    justifyContent: 'center',
    alignSelf: 'center',
    marginBottom: 8,
  },
  photoPreview: {
    width: 96,
    height: 96,
    borderRadius: 6,
  },
  photoPlaceholder: {
    alignItems: 'center',
    justifyContent: 'center',
  },
  photoButtonText: {
    fontSize: 12,
    color: '#1976D2',
    marginTop: 4,
    textAlign: 'center',
  },
});