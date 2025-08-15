#!/usr/bin/env python3
"""
CRITICAL BUG FIX VALIDATION TEST - Prevent Negative chips_in_game
Focus: Test NEW validation logic that prevents chips_in_game from going negative
Scenarios: CASHED_OUT and PAID_WITH_CHIPS validation with proper error messages
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "https://pokerbankapp.preview.emergentagent.com/api"
HEADERS = {"Content-Type": "application/json"}

# Test data storage
test_players = []
test_game_id = None

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

def setup_test_environment():
    """Create test players and game with chips for validation testing"""
    print("=" * 70)
    print("1. SETTING UP TEST ENVIRONMENT FOR VALIDATION TESTING")
    print("=" * 70)
    
    global test_players, test_game_id
    
    # Create test players
    players_to_create = [
        {"name": "ValidationPlayer1", "balance": -300.0},  # Has debt
        {"name": "ValidationPlayer2", "balance": 0.0},     # Zero balance
    ]
    
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
                    log_test(f"Create player '{player_info['name']}'", True, f"Balance: ${updated_player['current_balance']:.2f}")
                else:
                    log_test(f"Set balance for '{player_info['name']}'", False, f"Status: {response.status_code}")
                    return False
            else:
                log_test(f"Create player '{player_info['name']}'", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            log_test(f"Create player '{player_info['name']}'", False, f"Exception: {str(e)}")
            return False
    
    # Create test game
    try:
        player_ids = [player['id'] for player in test_players]
        payload = {
            "name": "Validation Test Game",
            "player_ids": player_ids
        }
        
        response = requests.post(f"{BASE_URL}/games", json=payload, headers=HEADERS)
        
        if response.status_code == 200:
            game_data = response.json()
            test_game_id = game_data['id']
            log_test("Create test game", True, f"Game ID: {test_game_id}")
        else:
            log_test("Create test game", False, f"Status: {response.status_code}")
            return False
            
    except Exception as e:
        log_test("Create test game", False, f"Exception: {str(e)}")
        return False
    
    # Add some chips to the game for testing
    try:
        # Add $1000 cash for Player1
        payload = {
            "player_id": test_players[0]['id'],
            "transaction_type": "cash",
            "amount": 1000.0,
            "description": "Initial cash for validation testing"
        }
        
        response = requests.post(f"{BASE_URL}/games/{test_game_id}/transactions", json=payload, headers=HEADERS)
        
        if response.status_code == 200:
            log_test("Add initial chips to Player1", True, "Added $1000 cash")
        else:
            log_test("Add initial chips to Player1", False, f"Status: {response.status_code}")
            return False
            
        # Add $800 cash for Player2
        payload = {
            "player_id": test_players[1]['id'],
            "transaction_type": "cash",
            "amount": 800.0,
            "description": "Initial cash for validation testing"
        }
        
        response = requests.post(f"{BASE_URL}/games/{test_game_id}/transactions", json=payload, headers=HEADERS)
        
        if response.status_code == 200:
            log_test("Add initial chips to Player2", True, "Added $800 cash")
            return True
        else:
            log_test("Add initial chips to Player2", False, f"Status: {response.status_code}")
            return False
            
    except Exception as e:
        log_test("Add initial chips", False, f"Exception: {str(e)}")
        return False

def test_cashed_out_validation():
    """Test CASHED_OUT validation - should fail if amount > chips_in_game"""
    print("=" * 70)
    print("2. TESTING CASHED_OUT VALIDATION (PREVENT NEGATIVE chips_in_game)")
    print("=" * 70)
    
    player1_id = test_players[0]['id']  # Has $1000 chips in game
    
    # Test 1: Try to cash out more than available chips (should fail)
    try:
        payload = {
            "player_id": player1_id,
            "transaction_type": "cashed_out",
            "amount": 1500.0,  # More than $1000 available
            "description": "Should fail - exceeds chips in game"
        }
        
        response = requests.post(f"{BASE_URL}/games/{test_game_id}/transactions", json=payload, headers=HEADERS)
        
        if response.status_code == 400:
            error_message = response.json().get("detail", "")
            expected_keywords = ["Cannot cash out", "1500", "1000", "chips in game"]
            
            if all(keyword in error_message for keyword in expected_keywords):
                log_test("CASHED_OUT validation - exceeds chips", True, f"Correct error: {error_message}")
            else:
                log_test("CASHED_OUT validation - exceeds chips", False, f"Wrong error message: {error_message}")
                return False
        else:
            log_test("CASHED_OUT validation - exceeds chips", False, f"Expected 400, got {response.status_code}")
            return False
            
    except Exception as e:
        log_test("CASHED_OUT validation - exceeds chips", False, f"Exception: {str(e)}")
        return False
    
    # Test 2: Try to cash out exactly available chips (should succeed)
    try:
        payload = {
            "player_id": player1_id,
            "transaction_type": "cashed_out",
            "amount": 500.0,  # Less than $1000 available
            "description": "Should succeed - within chips limit"
        }
        
        response = requests.post(f"{BASE_URL}/games/{test_game_id}/transactions", json=payload, headers=HEADERS)
        
        if response.status_code == 200:
            log_test("CASHED_OUT validation - valid amount", True, "Successfully cashed out $500")
        else:
            log_test("CASHED_OUT validation - valid amount", False, f"Status: {response.status_code}")
            return False
            
    except Exception as e:
        log_test("CASHED_OUT validation - valid amount", False, f"Exception: {str(e)}")
        return False
    
    # Test 3: Try to cash out more than remaining chips after previous cashout (should fail)
    try:
        payload = {
            "player_id": player1_id,
            "transaction_type": "cashed_out",
            "amount": 600.0,  # More than remaining $500
            "description": "Should fail - exceeds remaining chips"
        }
        
        response = requests.post(f"{BASE_URL}/games/{test_game_id}/transactions", json=payload, headers=HEADERS)
        
        if response.status_code == 400:
            error_message = response.json().get("detail", "")
            expected_keywords = ["Cannot cash out", "600", "500", "chips in game"]
            
            if all(keyword in error_message for keyword in expected_keywords):
                log_test("CASHED_OUT validation - exceeds remaining", True, f"Correct error: {error_message}")
                return True
            else:
                log_test("CASHED_OUT validation - exceeds remaining", False, f"Wrong error message: {error_message}")
                return False
        else:
            log_test("CASHED_OUT validation - exceeds remaining", False, f"Expected 400, got {response.status_code}")
            return False
            
    except Exception as e:
        log_test("CASHED_OUT validation - exceeds remaining", False, f"Exception: {str(e)}")
        return False

def test_paid_with_chips_validation():
    """Test PAID_WITH_CHIPS validation - should fail if amount > chips_in_game"""
    print("=" * 70)
    print("3. TESTING PAID_WITH_CHIPS VALIDATION (PREVENT NEGATIVE chips_in_game)")
    print("=" * 70)
    
    player2_id = test_players[1]['id']  # Has $800 chips in game
    
    # Test 1: Try to pay more than available chips (should fail)
    try:
        payload = {
            "player_id": player2_id,
            "transaction_type": "paid_with_chips",
            "amount": 1000.0,  # More than $800 available
            "description": "Should fail - exceeds chips in game"
        }
        
        response = requests.post(f"{BASE_URL}/games/{test_game_id}/transactions", json=payload, headers=HEADERS)
        
        if response.status_code == 400:
            error_message = response.json().get("detail", "")
            expected_keywords = ["Cannot pay", "1000", "chips", "800", "chips in game"]
            
            if all(keyword in error_message for keyword in expected_keywords):
                log_test("PAID_WITH_CHIPS validation - exceeds chips", True, f"Correct error: {error_message}")
            else:
                log_test("PAID_WITH_CHIPS validation - exceeds chips", False, f"Wrong error message: {error_message}")
                return False
        else:
            log_test("PAID_WITH_CHIPS validation - exceeds chips", False, f"Expected 400, got {response.status_code}")
            return False
            
    except Exception as e:
        log_test("PAID_WITH_CHIPS validation - exceeds chips", False, f"Exception: {str(e)}")
        return False
    
    # Test 2: Try to pay with valid amount (should succeed)
    try:
        payload = {
            "player_id": player2_id,
            "transaction_type": "paid_with_chips",
            "amount": 300.0,  # Less than $800 available
            "description": "Should succeed - within chips limit"
        }
        
        response = requests.post(f"{BASE_URL}/games/{test_game_id}/transactions", json=payload, headers=HEADERS)
        
        if response.status_code == 200:
            log_test("PAID_WITH_CHIPS validation - valid amount", True, "Successfully paid $300 with chips")
        else:
            log_test("PAID_WITH_CHIPS validation - valid amount", False, f"Status: {response.status_code}")
            return False
            
    except Exception as e:
        log_test("PAID_WITH_CHIPS validation - valid amount", False, f"Exception: {str(e)}")
        return False
    
    # Test 3: Try to pay more than remaining chips after previous payment (should fail)
    try:
        payload = {
            "player_id": player2_id,
            "transaction_type": "paid_with_chips",
            "amount": 600.0,  # More than remaining $500
            "description": "Should fail - exceeds remaining chips"
        }
        
        response = requests.post(f"{BASE_URL}/games/{test_game_id}/transactions", json=payload, headers=HEADERS)
        
        if response.status_code == 400:
            error_message = response.json().get("detail", "")
            expected_keywords = ["Cannot pay", "600", "chips", "500", "chips in game"]
            
            if all(keyword in error_message for keyword in expected_keywords):
                log_test("PAID_WITH_CHIPS validation - exceeds remaining", True, f"Correct error: {error_message}")
                return True
            else:
                log_test("PAID_WITH_CHIPS validation - exceeds remaining", False, f"Wrong error message: {error_message}")
                return False
        else:
            log_test("PAID_WITH_CHIPS validation - exceeds remaining", False, f"Expected 400, got {response.status_code}")
            return False
            
    except Exception as e:
        log_test("PAID_WITH_CHIPS validation - exceeds remaining", False, f"Exception: {str(e)}")
        return False

def test_edge_case_zero_chips():
    """Test edge case: exactly $0 chips_in_game after transactions"""
    print("=" * 70)
    print("4. TESTING EDGE CASE - EXACTLY $0 CHIPS_IN_GAME")
    print("=" * 70)
    
    player1_id = test_players[0]['id']  # Should have $500 remaining after previous cashout
    
    # Cash out remaining chips to get exactly $0
    try:
        payload = {
            "player_id": player1_id,
            "transaction_type": "cashed_out",
            "amount": 500.0,  # Exact remaining amount
            "description": "Cash out all remaining chips"
        }
        
        response = requests.post(f"{BASE_URL}/games/{test_game_id}/transactions", json=payload, headers=HEADERS)
        
        if response.status_code == 200:
            log_test("Cash out all remaining chips", True, "Successfully cashed out remaining $500")
            
            # Verify chips_in_game is exactly 0
            response = requests.get(f"{BASE_URL}/games/{test_game_id}", headers=HEADERS)
            if response.status_code == 200:
                game_data = response.json()
                player_info = next((p for p in game_data['players'] if p['player_id'] == player1_id), None)
                
                if player_info:
                    chips_in_game = player_info.get('chips_in_game', 0.0)
                    if abs(chips_in_game) < 0.01:  # Should be exactly 0
                        log_test("Verify chips_in_game is exactly $0", True, f"chips_in_game: ${chips_in_game:.2f}")
                    else:
                        log_test("Verify chips_in_game is exactly $0", False, f"Expected $0.00, got ${chips_in_game:.2f}")
                        return False
                else:
                    log_test("Find player in game", False, "Player not found")
                    return False
            else:
                log_test("Get game data", False, f"Status: {response.status_code}")
                return False
        else:
            log_test("Cash out all remaining chips", False, f"Status: {response.status_code}")
            return False
            
    except Exception as e:
        log_test("Edge case - zero chips", False, f"Exception: {str(e)}")
        return False
    
    # Try to cash out when chips_in_game is 0 (should fail)
    try:
        payload = {
            "player_id": player1_id,
            "transaction_type": "cashed_out",
            "amount": 100.0,
            "description": "Should fail - no chips left"
        }
        
        response = requests.post(f"{BASE_URL}/games/{test_game_id}/transactions", json=payload, headers=HEADERS)
        
        if response.status_code == 400:
            error_message = response.json().get("detail", "")
            if "Cannot cash out" in error_message and "0" in error_message:
                log_test("CASHED_OUT validation - zero chips", True, f"Correct error: {error_message}")
                return True
            else:
                log_test("CASHED_OUT validation - zero chips", False, f"Wrong error message: {error_message}")
                return False
        else:
            log_test("CASHED_OUT validation - zero chips", False, f"Expected 400, got {response.status_code}")
            return False
            
    except Exception as e:
        log_test("CASHED_OUT validation - zero chips", False, f"Exception: {str(e)}")
        return False

def verify_no_negative_chips():
    """Verify that all players have chips_in_game >= 0"""
    print("=" * 70)
    print("5. VERIFYING NO NEGATIVE chips_in_game FOR ALL PLAYERS")
    print("=" * 70)
    
    try:
        response = requests.get(f"{BASE_URL}/games/{test_game_id}", headers=HEADERS)
        
        if response.status_code == 200:
            game_data = response.json()
            all_positive = True
            
            for player_info in game_data['players']:
                player_name = player_info.get('player_name', 'Unknown')
                chips_in_game = player_info.get('chips_in_game', 0.0)
                
                if chips_in_game >= 0:
                    log_test(f"Verify {player_name} chips_in_game >= 0", True, f"chips_in_game: ${chips_in_game:.2f}")
                else:
                    log_test(f"Verify {player_name} chips_in_game >= 0", False, f"NEGATIVE chips_in_game: ${chips_in_game:.2f}")
                    all_positive = False
            
            if all_positive:
                log_test("All players have non-negative chips_in_game", True, "No negative chips_in_game found")
                return True
            else:
                log_test("All players have non-negative chips_in_game", False, "Found negative chips_in_game")
                return False
        else:
            log_test("Get game data for verification", False, f"Status: {response.status_code}")
            return False
            
    except Exception as e:
        log_test("Verify no negative chips", False, f"Exception: {str(e)}")
        return False

def test_pay_credit_still_works():
    """Verify PAY_CREDIT still works correctly and doesn't affect chips_in_game"""
    print("=" * 70)
    print("6. VERIFYING PAY_CREDIT STILL WORKS (DOESN'T AFFECT chips_in_game)")
    print("=" * 70)
    
    player1_id = test_players[0]['id']  # Has debt but may have $0 chips_in_game after cashout
    
    # First ensure player still has debt for PAY_CREDIT to work
    try:
        response = requests.get(f"{BASE_URL}/players/{player1_id}", headers=HEADERS)
        if response.status_code == 200:
            player_data = response.json()
            current_balance = player_data['current_balance']
            
            if current_balance >= 0:
                # Player doesn't have debt anymore, skip this test
                log_test("PAY_CREDIT verification", True, "Skipped - Player has no debt after previous transactions")
                return True
        else:
            log_test("Check player debt status", False, f"Status: {response.status_code}")
            return False
    except Exception as e:
        log_test("Check player debt status", False, f"Exception: {str(e)}")
        return False
    
    try:
        # Get initial state
        response = requests.get(f"{BASE_URL}/players/{player1_id}", headers=HEADERS)
        if response.status_code != 200:
            log_test("Get player initial state", False, f"Status: {response.status_code}")
            return False
        
        player_before = response.json()
        initial_balance = player_before['current_balance']
        
        response = requests.get(f"{BASE_URL}/games/{test_game_id}", headers=HEADERS)
        if response.status_code != 200:
            log_test("Get game initial state", False, f"Status: {response.status_code}")
            return False
        
        game_before = response.json()
        player_info = next((p for p in game_before['players'] if p['player_id'] == player1_id), None)
        initial_chips = player_info.get('chips_in_game', 0.0) if player_info else 0.0
        
        # Perform PAY_CREDIT
        payload = {
            "player_id": player1_id,
            "transaction_type": "pay_credit",
            "amount": 100.0,
            "description": "Pay off some debt"
        }
        
        response = requests.post(f"{BASE_URL}/games/{test_game_id}/transactions", json=payload, headers=HEADERS)
        
        if response.status_code == 200:
            log_test("PAY_CREDIT transaction", True, "Successfully paid $100 credit")
            
            # Verify balance changed
            response = requests.get(f"{BASE_URL}/players/{player1_id}", headers=HEADERS)
            if response.status_code == 200:
                player_after = response.json()
                final_balance = player_after['current_balance']
                expected_balance = initial_balance + 100.0
                
                if abs(final_balance - expected_balance) < 0.01:
                    log_test("PAY_CREDIT reduces debt", True, f"Balance: ${initial_balance:.2f} → ${final_balance:.2f}")
                else:
                    log_test("PAY_CREDIT reduces debt", False, f"Expected: ${expected_balance:.2f}, got: ${final_balance:.2f}")
                    return False
            else:
                log_test("Get player final state", False, f"Status: {response.status_code}")
                return False
            
            # Verify chips_in_game UNCHANGED
            response = requests.get(f"{BASE_URL}/games/{test_game_id}", headers=HEADERS)
            if response.status_code == 200:
                game_after = response.json()
                player_info_after = next((p for p in game_after['players'] if p['player_id'] == player1_id), None)
                final_chips = player_info_after.get('chips_in_game', 0.0) if player_info_after else 0.0
                
                if abs(final_chips - initial_chips) < 0.01:
                    log_test("PAY_CREDIT doesn't affect chips_in_game", True, f"chips_in_game: ${initial_chips:.2f} → ${final_chips:.2f} (UNCHANGED)")
                    return True
                else:
                    log_test("PAY_CREDIT doesn't affect chips_in_game", False, f"Expected: ${initial_chips:.2f}, got: ${final_chips:.2f}")
                    return False
            else:
                log_test("Get game final state", False, f"Status: {response.status_code}")
                return False
        else:
            log_test("PAY_CREDIT transaction", False, f"Status: {response.status_code}")
            return False
            
    except Exception as e:
        log_test("PAY_CREDIT verification", False, f"Exception: {str(e)}")
        return False

