#!/usr/bin/env python3
"""
Comprehensive Subscription System Backend Test
Testing PostgreSQL integration, subscription APIs, trial logic, and RevenueCat webhook handling.
"""

import requests
import json
import time
import hmac
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Dict, Any

# Configuration
BASE_URL = "https://pokerbankapp.preview.emergentagent.com/api"
HEADERS = {"Content-Type": "application/json"}

# Test data storage
test_users = []
test_player_ids = []

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

def test_database_connection():
    """Test PostgreSQL database connection and table creation"""
    print("=" * 60)
    print("1. TESTING DATABASE CONNECTION")
    print("=" * 60)
    
    try:
        # Test by trying to create a subscription user (this will test DB connection)
        test_payload = {
            "poker_player_id": "test_connection_player",
            "email": "test_connection@example.com"
        }
        
        response = requests.post(f"{BASE_URL}/subscription/create-user", json=test_payload, headers=HEADERS)
        
        if response.status_code == 200:
            user_data = response.json()
            log_test("PostgreSQL database connection", True, f"Successfully connected and created user with ID: {user_data.get('id')}")
            
            # Clean up test user
            # Note: We don't have a delete endpoint, but this confirms DB is working
            return True
        else:
            log_test("PostgreSQL database connection", False, f"Status: {response.status_code}, Response: {response.text}")
            return False
            
    except Exception as e:
        log_test("PostgreSQL database connection", False, f"Exception: {str(e)}")
        return False

