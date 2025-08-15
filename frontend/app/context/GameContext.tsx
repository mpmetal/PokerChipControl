import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';

interface Player {
  id: string;
  name: string;
  current_balance: number;
  total_played: number;
  photo?: string;
  created_date: string;
}

interface Game {
  id: string;
  name: string;
  date: string;
  players: Array<{
    player_id: string;
    player_name: string;
    starting_balance: number;
  }>;
  status: 'active' | 'closed';
  transactions: string[];
  final_balances: Record<string, number>;
  created_date: string;
}

interface Transaction {
  id: string;
  game_id: string;
  player_id: string;
  player_name: string;
  transaction_type: 'cash' | 'bank_transfer' | 'credit' | 'cashed_out' | 'paid_with_chips';
  amount: number;
  description?: string;
  timestamp: string;
}

interface GameContextType {
  players: Player[];
  games: Game[];
  currentGame: Game | null;
  transactions: Transaction[];
  isLoading: boolean;
  
  // Player methods
  fetchPlayers: () => Promise<void>;
  createPlayer: (name: string, photo?: string) => Promise<void>;
  updatePlayer: (playerId: string, name?: string, balance?: number, photo?: string) => Promise<void>;
  deletePlayer: (playerId: string) => Promise<void>;
  
  // Game methods
  fetchGames: () => Promise<void>;
  createGame: (name: string, playerIds: string[]) => Promise<void>;
  setCurrentGame: (game: Game) => void;
  closeCurrentGame: () => Promise<void>;
  addPlayerToGame: (gameId: string, playerId: string) => Promise<void>;
  
  // Transaction methods
  fetchGameTransactions: (gameId: string) => Promise<void>;
  createTransaction: (gameId: string, playerId: string, type: string, amount: number, description?: string) => Promise<void>;
  
  // Dashboard
  fetchDashboard: () => Promise<any>;
}

const GameContext = createContext<GameContextType | undefined>(undefined);

const API_BASE_URL = process.env.EXPO_PUBLIC_BACKEND_URL;

interface GameProviderProps {
  children: ReactNode;
}