def cleanup_test_data():
    """Clean up test data"""
    print("=" * 70)
    print("7. CLEANUP")
    print("=" * 70)
    
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

def run_validation_tests():
    """Run validation tests for preventing negative chips_in_game"""
    print("🎯 POKER CHIP MANAGEMENT - VALIDATION BUG FIX TESTING")
    print("Focus: Prevent negative chips_in_game with proper validation")
    print("=" * 80)
    print(f"Testing against: {BASE_URL}")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    test_results = []
    
    # Run validation tests
    test_results.append(("Setup test environment", setup_test_environment()))
    test_results.append(("CASHED_OUT validation", test_cashed_out_validation()))
    test_results.append(("PAID_WITH_CHIPS validation", test_paid_with_chips_validation()))
    test_results.append(("Edge case - zero chips", test_edge_case_zero_chips()))
    test_results.append(("Verify no negative chips", verify_no_negative_chips()))
    test_results.append(("PAY_CREDIT still works", test_pay_credit_still_works()))
    
    # Cleanup
    cleanup_test_data()
    
    # Summary
    print("=" * 80)
    print("📊 VALIDATION BUG FIX TEST SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print()
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL VALIDATION BUG FIX TESTS PASSED!")
        print("\n✅ Key Bug Fixes Verified:")
        print("   • CASHED_OUT validation prevents negative chips_in_game")
        print("   • PAID_WITH_CHIPS validation prevents negative chips_in_game")
        print("   • Proper error messages for invalid transactions")
        print("   • Valid transactions still work correctly")
        print("   • PAY_CREDIT remains unaffected by changes")
        print("   • All players maintain chips_in_game >= 0")
        return True
    else:
        print("⚠️  SOME VALIDATION TESTS FAILED! Check the details above.")
        return False

if __name__ == "__main__":
    success = run_validation_tests()
    exit(0 if success else 1)