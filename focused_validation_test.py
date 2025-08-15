#!/usr/bin/env python3
"""
FOCUSED VALIDATION TEST - Specific Bug Fix Scenarios from Review Request
Test the exact scenarios mentioned in the review request:
1. PAY_CREDIT still does NOT affect chips_in_game (already verified)
2. CASHED_OUT validation prevents negative chips_in_game
3. PAID_WITH_CHIPS validation prevents negative chips_in_game
"""

import requests
import json
from datetime import datetime

# Configuration
BASE_URL = "https://pokertable-app.preview.emergentagent.com/api"
HEADERS = {"Content-Type": "application/json"}

def log_test(test_name, success, details=""):
    """Log test results with timestamp"""
    status = "✅ PASS" if success else "❌ FAIL"
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {status} {test_name}")
    if details:
        print(f"    Details: {details}")
    print()

def test_scenario_1_cashed_out_validation():
    """Scenario 1 - Test CASHED_OUT Validation"""
    print("=" * 80)
    print("SCENARIO 1 - TEST CASHED_OUT VALIDATION")
    print("=" * 80)
    
    # Create player with debt
    try:
        payload = {"name": "CashOutTestPlayer"}
        response = requests.post(f"{BASE_URL}/players", json=payload, headers=HEADERS)
        if response.status_code != 200:
            log_test("Create player", False, f"Status: {response.status_code}")
            return False
        
        player_data = response.json()
        player_id = player_data['id']
        
        # Set debt
        update_payload = {"current_balance": -500.0}
        response = requests.put(f"{BASE_URL}/players/{player_id}", json=update_payload, headers=HEADERS)
        if response.status_code != 200:
            log_test("Set player debt", False, f"Status: {response.status_code}")
            return False
        
        log_test("Create player with debt", True, "Player has -$500 debt")
        
        # Create game
        game_payload = {"name": "CashOut Test Game", "player_ids": [player_id]}
        response = requests.post(f"{BASE_URL}/games", json=game_payload, headers=HEADERS)
        if response.status_code != 200:
            log_test("Create game", False, f"Status: {response.status_code}")
            return False
        
        game_data = response.json()
        game_id = game_data['id']
        log_test("Create game", True, f"Game ID: {game_id}")
        
        # Add $1000 cash to game
        cash_payload = {
            "player_id": player_id,
            "transaction_type": "cash",
            "amount": 1000.0,
            "description": "Add cash to game"
        }
        
        response = requests.post(f"{BASE_URL}/games/{game_id}/transactions", json=cash_payload, headers=HEADERS)
        if response.status_code != 200:
            log_test("Add $1000 cash", False, f"Status: {response.status_code}")
            return False
        
        log_test("Add $1000 cash", True, "Player has $1000 chips in game")
        
        # Try to CASH_OUT $1500 (more than $1000 in game) - should fail
        cashout_payload = {
            "player_id": player_id,
            "transaction_type": "cashed_out",
            "amount": 1500.0,
            "description": "Should fail - exceeds chips in game"
        }
        
        response = requests.post(f"{BASE_URL}/games/{game_id}/transactions", json=cashout_payload, headers=HEADERS)
        
        if response.status_code == 400:
            error_message = response.json().get("detail", "")
            if "Cannot cash out" in error_message and "1500" in error_message and "1000" in error_message and "chips in game" in error_message:
                log_test("CASHED_OUT validation fails correctly", True, f"Error: {error_message}")
            else:
                log_test("CASHED_OUT validation fails correctly", False, f"Wrong error: {error_message}")
                return False
        else:
            log_test("CASHED_OUT validation fails correctly", False, f"Expected 400, got {response.status_code}")
            return False
        
        # Try valid CASH_OUT $500 - should succeed
        valid_cashout_payload = {
            "player_id": player_id,
            "transaction_type": "cashed_out",
            "amount": 500.0,
            "description": "Valid cashout"
        }
        
        response = requests.post(f"{BASE_URL}/games/{game_id}/transactions", json=valid_cashout_payload, headers=HEADERS)
        
        if response.status_code == 200:
            log_test("Valid CASHED_OUT succeeds", True, "Successfully cashed out $500")
        else:
            log_test("Valid CASHED_OUT succeeds", False, f"Status: {response.status_code}")
            return False
        
        # Cleanup
        requests.post(f"{BASE_URL}/games/{game_id}/close", headers=HEADERS)
        requests.delete(f"{BASE_URL}/players/{player_id}", headers=HEADERS)
        
        return True
        
    except Exception as e:
        log_test("Scenario 1", False, f"Exception: {str(e)}")
        return False