export function GameProvider({ children }: GameProviderProps) {
  const [players, setPlayers] = useState<Player[]>([]);
  const [games, setGames] = useState<Game[]>([]);
  const [currentGame, setCurrentGameState] = useState<Game | null>(null);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const fetchPlayers = async () => {
    try {
      setIsLoading(true);
      const response = await fetch(`${API_BASE_URL}/api/players`);
      if (response.ok) {
        const data = await response.json();
        setPlayers(data);
      }
    } catch (error) {
      console.error('Error fetching players:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const createPlayer = async (name: string, photo?: string) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/players`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ name, photo }),
      });
      
      if (response.ok) {
        await fetchPlayers(); // Refresh players list
      } else {
        const errorText = await response.text();
        throw new Error(`Failed to create player: ${errorText}`);
      }
    } catch (error) {
      console.error('Error creating player:', error);
      throw error;
    }
  };

  const updatePlayer = async (playerId: string, name?: string, balance?: number, photo?: string) => {
    try {
      const updateData: any = {};
      if (name !== undefined) updateData.name = name;
      if (balance !== undefined) updateData.current_balance = balance;
      if (photo !== undefined) updateData.photo = photo;

      const response = await fetch(`${API_BASE_URL}/api/players/${playerId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(updateData),
      });
      
      if (response.ok) {
        await fetchPlayers(); // Refresh players list
      } else {
        const errorText = await response.text();
        throw new Error(`Failed to update player: ${errorText}`);
      }
    } catch (error) {
      console.error('Error updating player:', error);
      throw error;
    }
  };

  const deletePlayer = async (playerId: string) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/players/${playerId}`, {
        method: 'DELETE',
      });
      
      if (response.ok) {
        await fetchPlayers(); // Refresh players list
      } else {
        const errorText = await response.text();
        throw new Error(`Failed to delete player: ${errorText}`);
      }
    } catch (error) {
      console.error('Error deleting player:', error);
      throw error;
    }
  };

  const fetchGames = async () => {
    try {
      setIsLoading(true);
      const response = await fetch(`${API_BASE_URL}/api/games`);
      if (response.ok) {
        const data = await response.json();
        setGames(data);
        
        // Find active game if exists
        const activeGame = data.find((game: Game) => game.status === 'active');
        if (activeGame) {
          setCurrentGameState(activeGame);
        }
      }
    } catch (error) {
      console.error('Error fetching games:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const createGame = async (name: string, playerIds: string[]) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/games`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ name, player_ids: playerIds }),
      });
      
      if (response.ok) {
        const newGame = await response.json();
        setCurrentGameState(newGame);
        await fetchGames(); // Refresh games list
      }
    } catch (error) {
      console.error('Error creating game:', error);
    }
  };

  const setCurrentGame = (game: Game) => {
    setCurrentGameState(game);
    if (game) {
      fetchGameTransactions(game.id);
    }
  };

  const closeCurrentGame = async () => {
    if (!currentGame) {
      console.log('No current game to close');
      return;
    }
    
    console.log('Attempting to close game:', currentGame.id);
    
    try {
      const response = await fetch(`${API_BASE_URL}/api/games/${currentGame.id}/close`, {
        method: 'POST',
      });
      
      console.log('Close game response status:', response.status);
      
      if (response.ok) {
        const result = await response.json();
        console.log('Game closed successfully:', result);
        setCurrentGameState(null);
        await fetchGames(); // Refresh games list
        await fetchPlayers(); // Refresh players to get updated balances
      } else {
        const errorText = await response.text();
        console.error('Failed to close game:', response.status, errorText);
        throw new Error(`Failed to close game: ${errorText}`);
      }
    } catch (error) {
      console.error('Error closing game:', error);
      throw error; // Re-throw so the UI can handle it
    }
  };

  const fetchGameTransactions = async (gameId: string) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/games/${gameId}/transactions`);
      if (response.ok) {
        const data = await response.json();
        setTransactions(data);
      }
    } catch (error) {
      console.error('Error fetching transactions:', error);
    }
  };

  const createTransaction = async (gameId: string, playerId: string, type: string, amount: number, description?: string) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/games/${gameId}/transactions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          player_id: playerId,
          transaction_type: type,
          amount,
          description,
        }),
      });
      
      if (response.ok) {
        await fetchGameTransactions(gameId);
        await fetchPlayers(); // Refresh players to get updated balances
      }
    } catch (error) {
      console.error('Error creating transaction:', error);
    }
  };

  const addPlayerToGame = async (gameId: string, playerId: string) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/games/${gameId}/add-player`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ player_id: playerId }),
      });
      
      if (response.ok) {
        await fetchGames(); // Refresh games to update current game
        await fetchPlayers(); // Refresh players if needed
      } else {
        const errorText = await response.text();
        throw new Error(`Failed to add player: ${errorText}`);
      }
    } catch (error) {
      console.error('Error adding player to game:', error);
      throw error;
    }
  };

  const fetchDashboard = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/dashboard`);
      if (response.ok) {
        return await response.json();
      }
    } catch (error) {
      console.error('Error fetching dashboard:', error);
    }
  };

  useEffect(() => {
    fetchPlayers();
    fetchGames();
  }, []);

  const contextValue: GameContextType = {
    players,
    games,
    currentGame,
    transactions,
    isLoading,
    fetchPlayers,
    createPlayer,
    updatePlayer,
    deletePlayer,
    fetchGames,
    createGame,
    setCurrentGame,
    closeCurrentGame,
    fetchGameTransactions,
    createTransaction,
    addPlayerToGame,
    fetchDashboard,
  };

  return (
    <GameContext.Provider value={contextValue}>
      {children}
    </GameContext.Provider>
  );
}

export const useGame = () => {
  const context = useContext(GameContext);
  if (context === undefined) {
    throw new Error('useGame must be used within a GameProvider');
  }
  return context;
};