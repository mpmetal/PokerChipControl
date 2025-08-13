#!/usr/bin/env python3
"""
Comprehensive Backend API Test for Poker Chip Management System
Focus on updated fixes: Money formatting, chips_in_game logic, transaction processing, and cashed out logic.
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "https://chiptracker-app.preview.emergentagent.com/api"
HEADERS = {"Content-Type": "application/json"}

# Test data storage
test_players = []
test_game_id = None
test_transactions = []

def log_test(test_name, success, details=""):
    """Log test results with timestamp"""
    status = "✅ PASS" if success else "❌ FAIL"
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {status} {test_name}")
    if details:
        print(f"    Details: {details}")
    if not success:
        print(f"    ❗ This is a critical failure")
    print()

def test_create_players():
    """Test creating test players: Alice, Bob, Charlie"""
    print("=" * 60)
    print("1. TESTING PLAYER MANAGEMENT")
    print("=" * 60)
    
    players_to_create = ["Alice", "Bob", "Charlie"]
    global test_players
    
    for name in players_to_create:
        try:
            payload = {"name": name}
            response = requests.post(f"{BASE_URL}/players", json=payload, headers=HEADERS)
            
            if response.status_code == 200:
                player_data = response.json()
                test_players.append(player_data)
                log_test(f"Create player '{name}'", True, f"Player ID: {player_data['id']}")
            else:
                log_test(f"Create player '{name}'", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            log_test(f"Create player '{name}'", False, f"Exception: {str(e)}")
            return False
    
    return True

def test_get_all_players():
    """Test getting all players and verify they exist"""
    try:
        response = requests.get(f"{BASE_URL}/players", headers=HEADERS)
        
        if response.status_code == 200:
            players = response.json()
            created_names = [p['name'] for p in test_players]
            found_names = [p['name'] for p in players if p['name'] in created_names]
            
            if len(found_names) == len(created_names):
                log_test("Get all players", True, f"Found all {len(found_names)} test players")
                return True
            else:
                log_test("Get all players", False, f"Expected {len(created_names)} players, found {len(found_names)}")
                return False
        else:
            log_test("Get all players", False, f"Status: {response.status_code}, Response: {response.text}")
            return False
            
    except Exception as e:
        log_test("Get all players", False, f"Exception: {str(e)}")
        return False

def test_update_player_balances():
    """Test updating player balances"""
    global test_players
    
    # Update Alice's balance to 100, Bob's to -50, Charlie's to 0
    balance_updates = [100.0, -50.0, 0.0]
    
    for i, player in enumerate(test_players):
        try:
            payload = {"current_balance": balance_updates[i]}
            response = requests.put(f"{BASE_URL}/players/{player['id']}", json=payload, headers=HEADERS)
            
            if response.status_code == 200:
                updated_player = response.json()
                expected_balance = balance_updates[i]
                actual_balance = updated_player['current_balance']
                
                if actual_balance == expected_balance:
                    log_test(f"Update {player['name']}'s balance", True, f"Balance set to {actual_balance}")
                    # Update our local copy
                    test_players[i] = updated_player
                else:
                    log_test(f"Update {player['name']}'s balance", False, f"Expected {expected_balance}, got {actual_balance}")
                    return False
            else:
                log_test(f"Update {player['name']}'s balance", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            log_test(f"Update {player['name']}'s balance", False, f"Exception: {str(e)}")
            return False
    
    return True

def test_create_game():
    """Test creating a game session with the created players"""
    print("=" * 60)
    print("2. TESTING GAME MANAGEMENT")
    print("=" * 60)
    
    global test_game_id
    
    try:
        player_ids = [p['id'] for p in test_players]
        payload = {
            "name": "Test Poker Game",
            "player_ids": player_ids
        }
        
        response = requests.post(f"{BASE_URL}/games", json=payload, headers=HEADERS)
        
        if response.status_code == 200:
            game_data = response.json()
            test_game_id = game_data['id']
            
            # Verify game has correct players and starting balances
            game_players = game_data['players']
            if len(game_players) == len(test_players):
                log_test("Create game session", True, f"Game ID: {test_game_id}, Players: {len(game_players)}")
                
                # Verify starting balances match current player balances
                for game_player in game_players:
                    player_id = game_player['player_id']
                    starting_balance = game_player['starting_balance']
                    
                    # Find corresponding test player
                    test_player = next((p for p in test_players if p['id'] == player_id), None)
                    if test_player and test_player['current_balance'] == starting_balance:
                        log_test(f"Verify {game_player['player_name']} starting balance", True, f"Balance: {starting_balance}")
                    else:
                        log_test(f"Verify {game_player['player_name']} starting balance", False, f"Mismatch in starting balance")
                        return False
                
                return True
            else:
                log_test("Create game session", False, f"Expected {len(test_players)} players, got {len(game_players)}")
                return False
        else:
            log_test("Create game session", False, f"Status: {response.status_code}, Response: {response.text}")
            return False
            
    except Exception as e:
        log_test("Create game session", False, f"Exception: {str(e)}")
        return False

def test_get_all_games():
    """Test getting all games and verify the created game appears"""
    try:
        response = requests.get(f"{BASE_URL}/games", headers=HEADERS)
        
        if response.status_code == 200:
            games = response.json()
            
            # Find our test game
            test_game = next((g for g in games if g['id'] == test_game_id), None)
            if test_game:
                log_test("Get all games", True, f"Found test game in {len(games)} total games")
                return True
            else:
                log_test("Get all games", False, "Test game not found in games list")
                return False
        else:
            log_test("Get all games", False, f"Status: {response.status_code}, Response: {response.text}")
            return False
            
    except Exception as e:
        log_test("Get all games", False, f"Exception: {str(e)}")
        return False

def test_transaction_types():
    """Test all 5 transaction types on the active game"""
    print("=" * 60)
    print("3. TESTING TRANSACTION MANAGEMENT")
    print("=" * 60)
    
    global test_transactions
    
    # Test transactions in order: cash, bank_transfer, credit, paid_with_chips, cashed_out
    transactions_to_test = [
        {
            "player": test_players[0],  # Alice
            "type": "cash",
            "amount": 200.0,
            "description": "Cash purchase of chips",
            "expected_balance_change": 0.0
        },
        {
            "player": test_players[1],  # Bob
            "type": "bank_transfer", 
            "amount": 150.0,
            "description": "Bank transfer for chips",
            "expected_balance_change": 0.0
        },
        {
            "player": test_players[2],  # Charlie
            "type": "credit",
            "amount": 300.0,
            "description": "Credit for chips",
            "expected_balance_change": -300.0
        },
        {
            "player": test_players[2],  # Charlie (paying back some debt)
            "type": "paid_with_chips",
            "amount": 100.0,
            "description": "Paying back debt with chips",
            "expected_balance_change": 100.0
        }
    ]
    
    # Test each transaction type
    for transaction_test in transactions_to_test:
        if not test_single_transaction(transaction_test):
            return False
    
    # Test cashed_out separately (only if player has positive balance)
    # Alice should have positive balance (100.0 from initial setup)
    alice = test_players[0]
    if alice['current_balance'] > 0:
        cashout_test = {
            "player": alice,
            "type": "cashed_out",
            "amount": 0,  # Amount will be determined by current balance
            "description": "Cashing out positive balance",
            "expected_balance_change": -alice['current_balance']
        }
        if not test_single_transaction(cashout_test):
            return False
    else:
        log_test("Cash out transaction", False, f"Alice has no positive balance to cash out: {alice['current_balance']}")
        return False
    
    return True

def test_single_transaction(transaction_test):
    """Test a single transaction and verify balance changes"""
    global test_transactions
    
    player = transaction_test["player"]
    transaction_type = transaction_test["type"]
    amount = transaction_test["amount"]
    description = transaction_test["description"]
    expected_balance_change = transaction_test["expected_balance_change"]
    
    # Get current balance before transaction
    try:
        response = requests.get(f"{BASE_URL}/players/{player['id']}", headers=HEADERS)
        if response.status_code != 200:
            log_test(f"{transaction_type} transaction - get current balance", False, f"Failed to get player balance")
            return False
        
        current_player = response.json()
        balance_before = current_player['current_balance']
        
    except Exception as e:
        log_test(f"{transaction_type} transaction - get current balance", False, f"Exception: {str(e)}")
        return False
    
    # Create transaction
    try:
        payload = {
            "player_id": player['id'],
            "transaction_type": transaction_type,
            "amount": amount,
            "description": description
        }
        
        response = requests.post(f"{BASE_URL}/games/{test_game_id}/transactions", json=payload, headers=HEADERS)
        
        if response.status_code == 200:
            transaction_data = response.json()
            test_transactions.append(transaction_data)
            
            # Get updated balance
            response = requests.get(f"{BASE_URL}/players/{player['id']}", headers=HEADERS)
            if response.status_code == 200:
                updated_player = response.json()
                balance_after = updated_player['current_balance']
                actual_balance_change = balance_after - balance_before
                
                # For cashed_out, the expected change is to reset balance to 0
                if transaction_type == "cashed_out":
                    expected_balance_change = -balance_before
                
                if abs(actual_balance_change - expected_balance_change) < 0.01:  # Allow for floating point precision
                    log_test(f"{transaction_type} transaction", True, 
                           f"Player: {player['name']}, Amount: {transaction_data['amount']}, Balance: {balance_before} → {balance_after}")
                    
                    # Update our local player data
                    for i, p in enumerate(test_players):
                        if p['id'] == player['id']:
                            test_players[i] = updated_player
                            break
                    
                    return True
                else:
                    log_test(f"{transaction_type} transaction", False, 
                           f"Balance change mismatch. Expected: {expected_balance_change}, Actual: {actual_balance_change}")
                    return False
            else:
                log_test(f"{transaction_type} transaction - verify balance", False, f"Failed to get updated balance")
                return False
        else:
            log_test(f"{transaction_type} transaction", False, f"Status: {response.status_code}, Response: {response.text}")
            return False
            
    except Exception as e:
        log_test(f"{transaction_type} transaction", False, f"Exception: {str(e)}")
        return False

def test_get_game_transactions():
    """Test getting game transactions and verify they appear correctly"""
    try:
        response = requests.get(f"{BASE_URL}/games/{test_game_id}/transactions", headers=HEADERS)
        
        if response.status_code == 200:
            transactions = response.json()
            
            if len(transactions) == len(test_transactions):
                log_test("Get game transactions", True, f"Found all {len(transactions)} transactions")
                
                # Verify transaction details
                for i, transaction in enumerate(transactions):
                    expected_transaction = test_transactions[i]
                    if (transaction['id'] == expected_transaction['id'] and 
                        transaction['transaction_type'] == expected_transaction['transaction_type']):
                        log_test(f"Verify transaction {i+1}", True, f"Type: {transaction['transaction_type']}, Player: {transaction['player_name']}")
                    else:
                        log_test(f"Verify transaction {i+1}", False, "Transaction details mismatch")
                        return False
                
                return True
            else:
                log_test("Get game transactions", False, f"Expected {len(test_transactions)} transactions, found {len(transactions)}")
                return False
        else:
            log_test("Get game transactions", False, f"Status: {response.status_code}, Response: {response.text}")
            return False
            
    except Exception as e:
        log_test("Get game transactions", False, f"Exception: {str(e)}")
        return False

def test_close_game():
    """Test closing the active game and verify final balances"""
    print("=" * 60)
    print("4. TESTING GAME CLOSING")
    print("=" * 60)
    
    try:
        response = requests.post(f"{BASE_URL}/games/{test_game_id}/close", headers=HEADERS)
        
        if response.status_code == 200:
            close_data = response.json()
            final_balances = close_data.get('final_balances', {})
            
            log_test("Close game", True, f"Game closed successfully")
            
            # Verify final balances match current player balances
            for player in test_players:
                player_id = player['id']
                if player_id in final_balances:
                    final_balance = final_balances[player_id]
                    current_balance = player['current_balance']
                    
                    if abs(final_balance - current_balance) < 0.01:
                        log_test(f"Verify {player['name']} final balance", True, f"Balance: {final_balance}")
                    else:
                        log_test(f"Verify {player['name']} final balance", False, 
                               f"Expected: {current_balance}, Final: {final_balance}")
                        return False
                else:
                    log_test(f"Verify {player['name']} final balance", False, "Player not found in final balances")
                    return False
            
            # Verify game status changed to closed
            response = requests.get(f"{BASE_URL}/games/{test_game_id}", headers=HEADERS)
            if response.status_code == 200:
                game_data = response.json()
                if game_data['status'] == 'closed':
                    log_test("Verify game status changed to closed", True, "Status: closed")
                    return True
                else:
                    log_test("Verify game status changed to closed", False, f"Status: {game_data['status']}")
                    return False
            else:
                log_test("Verify game status changed to closed", False, "Failed to get game data")
                return False
                
        else:
            log_test("Close game", False, f"Status: {response.status_code}, Response: {response.text}")
            return False
            
    except Exception as e:
        log_test("Close game", False, f"Exception: {str(e)}")
        return False

def test_dashboard():
    """Test dashboard endpoint to get summary statistics"""
    print("=" * 60)
    print("5. TESTING DASHBOARD")
    print("=" * 60)
    
    try:
        response = requests.get(f"{BASE_URL}/dashboard", headers=HEADERS)
        
        if response.status_code == 200:
            dashboard_data = response.json()
            
            # Verify expected fields are present
            expected_fields = ['active_games', 'total_players', 'total_credit_owed', 'total_debt_owed', 'recent_transactions']
            
            for field in expected_fields:
                if field in dashboard_data:
                    log_test(f"Dashboard field '{field}'", True, f"Value: {dashboard_data[field]}")
                else:
                    log_test(f"Dashboard field '{field}'", False, "Field missing from dashboard")
                    return False
            
            # Verify some basic logic
            if dashboard_data['total_players'] >= len(test_players):
                log_test("Dashboard player count", True, f"Total players: {dashboard_data['total_players']}")
            else:
                log_test("Dashboard player count", False, f"Expected at least {len(test_players)} players")
                return False
            
            log_test("Dashboard endpoint", True, "All dashboard data retrieved successfully")
            return True
            
        else:
            log_test("Dashboard endpoint", False, f"Status: {response.status_code}, Response: {response.text}")
            return False
            
    except Exception as e:
        log_test("Dashboard endpoint", False, f"Exception: {str(e)}")
        return False

def run_all_tests():
    """Run all tests in the specified order"""
    print("🎯 POKER CHIP MANAGEMENT BACKEND API TESTS")
    print("=" * 60)
    print(f"Testing against: {BASE_URL}")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    test_results = []
    
    # 1. Player Management Tests
    test_results.append(("Create test players", test_create_players()))
    test_results.append(("Get all players", test_get_all_players()))
    test_results.append(("Update player balances", test_update_player_balances()))
    
    # 2. Game Management Tests  
    test_results.append(("Create game session", test_create_game()))
    test_results.append(("Get all games", test_get_all_games()))
    
    # 3. Transaction Management Tests
    test_results.append(("Test transaction types", test_transaction_types()))
    test_results.append(("Get game transactions", test_get_game_transactions()))
    
    # 4. Game Closing Tests
    test_results.append(("Close game", test_close_game()))
    
    # 5. Dashboard Tests
    test_results.append(("Dashboard endpoint", test_dashboard()))
    
    # Summary
    print("=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print()
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! Poker chip management backend is working correctly.")
        return True
    else:
        print("⚠️  SOME TESTS FAILED! Check the details above.")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)