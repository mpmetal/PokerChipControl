#!/usr/bin/env python3
"""
Isolated Pay Credit and Club Earnings Test
This test focuses specifically on the new features without interference from existing data
"""

import requests
import json
from datetime import datetime

# Configuration
BASE_URL = "https://chipmaster-2.preview.emergentagent.com/api"
HEADERS = {"Content-Type": "application/json"}

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

def test_pay_credit_validation_isolated():
    """Test PAY_CREDIT validation in isolation"""
    print("=" * 60)
    print("ISOLATED PAY_CREDIT VALIDATION TEST")
    print("=" * 60)
    
    # Create a player with positive balance (no debt)
    try:
        payload = {"name": "TestPlayerNoDebt"}
        response = requests.post(f"{BASE_URL}/players", json=payload, headers=HEADERS)
        
        if response.status_code != 200:
            log_test("Create test player", False, f"Status: {response.status_code}")
            return False
        
        player_data = response.json()
        player_id = player_data['id']
        
        # Set positive balance (no debt)
        update_payload = {"current_balance": 100.0}
        response = requests.put(f"{BASE_URL}/players/{player_id}", json=update_payload, headers=HEADERS)
        
        if response.status_code != 200:
            log_test("Set positive balance", False, f"Status: {response.status_code}")
            return False
        
        # Create a game with this player
        game_payload = {"name": "Validation Test Game", "player_ids": [player_id]}
        response = requests.post(f"{BASE_URL}/games", json=game_payload, headers=HEADERS)
        
        if response.status_code != 200:
            log_test("Create test game", False, f"Status: {response.status_code}")
            return False
        
        game_data = response.json()
        game_id = game_data['id']
        
        # Verify player has no debt
        response = requests.get(f"{BASE_URL}/players/{player_id}", headers=HEADERS)
        if response.status_code == 200:
            player_info = response.json()
            balance = player_info['current_balance']
            log_test("Verify player has no debt", True, f"Balance: ${balance:.2f}")
            
            if balance < 0:
                log_test("Player balance check", False, f"Expected positive balance, got ${balance:.2f}")
                return False
        else:
            log_test("Get player info", False, f"Status: {response.status_code}")
            return False
        
        # Try PAY_CREDIT transaction (should fail)
        pay_credit_payload = {
            "player_id": player_id,
            "transaction_type": "pay_credit",
            "amount": 50.0,
            "description": "Should fail - no debt"
        }
        
        response = requests.post(f"{BASE_URL}/games/{game_id}/transactions", json=pay_credit_payload, headers=HEADERS)
        
        if response.status_code == 400:
            log_test("PAY_CREDIT validation works", True, "Correctly rejected PAY_CREDIT for player with no debt")
            success = True
        else:
            log_test("PAY_CREDIT validation works", False, f"Expected 400, got {response.status_code}")
            if response.status_code == 200:
                print(f"    Transaction was incorrectly created: {response.json()}")
            success = False
        
        # Cleanup
        requests.post(f"{BASE_URL}/games/{game_id}/close", headers=HEADERS)
        requests.delete(f"{BASE_URL}/players/{player_id}", headers=HEADERS)
        
        return success
        
    except Exception as e:
        log_test("PAY_CREDIT validation test", False, f"Exception: {str(e)}")
        return False

