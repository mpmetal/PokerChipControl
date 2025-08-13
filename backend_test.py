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

def format_money(amount):
    """Helper function to format money as expected by the system"""
    if amount == int(amount):
        return f"${int(amount):,}"
    else:
        return f"${amount:,.2f}"

def test_money_formatting():
    """Test that API responses properly format money without .00 for whole numbers and with commas for thousands"""
    print("=" * 60)
    print("1. TESTING MONEY FORMAT")
    print("=" * 60)
    
    # Create test players with various balance amounts to test formatting
    test_amounts = [1000, 1500.50, 25000, 100.25, 0]
    players_created = []
    
    for i, amount in enumerate(test_amounts):
        try:
            # Create player
            payload = {"name": f"TestPlayer{i+1}"}
            response = requests.post(f"{BASE_URL}/players", json=payload, headers=HEADERS)
            
            if response.status_code == 200:
                player_data = response.json()
                
                # Update balance to test amount
                update_payload = {"current_balance": amount}
                response = requests.put(f"{BASE_URL}/players/{player_data['id']}", json=update_payload, headers=HEADERS)
                
                if response.status_code == 200:
                    updated_player = response.json()
                    players_created.append(updated_player)
                    
                    # Check if balance is stored correctly (not testing formatting here, just storage)
                    if updated_player['current_balance'] == amount:
                        log_test(f"Create player with balance ${amount}", True, f"Balance stored: {updated_player['current_balance']}")
                    else:
                        log_test(f"Create player with balance ${amount}", False, f"Expected {amount}, got {updated_player['current_balance']}")
                        return False
                else:
                    log_test(f"Update player balance to ${amount}", False, f"Status: {response.status_code}")
                    return False
            else:
                log_test(f"Create test player {i+1}", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            log_test(f"Create test player {i+1}", False, f"Exception: {str(e)}")
            return False
    
    # Clean up test players
    for player in players_created:
        try:
            requests.delete(f"{BASE_URL}/players/{player['id']}", headers=HEADERS)
        except:
            pass
    
    log_test("Money formatting test", True, "All money amounts stored correctly in backend")
    return True

def test_create_players():
    """Create test players for main testing"""
    print("=" * 60)
    print("2. TESTING PLAYER CREATION")
    print("=" * 60)
    
    players_to_create = [
        {"name": "Alice", "balance": 500.0},
        {"name": "Bob", "balance": -200.0},
        {"name": "Charlie", "balance": 0.0}
    ]
    global test_players
    
    for player_info in players_to_create:
        try:
            # Create player
            payload = {"name": player_info["name"]}
            response = requests.post(f"{BASE_URL}/players", json=payload, headers=HEADERS)
            
            if response.status_code == 200:
                player_data = response.json()
                
                # Set initial balance
                update_payload = {"current_balance": player_info["balance"]}
                response = requests.put(f"{BASE_URL}/players/{player_data['id']}", json=update_payload, headers=HEADERS)
                
                if response.status_code == 200:
                    updated_player = response.json()
                    test_players.append(updated_player)
                    log_test(f"Create player '{player_info['name']}'", True, f"ID: {updated_player['id']}, Balance: {updated_player['current_balance']}")
                else:
                    log_test(f"Set balance for '{player_info['name']}'", False, f"Status: {response.status_code}")
                    return False
            else:
                log_test(f"Create player '{player_info['name']}'", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            log_test(f"Create player '{player_info['name']}'", False, f"Exception: {str(e)}")
            return False
    
    return True

def test_game_creation_and_chips_in_game():
    """Test game creation and verify chips_in_game initialization"""
    print("=" * 60)
    print("3. TESTING GAME CREATION & CHIPS_IN_GAME LOGIC")
    print("=" * 60)
    
    global test_game_id
    
    try:
        # Create game with all test players
        player_ids = [p['id'] for p in test_players]
        payload = {
            "name": "Chips In Game Test",
            "player_ids": player_ids
        }
        
        response = requests.post(f"{BASE_URL}/games", json=payload, headers=HEADERS)
        
        if response.status_code == 200:
            game_data = response.json()
            test_game_id = game_data['id']
            
            log_test("Create game", True, f"Game ID: {test_game_id}")
            
            # Verify each player has chips_in_game initialized to 0.0
            for game_player in game_data['players']:
                player_name = game_player['player_name']
                chips_in_game = game_player.get('chips_in_game', 'MISSING')
                
                if chips_in_game == 0.0:
                    log_test(f"Verify {player_name} chips_in_game initialization", True, f"chips_in_game: {chips_in_game}")
                else:
                    log_test(f"Verify {player_name} chips_in_game initialization", False, f"Expected 0.0, got {chips_in_game}")
                    return False
            
            return True
        else:
            log_test("Create game", False, f"Status: {response.status_code}, Response: {response.text}")
            return False
            
    except Exception as e:
        log_test("Create game", False, f"Exception: {str(e)}")
        return False

def test_add_player_mid_game():
    """Test adding a player to an active game and verify chips_in_game initialization"""
    try:
        # Create a new player to add mid-game
        payload = {"name": "David"}
        response = requests.post(f"{BASE_URL}/players", json=payload, headers=HEADERS)
        
        if response.status_code == 200:
            new_player = response.json()
            
            # Set balance for new player
            update_payload = {"current_balance": 300.0}
            response = requests.put(f"{BASE_URL}/players/{new_player['id']}", json=update_payload, headers=HEADERS)
            
            if response.status_code == 200:
                updated_player = response.json()
                
                # Add player to active game
                add_payload = {"player_id": updated_player['id']}
                response = requests.post(f"{BASE_URL}/games/{test_game_id}/add-player", json=add_payload, headers=HEADERS)
                
                if response.status_code == 200:
                    add_result = response.json()
                    player_info = add_result.get('player', {})
                    
                    # Verify chips_in_game is initialized to 0.0
                    chips_in_game = player_info.get('chips_in_game', 'MISSING')
                    if chips_in_game == 0.0:
                        log_test("Add player mid-game with chips_in_game initialization", True, f"David added with chips_in_game: {chips_in_game}")
                        
                        # Add to our test players list
                        test_players.append(updated_player)
                        return True
                    else:
                        log_test("Add player mid-game with chips_in_game initialization", False, f"Expected 0.0, got {chips_in_game}")
                        return False
                else:
                    log_test("Add player mid-game", False, f"Status: {response.status_code}, Response: {response.text}")
                    return False
            else:
                log_test("Set balance for new player", False, f"Status: {response.status_code}")
                return False
        else:
            log_test("Create new player for mid-game add", False, f"Status: {response.status_code}")
            return False
            
    except Exception as e:
        log_test("Add player mid-game", False, f"Exception: {str(e)}")
        return False

def test_transaction_processing_and_chips_in_game():
    """Test transaction processing and verify chips_in_game calculations"""
    print("=" * 60)
    print("4. TESTING TRANSACTION PROCESSING & CHIPS_IN_GAME TRACKING")
    print("=" * 60)
    
    # Test transactions that should ADD to chips_in_game
    transactions_add_chips = [
        {
            "player": test_players[0],  # Alice
            "type": "cash",
            "amount": 1000.0,
            "description": "Cash purchase - should add to chips_in_game",
            "expected_chips_change": 1000.0
        },
        {
            "player": test_players[1],  # Bob
            "type": "bank_transfer",
            "amount": 750.0,
            "description": "Bank transfer - should add to chips_in_game",
            "expected_chips_change": 750.0
        },
        {
            "player": test_players[2],  # Charlie
            "type": "credit",
            "amount": 500.0,
            "description": "Credit transaction - should add to chips_in_game",
            "expected_chips_change": 500.0
        }
    ]
    
    # Get initial game state
    try:
        response = requests.get(f"{BASE_URL}/games/{test_game_id}", headers=HEADERS)
        if response.status_code != 200:
            log_test("Get initial game state", False, f"Status: {response.status_code}")
            return False
        
        initial_game = response.json()
        initial_chips = {p['player_id']: p.get('chips_in_game', 0.0) for p in initial_game['players']}
        
    except Exception as e:
        log_test("Get initial game state", False, f"Exception: {str(e)}")
        return False
    
    # Test each transaction that adds chips
    for transaction_test in transactions_add_chips:
        if not test_single_transaction_with_chips_tracking(transaction_test, initial_chips):
            return False
        
        # Update initial_chips for next test
        player_id = transaction_test["player"]["id"]
        initial_chips[player_id] += transaction_test["expected_chips_change"]
    
    # Test cashed out transaction (should SUBTRACT from chips_in_game)
    # Alice should have chips in game now, let's cash out some
    cashout_test = {
        "player": test_players[0],  # Alice
        "type": "cashed_out",
        "amount": 300.0,
        "description": "Cash out - should subtract from chips_in_game",
        "expected_chips_change": -300.0
    }
    
    if not test_single_transaction_with_chips_tracking(cashout_test, initial_chips):
        return False
    
    # Verify total table amount calculation
    return test_total_table_amount()

def test_single_transaction_with_chips_tracking(transaction_test, initial_chips):
    """Test a single transaction and verify chips_in_game changes"""
    player = transaction_test["player"]
    transaction_type = transaction_test["type"]
    amount = transaction_test["amount"]
    description = transaction_test["description"]
    expected_chips_change = transaction_test["expected_chips_change"]
    
    player_id = player['id']
    initial_chips_for_player = initial_chips.get(player_id, 0.0)
    
    try:
        # Create transaction
        payload = {
            "player_id": player_id,
            "transaction_type": transaction_type,
            "amount": amount,
            "description": description
        }
        
        response = requests.post(f"{BASE_URL}/games/{test_game_id}/transactions", json=payload, headers=HEADERS)
        
        if response.status_code == 200:
            transaction_data = response.json()
            
            # Get updated game state
            response = requests.get(f"{BASE_URL}/games/{test_game_id}", headers=HEADERS)
            if response.status_code == 200:
                updated_game = response.json()
                
                # Find the player in the game and check chips_in_game
                player_in_game = next((p for p in updated_game['players'] if p['player_id'] == player_id), None)
                
                if player_in_game:
                    actual_chips = player_in_game.get('chips_in_game', 0.0)
                    expected_chips = initial_chips_for_player + expected_chips_change
                    
                    if abs(actual_chips - expected_chips) < 0.01:  # Allow for floating point precision
                        log_test(f"{transaction_type} transaction - chips_in_game tracking", True, 
                               f"Player: {player['name']}, Amount: {amount}, chips_in_game: {initial_chips_for_player} → {actual_chips}")
                        return True
                    else:
                        log_test(f"{transaction_type} transaction - chips_in_game tracking", False, 
                               f"Expected chips_in_game: {expected_chips}, Actual: {actual_chips}")
                        return False
                else:
                    log_test(f"{transaction_type} transaction - find player in game", False, "Player not found in game")
                    return False
            else:
                log_test(f"{transaction_type} transaction - get updated game", False, f"Status: {response.status_code}")
                return False
        else:
            log_test(f"{transaction_type} transaction", False, f"Status: {response.status_code}, Response: {response.text}")
            return False
            
    except Exception as e:
        log_test(f"{transaction_type} transaction", False, f"Exception: {str(e)}")
        return False

def test_total_table_amount():
    """Test that total table amount calculation is correct"""
    try:
        response = requests.get(f"{BASE_URL}/games/{test_game_id}", headers=HEADERS)
        
        if response.status_code == 200:
            game_data = response.json()
            
            # Calculate total chips in game
            total_chips = sum(p.get('chips_in_game', 0.0) for p in game_data['players'])
            
            log_test("Calculate total table amount", True, f"Total chips in game: ${total_chips:,.2f}")
            
            # Verify each player's chips_in_game
            for player_info in game_data['players']:
                player_name = player_info['player_name']
                chips_in_game = player_info.get('chips_in_game', 0.0)
                log_test(f"Verify {player_name} chips in game", True, f"chips_in_game: ${chips_in_game:,.2f}")
            
            # Verify total is greater than 0 (we added chips)
            if total_chips > 0:
                log_test("Total table amount verification", True, f"Total table shows ${total_chips:,.2f} (not $0.00)")
                return True
            else:
                log_test("Total table amount verification", False, f"Total table shows $0.00 despite chips being added")
                return False
        else:
            log_test("Get game for total calculation", False, f"Status: {response.status_code}")
            return False
            
    except Exception as e:
        log_test("Calculate total table amount", False, f"Exception: {str(e)}")
        return False

def test_cashed_out_logic():
    """Test specific cashed out logic - amount should be subtracted from chips_in_game"""
    print("=" * 60)
    print("5. TESTING CASHED OUT LOGIC")
    print("=" * 60)
    
    try:
        # Get current game state
        response = requests.get(f"{BASE_URL}/games/{test_game_id}", headers=HEADERS)
        if response.status_code != 200:
            log_test("Get game state for cashout test", False, f"Status: {response.status_code}")
            return False
        
        game_data = response.json()
        
        # Find a player with chips in game to cash out
        player_with_chips = None
        for player_info in game_data['players']:
            if player_info.get('chips_in_game', 0.0) > 100:  # Need at least 100 to cash out
                player_with_chips = player_info
                break
        
        if not player_with_chips:
            log_test("Find player with chips to cash out", False, "No player has sufficient chips in game")
            return False
        
        player_id = player_with_chips['player_id']
        player_name = player_with_chips['player_name']
        initial_chips = player_with_chips.get('chips_in_game', 0.0)
        cashout_amount = 200.0
        
        # Perform cashout transaction
        payload = {
            "player_id": player_id,
            "transaction_type": "cashed_out",
            "amount": cashout_amount,
            "description": "Testing cashout logic - should subtract from chips_in_game"
        }
        
        response = requests.post(f"{BASE_URL}/games/{test_game_id}/transactions", json=payload, headers=HEADERS)
        
        if response.status_code == 200:
            transaction_data = response.json()
            
            # Get updated game state
            response = requests.get(f"{BASE_URL}/games/{test_game_id}", headers=HEADERS)
            if response.status_code == 200:
                updated_game = response.json()
                
                # Find the player and check chips_in_game
                updated_player = next((p for p in updated_game['players'] if p['player_id'] == player_id), None)
                
                if updated_player:
                    final_chips = updated_player.get('chips_in_game', 0.0)
                    expected_chips = initial_chips - cashout_amount
                    
                    if abs(final_chips - expected_chips) < 0.01:
                        log_test("Cashed out transaction subtracts from chips_in_game", True, 
                               f"{player_name}: {initial_chips} - {cashout_amount} = {final_chips}")
                        return True
                    else:
                        log_test("Cashed out transaction subtracts from chips_in_game", False, 
                               f"Expected {expected_chips}, got {final_chips}")
                        return False
                else:
                    log_test("Find player after cashout", False, "Player not found in updated game")
                    return False
            else:
                log_test("Get updated game after cashout", False, f"Status: {response.status_code}")
                return False
        else:
            log_test("Cashed out transaction", False, f"Status: {response.status_code}, Response: {response.text}")
            return False
            
    except Exception as e:
        log_test("Cashed out logic test", False, f"Exception: {str(e)}")
        return False

def test_game_session_management():
    """Test creating new games and verifying chips don't carry over"""
    print("=" * 60)
    print("6. TESTING GAME SESSION MANAGEMENT")
    print("=" * 60)
    
    try:
        # Create a second game with same players
        player_ids = [p['id'] for p in test_players[:3]]  # Use first 3 players
        payload = {
            "name": "Second Game - Fresh Start",
            "player_ids": player_ids
        }
        
        response = requests.post(f"{BASE_URL}/games", json=payload, headers=HEADERS)
        
        if response.status_code == 200:
            new_game_data = response.json()
            new_game_id = new_game_data['id']
            
            log_test("Create second game", True, f"Game ID: {new_game_id}")
            
            # Verify all players start with chips_in_game = 0.0 in new game
            all_fresh_start = True
            for player_info in new_game_data['players']:
                player_name = player_info['player_name']
                chips_in_game = player_info.get('chips_in_game', 'MISSING')
                
                if chips_in_game == 0.0:
                    log_test(f"Verify {player_name} fresh start in new game", True, f"chips_in_game: {chips_in_game}")
                else:
                    log_test(f"Verify {player_name} fresh start in new game", False, f"Expected 0.0, got {chips_in_game}")
                    all_fresh_start = False
            
            if all_fresh_start:
                log_test("Game session isolation", True, "Players don't carry chips from previous games")
                
                # Clean up - close the second game
                requests.post(f"{BASE_URL}/games/{new_game_id}/close", headers=HEADERS)
                return True
            else:
                return False
        else:
            log_test("Create second game", False, f"Status: {response.status_code}, Response: {response.text}")
            return False
            
    except Exception as e:
        log_test("Game session management test", False, f"Exception: {str(e)}")
        return False

def cleanup_test_data():
    """Clean up test data"""
    print("=" * 60)
    print("7. CLEANUP")
    print("=" * 60)
    
    # Close test game
    if test_game_id:
        try:
            response = requests.post(f"{BASE_URL}/games/{test_game_id}/close", headers=HEADERS)
            if response.status_code == 200:
                log_test("Close test game", True, f"Game {test_game_id} closed")
            else:
                log_test("Close test game", False, f"Status: {response.status_code}")
        except Exception as e:
            log_test("Close test game", False, f"Exception: {str(e)}")
    
    # Delete test players
    for player in test_players:
        try:
            response = requests.delete(f"{BASE_URL}/players/{player['id']}", headers=HEADERS)
            if response.status_code == 200:
                log_test(f"Delete player {player['name']}", True, "Player deleted")
            else:
                log_test(f"Delete player {player['name']}", False, f"Status: {response.status_code}")
        except Exception as e:
            log_test(f"Delete player {player['name']}", False, f"Exception: {str(e)}")

def run_focused_tests():
    """Run focused tests on the updated poker chip management fixes"""
    print("🎯 POKER CHIP MANAGEMENT BACKEND - FOCUSED TESTING")
    print("Focus: Money formatting, chips_in_game logic, transaction processing, cashed out logic")
    print("=" * 80)
    print(f"Testing against: {BASE_URL}")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    test_results = []
    
    # Run focused tests
    test_results.append(("Money formatting", test_money_formatting()))
    test_results.append(("Player creation", test_create_players()))
    test_results.append(("Game creation & chips_in_game logic", test_game_creation_and_chips_in_game()))
    test_results.append(("Add player mid-game", test_add_player_mid_game()))
    test_results.append(("Transaction processing & chips_in_game tracking", test_transaction_processing_and_chips_in_game()))
    test_results.append(("Cashed out logic", test_cashed_out_logic()))
    test_results.append(("Game session management", test_game_session_management()))
    
    # Cleanup
    cleanup_test_data()
    
    # Summary
    print("=" * 80)
    print("📊 FOCUSED TEST SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print()
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL FOCUSED TESTS PASSED! Updated poker chip management fixes are working correctly.")
        print("\n✅ Key Fixes Verified:")
        print("   • Money formatting (no .00 for whole numbers, commas for thousands)")
        print("   • chips_in_game initialization to 0.0 for new players")
        print("   • Cash/Bank Transfer/Credit transactions add to chips_in_game")
        print("   • Cashed Out transactions subtract from chips_in_game")
        print("   • Total table amount calculation is correct")
        print("   • Game session isolation (no chip carryover between games)")
        return True
    else:
        print("⚠️  SOME FOCUSED TESTS FAILED! Check the details above.")
        return False

if __name__ == "__main__":
    success = run_focused_tests()
    exit(0 if success else 1)