import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  Alert,
  Share,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useGame } from '../context/GameContext';
import { useRouter } from 'expo-router';

interface PlayerReport {
  player_id: string;
  player_name: string;
  total_chips_bought: number;
  total_cash_spent: number;
  total_bank_transfers: number;
  total_credit_taken: number;
  total_paid_with_chips: number;
  total_cashed_out: number;
  current_balance: number;
  net_profit_loss: number;
  games_played: number;
}

export default function ReportsScreen() {
  const router = useRouter();
  const { players, games, fetchPlayers, fetchGames } = useGame();
  const [playerReports, setPlayerReports] = useState<PlayerReport[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    generateReports();
  }, [players, games]);

  const generateReports = async () => {
    setIsLoading(true);
    try {
      const API_BASE_URL = process.env.EXPO_PUBLIC_BACKEND_URL;
      
      const reports: PlayerReport[] = [];
      
      for (const player of players) {
        // Get all transactions for this player
        let totalChipsBought = 0;
        let totalCashSpent = 0;
        let totalBankTransfers = 0;
        let totalCreditTaken = 0;
        let totalPaidWithChips = 0;
        let totalCashedOut = 0;
        let gamesPlayed = 0;
        
        // Get transactions for each game this player participated in
        for (const game of games) {
          const participatedInGame = game.players.some((p: any) => p.player_id === player.id);
          if (participatedInGame) {
            gamesPlayed++;
            
            // Fetch transactions for this game
            const response = await fetch(`${API_BASE_URL}/api/games/${game.id}/transactions`);
            if (response.ok) {
              const transactions = await response.json();
              const playerTransactions = transactions.filter((t: any) => t.player_id === player.id);
              
              for (const transaction of playerTransactions) {
                switch (transaction.transaction_type) {
                  case 'cash':
                    totalCashSpent += transaction.amount;
                    totalChipsBought += transaction.amount;
                    break;
                  case 'bank_transfer':
                    totalBankTransfers += transaction.amount;
                    totalChipsBought += transaction.amount;
                    break;
                  case 'credit':
                    totalCreditTaken += transaction.amount;
                    totalChipsBought += transaction.amount;
                    break;
                  case 'paid_with_chips':
                    totalPaidWithChips += transaction.amount;
                    break;
                  case 'cashed_out':
                    totalCashedOut += transaction.amount;
                    break;
                }
              }
            }
          }
        }
        
        // Calculate net profit/loss
        // Net = (Cashed Out + Paid with Chips) - (Cash Spent + Bank Transfers + Current Debt)
        const currentDebt = Math.max(0, -player.current_balance);
        const currentCredit = Math.max(0, player.current_balance);
        const netProfitLoss = (totalCashedOut + totalPaidWithChips + currentCredit) - (totalCashSpent + totalBankTransfers + totalCreditTaken + currentDebt);
        
        reports.push({
          player_id: player.id,
          player_name: player.name,
          total_chips_bought: totalChipsBought,
          total_cash_spent: totalCashSpent,
          total_bank_transfers: totalBankTransfers,
          total_credit_taken: totalCreditTaken,
          total_paid_with_chips: totalPaidWithChips,
          total_cashed_out: totalCashedOut,
          current_balance: player.current_balance,
          net_profit_loss: netProfitLoss,
          games_played: gamesPlayed,
        });
      }
      
      setPlayerReports(reports);
    } catch (error) {
      console.error('Error generating reports:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const exportToCSV = () => {
    const csvHeaders = [
      'Player Name',
      'Games Played',
      'Total Chips Bought',
      'Cash Spent',
      'Bank Transfers', 
      'Credit Taken',
      'Paid with Chips',
      'Cashed Out',
      'Current Balance',
      'Net Profit/Loss'
    ].join(',');
    
    const csvRows = playerReports.map(report => [
      report.player_name,
      report.games_played,
      formatMoney(report.total_chips_bought),
      formatMoney(report.total_cash_spent),
      formatMoney(report.total_bank_transfers),
      formatMoney(report.total_credit_taken),
      formatMoney(report.total_paid_with_chips),
      formatMoney(report.total_cashed_out),
      formatMoney(Math.abs(report.current_balance)),
      formatMoney(Math.abs(report.net_profit_loss))
    ].join(',')).join('\n');
    
    const csvContent = `${csvHeaders}\n${csvRows}`;
    
    // For mobile, we'll show the CSV content that can be copied
    Alert.alert(
      'Export CSV',
      'CSV data generated. You can copy this data and paste it into Excel:',
      [
        { 
          text: 'Share', 
          onPress: () => Share.share({ message: csvContent, title: 'Poker Reports' })
        },
        { text: 'OK' }
      ]
    );
  };

  const formatCurrency = (amount: number) => {
    const absAmount = Math.abs(amount);
    const formattedAmount = formatMoney(absAmount);
    return amount >= 0 ? `+$${formattedAmount}` : `-$${formattedAmount}`;
  };

  const formatMoney = (amount: number) => {
    // Remove .00 if the amount is a whole number, add commas for thousands
    if (amount % 1 === 0) {
      return amount.toLocaleString('en-US');
    } else {
      return amount.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    }
  };

  const getBalanceColor = (amount: number) => {
    if (amount > 0) return '#4CAF50';
    if (amount < 0) return '#f44336';
    return '#666';
  };

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => router.back()}>
          <Ionicons name="arrow-back" size={24} color="#fff" />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Player Reports</Text>
        <TouchableOpacity onPress={exportToCSV}>
          <Ionicons name="download" size={24} color="#fff" />
        </TouchableOpacity>
      </View>

      {/* Summary Cards */}
      <View style={styles.summaryContainer}>
        <View style={styles.summaryCard}>
          <Text style={styles.summaryTitle}>Total Players</Text>
          <Text style={styles.summaryValue}>{playerReports.length}</Text>
        </View>
        
        <View style={styles.summaryCard}>
          <Text style={styles.summaryTitle}>Total Games</Text>
          <Text style={styles.summaryValue}>{games.length}</Text>
        </View>
        
        <View style={styles.summaryCard}>
          <Text style={styles.summaryTitle}>Net House</Text>
          <Text style={[
            styles.summaryValue,
            { color: getBalanceColor(-playerReports.reduce((sum, p) => sum + p.net_profit_loss, 0)) }
          ]}>
            {formatCurrency(-playerReports.reduce((sum, p) => sum + p.net_profit_loss, 0))}
          </Text>
        </View>
      </View>

      {/* Export Button */}
      <TouchableOpacity style={styles.exportButton} onPress={exportToCSV}>
        <Ionicons name="document-text" size={20} color="#fff" />
        <Text style={styles.exportButtonText}>Export to CSV</Text>
      </TouchableOpacity>

      {/* Player Reports */}
      <ScrollView style={styles.reportsList}>
        {playerReports.map((report) => (
          <View key={report.player_id} style={styles.reportCard}>
            <View style={styles.reportHeader}>
              <Text style={styles.playerName}>{report.player_name}</Text>
              <Text style={[
                styles.netProfitLoss,
                { color: getBalanceColor(report.net_profit_loss) }
              ]}>
                {formatCurrency(report.net_profit_loss)}
              </Text>
            </View>
            
            <View style={styles.reportDetails}>
              <View style={styles.reportRow}>
                <Text style={styles.reportLabel}>Games Played:</Text>
                <Text style={styles.reportValue}>{report.games_played}</Text>
              </View>
              
              <View style={styles.reportRow}>
                <Text style={styles.reportLabel}>Total Chips Bought:</Text>
                <Text style={styles.reportValue}>${formatMoney(report.total_chips_bought)}</Text>
              </View>
              
              <View style={styles.reportRow}>
                <Text style={styles.reportLabel}>Cash Spent:</Text>
                <Text style={styles.reportValue}>${formatMoney(report.total_cash_spent)}</Text>
              </View>
              
              <View style={styles.reportRow}>
                <Text style={styles.reportLabel}>Bank Transfers:</Text>
                <Text style={styles.reportValue}>${formatMoney(report.total_bank_transfers)}</Text>
              </View>
              
              <View style={styles.reportRow}>
                <Text style={styles.reportLabel}>Credit Taken:</Text>
                <Text style={styles.reportValue}>${formatMoney(report.total_credit_taken)}</Text>
              </View>
              
              <View style={styles.reportRow}>
                <Text style={styles.reportLabel}>Paid with Chips:</Text>
                <Text style={styles.reportValue}>${formatMoney(report.total_paid_with_chips)}</Text>
              </View>
              
              <View style={styles.reportRow}>
                <Text style={styles.reportLabel}>Cashed Out:</Text>
                <Text style={styles.reportValue}>${formatMoney(report.total_cashed_out)}</Text>
              </View>
              
              <View style={styles.reportRow}>
                <Text style={styles.reportLabel}>Current Balance:</Text>
                <Text style={[
                  styles.reportValue,
                  { color: getBalanceColor(report.current_balance) }
                ]}>
                  {formatCurrency(report.current_balance)}
                </Text>
              </View>
            </View>
          </View>
        ))}

        {playerReports.length === 0 && !isLoading && (
          <View style={styles.emptyState}>
            <Ionicons name="document-text-outline" size={64} color="#ccc" />
            <Text style={styles.emptyText}>No data available</Text>
            <Text style={styles.emptySubtext}>Play some games to see reports</Text>
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
  summaryContainer: {
    flexDirection: 'row',
    padding: 16,
    gap: 12,
  },
  summaryCard: {
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
  summaryTitle: {
    fontSize: 12,
    color: '#666',
    marginBottom: 4,
  },
  summaryValue: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
  },
  exportButton: {
    backgroundColor: '#4CAF50',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    margin: 16,
    padding: 12,
    borderRadius: 8,
    gap: 8,
  },
  exportButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  reportsList: {
    flex: 1,
    paddingHorizontal: 16,
  },
  reportCard: {
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
  reportHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
    paddingBottom: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  playerName: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
  },
  netProfitLoss: {
    fontSize: 18,
    fontWeight: 'bold',
  },
  reportDetails: {
    gap: 8,
  },
  reportRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  reportLabel: {
    fontSize: 14,
    color: '#666',
  },
  reportValue: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
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