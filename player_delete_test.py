#!/usr/bin/env python3
"""
Player Delete API Testing - Focus on DELETE /api/players/{player_id} endpoint
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

def test_create_test_players():
    """Create test players for deletion testing"""
    print("=" * 60)
    print("1. CREATING TEST PLAYERS FOR DELETION TESTING")
    print("=" * 60)
    
    players_to_create = [
        {"name": "TestPlayer1", "balance": 0.0},
        {"name": "TestPlayer2", "balance": -100.0},
        {"name": "TestPlayer3", "balance": 200.0},
        {"name": "TestPlayer4", "balance": 0.0},
        {"name": "TestPlayer5", "balance": -50.0}
    ]
    
    global test_players
    
    for player_info in players_to_create:
        try:
            # Create player
            payload = {"name": player_info["name"]}
            response = requests.post(f"{BASE_URL}/players", json=payload, headers=HEADERS)
            
            if response.status_code == 200:
                player_data = response.json()
                
                # Set initial balance if needed
                if player_info["balance"] != 0.0:
                    update_payload = {"current_balance": player_info["balance"]}
                    response = requests.put(f"{BASE_URL}/players/{player_data['id']}", json=update_payload, headers=HEADERS)
                    
                    if response.status_code == 200:
                        updated_player = response.json()
                        test_players.append(updated_player)
                        log_test(f"Create player '{player_info['name']}'", True, f"ID: {updated_player['id']}, Balance: ${updated_player['current_balance']:.2f}")
                    else:
                        log_test(f"Set balance for '{player_info['name']}'", False, f"Status: {response.status_code}")
                        return False
                else:
                    test_players.append(player_data)
                    log_test(f"Create player '{player_info['name']}'", True, f"ID: {player_data['id']}, Balance: ${player_data['current_balance']:.2f}")
            else:
                log_test(f"Create player '{player_info['name']}'", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            log_test(f"Create player '{player_info['name']}'", False, f"Exception: {str(e)}")
            return False
    
    return True

def test_get_players_endpoint():
    """Test GET /api/players endpoint works correctly"""
    print("=" * 60)
    print("2. TESTING GET /api/players ENDPOINT")
    print("=" * 60)
    
    try:
        response = requests.get(f"{BASE_URL}/players", headers=HEADERS)
        
        if response.status_code == 200:
            players = response.json()
            
            if isinstance(players, list):
                log_test("GET /api/players returns list", True, f"Found {len(players)} players")
                
                # Verify our test players are in the list
                test_player_ids = {p['id'] for p in test_players}
                returned_player_ids = {p['id'] for p in players}
                
                if test_player_ids.issubset(returned_player_ids):
                    log_test("All test players found in GET response", True, f"All {len(test_players)} test players present")
                    return True
                else:
                    missing = test_player_ids - returned_player_ids
                    log_test("All test players found in GET response", False, f"Missing players: {missing}")
                    return False
            else:
                log_test("GET /api/players returns list", False, f"Expected list, got {type(players)}")
                return False
        else:
            log_test("GET /api/players", False, f"Status: {response.status_code}, Response: {response.text}")
            return False
            
    except Exception as e:
        log_test("GET /api/players test", False, f"Exception: {str(e)}")
        return False

def test_delete_player_not_in_game():
    """Test DELETE player who is NOT in any active game (should succeed)"""
    print("=" * 60)
    print("3. TESTING DELETE PLAYER NOT IN ACTIVE GAME")
    print("=" * 60)
    
    # Use TestPlayer1 who won't be added to any game
    player_to_delete = test_players[0]
    player_id = player_to_delete['id']
    player_name = player_to_delete['name']
    
    try:
        # First verify player exists
        response = requests.get(f"{BASE_URL}/players/{player_id}", headers=HEADERS)
        if response.status_code != 200:
            log_test(f"Verify {player_name} exists before deletion", False, f"Status: {response.status_code}")
            return False
        
        log_test(f"Verify {player_name} exists before deletion", True, f"Player found: {player_name}")
        
        # Attempt to delete the player
        response = requests.delete(f"{BASE_URL}/players/{player_id}", headers=HEADERS)
        
        if response.status_code == 200:
            response_data = response.json()
            log_test(f"DELETE {player_name} (not in game)", True, f"Response: {response_data.get('message', 'Success')}")
            
            # Verify player is actually deleted
            response = requests.get(f"{BASE_URL}/players/{player_id}", headers=HEADERS)
            if response.status_code == 404:
                log_test(f"Verify {player_name} deleted", True, "Player not found after deletion (correct)")
                
                # Remove from test_players list
                test_players.remove(player_to_delete)
                return True
            else:
                log_test(f"Verify {player_name} deleted", False, f"Player still exists after deletion, Status: {response.status_code}")
                return False
        else:
            log_test(f"DELETE {player_name} (not in game)", False, f"Status: {response.status_code}, Response: {response.text}")
            return False
            
    except Exception as e:
        log_test(f"Delete player not in game test", False, f"Exception: {str(e)}")
        return False

def test_create_active_game():
    """Create an active game with some players"""
    print("=" * 60)
    print("4. CREATING ACTIVE GAME FOR DELETION TESTING")
    print("=" * 60)
    
    global test_game_id
    
    # Use TestPlayer2 and TestPlayer3 for the game
    player_ids = [test_players[0]['id'], test_players[1]['id']]  # Adjusted indices after deletion
    
    try:
        payload = {
            "name": "Test Game for Player Deletion",
            "player_ids": player_ids
        }
        
        response = requests.post(f"{BASE_URL}/games", json=payload, headers=HEADERS)
        
        if response.status_code == 200:
            game_data = response.json()
            test_game_id = game_data['id']
            log_test("Create active game", True, f"Game ID: {test_game_id}")
            
            # Verify game has the correct players
            if len(game_data['players']) == 2:
                player_names = [p['player_name'] for p in game_data['players']]
                log_test("Game has correct players", True, f"Players: {', '.join(player_names)}")
                return True
            else:
                log_test("Game has correct players", False, f"Expected 2 players, got {len(game_data['players'])}")
                return False
        else:
            log_test("Create active game", False, f"Status: {response.status_code}, Response: {response.text}")
            return False
            
    except Exception as e:
        log_test("Create active game test", False, f"Exception: {str(e)}")
        return False

def test_delete_player_in_active_game():
    """Test DELETE player who IS in an active game (should fail)"""
    print("=" * 60)
    print("5. TESTING DELETE PLAYER IN ACTIVE GAME (SHOULD FAIL)")
    print("=" * 60)
    
    # Try to delete TestPlayer2 who is in the active game
    player_to_delete = test_players[0]  # Adjusted index after previous deletion
    player_id = player_to_delete['id']
    player_name = player_to_delete['name']
    
    try:
        # Verify player exists and is in active game
        response = requests.get(f"{BASE_URL}/games/{test_game_id}", headers=HEADERS)
        if response.status_code == 200:
            game_data = response.json()
            player_in_game = any(p['player_id'] == player_id for p in game_data['players'])
            
            if player_in_game:
                log_test(f"Verify {player_name} is in active game", True, "Player found in active game")
            else:
                log_test(f"Verify {player_name} is in active game", False, "Player not found in active game")
                return False
        else:
            log_test("Get game data", False, f"Status: {response.status_code}")
            return False
        
        # Attempt to delete the player (should fail)
        response = requests.delete(f"{BASE_URL}/players/{player_id}", headers=HEADERS)
        
        if response.status_code == 400:
            response_data = response.json()
            error_message = response_data.get('detail', '')
            
            if "active game" in error_message.lower():
                log_test(f"DELETE {player_name} (in active game)", True, f"Correctly rejected: {error_message}")
                
                # Verify player still exists
                response = requests.get(f"{BASE_URL}/players/{player_id}", headers=HEADERS)
                if response.status_code == 200:
                    log_test(f"Verify {player_name} still exists", True, "Player correctly preserved")
                    return True
                else:
                    log_test(f"Verify {player_name} still exists", False, f"Player missing after failed deletion, Status: {response.status_code}")
                    return False
            else:
                log_test(f"DELETE {player_name} (in active game)", False, f"Wrong error message: {error_message}")
                return False
        else:
            log_test(f"DELETE {player_name} (in active game)", False, f"Expected 400, got {response.status_code}, Response: {response.text}")
            return False
            
    except Exception as e:
        log_test(f"Delete player in active game test", False, f"Exception: {str(e)}")
        return False

def test_delete_invalid_player_id():
    """Test DELETE with invalid player ID (should fail with 404)"""
    print("=" * 60)
    print("6. TESTING DELETE WITH INVALID PLAYER ID")
    print("=" * 60)
    
    invalid_ids = [
        "nonexistent-id",
        "12345",
        "",
        "invalid-uuid-format"
    ]
    
    for invalid_id in invalid_ids:
        try:
            response = requests.delete(f"{BASE_URL}/players/{invalid_id}", headers=HEADERS)
            
            if response.status_code == 404:
                log_test(f"DELETE invalid ID '{invalid_id}'", True, "Correctly returned 404")
            else:
                log_test(f"DELETE invalid ID '{invalid_id}'", False, f"Expected 404, got {response.status_code}")
                return False
                
        except Exception as e:
            log_test(f"DELETE invalid ID '{invalid_id}'", False, f"Exception: {str(e)}")
            return False
    
    return True

def test_close_game_and_delete_player():
    """Test DELETE player after closing the game (should succeed)"""
    print("=" * 60)
    print("7. TESTING DELETE PLAYER AFTER CLOSING GAME")
    print("=" * 60)
    
    # Close the active game first
    try:
        response = requests.post(f"{BASE_URL}/games/{test_game_id}/close", headers=HEADERS)
        
        if response.status_code == 200:
            log_test("Close active game", True, f"Game {test_game_id} closed")
        else:
            log_test("Close active game", False, f"Status: {response.status_code}")
            return False
            
    except Exception as e:
        log_test("Close active game", False, f"Exception: {str(e)}")
        return False
    
    # Now try to delete the player who was in the game
    player_to_delete = test_players[0]  # TestPlayer2
    player_id = player_to_delete['id']
    player_name = player_to_delete['name']
    
    try:
        response = requests.delete(f"{BASE_URL}/players/{player_id}", headers=HEADERS)
        
        if response.status_code == 200:
            response_data = response.json()
            log_test(f"DELETE {player_name} (after game closed)", True, f"Response: {response_data.get('message', 'Success')}")
            
            # Verify player is actually deleted
            response = requests.get(f"{BASE_URL}/players/{player_id}", headers=HEADERS)
            if response.status_code == 404:
                log_test(f"Verify {player_name} deleted", True, "Player not found after deletion (correct)")
                
                # Remove from test_players list
                test_players.remove(player_to_delete)
                return True
            else:
                log_test(f"Verify {player_name} deleted", False, f"Player still exists after deletion, Status: {response.status_code}")
                return False
        else:
            log_test(f"DELETE {player_name} (after game closed)", False, f"Status: {response.status_code}, Response: {response.text}")
            return False
            
    except Exception as e:
        log_test(f"Delete player after game closed test", False, f"Exception: {str(e)}")
        return False

def test_post_players_still_works():
    """Test POST /api/players still works correctly after deletions"""
    print("=" * 60)
    print("8. TESTING POST /api/players STILL WORKS")
    print("=" * 60)
    
    try:
        payload = {"name": "NewTestPlayer", "photo": None}
        response = requests.post(f"{BASE_URL}/players", json=payload, headers=HEADERS)
        
        if response.status_code == 200:
            player_data = response.json()
            
            # Verify player has correct structure
            required_fields = ['id', 'name', 'current_balance', 'total_played', 'created_date']
            missing_fields = [field for field in required_fields if field not in player_data]
            
            if not missing_fields:
                log_test("POST /api/players creates player", True, f"Created: {player_data['name']} (ID: {player_data['id']})")
                
                # Clean up - delete this test player
                requests.delete(f"{BASE_URL}/players/{player_data['id']}", headers=HEADERS)
                return True
            else:
                log_test("POST /api/players creates player", False, f"Missing fields: {missing_fields}")
                return False
        else:
            log_test("POST /api/players", False, f"Status: {response.status_code}, Response: {response.text}")
            return False
            
    except Exception as e:
        log_test("POST /api/players test", False, f"Exception: {str(e)}")
        return False

def cleanup_remaining_players():
    """Clean up remaining test players"""
    print("=" * 60)
    print("9. CLEANUP REMAINING TEST PLAYERS")
    print("=" * 60)
    
    for player in test_players[:]:  # Use slice to avoid modifying list during iteration
        try:
            response = requests.delete(f"{BASE_URL}/players/{player['id']}", headers=HEADERS)
            if response.status_code == 200:
                log_test(f"Delete player {player['name']}", True, "Player deleted")
                test_players.remove(player)
            else:
                log_test(f"Delete player {player['name']}", False, f"Status: {response.status_code}")
        except Exception as e:
            log_test(f"Delete player {player['name']}", False, f"Exception: {str(e)}")

def run_player_delete_tests():
    """Run comprehensive player deletion tests"""
    print("🎯 PLAYER DELETE API TESTING")
    print("Focus: DELETE /api/players/{player_id} endpoint functionality")
    print("User Issue: 'No puedo borrar jugadores' (Cannot delete players)")
    print("=" * 80)
    print(f"Testing against: {BASE_URL}")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    test_results = []
    
    # Run comprehensive delete tests
    test_results.append(("Create test players", test_create_test_players()))
    test_results.append(("GET /api/players works", test_get_players_endpoint()))
    test_results.append(("DELETE player not in game", test_delete_player_not_in_game()))
    test_results.append(("Create active game", test_create_active_game()))
    test_results.append(("DELETE player in active game (should fail)", test_delete_player_in_active_game()))
    test_results.append(("DELETE invalid player ID", test_delete_invalid_player_id()))
    test_results.append(("DELETE player after closing game", test_close_game_and_delete_player()))
    test_results.append(("POST /api/players still works", test_post_players_still_works()))
    
    # Cleanup
    cleanup_remaining_players()
    
    # Summary
    print("=" * 80)
    print("📊 PLAYER DELETE API TEST SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print()
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL PLAYER DELETE TESTS PASSED!")
        print("\n✅ Key Features Verified:")
        print("   • DELETE /api/players/{player_id} works correctly")
        print("   • Players NOT in active games can be deleted")
        print("   • Players IN active games cannot be deleted (proper validation)")
        print("   • Players can be deleted after games are closed")
        print("   • Invalid player IDs return proper 404 errors")
        print("   • GET and POST /api/players still work after deletions")
        print("\n🔍 User Issue Analysis:")
        print("   • Backend DELETE API is working correctly")
        print("   • Issue likely in frontend implementation, not backend")
        return True
    else:
        print("⚠️  SOME TESTS FAILED! Check the details above.")
        print("\n🔍 User Issue Analysis:")
        print("   • Backend DELETE API has issues - see failed tests above")
        return False

if __name__ == "__main__":
    success = run_player_delete_tests()
    exit(0 if success else 1)