def test_scenario_2_paid_with_chips_validation():
    """Scenario 2 - Test PAID_WITH_CHIPS Validation"""
    print("=" * 80)
    print("SCENARIO 2 - TEST PAID_WITH_CHIPS VALIDATION")
    print("=" * 80)
    
    try:
        # Create player
        payload = {"name": "PaidWithChipsTestPlayer"}
        response = requests.post(f"{BASE_URL}/players", json=payload, headers=HEADERS)
        if response.status_code != 200:
            log_test("Create player", False, f"Status: {response.status_code}")
            return False
        
        player_data = response.json()
        player_id = player_data['id']
        log_test("Create player", True, "Player created")
        
        # Create game
        game_payload = {"name": "PaidWithChips Test Game", "player_ids": [player_id]}
        response = requests.post(f"{BASE_URL}/games", json=game_payload, headers=HEADERS)
        if response.status_code != 200:
            log_test("Create game", False, f"Status: {response.status_code}")
            return False
        
        game_data = response.json()
        game_id = game_data['id']
        log_test("Create game", True, f"Game ID: {game_id}")
        
        # Add $800 cash to game
        cash_payload = {
            "player_id": player_id,
            "transaction_type": "cash",
            "amount": 800.0,
            "description": "Add cash to game"
        }
        
        response = requests.post(f"{BASE_URL}/games/{game_id}/transactions", json=cash_payload, headers=HEADERS)
        if response.status_code != 200:
            log_test("Add $800 cash", False, f"Status: {response.status_code}")
            return False
        
        log_test("Add $800 cash", True, "Player has $800 chips in game")
        
        # Try PAID_WITH_CHIPS $1000 (more than $800 available) - should fail
        pay_payload = {
            "player_id": player_id,
            "transaction_type": "paid_with_chips",
            "amount": 1000.0,
            "description": "Should fail - exceeds chips in game"
        }
        
        response = requests.post(f"{BASE_URL}/games/{game_id}/transactions", json=pay_payload, headers=HEADERS)
        
        if response.status_code == 400:
            error_message = response.json().get("detail", "")
            if "Cannot pay" in error_message and "1000" in error_message and "800" in error_message and "chips in game" in error_message:
                log_test("PAID_WITH_CHIPS validation fails correctly", True, f"Error: {error_message}")
            else:
                log_test("PAID_WITH_CHIPS validation fails correctly", False, f"Wrong error: {error_message}")
                return False
        else:
            log_test("PAID_WITH_CHIPS validation fails correctly", False, f"Expected 400, got {response.status_code}")
            return False
        
        # Try valid PAID_WITH_CHIPS $300 - should succeed
        valid_pay_payload = {
            "player_id": player_id,
            "transaction_type": "paid_with_chips",
            "amount": 300.0,
            "description": "Valid payment with chips"
        }
        
        response = requests.post(f"{BASE_URL}/games/{game_id}/transactions", json=valid_pay_payload, headers=HEADERS)
        
        if response.status_code == 200:
            log_test("Valid PAID_WITH_CHIPS succeeds", True, "Successfully paid $300 with chips")
        else:
            log_test("Valid PAID_WITH_CHIPS succeeds", False, f"Status: {response.status_code}")
            return False
        
        # Cleanup
        requests.post(f"{BASE_URL}/games/{game_id}/close", headers=HEADERS)
        requests.delete(f"{BASE_URL}/players/{player_id}", headers=HEADERS)
        
        return True
        
    except Exception as e:
        log_test("Scenario 2", False, f"Exception: {str(e)}")
        return False

