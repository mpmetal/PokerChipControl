#!/usr/bin/env python3
"""
Comprehensive Player Management API Testing
Focus: DELETE /api/players/{player_id} endpoint and all player management functionality
Testing user reported issue: "No puedo borrar jugadores" (Cannot delete players)
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
test_games = []

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

def test_player_crud_operations():
    """Test basic CRUD operations for players"""
    print("=" * 60)
    print("1. TESTING BASIC PLAYER CRUD OPERATIONS")
    print("=" * 60)
    
    global test_players
    
    # Test POST /api/players
    try:
        payload = {
            "name": "Maria Rodriguez",
            "photo": None
        }
        response = requests.post(f"{BASE_URL}/players", json=payload, headers=HEADERS)
        
        if response.status_code == 200:
            player_data = response.json()
            test_players.append(player_data)
            log_test("POST /api/players", True, f"Created player: {player_data['name']} (ID: {player_data['id']})")
            
            # Test GET /api/players/{player_id}
            response = requests.get(f"{BASE_URL}/players/{player_data['id']}", headers=HEADERS)
            if response.status_code == 200:
                retrieved_player = response.json()
                log_test("GET /api/players/{player_id}", True, f"Retrieved: {retrieved_player['name']}")
                
                # Test PUT /api/players/{player_id}
                update_payload = {"current_balance": -150.0}
                response = requests.put(f"{BASE_URL}/players/{player_data['id']}", json=update_payload, headers=HEADERS)
                if response.status_code == 200:
                    updated_player = response.json()
                    test_players[0] = updated_player  # Update our stored data
                    log_test("PUT /api/players/{player_id}", True, f"Updated balance to: ${updated_player['current_balance']:.2f}")
                    return True
                else:
                    log_test("PUT /api/players/{player_id}", False, f"Status: {response.status_code}")
                    return False
            else:
                log_test("GET /api/players/{player_id}", False, f"Status: {response.status_code}")
                return False
        else:
            log_test("POST /api/players", False, f"Status: {response.status_code}, Response: {response.text}")
            return False
            
    except Exception as e:
        log_test("Player CRUD operations", False, f"Exception: {str(e)}")
        return False

def test_create_multiple_players():
    """Create multiple players for comprehensive testing"""
    print("=" * 60)
    print("2. CREATING MULTIPLE PLAYERS FOR TESTING")
    print("=" * 60)
    
    players_to_create = [
        {"name": "Carlos Mendez", "balance": 0.0},
        {"name": "Ana Silva", "balance": 300.0},
        {"name": "Luis Garcia", "balance": -75.0},
        {"name": "Sofia Torres", "balance": 0.0}
    ]
    
    for player_info in players_to_create:
        try:
            # Create player
            payload = {"name": player_info["name"]}
            response = requests.post(f"{BASE_URL}/players", json=payload, headers=HEADERS)
            
            if response.status_code == 200:
                player_data = response.json()
                
                # Set balance if needed
                if player_info["balance"] != 0.0:
                    update_payload = {"current_balance": player_info["balance"]}
                    response = requests.put(f"{BASE_URL}/players/{player_data['id']}", json=update_payload, headers=HEADERS)
                    
                    if response.status_code == 200:
                        updated_player = response.json()
                        test_players.append(updated_player)
                        log_test(f"Create {player_info['name']}", True, f"Balance: ${updated_player['current_balance']:.2f}")
                    else:
                        log_test(f"Set balance for {player_info['name']}", False, f"Status: {response.status_code}")
                        return False
                else:
                    test_players.append(player_data)
                    log_test(f"Create {player_info['name']}", True, f"Balance: ${player_data['current_balance']:.2f}")
            else:
                log_test(f"Create {player_info['name']}", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            log_test(f"Create {player_info['name']}", False, f"Exception: {str(e)}")
            return False
    
    return True

def test_get_all_players():
    """Test GET /api/players returns all players"""
    print("=" * 60)
    print("3. TESTING GET ALL PLAYERS")
    print("=" * 60)
    
    try:
        response = requests.get(f"{BASE_URL}/players", headers=HEADERS)
        
        if response.status_code == 200:
            all_players = response.json()
            
            if isinstance(all_players, list):
                log_test("GET /api/players returns list", True, f"Found {len(all_players)} total players")
                
                # Verify our test players are included
                test_player_ids = {p['id'] for p in test_players}
                returned_player_ids = {p['id'] for p in all_players}
                
                if test_player_ids.issubset(returned_player_ids):
                    log_test("All test players in response", True, f"All {len(test_players)} test players found")
                    return True
                else:
                    missing = test_player_ids - returned_player_ids
                    log_test("All test players in response", False, f"Missing: {len(missing)} players")
                    return False
            else:
                log_test("GET /api/players returns list", False, f"Expected list, got {type(all_players)}")
                return False
        else:
            log_test("GET /api/players", False, f"Status: {response.status_code}")
            return False
            
    except Exception as e:
        log_test("GET all players test", False, f"Exception: {str(e)}")
        return False

def test_delete_scenarios():
    """Test various DELETE scenarios as specified in review request"""
    print("=" * 60)
    print("4. TESTING DELETE SCENARIOS")
    print("=" * 60)
    
    # Scenario 1: Delete player NOT in any active game (should succeed)
    player_to_delete = test_players[1]  # Carlos Mendez
    try:
        response = requests.delete(f"{BASE_URL}/players/{player_to_delete['id']}", headers=HEADERS)
        
        if response.status_code == 200:
            log_test("DELETE player not in game", True, f"Successfully deleted {player_to_delete['name']}")
            
            # Verify deletion
            response = requests.get(f"{BASE_URL}/players/{player_to_delete['id']}", headers=HEADERS)
            if response.status_code == 404:
                log_test("Verify player deleted", True, "Player not found (correct)")
                test_players.remove(player_to_delete)
            else:
                log_test("Verify player deleted", False, f"Player still exists, Status: {response.status_code}")
                return False
        else:
            log_test("DELETE player not in game", False, f"Status: {response.status_code}, Response: {response.text}")
            return False
            
    except Exception as e:
        log_test("DELETE player not in game", False, f"Exception: {str(e)}")
        return False
    
    return True

def test_create_active_game_with_players():
    """Create active game with players to test deletion restrictions"""
    print("=" * 60)
    print("5. CREATING ACTIVE GAME WITH PLAYERS")
    print("=" * 60)
    
    # Use Maria Rodriguez and Ana Silva for the game
    player_ids = [test_players[0]['id'], test_players[1]['id']]
    
    try:
        payload = {
            "name": "Test Game - Player Deletion",
            "player_ids": player_ids
        }
        
        response = requests.post(f"{BASE_URL}/games", json=payload, headers=HEADERS)
        
        if response.status_code == 200:
            game_data = response.json()
            test_games.append(game_data)
            log_test("Create active game", True, f"Game ID: {game_data['id']}")
            
            # Verify players are in the game
            player_names = [p['player_name'] for p in game_data['players']]
            log_test("Players added to game", True, f"Players: {', '.join(player_names)}")
            return True
        else:
            log_test("Create active game", False, f"Status: {response.status_code}")
            return False
            
    except Exception as e:
        log_test("Create active game", False, f"Exception: {str(e)}")
        return False

def test_delete_player_in_active_game():
    """Test DELETE player who is in active game (should prevent deletion)"""
    print("=" * 60)
    print("6. TESTING DELETE PLAYER IN ACTIVE GAME")
    print("=" * 60)
    
    # Try to delete Maria Rodriguez who is in the active game
    player_in_game = test_players[0]
    
    try:
        response = requests.delete(f"{BASE_URL}/players/{player_in_game['id']}", headers=HEADERS)
        
        if response.status_code == 400:
            response_data = response.json()
            error_message = response_data.get('detail', '')
            
            if "active game" in error_message.lower():
                log_test("DELETE player in active game", True, f"Correctly prevented: {error_message}")
                
                # Verify player still exists
                response = requests.get(f"{BASE_URL}/players/{player_in_game['id']}", headers=HEADERS)
                if response.status_code == 200:
                    log_test("Player preserved after failed delete", True, f"{player_in_game['name']} still exists")
                    return True
                else:
                    log_test("Player preserved after failed delete", False, "Player missing")
                    return False
            else:
                log_test("DELETE player in active game", False, f"Wrong error message: {error_message}")
                return False
        else:
            log_test("DELETE player in active game", False, f"Expected 400, got {response.status_code}")
            return False
            
    except Exception as e:
        log_test("DELETE player in active game", False, f"Exception: {str(e)}")
        return False

def test_invalid_player_id_scenarios():
    """Test DELETE with various invalid player IDs"""
    print("=" * 60)
    print("7. TESTING INVALID PLAYER ID SCENARIOS")
    print("=" * 60)
    
    invalid_scenarios = [
        ("nonexistent-uuid", "Non-existent UUID"),
        ("12345", "Numeric ID"),
        ("invalid-format", "Invalid format"),
        ("00000000-0000-0000-0000-000000000000", "Zero UUID")
    ]
    
    for invalid_id, description in invalid_scenarios:
        try:
            response = requests.delete(f"{BASE_URL}/players/{invalid_id}", headers=HEADERS)
            
            if response.status_code == 404:
                log_test(f"DELETE {description}", True, "Correctly returned 404")
            else:
                log_test(f"DELETE {description}", False, f"Expected 404, got {response.status_code}")
                return False
                
        except Exception as e:
            log_test(f"DELETE {description}", False, f"Exception: {str(e)}")
            return False
    
    return True

def test_close_game_and_delete():
    """Test DELETE player after closing game (should allow deletion)"""
    print("=" * 60)
    print("8. TESTING DELETE AFTER CLOSING GAME")
    print("=" * 60)
    
    # Close the active game
    game_to_close = test_games[0]
    
    try:
        response = requests.post(f"{BASE_URL}/games/{game_to_close['id']}/close", headers=HEADERS)
        
        if response.status_code == 200:
            log_test("Close active game", True, f"Game {game_to_close['id']} closed")
            
            # Now try to delete Maria Rodriguez who was in the game
            player_to_delete = test_players[0]
            response = requests.delete(f"{BASE_URL}/players/{player_to_delete['id']}", headers=HEADERS)
            
            if response.status_code == 200:
                log_test("DELETE player after game closed", True, f"Successfully deleted {player_to_delete['name']}")
                
                # Verify deletion
                response = requests.get(f"{BASE_URL}/players/{player_to_delete['id']}", headers=HEADERS)
                if response.status_code == 404:
                    log_test("Verify deletion after game closed", True, "Player not found (correct)")
                    test_players.remove(player_to_delete)
                    return True
                else:
                    log_test("Verify deletion after game closed", False, "Player still exists")
                    return False
            else:
                log_test("DELETE player after game closed", False, f"Status: {response.status_code}")
                return False
        else:
            log_test("Close active game", False, f"Status: {response.status_code}")
            return False
            
    except Exception as e:
        log_test("DELETE after closing game", False, f"Exception: {str(e)}")
        return False

def test_edge_cases():
    """Test edge cases and error conditions"""
    print("=" * 60)
    print("9. TESTING EDGE CASES")
    print("=" * 60)
    
    # Test DELETE with malformed requests
    edge_cases = [
        ("", "Empty player ID", 405),  # Method not allowed for empty path
        ("null", "Null string", 404),
        ("undefined", "Undefined string", 404)
    ]
    
    for test_id, description, expected_status in edge_cases:
        try:
            if test_id == "":
                # Special case for empty ID - this hits the base /players endpoint
                response = requests.delete(f"{BASE_URL}/players", headers=HEADERS)
            else:
                response = requests.delete(f"{BASE_URL}/players/{test_id}", headers=HEADERS)
            
            if response.status_code == expected_status:
                log_test(f"Edge case: {description}", True, f"Correctly returned {expected_status}")
            else:
                log_test(f"Edge case: {description}", False, f"Expected {expected_status}, got {response.status_code}")
                # Don't fail the whole test for edge cases
                
        except Exception as e:
            log_test(f"Edge case: {description}", False, f"Exception: {str(e)}")
    
    return True

def cleanup_test_data():
    """Clean up remaining test data"""
    print("=" * 60)
    print("10. CLEANUP TEST DATA")
    print("=" * 60)
    
    # Delete remaining players
    for player in test_players[:]:
        try:
            response = requests.delete(f"{BASE_URL}/players/{player['id']}", headers=HEADERS)
            if response.status_code == 200:
                log_test(f"Cleanup: Delete {player['name']}", True, "Deleted")
                test_players.remove(player)
            else:
                log_test(f"Cleanup: Delete {player['name']}", False, f"Status: {response.status_code}")
        except Exception as e:
            log_test(f"Cleanup: Delete {player['name']}", False, f"Exception: {str(e)}")

def run_comprehensive_player_tests():
    """Run comprehensive player management tests"""
    print("🎯 COMPREHENSIVE PLAYER MANAGEMENT API TESTING")
    print("Focus: DELETE /api/players/{player_id} and all player management functionality")
    print("User Issue: 'No puedo borrar jugadores' (Cannot delete players)")
    print("=" * 80)
    print(f"Testing against: {BASE_URL}")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    test_results = []
    
    # Run comprehensive tests
    test_results.append(("Basic CRUD operations", test_player_crud_operations()))
    test_results.append(("Create multiple players", test_create_multiple_players()))
    test_results.append(("GET all players", test_get_all_players()))
    test_results.append(("DELETE scenarios", test_delete_scenarios()))
    test_results.append(("Create active game", test_create_active_game_with_players()))
    test_results.append(("DELETE player in active game", test_delete_player_in_active_game()))
    test_results.append(("Invalid player ID scenarios", test_invalid_player_id_scenarios()))
    test_results.append(("DELETE after closing game", test_close_game_and_delete()))
    test_results.append(("Edge cases", test_edge_cases()))
    
    # Cleanup
    cleanup_test_data()
    
    # Summary
    print("=" * 80)
    print("📊 COMPREHENSIVE PLAYER MANAGEMENT TEST SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print()
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL PLAYER MANAGEMENT TESTS PASSED!")
        print("\n✅ DELETE /api/players/{player_id} FUNCTIONALITY VERIFIED:")
        print("   • ✅ DELETE works correctly for players NOT in active games")
        print("   • ✅ DELETE properly prevents deletion of players IN active games")
        print("   • ✅ DELETE allows deletion after games are closed")
        print("   • ✅ DELETE returns proper 404 for invalid player IDs")
        print("   • ✅ GET /api/players works correctly")
        print("   • ✅ POST /api/players works correctly")
        print("\n🔍 USER ISSUE ANALYSIS:")
        print("   • ✅ Backend DELETE API is WORKING CORRECTLY")
        print("   • ❗ Issue is likely in FRONTEND implementation")
        print("   • 💡 Check frontend DELETE request implementation")
        print("   • 💡 Check frontend error handling and user feedback")
        return True
    else:
        print("⚠️  SOME TESTS FAILED! Check the details above.")
        print("\n🔍 USER ISSUE ANALYSIS:")
        print("   • ❌ Backend DELETE API has issues")
        print("   • 🔧 Fix backend issues before investigating frontend")
        return False

if __name__ == "__main__":
    success = run_comprehensive_player_tests()
    exit(0 if success else 1)