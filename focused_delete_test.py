#!/usr/bin/env python3
"""
Focused Player DELETE API Testing
Specifically testing the user-reported issue: "No puedo borrar jugadores"
Focus on the exact workflow the user would experience
"""

import requests
import json
import time
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

def test_user_workflow():
    """Test the exact workflow a user would experience"""
    print("🎯 TESTING USER WORKFLOW: CREATE → VERIFY → DELETE → VERIFY REMOVAL")
    print("=" * 80)
    
    # Step 1: Create a test player (like user would)
    print("\n1️⃣ STEP 1: CREATE A TEST PLAYER")
    try:
        payload = {"name": "Juan Carlos", "photo": None}
        response = requests.post(f"{BASE_URL}/players", json=payload, headers=HEADERS)
        
        if response.status_code == 200:
            player_data = response.json()
            player_id = player_data['id']
            player_name = player_data['name']
            log_test("Create test player", True, f"Created '{player_name}' with ID: {player_id}")
        else:
            log_test("Create test player", False, f"Status: {response.status_code}")
            return False
    except Exception as e:
        log_test("Create test player", False, f"Exception: {str(e)}")
        return False
    
    # Step 2: Verify player exists in the list (like user would see)
    print("\n2️⃣ STEP 2: VERIFY PLAYER EXISTS IN GET /api/players")
    try:
        response = requests.get(f"{BASE_URL}/players", headers=HEADERS)
        
        if response.status_code == 200:
            all_players = response.json()
            player_found = any(p['id'] == player_id for p in all_players)
            
            if player_found:
                log_test("Player exists in players list", True, f"'{player_name}' found in list of {len(all_players)} players")
            else:
                log_test("Player exists in players list", False, f"'{player_name}' not found in players list")
                return False
        else:
            log_test("Get players list", False, f"Status: {response.status_code}")
            return False
    except Exception as e:
        log_test("Verify player exists", False, f"Exception: {str(e)}")
        return False
    
    # Step 3: Delete the player (the problematic step for user)
    print("\n3️⃣ STEP 3: DELETE THE PLAYER (USER'S PROBLEM AREA)")
    try:
        response = requests.delete(f"{BASE_URL}/players/{player_id}", headers=HEADERS)
        
        if response.status_code == 200:
            response_data = response.json()
            log_test("DELETE player request", True, f"Response: {response_data.get('message', 'Success')}")
        else:
            log_test("DELETE player request", False, f"Status: {response.status_code}, Response: {response.text}")
            return False
    except Exception as e:
        log_test("DELETE player request", False, f"Exception: {str(e)}")
        return False
    
    # Step 4: Verify player is actually removed (user's expectation)
    print("\n4️⃣ STEP 4: VERIFY PLAYER IS ACTUALLY REMOVED")
    try:
        # Check individual player endpoint
        response = requests.get(f"{BASE_URL}/players/{player_id}", headers=HEADERS)
        
        if response.status_code == 404:
            log_test("Player removed (individual check)", True, f"GET /players/{player_id} returns 404 (correct)")
        else:
            log_test("Player removed (individual check)", False, f"Expected 404, got {response.status_code}")
            return False
            
        # Check players list (what user sees in UI)
        response = requests.get(f"{BASE_URL}/players", headers=HEADERS)
        
        if response.status_code == 200:
            all_players = response.json()
            player_still_exists = any(p['id'] == player_id for p in all_players)
            
            if not player_still_exists:
                log_test("Player removed from players list", True, f"'{player_name}' no longer in list of {len(all_players)} players")
                return True
            else:
                log_test("Player removed from players list", False, f"'{player_name}' still found in players list!")
                return False
        else:
            log_test("Get updated players list", False, f"Status: {response.status_code}")
            return False
            
    except Exception as e:
        log_test("Verify player removal", False, f"Exception: {str(e)}")
        return False

