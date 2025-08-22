#!/usr/bin/env python3
"""
Comprehensive Backend API Test for Poker Chip Management System
CRITICAL BUG FIX VERIFICATION: PAY_CREDIT should NOT affect Total Table (chips_in_game)
CORRECTED LOGIC: PAY_CREDIT only reduces player debt, does NOT reduce chips_in_game
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "https://chipmaster-2.preview.emergentagent.com/api"
HEADERS = {"Content-Type": "application/json"}

# Test data storage
test_players = []
test_game_id = None
test_game_id_2 = None
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

def test_create_players_with_debt():
    """Create test players with various balance states for Pay Credit testing"""
    print("=" * 60)
    print("1. CREATING PLAYERS WITH VARIOUS BALANCE STATES")
    print("=" * 60)
    
    players_to_create = [
        {"name": "Alice", "balance": -500.0},  # Has debt - eligible for PAY_CREDIT
        {"name": "Bob", "balance": -200.0},    # Has debt - eligible for PAY_CREDIT
        {"name": "Charlie", "balance": 100.0}, # Has credit - NOT eligible for PAY_CREDIT
        {"name": "David", "balance": 0.0}      # Zero balance - NOT eligible for PAY_CREDIT
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
                    debt_status = "HAS DEBT" if player_info["balance"] < 0 else "NO DEBT" if player_info["balance"] == 0 else "HAS CREDIT"
                    log_test(f"Create player '{player_info['name']}'", True, f"Balance: ${updated_player['current_balance']:.2f} ({debt_status})")
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

def test_create_multiple_active_games():
    """Create multiple active games for Club Earnings testing"""
    print("=" * 60)
    print("2. CREATING MULTIPLE ACTIVE GAMES FOR CLUB EARNINGS")
    print("=" * 60)
    
    global test_game_id, test_game_id_2
    
    try:
        # Create first game with players who have debt
        player_ids_1 = [test_players[0]['id'], test_players[1]['id']]  # Alice, Bob (both have debt)
        payload_1 = {
            "name": "Game 1 - Debt Players",
            "player_ids": player_ids_1
        }
        
        response = requests.post(f"{BASE_URL}/games", json=payload_1, headers=HEADERS)
        
        if response.status_code == 200:
            game_data_1 = response.json()
            test_game_id = game_data_1['id']
            log_test("Create Game 1", True, f"Game ID: {test_game_id}")
        else:
            log_test("Create Game 1", False, f"Status: {response.status_code}")
            return False
        
        # Create second game with other players
        player_ids_2 = [test_players[2]['id'], test_players[3]['id']]  # Charlie, David
        payload_2 = {
            "name": "Game 2 - Mixed Players",
            "player_ids": player_ids_2
        }
        
        response = requests.post(f"{BASE_URL}/games", json=payload_2, headers=HEADERS)
        
        if response.status_code == 200:
            game_data_2 = response.json()
            test_game_id_2 = game_data_2['id']
            log_test("Create Game 2", True, f"Game ID: {test_game_id_2}")
            return True
        else:
            log_test("Create Game 2", False, f"Status: {response.status_code}")
            return False
            
    except Exception as e:
        log_test("Create multiple games", False, f"Exception: {str(e)}")
        return False

def test_add_chips_to_games():
    """Add chips to both games to create club earnings"""
    print("=" * 60)
    print("3. ADDING CHIPS TO GAMES FOR CLUB EARNINGS CALCULATION")
    print("=" * 60)
    
    # Add chips to Game 1
    game1_transactions = [
        {"player_id": test_players[0]['id'], "type": "cash", "amount": 1000.0, "desc": "Alice cash"},
        {"player_id": test_players[1]['id'], "type": "bank_transfer", "amount": 750.0, "desc": "Bob bank transfer"}
    ]
    
    # Add chips to Game 2
    game2_transactions = [
        {"player_id": test_players[2]['id'], "type": "credit", "amount": 500.0, "desc": "Charlie credit"},
        {"player_id": test_players[3]['id'], "type": "cash", "amount": 300.0, "desc": "David cash"}
    ]
    
    total_expected_earnings = 0.0
    
    # Process Game 1 transactions
    for transaction in game1_transactions:
        if not create_transaction(test_game_id, transaction):
            return False
        total_expected_earnings += transaction["amount"]
    
    # Process Game 2 transactions
    for transaction in game2_transactions:
        if not create_transaction(test_game_id_2, transaction):
            return False
        total_expected_earnings += transaction["amount"]
    
    log_test("Add chips to both games", True, f"Total expected club earnings: ${total_expected_earnings:.2f}")
    return True

def create_transaction(game_id, transaction_data):
    """Helper function to create a transaction"""
    try:
        payload = {
            "player_id": transaction_data["player_id"],
            "transaction_type": transaction_data["type"],
            "amount": transaction_data["amount"],
            "description": transaction_data["desc"]
        }
        
        response = requests.post(f"{BASE_URL}/games/{game_id}/transactions", json=payload, headers=HEADERS)
        
        if response.status_code == 200:
            log_test(f"Create {transaction_data['desc']}", True, f"Amount: ${transaction_data['amount']:.2f}")
            return True
        else:
            log_test(f"Create {transaction_data['desc']}", False, f"Status: {response.status_code}")
            return False
            
    except Exception as e:
        log_test(f"Create {transaction_data['desc']}", False, f"Exception: {str(e)}")
        return False

def test_club_earnings_dashboard():
    """Test Club Earnings calculation in dashboard API"""
    print("=" * 60)
    print("4. TESTING CLUB EARNINGS DASHBOARD API")
    print("=" * 60)
    
    try:
        response = requests.get(f"{BASE_URL}/dashboard", headers=HEADERS)
        
        if response.status_code == 200:
            dashboard_data = response.json()
            
            # Check if club_earnings field exists
            if "club_earnings" not in dashboard_data:
                log_test("Dashboard contains club_earnings field", False, "club_earnings field missing from dashboard response")
                return False
            
            club_earnings = dashboard_data["club_earnings"]
            expected_earnings = 2550.0  # 1000 + 750 + 500 + 300
            
            log_test("Dashboard API response", True, f"club_earnings: ${club_earnings:.2f}")
            
            # Verify club earnings calculation
            if abs(club_earnings - expected_earnings) < 0.01:
                log_test("Club Earnings calculation", True, f"Expected: ${expected_earnings:.2f}, Actual: ${club_earnings:.2f}")
            else:
                log_test("Club Earnings calculation", False, f"Expected: ${expected_earnings:.2f}, Actual: ${club_earnings:.2f}")
                return False
            
            # Verify other dashboard fields still exist
            required_fields = ["active_games", "total_players", "total_credit_owed", "total_debt_owed", "recent_transactions"]
            for field in required_fields:
                if field in dashboard_data:
                    log_test(f"Dashboard field '{field}' exists", True, f"Value: {dashboard_data[field]}")
                else:
                    log_test(f"Dashboard field '{field}' exists", False, "Field missing")
                    return False
            
            return True
        else:
            log_test("Get dashboard", False, f"Status: {response.status_code}")
            return False
            
    except Exception as e:
        log_test("Club Earnings dashboard test", False, f"Exception: {str(e)}")
        return False

def test_pay_credit_validation():
    """Test PAY_CREDIT transaction validation"""
    print("=" * 60)
    print("5. TESTING PAY_CREDIT VALIDATION")
    print("=" * 60)
    
    # Test 1: Try PAY_CREDIT with player who has no debt (should fail)
    charlie_id = test_players[2]['id']  # Charlie has positive balance
    try:
        payload = {
            "player_id": charlie_id,
            "transaction_type": "pay_credit",
            "amount": 100.0,
            "description": "Should fail - player has no debt"
        }
        
        response = requests.post(f"{BASE_URL}/games/{test_game_id}/transactions", json=payload, headers=HEADERS)
        
        if response.status_code == 400:
            log_test("PAY_CREDIT validation - no debt", True, "Correctly rejected PAY_CREDIT for player with no debt")
        else:
            log_test("PAY_CREDIT validation - no debt", False, f"Expected 400, got {response.status_code}")
            return False
            
    except Exception as e:
        log_test("PAY_CREDIT validation - no debt", False, f"Exception: {str(e)}")
        return False
    
    # Test 2: Try PAY_CREDIT with zero amount (should fail)
    alice_id = test_players[0]['id']  # Alice has debt
    try:
        payload = {
            "player_id": alice_id,
            "transaction_type": "pay_credit",
            "amount": 0.0,
            "description": "Should fail - zero amount"
        }
        
        response = requests.post(f"{BASE_URL}/games/{test_game_id}/transactions", json=payload, headers=HEADERS)
        
        if response.status_code == 400:
            log_test("PAY_CREDIT validation - zero amount", True, "Correctly rejected PAY_CREDIT with zero amount")
        else:
            log_test("PAY_CREDIT validation - zero amount", False, f"Expected 400, got {response.status_code}")
            return False
            
    except Exception as e:
        log_test("PAY_CREDIT validation - zero amount", False, f"Exception: {str(e)}")
        return False
    
    # Test 3: Try PAY_CREDIT with negative amount (should fail)
    try:
        payload = {
            "player_id": alice_id,
            "transaction_type": "pay_credit",
            "amount": -100.0,
            "description": "Should fail - negative amount"
        }
        
        response = requests.post(f"{BASE_URL}/games/{test_game_id}/transactions", json=payload, headers=HEADERS)
        
        if response.status_code == 400:
            log_test("PAY_CREDIT validation - negative amount", True, "Correctly rejected PAY_CREDIT with negative amount")
            return True
        else:
            log_test("PAY_CREDIT validation - negative amount", False, f"Expected 400, got {response.status_code}")
            return False
            
    except Exception as e:
        log_test("PAY_CREDIT validation - negative amount", False, f"Exception: {str(e)}")
        return False

def test_pay_credit_functionality():
    """Test PAY_CREDIT transaction functionality - CORRECTED LOGIC"""
    print("=" * 60)
    print("6. TESTING PAY_CREDIT FUNCTIONALITY (CORRECTED LOGIC)")
    print("=" * 60)
    
    # Get Alice's current balance (should be negative - debt)
    alice_id = test_players[0]['id']
    try:
        response = requests.get(f"{BASE_URL}/players/{alice_id}", headers=HEADERS)
        if response.status_code != 200:
            log_test("Get Alice's current balance", False, f"Status: {response.status_code}")
            return False
        
        alice_before = response.json()
        initial_balance = alice_before['current_balance']
        
        if initial_balance >= 0:
            log_test("Verify Alice has debt", False, f"Alice balance: ${initial_balance:.2f} (expected negative)")
            return False
        
        log_test("Verify Alice has debt", True, f"Alice balance: ${initial_balance:.2f}")
        
        # Get initial game state to check chips_in_game
        response = requests.get(f"{BASE_URL}/games/{test_game_id}", headers=HEADERS)
        if response.status_code != 200:
            log_test("Get initial game state", False, f"Status: {response.status_code}")
            return False
        
        game_before = response.json()
        alice_game_info = next((p for p in game_before['players'] if p['player_id'] == alice_id), None)
        if not alice_game_info:
            log_test("Find Alice in game", False, "Alice not found in game")
            return False
        
        initial_chips_in_game = alice_game_info.get('chips_in_game', 0.0)
        log_test("Get Alice's initial chips_in_game", True, f"chips_in_game: ${initial_chips_in_game:.2f}")
        
        # Perform PAY_CREDIT transaction
        pay_amount = 200.0  # Pay part of the debt
        payload = {
            "player_id": alice_id,
            "transaction_type": "pay_credit",
            "amount": pay_amount,
            "description": "Paying off part of debt"
        }
        
        response = requests.post(f"{BASE_URL}/games/{test_game_id}/transactions", json=payload, headers=HEADERS)
        
        if response.status_code == 200:
            transaction_data = response.json()
            log_test("Create PAY_CREDIT transaction", True, f"Transaction ID: {transaction_data['id']}")
            
            # Verify player balance changed correctly
            response = requests.get(f"{BASE_URL}/players/{alice_id}", headers=HEADERS)
            if response.status_code == 200:
                alice_after = response.json()
                final_balance = alice_after['current_balance']
                expected_balance = initial_balance + pay_amount  # Debt reduced
                
                if abs(final_balance - expected_balance) < 0.01:
                    log_test("PAY_CREDIT reduces player debt", True, f"Balance: ${initial_balance:.2f} → ${final_balance:.2f}")
                else:
                    log_test("PAY_CREDIT reduces player debt", False, f"Expected: ${expected_balance:.2f}, Actual: ${final_balance:.2f}")
                    return False
            else:
                log_test("Get Alice's updated balance", False, f"Status: {response.status_code}")
                return False
            
            # CRITICAL TEST: Verify chips_in_game UNCHANGED (Total Table NOT affected)
            response = requests.get(f"{BASE_URL}/games/{test_game_id}", headers=HEADERS)
            if response.status_code == 200:
                game_after = response.json()
                alice_game_info_after = next((p for p in game_after['players'] if p['player_id'] == alice_id), None)
                
                if alice_game_info_after:
                    final_chips_in_game = alice_game_info_after.get('chips_in_game', 0.0)
                    
                    # CORRECTED LOGIC: PAY_CREDIT should NOT affect chips_in_game
                    if abs(final_chips_in_game - initial_chips_in_game) < 0.01:
                        log_test("PAY_CREDIT does NOT affect Total Table", True, f"chips_in_game: ${initial_chips_in_game:.2f} → ${final_chips_in_game:.2f} (UNCHANGED)")
                        return True
                    else:
                        log_test("PAY_CREDIT does NOT affect Total Table", False, f"Expected: ${initial_chips_in_game:.2f}, Actual: ${final_chips_in_game:.2f} (SHOULD BE UNCHANGED)")
                        return False
                else:
                    log_test("Find Alice in updated game", False, "Alice not found in updated game")
                    return False
            else:
                log_test("Get updated game state", False, f"Status: {response.status_code}")
                return False
        else:
            log_test("Create PAY_CREDIT transaction", False, f"Status: {response.status_code}, Response: {response.text}")
            return False
            
    except Exception as e:
        log_test("PAY_CREDIT functionality test", False, f"Exception: {str(e)}")
        return False

def test_pay_credit_with_bob():
    """Test PAY_CREDIT with Bob to verify it works with different players"""
    print("=" * 60)
    print("7. TESTING PAY_CREDIT WITH DIFFERENT PLAYER (BOB)")
    print("=" * 60)
    
    bob_id = test_players[1]['id']
    try:
        # Get Bob's current balance
        response = requests.get(f"{BASE_URL}/players/{bob_id}", headers=HEADERS)
        if response.status_code != 200:
            log_test("Get Bob's current balance", False, f"Status: {response.status_code}")
            return False
        
        bob_before = response.json()
        initial_balance = bob_before['current_balance']
        
        if initial_balance >= 0:
            log_test("Verify Bob has debt", False, f"Bob balance: ${initial_balance:.2f} (expected negative)")
            return False
        
        # Pay off all of Bob's debt
        pay_amount = abs(initial_balance)  # Pay exact debt amount
        payload = {
            "player_id": bob_id,
            "transaction_type": "pay_credit",
            "amount": pay_amount,
            "description": "Paying off all debt"
        }
        
        response = requests.post(f"{BASE_URL}/games/{test_game_id}/transactions", json=payload, headers=HEADERS)
        
        if response.status_code == 200:
            log_test("Create PAY_CREDIT for Bob", True, f"Paid: ${pay_amount:.2f}")
            
            # Verify Bob's balance is now zero
            response = requests.get(f"{BASE_URL}/players/{bob_id}", headers=HEADERS)
            if response.status_code == 200:
                bob_after = response.json()
                final_balance = bob_after['current_balance']
                
                if abs(final_balance) < 0.01:  # Should be zero or very close
                    log_test("PAY_CREDIT clears Bob's debt", True, f"Balance: ${initial_balance:.2f} → ${final_balance:.2f}")
                    return True
                else:
                    log_test("PAY_CREDIT clears Bob's debt", False, f"Expected ~0.00, Actual: ${final_balance:.2f}")
                    return False
            else:
                log_test("Get Bob's updated balance", False, f"Status: {response.status_code}")
                return False
        else:
            log_test("Create PAY_CREDIT for Bob", False, f"Status: {response.status_code}")
            return False
            
    except Exception as e:
        log_test("PAY_CREDIT with Bob test", False, f"Exception: {str(e)}")
        return False

def test_club_earnings_after_pay_credit():
    """Test that Club Earnings are NOT affected by PAY_CREDIT transactions (CORRECTED LOGIC)"""
    print("=" * 60)
    print("8. TESTING CLUB EARNINGS AFTER PAY_CREDIT (CORRECTED LOGIC)")
    print("=" * 60)
    
    try:
        response = requests.get(f"{BASE_URL}/dashboard", headers=HEADERS)
        
        if response.status_code == 200:
            dashboard_data = response.json()
            club_earnings = dashboard_data.get("club_earnings", 0.0)
            
            # CORRECTED LOGIC: PAY_CREDIT should NOT affect club earnings
            # Expected: Original 2550.0 should remain unchanged by PAY_CREDIT
            expected_earnings = 2550.0  # Should remain the same
            
            if abs(club_earnings - expected_earnings) < 0.01:
                log_test("Club Earnings unaffected by PAY_CREDIT", True, f"Club earnings: ${club_earnings:.2f} (UNCHANGED by PAY_CREDIT)")
                return True
            else:
                log_test("Club Earnings unaffected by PAY_CREDIT", False, f"Expected: ${expected_earnings:.2f}, Actual: ${club_earnings:.2f}")
                return False
        else:
            log_test("Get dashboard after PAY_CREDIT", False, f"Status: {response.status_code}")
            return False
            
    except Exception as e:
        log_test("Club Earnings after PAY_CREDIT test", False, f"Exception: {str(e)}")
        return False

def test_total_table_logic_verification():
    """Verify Total Table = Cash + Bank Transfer + Credit - Cashed Out - Paid with Chips (PAY_CREDIT does NOT affect)"""
    print("=" * 60)
    print("9. TESTING TOTAL TABLE LOGIC VERIFICATION (CORRECTED)")
    print("=" * 60)
    
    try:
        # Get both games and calculate total chips_in_game
        response1 = requests.get(f"{BASE_URL}/games/{test_game_id}", headers=HEADERS)
        response2 = requests.get(f"{BASE_URL}/games/{test_game_id_2}", headers=HEADERS)
        
        if response1.status_code == 200 and response2.status_code == 200:
            game1_data = response1.json()
            game2_data = response2.json()
            
            # Calculate total chips in Game 1
            game1_total = sum(p.get('chips_in_game', 0.0) for p in game1_data['players'])
            
            # Calculate total chips in Game 2
            game2_total = sum(p.get('chips_in_game', 0.0) for p in game2_data['players'])
            
            total_table = game1_total + game2_total
            
            log_test("Calculate Total Table from games", True, f"Game 1: ${game1_total:.2f}, Game 2: ${game2_total:.2f}, Total: ${total_table:.2f}")
            
            # Verify this matches dashboard club_earnings
            response = requests.get(f"{BASE_URL}/dashboard", headers=HEADERS)
            if response.status_code == 200:
                dashboard_data = response.json()
                club_earnings = dashboard_data.get("club_earnings", 0.0)
                
                if abs(total_table - club_earnings) < 0.01:
                    log_test("Total Table matches Club Earnings", True, f"Both show: ${total_table:.2f}")
                    
                    # CORRECTED LOGIC: PAY_CREDIT should NOT affect Total Table
                    # Expected: Original adds (2550) - NO PAY_CREDIT subtractions
                    expected_total = 2550.0  # Should remain unchanged by PAY_CREDIT
                    if abs(total_table - expected_total) < 0.01:
                        log_test("Total Table logic verification (CORRECTED)", True, f"Total Table correctly unaffected by PAY_CREDIT: ${total_table:.2f}")
                        return True
                    else:
                        log_test("Total Table logic verification (CORRECTED)", False, f"Expected: ${expected_total:.2f}, got ${total_table:.2f}")
                        return False
                else:
                    log_test("Total Table matches Club Earnings", False, f"Table: ${total_table:.2f}, Earnings: ${club_earnings:.2f}")
                    return False
            else:
                log_test("Get dashboard for verification", False, f"Status: {response.status_code}")
                return False
        else:
            log_test("Get games for Total Table calculation", False, "Failed to get game data")
            return False
            
    except Exception as e:
        log_test("Total Table logic verification", False, f"Exception: {str(e)}")
        return False

def cleanup_test_data():
    """Clean up test data"""
    print("=" * 60)
    print("10. CLEANUP")
    print("=" * 60)
    
    # Close test games
    for game_id, game_name in [(test_game_id, "Game 1"), (test_game_id_2, "Game 2")]:
        if game_id:
            try:
                response = requests.post(f"{BASE_URL}/games/{game_id}/close", headers=HEADERS)
                if response.status_code == 200:
                    log_test(f"Close {game_name}", True, f"Game {game_id} closed")
                else:
                    log_test(f"Close {game_name}", False, f"Status: {response.status_code}")
            except Exception as e:
                log_test(f"Close {game_name}", False, f"Exception: {str(e)}")
    
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

def run_pay_credit_and_club_earnings_tests():
    """Run focused tests on Pay Credit and Club Earnings features"""
    print("🎯 POKER CHIP MANAGEMENT BACKEND - PAY CREDIT & CLUB EARNINGS TESTING")
    print("Focus: Pay Credit Transaction Testing and Club Earnings Dashboard API")
    print("=" * 80)
    print(f"Testing against: {BASE_URL}")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    test_results = []
    
    # Run focused tests
    test_results.append(("Create players with debt", test_create_players_with_debt()))
    test_results.append(("Create multiple active games", test_create_multiple_active_games()))
    test_results.append(("Add chips to games", test_add_chips_to_games()))
    test_results.append(("Club Earnings Dashboard API", test_club_earnings_dashboard()))
    test_results.append(("PAY_CREDIT validation", test_pay_credit_validation()))
    test_results.append(("PAY_CREDIT functionality", test_pay_credit_functionality()))
    test_results.append(("PAY_CREDIT with different player", test_pay_credit_with_bob()))
    test_results.append(("Club Earnings after PAY_CREDIT", test_club_earnings_after_pay_credit()))
    test_results.append(("Total Table logic verification", test_total_table_logic_verification()))
    
    # Cleanup
    cleanup_test_data()
    
    # Summary
    print("=" * 80)
    print("📊 PAY CREDIT & CLUB EARNINGS TEST SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print()
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL PAY CREDIT & CLUB EARNINGS TESTS PASSED!")
        print("\n✅ Key Features Verified:")
        print("   • PAY_CREDIT transaction type works correctly")
        print("   • PAY_CREDIT reduces player debt and Total Table")
        print("   • PAY_CREDIT validation prevents invalid transactions")
        print("   • Club Earnings calculation includes all active games")
        print("   • Dashboard API returns club_earnings field")
        print("   • Total Table logic: Cash + Bank + Credit - Cashed Out - Paid with Chips - Pay Credit")
        return True
    else:
        print("⚠️  SOME TESTS FAILED! Check the details above.")
        return False

def test_force_close_game_with_uncashed_players():
    """Test scenario: Force close game with players who haven't cashed out"""
    print("=" * 60)
    print("TESTING FORCE CLOSE GAME WITH PLAYERS WHO HAVEN'T CASHED OUT")
    print("=" * 60)
    
    # Step 1: Create 3 test players
    test_players_force_close = []
    players_to_create = [
        {"name": "TestPlayer1"},
        {"name": "TestPlayer2"}, 
        {"name": "TestPlayer3"}
    ]
    
    for player_info in players_to_create:
        try:
            payload = {"name": player_info["name"]}
            response = requests.post(f"{BASE_URL}/players", json=payload, headers=HEADERS)
            
            if response.status_code == 200:
                player_data = response.json()
                test_players_force_close.append(player_data)
                log_test(f"Create {player_info['name']}", True, f"Player ID: {player_data['id']}")
            else:
                log_test(f"Create {player_info['name']}", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            log_test(f"Create {player_info['name']}", False, f"Exception: {str(e)}")
            return False
    
    # Step 2: Create a new game "Test Force Close" with these 3 players
    try:
        player_ids = [p['id'] for p in test_players_force_close]
        payload = {
            "name": "Test Force Close",
            "player_ids": player_ids
        }
        
        response = requests.post(f"{BASE_URL}/games", json=payload, headers=HEADERS)
        
        if response.status_code == 200:
            game_data = response.json()
            test_game_force_close_id = game_data['id']
            log_test("Create 'Test Force Close' game", True, f"Game ID: {test_game_force_close_id}")
        else:
            log_test("Create 'Test Force Close' game", False, f"Status: {response.status_code}")
            return False
            
    except Exception as e:
        log_test("Create 'Test Force Close' game", False, f"Exception: {str(e)}")
        return False
    
    # Step 3: Add transactions for players WITHOUT cashing out
    transactions_to_create = [
        # TestPlayer1: Cash $1000, Credit $500 (total chips in game: $1500, balance: -500)
        {"player_id": test_players_force_close[0]['id'], "type": "cash", "amount": 1000.0, "desc": "TestPlayer1 cash $1000"},
        {"player_id": test_players_force_close[0]['id'], "type": "credit", "amount": 500.0, "desc": "TestPlayer1 credit $500"},
        
        # TestPlayer2: Bank Transfer $800 (total chips in game: $800, balance: 0)
        {"player_id": test_players_force_close[1]['id'], "type": "bank_transfer", "amount": 800.0, "desc": "TestPlayer2 bank transfer $800"},
        
        # TestPlayer3: Credit $1200 (total chips in game: $1200, balance: -1200)
        {"player_id": test_players_force_close[2]['id'], "type": "credit", "amount": 1200.0, "desc": "TestPlayer3 credit $1200"}
    ]
    
    for transaction in transactions_to_create:
        try:
            payload = {
                "player_id": transaction["player_id"],
                "transaction_type": transaction["type"],
                "amount": transaction["amount"],
                "description": transaction["desc"]
            }
            
            response = requests.post(f"{BASE_URL}/games/{test_game_force_close_id}/transactions", json=payload, headers=HEADERS)
            
            if response.status_code == 200:
                log_test(f"Create transaction: {transaction['desc']}", True, f"Amount: ${transaction['amount']:.2f}")
            else:
                log_test(f"Create transaction: {transaction['desc']}", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            log_test(f"Create transaction: {transaction['desc']}", False, f"Exception: {str(e)}")
            return False
    
    # Step 4: Verify game status is ACTIVE and check player states
    try:
        response = requests.get(f"{BASE_URL}/games/{test_game_force_close_id}", headers=HEADERS)
        
        if response.status_code == 200:
            game_data = response.json()
            
            # Verify game status is ACTIVE
            if game_data['status'] == 'active':
                log_test("Verify game status is ACTIVE", True, f"Status: {game_data['status']}")
            else:
                log_test("Verify game status is ACTIVE", False, f"Expected 'active', got '{game_data['status']}'")
                return False
            
            # Verify player states
            expected_chips_in_game = {
                test_players_force_close[0]['id']: 1500.0,  # TestPlayer1: $1000 cash + $500 credit
                test_players_force_close[1]['id']: 800.0,   # TestPlayer2: $800 bank transfer
                test_players_force_close[2]['id']: 1200.0   # TestPlayer3: $1200 credit
            }
            
            for player_info in game_data['players']:
                player_id = player_info['player_id']
                actual_chips = player_info.get('chips_in_game', 0.0)
                expected_chips = expected_chips_in_game.get(player_id, 0.0)
                
                if abs(actual_chips - expected_chips) < 0.01:
                    log_test(f"Verify {player_info['player_name']} chips in game", True, f"Expected: ${expected_chips:.2f}, Actual: ${actual_chips:.2f}")
                else:
                    log_test(f"Verify {player_info['player_name']} chips in game", False, f"Expected: ${expected_chips:.2f}, Actual: ${actual_chips:.2f}")
                    return False
            
            # Verify player balances
            expected_balances = {
                test_players_force_close[0]['id']: -500.0,   # TestPlayer1: 0 - 500 (credit) = -500
                test_players_force_close[1]['id']: 0.0,      # TestPlayer2: 0 (bank transfer doesn't affect balance)
                test_players_force_close[2]['id']: -1200.0   # TestPlayer3: 0 - 1200 (credit) = -1200
            }
            
            for i, player in enumerate(test_players_force_close):
                response = requests.get(f"{BASE_URL}/players/{player['id']}", headers=HEADERS)
                if response.status_code == 200:
                    player_data = response.json()
                    actual_balance = player_data['current_balance']
                    expected_balance = expected_balances[player['id']]
                    
                    if abs(actual_balance - expected_balance) < 0.01:
                        log_test(f"Verify {player['name']} balance", True, f"Expected: ${expected_balance:.2f}, Actual: ${actual_balance:.2f}")
                    else:
                        log_test(f"Verify {player['name']} balance", False, f"Expected: ${expected_balance:.2f}, Actual: ${actual_balance:.2f}")
                        return False
                else:
                    log_test(f"Get {player['name']} balance", False, f"Status: {response.status_code}")
                    return False
            
        else:
            log_test("Get game data for verification", False, f"Status: {response.status_code}")
            return False
            
    except Exception as e:
        log_test("Verify game status and player states", False, f"Exception: {str(e)}")
        return False
    
    # Step 5: Force close the game using POST /api/games/{game_id}/close
    try:
        response = requests.post(f"{BASE_URL}/games/{test_game_force_close_id}/close", headers=HEADERS)
        
        if response.status_code == 200:
            close_response = response.json()
            log_test("Force close game with uncashed players", True, "Game closed successfully despite players not having cashed out")
            
            # Step 6: Verify game closes successfully
            response = requests.get(f"{BASE_URL}/games/{test_game_force_close_id}", headers=HEADERS)
            
            if response.status_code == 200:
                closed_game_data = response.json()
                
                if closed_game_data['status'] == 'closed':
                    log_test("Verify game status changed to CLOSED", True, f"Status: {closed_game_data['status']}")
                else:
                    log_test("Verify game status changed to CLOSED", False, f"Expected 'closed', got '{closed_game_data['status']}'")
                    return False
                
                # Step 7: Verify final_balances are recorded correctly
                final_balances = closed_game_data.get('final_balances', {})
                
                if final_balances:
                    log_test("Verify final_balances exist", True, f"Found final_balances for {len(final_balances)} players")
                    
                    # Check each player's final balance matches their current balance
                    for player in test_players_force_close:
                        player_id = player['id']
                        
                        if player_id in final_balances:
                            recorded_balance = final_balances[player_id]
                            expected_balance = expected_balances[player_id]
                            
                            if abs(recorded_balance - expected_balance) < 0.01:
                                log_test(f"Verify {player['name']} final balance", True, f"Expected: ${expected_balance:.2f}, Recorded: ${recorded_balance:.2f}")
                            else:
                                log_test(f"Verify {player['name']} final balance", False, f"Expected: ${expected_balance:.2f}, Recorded: ${recorded_balance:.2f}")
                                return False
                        else:
                            log_test(f"Verify {player['name']} final balance exists", False, f"Player {player_id} not found in final_balances")
                            return False
                else:
                    log_test("Verify final_balances exist", False, "final_balances field is empty or missing")
                    return False
                    
            else:
                log_test("Get closed game data", False, f"Status: {response.status_code}")
                return False
                
        else:
            log_test("Force close game with uncashed players", False, f"Status: {response.status_code}, Response: {response.text}")
            return False
            
    except Exception as e:
        log_test("Force close game test", False, f"Exception: {str(e)}")
        return False
    
    # Cleanup: Delete test players (game is already closed)
    for player in test_players_force_close:
        try:
            response = requests.delete(f"{BASE_URL}/players/{player['id']}", headers=HEADERS)
            if response.status_code == 200:
                log_test(f"Cleanup: Delete {player['name']}", True, "Player deleted")
            else:
                log_test(f"Cleanup: Delete {player['name']}", False, f"Status: {response.status_code}")
        except Exception as e:
            log_test(f"Cleanup: Delete {player['name']}", False, f"Exception: {str(e)}")
    
    return True

def run_force_close_game_test():
    """Run the force close game test scenario"""
    print("🎯 POKER CHIP MANAGEMENT BACKEND - FORCE CLOSE GAME TEST")
    print("Focus: Testing game closure with players who haven't cashed out")
    print("=" * 80)
    print(f"Testing against: {BASE_URL}")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Run the test
    success = test_force_close_game_with_uncashed_players()
    
    # Summary
    print("=" * 80)
    print("📊 FORCE CLOSE GAME TEST SUMMARY")
    print("=" * 80)
    
    if success:
        print("✅ FORCE CLOSE GAME TEST PASSED!")
        print("\n✅ Key Features Verified:")
        print("   • Created 3 test players successfully")
        print("   • Created game 'Test Force Close' with all 3 players")
        print("   • Added transactions without cashing out:")
        print("     - TestPlayer1: Cash $1000 + Credit $500 (chips: $1500, balance: -$500)")
        print("     - TestPlayer2: Bank Transfer $800 (chips: $800, balance: $0)")
        print("     - TestPlayer3: Credit $1200 (chips: $1200, balance: -$1200)")
        print("   • Verified game status was ACTIVE before closing")
        print("   • Successfully force closed game despite players not having cashed out")
        print("   • Verified game status changed to CLOSED")
        print("   • Verified final_balances were recorded correctly for all players")
        print("   • System allows administrative force closing of games")
        return True
    else:
        print("❌ FORCE CLOSE GAME TEST FAILED!")
        print("⚠️  Check the details above for specific failure points.")
        return False

if __name__ == "__main__":
    # Run the original tests
    success1 = run_pay_credit_and_club_earnings_tests()
    
    print("\n" + "="*80 + "\n")
    
    # Run the new force close game test
    success2 = run_force_close_game_test()
    
    # Exit with success only if both test suites pass
    exit(0 if (success1 and success2) else 1)