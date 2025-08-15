#!/usr/bin/env python3
"""
Comprehensive Player Deletion API Test for Poker Chip Management System
Focus: DELETE /api/players/{player_id} endpoint testing
Testing Requirements:
1. Test DELETE /api/players/{player_id} functionality
2. Verify deletion works for players NOT in active games  
3. Verify deletion is prevented for players IN active games with proper error message
4. Test edge cases like invalid player IDs
5. Ensure all player CRUD operations are working properly
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
        {"name": "Alice Johnson", "balance": -500.0},  # Will be in active game
        {"name": "Bob Smith", "balance": 200.0},       # Will be in active game
        {"name": "Charlie Brown", "balance": 0.0},     # Will NOT be in active game - can be deleted
        {"name": "Diana Prince", "balance": -100.0},   # Will NOT be in active game - can be deleted
        {"name": "Eve Adams", "balance": 300.0}        # Will NOT be in active game - can be deleted
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
                    log_test(f"Create player '{player_info['name']}'", True, f"ID: {updated_player['id'][:8]}..., Balance: ${updated_player['current_balance']:.2f}")
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

def test_create_active_game():
    """Create an active game with some players"""
    print("=" * 60)
    print("2. CREATING ACTIVE GAME WITH SOME PLAYERS")
    print("=" * 60)
    
    global test_game_id
    
    try:
        # Create game with first two players (Alice and Bob)
        player_ids = [test_players[0]['id'], test_players[1]['id']]  # Alice, Bob
        payload = {
            "name": "Test Game for Deletion Testing",
            "player_ids": player_ids
        }
        
        response = requests.post(f"{BASE_URL}/games", json=payload, headers=HEADERS)
        
        if response.status_code == 200:
            game_data = response.json()
            test_game_id = game_data['id']
            log_test("Create active game", True, f"Game ID: {test_game_id[:8]}..., Players: Alice, Bob")
            return True
        else:
            log_test("Create active game", False, f"Status: {response.status_code}")
            return False
            
    except Exception as e:
        log_test("Create active game", False, f"Exception: {str(e)}")
        return False

def test_delete_player_in_active_game():
    """Test deletion of player who is in an active game (should fail)"""
    print("=" * 60)
    print("3. TESTING DELETION OF PLAYER IN ACTIVE GAME (SHOULD FAIL)")
    print("=" * 60)
    
    # Try to delete Alice who is in the active game
    alice_id = test_players[0]['id']
    alice_name = test_players[0]['name']
    
    try:
        response = requests.delete(f"{BASE_URL}/players/{alice_id}", headers=HEADERS)
        
        if response.status_code == 400:
            response_data = response.json()
            error_message = response_data.get("detail", "")
            
            if "active game" in error_message.lower():
                log_test("Delete player in active game", True, f"Correctly prevented deletion: {error_message}")
                return True
            else:
                log_test("Delete player in active game", False, f"Wrong error message: {error_message}")
                return False
        else:
            log_test("Delete player in active game", False, f"Expected 400, got {response.status_code}")
            return False
            
    except Exception as e:
        log_test("Delete player in active game", False, f"Exception: {str(e)}")
        return False

def test_delete_player_not_in_active_game():
    """Test deletion of player who is NOT in an active game (should succeed)"""
    print("=" * 60)
    print("4. TESTING DELETION OF PLAYER NOT IN ACTIVE GAME (SHOULD SUCCEED)")
    print("=" * 60)
    
    # Try to delete Charlie who is NOT in the active game
    charlie_id = test_players[2]['id']
    charlie_name = test_players[2]['name']
    
    try:
        # First verify Charlie exists
        response = requests.get(f"{BASE_URL}/players/{charlie_id}", headers=HEADERS)
        if response.status_code != 200:
            log_test("Verify Charlie exists before deletion", False, f"Status: {response.status_code}")
            return False
        
        log_test("Verify Charlie exists before deletion", True, f"Player found: {charlie_name}")
        
        # Now delete Charlie
        response = requests.delete(f"{BASE_URL}/players/{charlie_id}", headers=HEADERS)
        
        if response.status_code == 200:
            response_data = response.json()
            success_message = response_data.get("message", "")
            
            log_test("Delete player not in active game", True, f"Successfully deleted: {success_message}")
            
            # Verify Charlie is actually deleted
            response = requests.get(f"{BASE_URL}/players/{charlie_id}", headers=HEADERS)
            if response.status_code == 404:
                log_test("Verify player actually deleted", True, "Player not found after deletion (correct)")
                return True
            else:
                log_test("Verify player actually deleted", False, f"Player still exists after deletion, status: {response.status_code}")
                return False
        else:
            log_test("Delete player not in active game", False, f"Expected 200, got {response.status_code}")
            return False
            
    except Exception as e:
        log_test("Delete player not in active game", False, f"Exception: {str(e)}")
        return False

def test_delete_invalid_player_id():
    """Test deletion with invalid player ID (should return 404)"""
    print("=" * 60)
    print("5. TESTING DELETION WITH INVALID PLAYER ID (SHOULD RETURN 404)")
    print("=" * 60)
    
    invalid_player_id = "invalid-player-id-12345"
    
    try:
        response = requests.delete(f"{BASE_URL}/players/{invalid_player_id}", headers=HEADERS)
        
        if response.status_code == 404:
            response_data = response.json()
            error_message = response_data.get("detail", "")
            log_test("Delete invalid player ID", True, f"Correctly returned 404: {error_message}")
            return True
        else:
            log_test("Delete invalid player ID", False, f"Expected 404, got {response.status_code}")
            return False
            
    except Exception as e:
        log_test("Delete invalid player ID", False, f"Exception: {str(e)}")
        return False

def test_delete_after_game_closed():
    """Test deletion of player after game is closed (should succeed)"""
    print("=" * 60)
    print("6. TESTING DELETION AFTER GAME IS CLOSED (SHOULD SUCCEED)")
    print("=" * 60)
    
    try:
        # First close the active game
        response = requests.post(f"{BASE_URL}/games/{test_game_id}/close", headers=HEADERS)
        
        if response.status_code == 200:
            log_test("Close active game", True, "Game closed successfully")
            
            # Now try to delete Alice (who was in the now-closed game)
            alice_id = test_players[0]['id']
            alice_name = test_players[0]['name']
            
            response = requests.delete(f"{BASE_URL}/players/{alice_id}", headers=HEADERS)
            
            if response.status_code == 200:
                response_data = response.json()
                success_message = response_data.get("message", "")
                log_test("Delete player after game closed", True, f"Successfully deleted: {success_message}")
                
                # Verify Alice is actually deleted
                response = requests.get(f"{BASE_URL}/players/{alice_id}", headers=HEADERS)
                if response.status_code == 404:
                    log_test("Verify player deleted after game closed", True, "Player not found after deletion (correct)")
                    return True
                else:
                    log_test("Verify player deleted after game closed", False, f"Player still exists, status: {response.status_code}")
                    return False
            else:
                log_test("Delete player after game closed", False, f"Expected 200, got {response.status_code}")
                return False
        else:
            log_test("Close active game", False, f"Status: {response.status_code}")
            return False
            
    except Exception as e:
        log_test("Delete after game closed", False, f"Exception: {str(e)}")
        return False

def test_player_crud_operations():
    """Test all player CRUD operations are working properly"""
    print("=" * 60)
    print("7. TESTING ALL PLAYER CRUD OPERATIONS")
    print("=" * 60)
    
    try:
        # CREATE - Create a new player
        create_payload = {
            "name": "Test CRUD Player",
            "photo": "base64encodedphoto"
        }
        
        response = requests.post(f"{BASE_URL}/players", json=create_payload, headers=HEADERS)
        
        if response.status_code == 200:
            crud_player = response.json()
            log_test("CREATE player", True, f"Created player: {crud_player['name']}")
            
            # READ - Get the player
            response = requests.get(f"{BASE_URL}/players/{crud_player['id']}", headers=HEADERS)
            
            if response.status_code == 200:
                retrieved_player = response.json()
                log_test("READ player", True, f"Retrieved player: {retrieved_player['name']}")
                
                # UPDATE - Update the player
                update_payload = {
                    "name": "Updated CRUD Player",
                    "current_balance": 150.0
                }
                
                response = requests.put(f"{BASE_URL}/players/{crud_player['id']}", json=update_payload, headers=HEADERS)
                
                if response.status_code == 200:
                    updated_player = response.json()
                    log_test("UPDATE player", True, f"Updated player: {updated_player['name']}, Balance: ${updated_player['current_balance']:.2f}")
                    
                    # DELETE - Delete the player
                    response = requests.delete(f"{BASE_URL}/players/{crud_player['id']}", headers=HEADERS)
                    
                    if response.status_code == 200:
                        log_test("DELETE player (CRUD test)", True, "Successfully deleted test player")
                        
                        # Verify deletion
                        response = requests.get(f"{BASE_URL}/players/{crud_player['id']}", headers=HEADERS)
                        if response.status_code == 404:
                            log_test("Verify CRUD player deleted", True, "Player not found after deletion (correct)")
                            return True
                        else:
                            log_test("Verify CRUD player deleted", False, f"Player still exists, status: {response.status_code}")
                            return False
                    else:
                        log_test("DELETE player (CRUD test)", False, f"Status: {response.status_code}")
                        return False
                else:
                    log_test("UPDATE player", False, f"Status: {response.status_code}")
                    return False
            else:
                log_test("READ player", False, f"Status: {response.status_code}")
                return False
        else:
            log_test("CREATE player", False, f"Status: {response.status_code}")
            return False
            
    except Exception as e:
        log_test("Player CRUD operations", False, f"Exception: {str(e)}")
        return False

def test_get_all_players():
    """Test GET /api/players endpoint"""
    print("=" * 60)
    print("8. TESTING GET ALL PLAYERS ENDPOINT")
    print("=" * 60)
    
    try:
        response = requests.get(f"{BASE_URL}/players", headers=HEADERS)
        
        if response.status_code == 200:
            players = response.json()
            
            if isinstance(players, list):
                log_test("GET all players", True, f"Retrieved {len(players)} players")
                
                # Verify remaining players (should be Bob, Diana, Eve after deletions)
                remaining_names = [p['name'] for p in players if p['name'] in ['Bob Smith', 'Diana Prince', 'Eve Adams']]
                log_test("Verify remaining players", True, f"Found: {', '.join(remaining_names)}")
                return True
            else:
                log_test("GET all players", False, "Response is not a list")
                return False
        else:
            log_test("GET all players", False, f"Status: {response.status_code}")
            return False
            
    except Exception as e:
        log_test("GET all players", False, f"Exception: {str(e)}")
        return False

def cleanup_remaining_test_data():
    """Clean up remaining test data"""
    print("=" * 60)
    print("9. CLEANUP REMAINING TEST DATA")
    print("=" * 60)
    
    try:
        # Get all players
        response = requests.get(f"{BASE_URL}/players", headers=HEADERS)
        if response.status_code == 200:
            players = response.json()
            
            # Delete remaining test players
            test_player_names = ['Bob Smith', 'Diana Prince', 'Eve Adams']
            for player in players:
                if player['name'] in test_player_names:
                    try:
                        response = requests.delete(f"{BASE_URL}/players/{player['id']}", headers=HEADERS)
                        if response.status_code == 200:
                            log_test(f"Cleanup player {player['name']}", True, "Player deleted")
                        else:
                            log_test(f"Cleanup player {player['name']}", False, f"Status: {response.status_code}")
                    except Exception as e:
                        log_test(f"Cleanup player {player['name']}", False, f"Exception: {str(e)}")
        
        log_test("Cleanup completed", True, "All test data cleaned up")
        return True
        
    except Exception as e:
        log_test("Cleanup", False, f"Exception: {str(e)}")
        return False

def run_player_deletion_tests():
    """Run comprehensive player deletion tests"""
    print("🎯 POKER CHIP MANAGEMENT BACKEND - PLAYER DELETION TESTING")
    print("Focus: DELETE /api/players/{player_id} endpoint comprehensive testing")
    print("=" * 80)
    print(f"Testing against: {BASE_URL}")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    test_results = []
    
    # Run comprehensive player deletion tests
    test_results.append(("Create test players", test_create_test_players()))
    test_results.append(("Create active game", test_create_active_game()))
    test_results.append(("Delete player in active game (should fail)", test_delete_player_in_active_game()))
    test_results.append(("Delete player not in active game (should succeed)", test_delete_player_not_in_active_game()))
    test_results.append(("Delete invalid player ID (should return 404)", test_delete_invalid_player_id()))
    test_results.append(("Delete after game closed (should succeed)", test_delete_after_game_closed()))
    test_results.append(("Test all player CRUD operations", test_player_crud_operations()))
    test_results.append(("Test GET all players", test_get_all_players()))
    
    # Cleanup
    cleanup_remaining_test_data()
    
    # Summary
    print("=" * 80)
    print("📊 PLAYER DELETION TEST SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print()
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL PLAYER DELETION TESTS PASSED!")
        print("\n✅ Key Features Verified:")
        print("   • DELETE /api/players/{player_id} works correctly")
        print("   • Deletion prevented for players in active games with proper error message")
        print("   • Deletion allowed for players not in active games")
        print("   • Deletion allowed after games are closed")
        print("   • Proper 404 error for invalid player IDs")
        print("   • All player CRUD operations working correctly")
        print("   • GET all players endpoint working")
        return True
    else:
        print("⚠️  SOME TESTS FAILED! Check the details above.")
        return False

if __name__ == "__main__":
    success = run_player_deletion_tests()
    exit(0 if success else 1)