def test_multiple_deletions():
    """Test multiple consecutive deletions (common user scenario)"""
    print("\n🔄 TESTING MULTIPLE CONSECUTIVE DELETIONS")
    print("=" * 80)
    
    players_created = []
    
    # Create multiple players
    for i in range(3):
        try:
            payload = {"name": f"TestUser{i+1}", "photo": None}
            response = requests.post(f"{BASE_URL}/players", json=payload, headers=HEADERS)
            
            if response.status_code == 200:
                player_data = response.json()
                players_created.append(player_data)
                log_test(f"Create TestUser{i+1}", True, f"ID: {player_data['id']}")
            else:
                log_test(f"Create TestUser{i+1}", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            log_test(f"Create TestUser{i+1}", False, f"Exception: {str(e)}")
            return False
    
    # Delete all players one by one
    for i, player in enumerate(players_created):
        try:
            response = requests.delete(f"{BASE_URL}/players/{player['id']}", headers=HEADERS)
            
            if response.status_code == 200:
                log_test(f"Delete {player['name']}", True, "Successfully deleted")
                
                # Verify immediate removal
                response = requests.get(f"{BASE_URL}/players/{player['id']}", headers=HEADERS)
                if response.status_code == 404:
                    log_test(f"Verify {player['name']} removed", True, "Player correctly removed")
                else:
                    log_test(f"Verify {player['name']} removed", False, f"Player still exists, status: {response.status_code}")
                    return False
            else:
                log_test(f"Delete {player['name']}", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            log_test(f"Delete {player['name']}", False, f"Exception: {str(e)}")
            return False
    
    return True

def test_edge_cases():
    """Test edge cases that might cause user issues"""
    print("\n🔍 TESTING EDGE CASES")
    print("=" * 80)
    
    # Test 1: Delete with malformed ID (what if frontend sends wrong ID?)
    try:
        response = requests.delete(f"{BASE_URL}/players/invalid-id-format", headers=HEADERS)
        
        if response.status_code == 404:
            log_test("Delete with invalid ID format", True, "Correctly returns 404")
        else:
            log_test("Delete with invalid ID format", False, f"Expected 404, got {response.status_code}")
            return False
    except Exception as e:
        log_test("Delete with invalid ID format", False, f"Exception: {str(e)}")
        return False
    
    # Test 2: Double deletion (what if user clicks delete twice?)
    try:
        # Create a player
        payload = {"name": "DoubleDeleteTest", "photo": None}
        response = requests.post(f"{BASE_URL}/players", json=payload, headers=HEADERS)
        
        if response.status_code == 200:
            player_data = response.json()
            player_id = player_data['id']
            
            # First deletion
            response = requests.delete(f"{BASE_URL}/players/{player_id}", headers=HEADERS)
            if response.status_code == 200:
                log_test("First deletion", True, "Successfully deleted")
                
                # Second deletion (should fail gracefully)
                response = requests.delete(f"{BASE_URL}/players/{player_id}", headers=HEADERS)
                if response.status_code == 404:
                    log_test("Second deletion (double delete)", True, "Correctly returns 404 for already deleted player")
                    return True
                else:
                    log_test("Second deletion (double delete)", False, f"Expected 404, got {response.status_code}")
                    return False
            else:
                log_test("First deletion", False, f"Status: {response.status_code}")
                return False
        else:
            log_test("Create player for double delete test", False, f"Status: {response.status_code}")
            return False
    except Exception as e:
        log_test("Double deletion test", False, f"Exception: {str(e)}")
        return False

def run_focused_delete_tests():
    """Run focused tests on the user's specific issue"""
    print("🎯 FOCUSED PLAYER DELETE TESTING")
    print("User Issue: 'No puedo borrar jugadores' (Cannot delete players)")
    print("Focus: Verify backend DELETE functionality works as expected")
    print("=" * 80)
    print(f"Testing against: {BASE_URL}")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    test_results = []
    
    # Run focused tests
    test_results.append(("User workflow test", test_user_workflow()))
    test_results.append(("Multiple deletions test", test_multiple_deletions()))
    test_results.append(("Edge cases test", test_edge_cases()))
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 FOCUSED DELETE TEST SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL FOCUSED DELETE TESTS PASSED!")
        print("\n✅ BACKEND DELETE API IS FULLY FUNCTIONAL:")
        print("   • CREATE player works correctly")
        print("   • GET /api/players shows created players")
        print("   • DELETE /api/players/{player_id} works correctly")
        print("   • GET /api/players shows players are removed after deletion")
        print("   • Multiple consecutive deletions work")
        print("   • Edge cases handled properly")
        print("\n🔍 CONCLUSION FOR USER ISSUE:")
        print("   ❗ Backend DELETE API is working correctly")
        print("   ❗ User issue 'No puedo borrar jugadores' is NOT a backend problem")
        print("   ❗ Issue is likely in FRONTEND implementation:")
        print("     - Frontend not sending DELETE requests correctly")
        print("     - Frontend not refreshing player list after deletion")
        print("     - Frontend error handling not working")
        print("     - Frontend-backend communication issues")
        return True
    else:
        print("\n⚠️  SOME FOCUSED TESTS FAILED!")
        print("   Backend DELETE API has issues that could cause user problems")
        return False

if __name__ == "__main__":
    success = run_focused_delete_tests()
    exit(0 if success else 1)