def test_scenario_3_verify_no_negative_chips():
    """Scenario 3 - Verify chips_in_game Never Goes Negative"""
    print("=" * 80)
    print("SCENARIO 3 - VERIFY chips_in_game NEVER GOES NEGATIVE")
    print("=" * 80)
    
    try:
        # Create player
        payload = {"name": "NoNegativeChipsPlayer"}
        response = requests.post(f"{BASE_URL}/players", json=payload, headers=HEADERS)
        if response.status_code != 200:
            log_test("Create player", False, f"Status: {response.status_code}")
            return False
        
        player_data = response.json()
        player_id = player_data['id']
        
        # Create game
        game_payload = {"name": "No Negative Chips Game", "player_ids": [player_id]}
        response = requests.post(f"{BASE_URL}/games", json=game_payload, headers=HEADERS)
        if response.status_code != 200:
            log_test("Create game", False, f"Status: {response.status_code}")
            return False
        
        game_data = response.json()
        game_id = game_data['id']
        
        # Add $100 cash
        cash_payload = {
            "player_id": player_id,
            "transaction_type": "cash",
            "amount": 100.0,
            "description": "Add small amount"
        }
        
        response = requests.post(f"{BASE_URL}/games/{game_id}/transactions", json=cash_payload, headers=HEADERS)
        if response.status_code != 200:
            log_test("Add $100 cash", False, f"Status: {response.status_code}")
            return False
        
        log_test("Add $100 cash", True, "Player has $100 chips in game")
        
        # Cash out exactly $100 (should work)
        cashout_payload = {
            "player_id": player_id,
            "transaction_type": "cashed_out",
            "amount": 100.0,
            "description": "Cash out all chips"
        }
        
        response = requests.post(f"{BASE_URL}/games/{game_id}/transactions", json=cashout_payload, headers=HEADERS)
        if response.status_code != 200:
            log_test("Cash out all chips", False, f"Status: {response.status_code}")
            return False
        
        log_test("Cash out all chips", True, "Successfully cashed out $100")
        
        # Verify chips_in_game is exactly 0
        response = requests.get(f"{BASE_URL}/games/{game_id}", headers=HEADERS)
        if response.status_code == 200:
            game_data = response.json()
            player_info = next((p for p in game_data['players'] if p['player_id'] == player_id), None)
            
            if player_info:
                chips_in_game = player_info.get('chips_in_game', 0.0)
                if chips_in_game >= 0:
                    log_test("chips_in_game >= 0 after transactions", True, f"chips_in_game: ${chips_in_game:.2f}")
                else:
                    log_test("chips_in_game >= 0 after transactions", False, f"NEGATIVE chips_in_game: ${chips_in_game:.2f}")
                    return False
            else:
                log_test("Find player in game", False, "Player not found")
                return False
        else:
            log_test("Get game data", False, f"Status: {response.status_code}")
            return False
        
        # Cleanup
        requests.post(f"{BASE_URL}/games/{game_id}/close", headers=HEADERS)
        requests.delete(f"{BASE_URL}/players/{player_id}", headers=HEADERS)
        
        return True
        
    except Exception as e:
        log_test("Scenario 3", False, f"Exception: {str(e)}")
        return False

