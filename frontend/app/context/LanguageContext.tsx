import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';

type Language = 'en' | 'es';

interface Translations {
  // Home Screen
  poker_club_manager: string;
  manage_chips_players_sessions: string;
  players: string;
  active_games: string;
  credit_owed: string;
  debt_owed: string;
  money_owed_to_players: string;
  money_owed_by_players: string;
  continue_game: string;
  new_game_session: string;
  manage_players: string;
  game_history: string;
  player_reports: string;
  recent_transactions: string;
  
  // Player Management
  add_new_player: string;
  start_new_game: string;
  player_name: string;
  cancel: string;
  add_player: string;
  total_played: string;
  credit: string;
  debt: string;
  even: string;
  
  // Game Screen
  active_game: string;
  close_game: string;
  add_player: string;
  started: string;
  cash: string;
  bank_transfer: string;
  credit_transaction: string;
  cashed_out: string;
  paid_with_chips: string;
  
  // Transaction Descriptions
  cash_description: string;
  bank_transfer_description: string;
  credit_description: string;
  cashed_out_description: string;
  paid_chips_description: string;
  
  // Common
  amount: string;
  description: string;
  optional: string;
  confirm: string;
  error: string;
  success: string;
  loading: string;
  
  // Reports
  export_csv: string;
  net_house: string;
  games_played: string;
  cash_spent: string;
  bank_transfers: string;
  credit_taken: string;
}

const translations: Record<Language, Translations> = {
  en: {
    // Home Screen
    poker_club_manager: 'Poker Club Manager',
    manage_chips_players_sessions: 'Manage chips, players, and sessions',
    players: 'Players',
    active_games: 'Active Games',
    credit_owed: 'Credit Owed',
    debt_owed: 'Debt Owed',
    money_owed_to_players: 'Money owed to players',
    money_owed_by_players: 'Money owed by players',
    continue_game: 'Continue Game',
    new_game_session: 'New Game Session',
    manage_players: 'Manage Players',
    game_history: 'Game History',
    player_reports: 'Player Reports',
    recent_transactions: 'Recent Transactions',
    
    // Player Management
    add_new_player: 'Add New Player',
    start_new_game: 'Start New Game',
    player_name: 'Player name',
    cancel: 'Cancel',
    add_player: 'Add Player',
    total_played: 'Total Played',
    credit: 'Credit',
    debt: 'Debt',
    even: 'Even',
    
    // Game Screen
    active_game: 'Active Game',
    close_game: 'Close Game',
    add_player: 'Add Player',
    started: 'Started',
    cash: 'Cash',
    bank_transfer: 'Bank Transfer',
    credit_transaction: 'Credit',
    cashed_out: 'Cashed Out',
    paid_with_chips: 'Paid with Chips',
    
    // Transaction Descriptions
    cash_description: 'Player buys chips with cash (no balance change)',
    bank_transfer_description: 'Player buys chips via bank transfer (no balance change)',
    credit_description: 'Player receives chips on credit (creates debt)',
    cashed_out_description: 'Player cashes out winnings (enter amount won)',
    paid_chips_description: 'Player pays debt or creates credit with chips',
    
    // Common
    amount: 'Amount',
    description: 'Description',
    optional: 'optional',
    confirm: 'Confirm',
    error: 'Error',
    success: 'Success',
    loading: 'Loading',
    
    // Reports
    export_csv: 'Export to CSV',
    net_house: 'Net House',
    games_played: 'Games Played',
    cash_spent: 'Cash Spent',
    bank_transfers: 'Bank Transfers',
    credit_taken: 'Credit Taken',
  },
  es: {
    // Home Screen
    poker_club_manager: 'Gestor de Club de Póker',
    manage_chips_players_sessions: 'Gestiona fichas, jugadores y sesiones',
    players: 'Jugadores',
    active_games: 'Juegos Activos',
    credit_owed: 'Crédito Adeudado',
    debt_owed: 'Deuda Adeudada',
    money_owed_to_players: 'Dinero adeudado a jugadores',
    money_owed_by_players: 'Dinero adeudado por jugadores',
    continue_game: 'Continuar Juego',
    new_game_session: 'Nueva Sesión de Juego',
    manage_players: 'Gestionar Jugadores',
    game_history: 'Historial de Juegos',
    player_reports: 'Reportes de Jugadores',
    recent_transactions: 'Transacciones Recientes',
    
    // Player Management
    add_new_player: 'Agregar Nuevo Jugador',
    start_new_game: 'Iniciar Nuevo Juego',
    player_name: 'Nombre del jugador',
    cancel: 'Cancelar',
    add_player: 'Agregar Jugador',
    total_played: 'Total Jugado',
    credit: 'Crédito',
    debt: 'Deuda',
    even: 'Parejo',
    
    // Game Screen
    active_game: 'Juego Activo',
    close_game: 'Cerrar Juego',
    add_player: 'Agregar Jugador',
    started: 'Comenzó',
    cash: 'Efectivo',
    bank_transfer: 'Transferencia',
    credit_transaction: 'Crédito',
    cashed_out: 'Cobrado',
    paid_with_chips: 'Pagó con Fichas',
    
    // Transaction Descriptions
    cash_description: 'Jugador compra fichas con efectivo (sin cambio de balance)',
    bank_transfer_description: 'Jugador compra fichas por transferencia (sin cambio de balance)',
    credit_description: 'Jugador recibe fichas a crédito (crea deuda)',
    cashed_out_description: 'Jugador cobra ganancias (ingrese monto ganado)',
    paid_chips_description: 'Jugador paga deuda o crea crédito con fichas',
    
    // Common
    amount: 'Monto',
    description: 'Descripción',
    optional: 'opcional',
    confirm: 'Confirmar',
    error: 'Error',
    success: 'Éxito',
    loading: 'Cargando',
    
    // Reports
    export_csv: 'Exportar a CSV',
    net_house: 'Casa Neta',
    games_played: 'Juegos Jugados',
    cash_spent: 'Efectivo Gastado',
    bank_transfers: 'Transferencias',
    credit_taken: 'Crédito Tomado',
  }
};

interface LanguageContextType {
  language: Language;
  setLanguage: (lang: Language) => void;
  t: Translations;
}

const LanguageContext = createContext<LanguageContextType | undefined>(undefined);

interface LanguageProviderProps {
  children: ReactNode;
}

export default function LanguageProvider({ children }: LanguageProviderProps) {
  const [language, setLanguageState] = useState<Language>('en');

  useEffect(() => {
    loadLanguage();
  }, []);

  const loadLanguage = async () => {
    try {
      const savedLanguage = await AsyncStorage.getItem('app_language');
      if (savedLanguage && (savedLanguage === 'en' || savedLanguage === 'es')) {
        setLanguageState(savedLanguage as Language);
      }
    } catch (error) {
      console.error('Error loading language:', error);
    }
  };

  const setLanguage = async (lang: Language) => {
    try {
      await AsyncStorage.setItem('app_language', lang);
      setLanguageState(lang);
    } catch (error) {
      console.error('Error saving language:', error);
    }
  };

  const contextValue: LanguageContextType = {
    language,
    setLanguage,
    t: translations[language],
  };

  return (
    <LanguageContext.Provider value={contextValue}>
      {children}
    </LanguageContext.Provider>
  );
}

export const useLanguage = () => {
  const context = useContext(LanguageContext);
  if (context === undefined) {
    throw new Error('useLanguage must be used within a LanguageProvider');
  }
  return context;
};