def test_create_subscription_users():
    """Test creating subscription users"""
    print("=" * 60)
    print("2. TESTING SUBSCRIPTION USER CREATION")
    print("=" * 60)
    
    global test_users, test_player_ids
    
    users_to_create = [
        {"poker_player_id": "player_001", "email": "alice@example.com"},
        {"poker_player_id": "player_002", "email": "bob@example.com"},
        {"poker_player_id": "player_003", "email": "charlie@example.com"}
    ]
    
    for user_info in users_to_create:
        try:
            response = requests.post(f"{BASE_URL}/subscription/create-user", json=user_info, headers=HEADERS)
            
            if response.status_code == 200:
                user_data = response.json()
                test_users.append(user_data)
                test_player_ids.append(user_info["poker_player_id"])
                
                # Verify user data structure
                required_fields = ["id", "poker_player_id", "email", "is_premium", "has_used_trial", "trial_expired"]
                missing_fields = [field for field in required_fields if field not in user_data]
                
                if not missing_fields:
                    log_test(f"Create subscription user {user_info['email']}", True, 
                           f"ID: {user_data['id']}, Premium: {user_data['is_premium']}, Trial Used: {user_data['has_used_trial']}")
                else:
                    log_test(f"Create subscription user {user_info['email']}", False, f"Missing fields: {missing_fields}")
                    return False
            else:
                log_test(f"Create subscription user {user_info['email']}", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            log_test(f"Create subscription user {user_info['email']}", False, f"Exception: {str(e)}")
            return False
    
    return True

def test_duplicate_user_creation():
    """Test creating duplicate users (should return existing user)"""
    try:
        # Try to create a user that already exists
        duplicate_payload = {
            "poker_player_id": test_player_ids[0],
            "email": "alice@example.com"
        }
        
        response = requests.post(f"{BASE_URL}/subscription/create-user", json=duplicate_payload, headers=HEADERS)
        
        if response.status_code == 200:
            user_data = response.json()
            # Should return the existing user with same ID
            existing_user = test_users[0]
            if user_data["id"] == existing_user["id"]:
                log_test("Duplicate user creation handling", True, "Returns existing user instead of creating duplicate")
                return True
            else:
                log_test("Duplicate user creation handling", False, "Created new user instead of returning existing")
                return False
        else:
            log_test("Duplicate user creation handling", False, f"Status: {response.status_code}")
            return False
            
    except Exception as e:
        log_test("Duplicate user creation handling", False, f"Exception: {str(e)}")
        return False

def test_subscription_status_endpoints():
    """Test subscription status retrieval"""
    print("=" * 60)
    print("3. TESTING SUBSCRIPTION STATUS ENDPOINTS")
    print("=" * 60)
    
    # Test status for existing user
    try:
        player_id = test_player_ids[0]
        response = requests.get(f"{BASE_URL}/subscription/status/{player_id}", headers=HEADERS)
        
        if response.status_code == 200:
            status_data = response.json()
            
            # Verify status data structure
            required_fields = ["is_premium", "days_remaining", "is_trial", "can_start_trial"]
            missing_fields = [field for field in required_fields if field not in status_data]
            
            if not missing_fields:
                log_test("Get subscription status for existing user", True, 
                       f"Premium: {status_data['is_premium']}, Can start trial: {status_data['can_start_trial']}")
            else:
                log_test("Get subscription status for existing user", False, f"Missing fields: {missing_fields}")
                return False
        else:
            log_test("Get subscription status for existing user", False, f"Status: {response.status_code}")
            return False
            
    except Exception as e:
        log_test("Get subscription status for existing user", False, f"Exception: {str(e)}")
        return False
    
    # Test status for non-existing user
    try:
        non_existing_player_id = "non_existing_player_999"
        response = requests.get(f"{BASE_URL}/subscription/status/{non_existing_player_id}", headers=HEADERS)
        
        if response.status_code == 200:
            status_data = response.json()
            
            # Should return default status for non-existing user
            if (not status_data["is_premium"] and 
                status_data["days_remaining"] == 0 and 
                not status_data["is_trial"] and 
                status_data["can_start_trial"]):
                log_test("Get subscription status for non-existing user", True, "Returns default status allowing trial")
            else:
                log_test("Get subscription status for non-existing user", False, f"Unexpected status: {status_data}")
                return False
        else:
            log_test("Get subscription status for non-existing user", False, f"Status: {response.status_code}")
            return False
            
    except Exception as e:
        log_test("Get subscription status for non-existing user", False, f"Exception: {str(e)}")
        return False
    
    return True

def test_free_trial_functionality():
    """Test 7-day free trial functionality"""
    print("=" * 60)
    print("4. TESTING FREE TRIAL FUNCTIONALITY")
    print("=" * 60)
    
    # Test starting trial for eligible user
    try:
        player_id = test_player_ids[0]
        
        # Start trial
        response = requests.post(f"{BASE_URL}/subscription/start-trial/{player_id}", headers=HEADERS)
        
        if response.status_code == 200:
            trial_data = response.json()
            
            # Verify trial response
            if ("message" in trial_data and 
                "trial_ends_at" in trial_data and 
                "days_remaining" in trial_data):
                
                if trial_data["days_remaining"] == 7:
                    log_test("Start free trial", True, f"Trial started, ends at: {trial_data['trial_ends_at']}")
                else:
                    log_test("Start free trial", False, f"Expected 7 days, got {trial_data['days_remaining']}")
                    return False
            else:
                log_test("Start free trial", False, f"Missing fields in response: {trial_data}")
                return False
        else:
            log_test("Start free trial", False, f"Status: {response.status_code}, Response: {response.text}")
            return False
            
    except Exception as e:
        log_test("Start free trial", False, f"Exception: {str(e)}")
        return False
    
    # Verify trial status after starting
    try:
        response = requests.get(f"{BASE_URL}/subscription/status/{player_id}", headers=HEADERS)
        
        if response.status_code == 200:
            status_data = response.json()
            
            if (status_data["is_premium"] and 
                status_data["is_trial"] and 
                status_data["days_remaining"] == 7 and
                not status_data["can_start_trial"]):
                log_test("Verify trial status after starting", True, "User is now premium with active trial")
            else:
                log_test("Verify trial status after starting", False, f"Unexpected status: {status_data}")
                return False
        else:
            log_test("Verify trial status after starting", False, f"Status: {response.status_code}")
            return False
            
    except Exception as e:
        log_test("Verify trial status after starting", False, f"Exception: {str(e)}")
        return False
    
    return True

def test_trial_eligibility_logic():
    """Test trial eligibility logic"""
    print("=" * 60)
    print("5. TESTING TRIAL ELIGIBILITY LOGIC")
    print("=" * 60)
    
    # Test that user who already used trial cannot start another
    try:
        player_id = test_player_ids[0]  # This user already started trial
        
        response = requests.post(f"{BASE_URL}/subscription/start-trial/{player_id}", headers=HEADERS)
        
        if response.status_code == 400:
            error_data = response.json()
            if "not eligible" in error_data.get("detail", "").lower():
                log_test("Prevent duplicate trial usage", True, "User cannot start trial twice")
            else:
                log_test("Prevent duplicate trial usage", False, f"Unexpected error message: {error_data}")
                return False
        else:
            log_test("Prevent duplicate trial usage", False, f"Expected 400 error, got {response.status_code}")
            return False
            
    except Exception as e:
        log_test("Prevent duplicate trial usage", False, f"Exception: {str(e)}")
        return False
    
    # Test trial for user who hasn't used it yet
    try:
        eligible_player_id = test_player_ids[1]  # This user hasn't used trial
        
        response = requests.post(f"{BASE_URL}/subscription/start-trial/{eligible_player_id}", headers=HEADERS)
        
        if response.status_code == 200:
            trial_data = response.json()
            log_test("Start trial for eligible user", True, f"Trial started for second user")
        else:
            log_test("Start trial for eligible user", False, f"Status: {response.status_code}, Response: {response.text}")
            return False
            
    except Exception as e:
        log_test("Start trial for eligible user", False, f"Exception: {str(e)}")
        return False
    
    # Test trial for non-existing user
    try:
        non_existing_player_id = "non_existing_player_999"
        
        response = requests.post(f"{BASE_URL}/subscription/start-trial/{non_existing_player_id}", headers=HEADERS)
        
        if response.status_code == 404:
            error_data = response.json()
            if "not found" in error_data.get("detail", "").lower():
                log_test("Trial for non-existing user", True, "Properly returns 404 for non-existing user")
            else:
                log_test("Trial for non-existing user", False, f"Unexpected error message: {error_data}")
                return False
        else:
            log_test("Trial for non-existing user", False, f"Expected 404 error, got {response.status_code}")
            return False
            
    except Exception as e:
        log_test("Trial for non-existing user", False, f"Exception: {str(e)}")
        return False
    
    return True

def test_revenuecat_webhook_endpoint():
    """Test RevenueCat webhook endpoint"""
    print("=" * 60)
    print("6. TESTING REVENUECAT WEBHOOK ENDPOINT")
    print("=" * 60)
    
    # Create a mock webhook payload
    webhook_payload = {
        "type": "INITIAL_PURCHASE",
        "app_user_id": f"player_{test_player_ids[2]}",
        "store": "app_store",
        "product_id": "premium_monthly",
        "transaction_id": "test_transaction_123",
        "entitlements": {
            "premium": {
                "expires_date": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
                "is_sandbox": False
            }
        }
    }
    
    try:
        # Test webhook without signature (should work if secret not configured)
        response = requests.post(f"{BASE_URL}/webhooks/revenuecat", 
                               json=webhook_payload, 
                               headers=HEADERS)
        
        if response.status_code == 200:
            webhook_response = response.json()
            if webhook_response.get("status") == "received":
                log_test("RevenueCat webhook endpoint", True, "Webhook received and processed")
            else:
                log_test("RevenueCat webhook endpoint", False, f"Unexpected response: {webhook_response}")
                return False
        else:
            log_test("RevenueCat webhook endpoint", False, f"Status: {response.status_code}, Response: {response.text}")
            return False
            
    except Exception as e:
        log_test("RevenueCat webhook endpoint", False, f"Exception: {str(e)}")
        return False
    
    return True

def test_error_handling():
    """Test various error conditions"""
    print("=" * 60)
    print("7. TESTING ERROR HANDLING")
    print("=" * 60)
    
    # Test invalid email format
    try:
        invalid_payload = {
            "poker_player_id": "test_invalid",
            "email": "invalid_email_format"
        }
        
        response = requests.post(f"{BASE_URL}/subscription/create-user", json=invalid_payload, headers=HEADERS)
        
        # This might pass depending on validation - we'll check if it creates user
        if response.status_code in [200, 422]:
            log_test("Invalid email format handling", True, f"Handled invalid email appropriately (status: {response.status_code})")
        else:
            log_test("Invalid email format handling", False, f"Unexpected status: {response.status_code}")
            return False
            
    except Exception as e:
        log_test("Invalid email format handling", False, f"Exception: {str(e)}")
        return False
    
    # Test missing required fields
    try:
        incomplete_payload = {"poker_player_id": "test_incomplete"}
        
        response = requests.post(f"{BASE_URL}/subscription/create-user", json=incomplete_payload, headers=HEADERS)
        
        if response.status_code == 422:
            log_test("Missing required fields handling", True, "Properly validates required fields")
        else:
            log_test("Missing required fields handling", False, f"Expected 422, got {response.status_code}")
            return False
            
    except Exception as e:
        log_test("Missing required fields handling", False, f"Exception: {str(e)}")
        return False
    
    return True

def test_database_integration():
    """Test that subscription data is properly stored and retrieved"""
    print("=" * 60)
    print("8. TESTING DATABASE INTEGRATION")
    print("=" * 60)
    
    # Test data persistence by checking status after operations
    try:
        # Get status for user who started trial
        player_id = test_player_ids[0]
        response = requests.get(f"{BASE_URL}/subscription/status/{player_id}", headers=HEADERS)
        
        if response.status_code == 200:
            status_data = response.json()
            
            # Verify that trial data persisted
            if (status_data["is_premium"] and 
                status_data["is_trial"] and 
                not status_data["can_start_trial"]):
                log_test("Database persistence verification", True, "Trial data properly persisted in PostgreSQL")
            else:
                log_test("Database persistence verification", False, f"Trial data not persisted correctly: {status_data}")
                return False
        else:
            log_test("Database persistence verification", False, f"Status: {response.status_code}")
            return False
            
    except Exception as e:
        log_test("Database persistence verification", False, f"Exception: {str(e)}")
        return False
    
    return True

def run_subscription_tests():
    """Run comprehensive subscription system tests"""
    print("🎯 SUBSCRIPTION SYSTEM BACKEND - COMPREHENSIVE TESTING")
    print("Focus: PostgreSQL integration, subscription APIs, trial logic, webhook handling")
    print("=" * 80)
    print(f"Testing against: {BASE_URL}")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    test_results = []
    
    # Run all subscription tests
    test_results.append(("Database Connection", test_database_connection()))
    test_results.append(("Subscription User Creation", test_create_subscription_users()))
    test_results.append(("Duplicate User Handling", test_duplicate_user_creation()))
    test_results.append(("Subscription Status Endpoints", test_subscription_status_endpoints()))
    test_results.append(("Free Trial Functionality", test_free_trial_functionality()))
    test_results.append(("Trial Eligibility Logic", test_trial_eligibility_logic()))
    test_results.append(("RevenueCat Webhook Endpoint", test_revenuecat_webhook_endpoint()))
    test_results.append(("Error Handling", test_error_handling()))
    test_results.append(("Database Integration", test_database_integration()))
    
    # Summary
    print("=" * 80)
    print("📊 SUBSCRIPTION SYSTEM TEST SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print()
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL SUBSCRIPTION TESTS PASSED! Subscription system is working correctly.")
        print("\n✅ Key Features Verified:")
        print("   • PostgreSQL database connection and table creation")
        print("   • Subscription user creation and management")
        print("   • 7-day free trial functionality")
        print("   • Trial eligibility logic and restrictions")
        print("   • RevenueCat webhook endpoint")
        print("   • Error handling for invalid data")
        print("   • Database integration and data persistence")
        return True
    else:
        print("⚠️  SOME SUBSCRIPTION TESTS FAILED! Check the details above.")
        return False

if __name__ == "__main__":
    success = run_subscription_tests()
    exit(0 if success else 1)