def test_pay_credit_verification():
    """Verify PAY_CREDIT still works and doesn't affect chips_in_game"""
    print("=" * 80)
    print("PAY_CREDIT VERIFICATION - DOESN'T AFFECT chips_in_game")
    print("=" * 80)
    
    try:
        # Create player with debt
        payload = {"name": "PayCreditTestPlayer"}
        response = requests.post(f"{BASE_URL}/players", json=payload, headers=HEADERS)
        if response.status_code != 200:
            log_test("Create player", False, f"Status: {response.status_code}")
            return False
        
        player_data = response.json()
        player_id = player_data['id']
        
        # Set debt
        update_payload = {"current_balance": -300.0}
        response = requests.put(f"{BASE_URL}/players/{player_id}", json=update_payload, headers=HEADERS)
        if response.status_code != 200:
            log_test("Set player debt", False, f"Status: {response.status_code}")
            return False
        
        # Create game
        game_payload = {"name": "PayCredit Test Game", "player_ids": [player_id]}
        response = requests.post(f"{BASE_URL}/games", json=game_payload, headers=HEADERS)
        if response.status_code != 200:
            log_test("Create game", False, f"Status: {response.status_code}")
            return False
        
        game_data = response.json()
        game_id = game_data['id']
        
        # Add $500 cash to game
        cash_payload = {
            "player_id": player_id,
            "transaction_type": "cash",
            "amount": 500.0,
            "description": "Add cash to game"
        }
        
        response = requests.post(f"{BASE_URL}/games/{game_id}/transactions", json=cash_payload, headers=HEADERS)
        if response.status_code != 200:
            log_test("Add $500 cash", False, f"Status: {response.status_code}")
            return False
        
        # Get initial chips_in_game
        response = requests.get(f"{BASE_URL}/games/{game_id}", headers=HEADERS)
        if response.status_code != 200:
            log_test("Get initial game state", False, f"Status: {response.status_code}")
            return False
        
        game_before = response.json()
        player_info = next((p for p in game_before['players'] if p['player_id'] == player_id), None)
        initial_chips = player_info.get('chips_in_game', 0.0) if player_info else 0.0
        
        log_test("Initial state", True, f"chips_in_game: ${initial_chips:.2f}")
        
        # Perform PAY_CREDIT
        pay_credit_payload = {
            "player_id": player_id,
            "transaction_type": "pay_credit",
            "amount": 200.0,
            "description": "Pay off debt"
        }
        
        response = requests.post(f"{BASE_URL}/games/{game_id}/transactions", json=pay_credit_payload, headers=HEADERS)
        if response.status_code != 200:
            log_test("PAY_CREDIT transaction", False, f"Status: {response.status_code}")
            return False
        
        log_test("PAY_CREDIT transaction", True, "Successfully paid $200 credit")
        
        # Verify chips_in_game UNCHANGED
        response = requests.get(f"{BASE_URL}/games/{game_id}", headers=HEADERS)
        if response.status_code == 200:
            game_after = response.json()
            player_info_after = next((p for p in game_after['players'] if p['player_id'] == player_id), None)
            final_chips = player_info_after.get('chips_in_game', 0.0) if player_info_after else 0.0
            
            if abs(final_chips - initial_chips) < 0.01:
                log_test("PAY_CREDIT doesn't affect chips_in_game", True, f"chips_in_game: ${initial_chips:.2f} → ${final_chips:.2f} (UNCHANGED)")
            else:
                log_test("PAY_CREDIT doesn't affect chips_in_game", False, f"Expected: ${initial_chips:.2f}, got: ${final_chips:.2f}")
                return False
        else:
            log_test("Get final game state", False, f"Status: {response.status_code}")
            return False
        
        # Cleanup
        requests.post(f"{BASE_URL}/games/{game_id}/close", headers=HEADERS)
        requests.delete(f"{BASE_URL}/players/{player_id}", headers=HEADERS)
        
        return True
        
    except Exception as e:
        log_test("PAY_CREDIT verification", False, f"Exception: {str(e)}")
        return False

def run_focused_validation_tests():
    """Run the focused validation tests"""
    print("🎯 FOCUSED VALIDATION TESTING - BUG FIX VERIFICATION")
    print("Testing specific scenarios from review request")
    print("=" * 80)
    print(f"Testing against: {BASE_URL}")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    test_results = []
    
    # Run the specific scenarios
    test_results.append(("Scenario 1 - CASHED_OUT Validation", test_scenario_1_cashed_out_validation()))
    test_results.append(("Scenario 2 - PAID_WITH_CHIPS Validation", test_scenario_2_paid_with_chips_validation()))
    test_results.append(("Scenario 3 - No Negative chips_in_game", test_scenario_3_verify_no_negative_chips()))
    test_results.append(("PAY_CREDIT Verification", test_pay_credit_verification()))
    
    # Summary
    print("=" * 80)
    print("📊 FOCUSED VALIDATION TEST SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print()
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL FOCUSED VALIDATION TESTS PASSED!")
        print("\n✅ Bug Fixes Verified:")
        print("   • CASHED_OUT validation prevents negative chips_in_game")
        print("   • PAID_WITH_CHIPS validation prevents negative chips_in_game")
        print("   • Proper error messages for invalid transactions")
        print("   • Valid transactions still work correctly")
        print("   • PAY_CREDIT remains unaffected by validation changes")
        print("   • chips_in_game never goes negative")
        return True
    else:
        print("⚠️  SOME VALIDATION TESTS FAILED!")
        return False

if __name__ == "__main__":
    success = run_focused_validation_tests()
    exit(0 if success else 1)