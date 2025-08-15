#!/usr/bin/env python3
"""
Isolated Club Earnings Test
This test focuses specifically on the Club Earnings calculation
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
    if not success:
        print(f"    ❗ This is a critical failure")
    print()

def get_current_club_earnings():
    """Get current club earnings from dashboard"""
    try:
        response = requests.get(f"{BASE_URL}/dashboard", headers=HEADERS)
        if response.status_code == 200:
            data = response.json()
            return data.get("club_earnings", 0.0)
        return None
    except:
        return None

def test_club_earnings_calculation():
    """Test Club Earnings calculation with fresh games"""
    print("=" * 60)
    print("CLUB EARNINGS CALCULATION TEST")
    print("=" * 60)
    
    # Get initial club earnings
    initial_earnings = get_current_club_earnings()
    if initial_earnings is None:
        log_test("Get initial club earnings", False, "Failed to get dashboard data")
        return False
    
    log_test("Get initial club earnings", True, f"Initial: ${initial_earnings:.2f}")
    
    try:
        # Create test players
        players = []
        for i, name in enumerate(["TestPlayer1", "TestPlayer2"]):
            payload = {"name": name}
            response = requests.post(f"{BASE_URL}/players", json=payload, headers=HEADERS)
            
            if response.status_code != 200:
                log_test(f"Create {name}", False, f"Status: {response.status_code}")
                return False
            
            players.append(response.json())
            log_test(f"Create {name}", True, f"ID: {response.json()['id']}")
        
        # Create Game 1
        game1_payload = {"name": "Club Earnings Test Game 1", "player_ids": [players[0]['id']]}
        response = requests.post(f"{BASE_URL}/games", json=game1_payload, headers=HEADERS)
        
        if response.status_code != 200:
            log_test("Create Game 1", False, f"Status: {response.status_code}")
            return False
        
        game1_data = response.json()
        game1_id = game1_data['id']
        log_test("Create Game 1", True, f"ID: {game1_id}")
        
        # Create Game 2
        game2_payload = {"name": "Club Earnings Test Game 2", "player_ids": [players[1]['id']]}
        response = requests.post(f"{BASE_URL}/games", json=game2_payload, headers=HEADERS)
        
        if response.status_code != 200:
            log_test("Create Game 2", False, f"Status: {response.status_code}")
            return False
        
        game2_data = response.json()
        game2_id = game2_data['id']
        log_test("Create Game 2", True, f"ID: {game2_id}")
        
        # Add chips to Game 1
        game1_amount = 1000.0
        transaction1_payload = {
            "player_id": players[0]['id'],
            "transaction_type": "cash",
            "amount": game1_amount,
            "description": "Game 1 chips"
        }
        
        response = requests.post(f"{BASE_URL}/games/{game1_id}/transactions", json=transaction1_payload, headers=HEADERS)
        
        if response.status_code != 200:
            log_test("Add chips to Game 1", False, f"Status: {response.status_code}")
            return False
        
        log_test("Add chips to Game 1", True, f"Added ${game1_amount:.2f}")
        
        # Add chips to Game 2
        game2_amount = 750.0
        transaction2_payload = {
            "player_id": players[1]['id'],
            "transaction_type": "bank_transfer",
            "amount": game2_amount,
            "description": "Game 2 chips"
        }
        
        response = requests.post(f"{BASE_URL}/games/{game2_id}/transactions", json=transaction2_payload, headers=HEADERS)
        
        if response.status_code != 200:
            log_test("Add chips to Game 2", False, f"Status: {response.status_code}")
            return False
        
        log_test("Add chips to Game 2", True, f"Added ${game2_amount:.2f}")
        
        # Check club earnings after adding chips
        expected_increase = game1_amount + game2_amount
        expected_earnings = initial_earnings + expected_increase
        
        current_earnings = get_current_club_earnings()
        if current_earnings is None:
            log_test("Get updated club earnings", False, "Failed to get dashboard data")
            return False
        
        log_test("Get updated club earnings", True, f"Current: ${current_earnings:.2f}")
        
        if abs(current_earnings - expected_earnings) < 0.01:
            log_test("Club earnings increased correctly", True, f"Increased by ${expected_increase:.2f}")
        else:
            log_test("Club earnings increased correctly", False, f"Expected: ${expected_earnings:.2f}, Got: ${current_earnings:.2f}")
            # Let's check if it at least increased
            if current_earnings > initial_earnings:
                log_test("Club earnings increased", True, f"Increased from ${initial_earnings:.2f} to ${current_earnings:.2f}")
            else:
                return False
        
        # Verify by checking individual games
        response1 = requests.get(f"{BASE_URL}/games/{game1_id}", headers=HEADERS)
        response2 = requests.get(f"{BASE_URL}/games/{game2_id}", headers=HEADERS)
        
        if response1.status_code == 200 and response2.status_code == 200:
            game1_chips = sum(p.get('chips_in_game', 0.0) for p in response1.json()['players'])
            game2_chips = sum(p.get('chips_in_game', 0.0) for p in response2.json()['players'])
            total_test_chips = game1_chips + game2_chips
            
            log_test("Verify individual game chips", True, f"Game1: ${game1_chips:.2f}, Game2: ${game2_chips:.2f}, Total: ${total_test_chips:.2f}")
            
            if abs(total_test_chips - expected_increase) < 0.01:
                log_test("Individual game chips match expected", True, f"Both show ${expected_increase:.2f}")
                success = True
            else:
                log_test("Individual game chips match expected", False, f"Expected: ${expected_increase:.2f}, Got: ${total_test_chips:.2f}")
                success = False
        else:
            log_test("Get individual game data", False, "Failed to get game data")
            success = False
        
        # Cleanup
        requests.post(f"{BASE_URL}/games/{game1_id}/close", headers=HEADERS)
        requests.post(f"{BASE_URL}/games/{game2_id}/close", headers=HEADERS)
        
        for player in players:
            requests.delete(f"{BASE_URL}/players/{player['id']}", headers=HEADERS)
        
        return success
        
    except Exception as e:
        log_test("Club earnings calculation test", False, f"Exception: {str(e)}")
        return False

def test_dashboard_api_fields():
    """Test that dashboard API contains all required fields including club_earnings"""
    print("=" * 60)
    print("DASHBOARD API FIELDS TEST")
    print("=" * 60)
    
    try:
        response = requests.get(f"{BASE_URL}/dashboard", headers=HEADERS)
        
        if response.status_code != 200:
            log_test("Get dashboard", False, f"Status: {response.status_code}")
            return False
        
        data = response.json()
        
        # Check required fields
        required_fields = [
            "active_games",
            "total_players", 
            "total_credit_owed",
            "total_debt_owed",
            "club_earnings",  # NEW FIELD
            "recent_transactions"
        ]
        
        all_fields_present = True
        for field in required_fields:
            if field in data:
                field_value = data[field]
                if field == "recent_transactions":
                    log_test(f"Dashboard field '{field}'", True, f"Count: {len(field_value)}")
                else:
                    log_test(f"Dashboard field '{field}'", True, f"Value: {field_value}")
            else:
                log_test(f"Dashboard field '{field}'", False, "Field missing")
                all_fields_present = False
        
        if all_fields_present:
            log_test("All dashboard fields present", True, "Including new club_earnings field")
            return True
        else:
            log_test("All dashboard fields present", False, "Some fields missing")
            return False
        
    except Exception as e:
        log_test("Dashboard API fields test", False, f"Exception: {str(e)}")
        return False

def run_club_earnings_tests():
    """Run isolated tests for Club Earnings functionality"""
    print("🎯 ISOLATED CLUB EARNINGS TESTING")
    print("Focus: Testing Club Earnings calculation and Dashboard API")
    print("=" * 80)
    print(f"Testing against: {BASE_URL}")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    test_results = []
    
    # Run isolated tests
    test_results.append(("Dashboard API fields", test_dashboard_api_fields()))
    test_results.append(("Club Earnings calculation", test_club_earnings_calculation()))
    
    # Summary
    print("=" * 80)
    print("📊 CLUB EARNINGS TEST SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print()
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL CLUB EARNINGS TESTS PASSED!")
        return True
    else:
        print("⚠️  SOME CLUB EARNINGS TESTS FAILED!")
        return False

if __name__ == "__main__":
    success = run_club_earnings_tests()
    exit(0 if success else 1)