def test_pay_credit_with_debt_player():
    """Test PAY_CREDIT with a player who actually has debt"""
    print("=" * 60)
    print("PAY_CREDIT WITH DEBT PLAYER TEST")
    print("=" * 60)
    
    try:
        # Create a player with debt
        payload = {"name": "TestPlayerWithDebt"}
        response = requests.post(f"{BASE_URL}/players", json=payload, headers=HEADERS)
        
        if response.status_code != 200:
            log_test("Create debt player", False, f"Status: {response.status_code}")
            return False
        
        player_data = response.json()
        player_id = player_data['id']
        
        # Set negative balance (debt)
        update_payload = {"current_balance": -300.0}
        response = requests.put(f"{BASE_URL}/players/{player_id}", json=update_payload, headers=HEADERS)
        
        if response.status_code != 200:
            log_test("Set negative balance", False, f"Status: {response.status_code}")
            return False
        
        # Create a game with this player
        game_payload = {"name": "Debt Test Game", "player_ids": [player_id]}
        response = requests.post(f"{BASE_URL}/games", json=game_payload, headers=HEADERS)
        
        if response.status_code != 200:
            log_test("Create debt test game", False, f"Status: {response.status_code}")
            return False
        
        game_data = response.json()
        game_id = game_data['id']
        
        # Add some chips to the game first
        cash_payload = {
            "player_id": player_id,
            "transaction_type": "cash",
            "amount": 500.0,
            "description": "Add chips to game"
        }
        
        response = requests.post(f"{BASE_URL}/games/{game_id}/transactions", json=cash_payload, headers=HEADERS)
        if response.status_code != 200:
            log_test("Add chips to game", False, f"Status: {response.status_code}")
            return False
        
        log_test("Add chips to game", True, "Added $500 in chips")
        
        # Get initial state
        response = requests.get(f"{BASE_URL}/players/{player_id}", headers=HEADERS)
        if response.status_code != 200:
            log_test("Get initial player state", False, f"Status: {response.status_code}")
            return False
        
        initial_player = response.json()
        initial_balance = initial_player['current_balance']
        
        response = requests.get(f"{BASE_URL}/games/{game_id}", headers=HEADERS)
        if response.status_code != 200:
            log_test("Get initial game state", False, f"Status: {response.status_code}")
            return False
        
        initial_game = response.json()
        initial_chips = initial_game['players'][0].get('chips_in_game', 0.0)
        
        log_test("Get initial states", True, f"Balance: ${initial_balance:.2f}, Chips in game: ${initial_chips:.2f}")
        
        # Try PAY_CREDIT transaction (should succeed)
        pay_amount = 150.0
        pay_credit_payload = {
            "player_id": player_id,
            "transaction_type": "pay_credit",
            "amount": pay_amount,
            "description": "Pay off part of debt"
        }
        
        response = requests.post(f"{BASE_URL}/games/{game_id}/transactions", json=pay_credit_payload, headers=HEADERS)
        
        if response.status_code == 200:
            log_test("PAY_CREDIT transaction created", True, f"Paid ${pay_amount:.2f}")
            
            # Check final states
            response = requests.get(f"{BASE_URL}/players/{player_id}", headers=HEADERS)
            if response.status_code == 200:
                final_player = response.json()
                final_balance = final_player['current_balance']
                expected_balance = initial_balance + pay_amount
                
                if abs(final_balance - expected_balance) < 0.01:
                    log_test("Player debt reduced", True, f"Balance: ${initial_balance:.2f} → ${final_balance:.2f}")
                else:
                    log_test("Player debt reduced", False, f"Expected: ${expected_balance:.2f}, Got: ${final_balance:.2f}")
                    return False
            
            response = requests.get(f"{BASE_URL}/games/{game_id}", headers=HEADERS)
            if response.status_code == 200:
                final_game = response.json()
                final_chips = final_game['players'][0].get('chips_in_game', 0.0)
                expected_chips = initial_chips - pay_amount
                
                if abs(final_chips - expected_chips) < 0.01:
                    log_test("Chips in game reduced", True, f"Chips: ${initial_chips:.2f} → ${final_chips:.2f}")
                    success = True
                else:
                    log_test("Chips in game reduced", False, f"Expected: ${expected_chips:.2f}, Got: ${final_chips:.2f}")
                    success = False
            else:
                log_test("Get final game state", False, f"Status: {response.status_code}")
                success = False
        else:
            log_test("PAY_CREDIT transaction created", False, f"Status: {response.status_code}, Response: {response.text}")
            success = False
        
        # Cleanup
        requests.post(f"{BASE_URL}/games/{game_id}/close", headers=HEADERS)
        requests.delete(f"{BASE_URL}/players/{player_id}", headers=HEADERS)
        
        return success
        
    except Exception as e:
        log_test("PAY_CREDIT with debt test", False, f"Exception: {str(e)}")
        return False

def run_isolated_tests():
    """Run isolated tests for Pay Credit functionality"""
    print("🎯 ISOLATED PAY CREDIT TESTING")
    print("Focus: Testing Pay Credit validation and functionality in isolation")
    print("=" * 80)
    print(f"Testing against: {BASE_URL}")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    test_results = []
    
    # Run isolated tests
    test_results.append(("PAY_CREDIT validation (no debt)", test_pay_credit_validation_isolated()))
    test_results.append(("PAY_CREDIT functionality (with debt)", test_pay_credit_with_debt_player()))
    
    # Summary
    print("=" * 80)
    print("📊 ISOLATED TEST SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print()
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL ISOLATED PAY CREDIT TESTS PASSED!")
        return True
    else:
        print("⚠️  SOME ISOLATED TESTS FAILED!")
        return False

if __name__ == "__main__":
    success = run_isolated_tests()
    exit(0 if success else 1)