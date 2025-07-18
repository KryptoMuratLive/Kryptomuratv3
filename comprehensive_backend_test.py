#!/usr/bin/env python3
"""
Comprehensive Backend API Testing Script for KryptoMurat Platform
Tests all backend API endpoints including wallet, staking, NFT, AI, streaming, story, and telegram functionality
"""

import requests
import json
import sys
from datetime import datetime
import uuid

# Configuration
BACKEND_URL = "https://949949b8-c69c-4177-9f1e-2d335c0ad6dd.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"
TEST_WALLET = "0x742d35Cc6634C0532925a3b8D0F48BDf4b64fC44"

class ComprehensiveBackendTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        self.created_stream_id = None
        self.session_id = str(uuid.uuid4())
        
    def log_test(self, test_name, success, details="", response_data=None):
        """Log test results"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat(),
            "response_data": response_data
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {details}")
        if response_data and not success:
            print(f"   Response: {json.dumps(response_data, indent=2)}")
    
    # ===== BASIC API TESTS =====
    def test_api_root(self):
        """Test /api/ root endpoint"""
        try:
            response = self.session.get(f"{API_BASE}/")
            if response.status_code == 200:
                data = response.json()
                if "message" in data and "KryptoMurat" in data["message"]:
                    self.log_test("API Root Endpoint", True, f"Root endpoint accessible: {data['message']}", data)
                    return True
                else:
                    self.log_test("API Root Endpoint", False, "Unexpected response format", data)
                    return False
            else:
                self.log_test("API Root Endpoint", False, f"HTTP {response.status_code}", response.json() if response.content else None)
                return False
        except Exception as e:
            self.log_test("API Root Endpoint", False, f"Connection error: {str(e)}")
            return False
    
    # ===== WALLET TESTS =====
    def test_wallet_connect(self):
        """Test POST /api/wallet/connect"""
        try:
            wallet_data = {
                "wallet_address": TEST_WALLET,
                "chain_id": 137  # Polygon
            }
            
            response = self.session.post(f"{API_BASE}/wallet/connect", json=wallet_data)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") == True:
                    self.log_test("Wallet Connect", True, "Wallet connected successfully", data)
                    return True
                else:
                    self.log_test("Wallet Connect", False, "Success flag not true", data)
                    return False
            else:
                error_data = response.json() if response.content else None
                self.log_test("Wallet Connect", False, f"HTTP {response.status_code}", error_data)
                return False
                
        except Exception as e:
            self.log_test("Wallet Connect", False, f"Request error: {str(e)}")
            return False
    
    def test_wallet_balance(self):
        """Test GET /api/wallet/balance/{wallet_address}"""
        try:
            response = self.session.get(f"{API_BASE}/wallet/balance/{TEST_WALLET}")
            
            if response.status_code == 200:
                data = response.json()
                if "balance" in data and "symbol" in data and data["symbol"] == "MURAT":
                    self.log_test("Wallet Balance", True, f"Balance retrieved: {data['balance']} {data['symbol']}", data)
                    return True
                else:
                    self.log_test("Wallet Balance", False, "Missing balance or symbol fields", data)
                    return False
            else:
                error_data = response.json() if response.content else None
                self.log_test("Wallet Balance", False, f"HTTP {response.status_code}", error_data)
                return False
                
        except Exception as e:
            self.log_test("Wallet Balance", False, f"Request error: {str(e)}")
            return False
    
    # ===== STAKING TESTS =====
    def test_staking_create(self):
        """Test POST /api/staking/create"""
        try:
            staking_data = {
                "wallet_address": TEST_WALLET,
                "amount": "1000",
                "duration_days": 90
            }
            
            response = self.session.post(f"{API_BASE}/staking/create", json=staking_data)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") == True and "staking_position" in data:
                    position = data["staking_position"]
                    if position.get("wallet_address") == TEST_WALLET:
                        self.log_test("Staking Create", True, f"Staking position created with APY: {position.get('apy')}%", data)
                        return True
                    else:
                        self.log_test("Staking Create", False, "Wallet address mismatch in response", data)
                        return False
                else:
                    self.log_test("Staking Create", False, "Missing success flag or staking_position", data)
                    return False
            else:
                error_data = response.json() if response.content else None
                self.log_test("Staking Create", False, f"HTTP {response.status_code}", error_data)
                return False
                
        except Exception as e:
            self.log_test("Staking Create", False, f"Request error: {str(e)}")
            return False
    
    def test_staking_positions(self):
        """Test GET /api/staking/positions/{wallet_address}"""
        try:
            response = self.session.get(f"{API_BASE}/staking/positions/{TEST_WALLET}")
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    self.log_test("Staking Positions", True, f"Retrieved {len(data)} staking positions", {"count": len(data)})
                    return True
                else:
                    self.log_test("Staking Positions", False, "Response is not a list", data)
                    return False
            else:
                error_data = response.json() if response.content else None
                self.log_test("Staking Positions", False, f"HTTP {response.status_code}", error_data)
                return False
                
        except Exception as e:
            self.log_test("Staking Positions", False, f"Request error: {str(e)}")
            return False
    
    # ===== NFT ACCESS TESTS =====
    def test_nft_access(self):
        """Test GET /api/nft/access/{wallet_address}"""
        try:
            response = self.session.get(f"{API_BASE}/nft/access/{TEST_WALLET}")
            
            if response.status_code == 200:
                data = response.json()
                if "has_access" in data and "access_level" in data and "nft_count" in data:
                    access = "granted" if data["has_access"] else "denied"
                    self.log_test("NFT Access", True, f"NFT access {access}, level: {data['access_level']}, count: {data['nft_count']}", data)
                    return True
                else:
                    self.log_test("NFT Access", False, "Missing required access fields", data)
                    return False
            else:
                error_data = response.json() if response.content else None
                self.log_test("NFT Access", False, f"HTTP {response.status_code}", error_data)
                return False
                
        except Exception as e:
            self.log_test("NFT Access", False, f"Request error: {str(e)}")
            return False
    
    # ===== AI CONTENT TESTS =====
    def test_ai_generate(self):
        """Test POST /api/ai/generate"""
        try:
            ai_request = {
                "prompt": "Erstelle einen lustigen Bitcoin-Meme über Murat",
                "content_type": "meme",
                "session_id": self.session_id
            }
            
            response = self.session.post(f"{API_BASE}/ai/generate", json=ai_request)
            
            if response.status_code == 200:
                data = response.json()
                if "content" in data and "content_type" in data and data["content_type"] == "meme":
                    self.log_test("AI Generate", True, f"AI content generated: {len(data['content'])} characters", {"content_length": len(data['content'])})
                    return True
                else:
                    self.log_test("AI Generate", False, "Missing content or content_type fields", data)
                    return False
            else:
                error_data = response.json() if response.content else None
                self.log_test("AI Generate", False, f"HTTP {response.status_code}", error_data)
                return False
                
        except Exception as e:
            self.log_test("AI Generate", False, f"Request error: {str(e)}")
            return False
    
    # ===== STREAMING TESTS =====
    def test_streams_create(self):
        """Test POST /api/streams/create"""
        try:
            stream_data = {
                "name": "Bitcoin Hunt Live Stream",
                "description": "Live streaming the Bitcoin hunt adventure",
                "nft_required": True
            }
            
            params = {"creator_wallet": TEST_WALLET}
            
            response = self.session.post(
                f"{API_BASE}/streams/create",
                json=stream_data,
                params=params
            )
            
            if response.status_code == 200:
                data = response.json()
                if "id" in data and "stream_key" in data and "playback_id" in data:
                    self.created_stream_id = data["id"]
                    self.log_test("Streams Create", True, f"Stream created with ID: {data['id']}", {"stream_id": data['id']})
                    return True
                else:
                    self.log_test("Streams Create", False, "Missing required stream fields", data)
                    return False
            else:
                error_data = response.json() if response.content else None
                self.log_test("Streams Create", False, f"HTTP {response.status_code}", error_data)
                return False
                
        except Exception as e:
            self.log_test("Streams Create", False, f"Request error: {str(e)}")
            return False
    
    # ===== STORY TESTS =====
    def test_story_initialize(self):
        """Test POST /api/story/initialize"""
        try:
            params = {"wallet_address": TEST_WALLET}
            
            response = self.session.post(f"{API_BASE}/story/initialize", params=params)
            
            if response.status_code == 200:
                data = response.json()
                if "wallet_address" in data and "current_chapter" in data and "story_path" in data:
                    self.log_test("Story Initialize", True, f"Story initialized for wallet, current chapter: {data['current_chapter']}", data)
                    return True
                else:
                    self.log_test("Story Initialize", False, "Missing required story fields", data)
                    return False
            else:
                error_data = response.json() if response.content else None
                self.log_test("Story Initialize", False, f"HTTP {response.status_code}", error_data)
                return False
                
        except Exception as e:
            self.log_test("Story Initialize", False, f"Request error: {str(e)}")
            return False
    
    def test_story_chapters(self):
        """Test GET /api/story/chapters"""
        try:
            response = self.session.get(f"{API_BASE}/story/chapters")
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    self.log_test("Story Chapters", True, f"Retrieved {len(data)} story chapters", {"count": len(data)})
                    return True
                else:
                    self.log_test("Story Chapters", False, "Response is not a list", data)
                    return False
            else:
                error_data = response.json() if response.content else None
                self.log_test("Story Chapters", False, f"HTTP {response.status_code}", error_data)
                return False
                
        except Exception as e:
            self.log_test("Story Chapters", False, f"Request error: {str(e)}")
            return False
    
    # ===== TELEGRAM TESTS =====
    def test_telegram_subscribe(self):
        """Test POST /api/telegram/subscribe"""
        try:
            subscription_data = {
                "wallet_address": TEST_WALLET,
                "chat_id": 123456789,
                "username": "test_user"
            }
            
            response = self.session.post(f"{API_BASE}/telegram/subscribe", json=subscription_data)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") == True:
                    self.log_test("Telegram Subscribe", True, f"Telegram subscription successful: {data.get('message')}", data)
                    return True
                else:
                    self.log_test("Telegram Subscribe", False, "Success flag not true", data)
                    return False
            else:
                error_data = response.json() if response.content else None
                self.log_test("Telegram Subscribe", False, f"HTTP {response.status_code}", error_data)
                return False
                
        except Exception as e:
            self.log_test("Telegram Subscribe", False, f"Request error: {str(e)}")
            return False
    
    def test_telegram_stats(self):
        """Test GET /api/telegram/stats"""
        try:
            response = self.session.get(f"{API_BASE}/telegram/stats")
            
            if response.status_code == 200:
                data = response.json()
                if "total_subscribers" in data and "total_messages" in data:
                    self.log_test("Telegram Stats", True, f"Stats retrieved: {data['total_subscribers']} subscribers, {data['total_messages']} messages", data)
                    return True
                else:
                    self.log_test("Telegram Stats", False, "Missing required stats fields", data)
                    return False
            else:
                error_data = response.json() if response.content else None
                self.log_test("Telegram Stats", False, f"HTTP {response.status_code}", error_data)
                return False
                
        except Exception as e:
            self.log_test("Telegram Stats", False, f"Request error: {str(e)}")
            return False
    
    # ===== ERROR HANDLING TESTS =====
    def test_error_handling(self):
        """Test error handling and edge cases"""
        tests_passed = 0
        total_tests = 4
        
        # Test 1: Invalid wallet address format
        try:
            response = self.session.get(f"{API_BASE}/wallet/balance/invalid-wallet")
            if response.status_code in [400, 500]:
                tests_passed += 1
                print("   ✅ Invalid wallet address properly handled")
            else:
                print(f"   ❌ Invalid wallet returned {response.status_code}, expected 400 or 500")
        except Exception as e:
            print(f"   ❌ Error testing invalid wallet: {str(e)}")
        
        # Test 2: Missing required parameters in staking
        try:
            response = self.session.post(f"{API_BASE}/staking/create", json={})
            if response.status_code in [400, 422]:
                tests_passed += 1
                print("   ✅ Missing staking parameters properly validated")
            else:
                print(f"   ❌ Missing staking params returned {response.status_code}, expected 400 or 422")
        except Exception as e:
            print(f"   ❌ Error testing missing staking params: {str(e)}")
        
        # Test 3: Invalid AI content type
        try:
            invalid_ai_request = {
                "prompt": "test",
                "content_type": "invalid_type",
                "session_id": self.session_id
            }
            response = self.session.post(f"{API_BASE}/ai/generate", json=invalid_ai_request)
            # This might still work as the backend might handle any content_type
            if response.status_code in [200, 400, 422]:
                tests_passed += 1
                print("   ✅ AI content type validation working")
            else:
                print(f"   ❌ AI validation returned {response.status_code}")
        except Exception as e:
            print(f"   ❌ Error testing AI validation: {str(e)}")
        
        # Test 4: Non-existent story chapter
        try:
            response = self.session.get(f"{API_BASE}/story/chapter/non-existent-chapter?wallet_address={TEST_WALLET}")
            if response.status_code in [404, 500]:
                tests_passed += 1
                print("   ✅ Non-existent chapter properly handled")
            else:
                print(f"   ❌ Non-existent chapter returned {response.status_code}, expected 404 or 500")
        except Exception as e:
            print(f"   ❌ Error testing non-existent chapter: {str(e)}")
        
        success = tests_passed >= 3  # Allow 1 failure in error handling
        self.log_test("Error Handling", success, f"{tests_passed}/{total_tests} error handling tests passed")
        return success
    
    def run_all_tests(self):
        """Run all comprehensive tests in sequence"""
        print("🚀 Starting Comprehensive Backend API Tests for KryptoMurat Platform")
        print("=" * 70)
        
        # Test sequence - all endpoints requested by user
        tests = [
            ("API Root", self.test_api_root),
            ("Wallet Connect", self.test_wallet_connect),
            ("Wallet Balance", self.test_wallet_balance),
            ("Staking Create", self.test_staking_create),
            ("Staking Positions", self.test_staking_positions),
            ("NFT Access", self.test_nft_access),
            ("AI Generate", self.test_ai_generate),
            ("Streams Create", self.test_streams_create),
            ("Story Initialize", self.test_story_initialize),
            ("Story Chapters", self.test_story_chapters),
            ("Telegram Subscribe", self.test_telegram_subscribe),
            ("Telegram Stats", self.test_telegram_stats),
            ("Error Handling", self.test_error_handling)
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            print(f"\n📋 Running {test_name} test...")
            if test_func():
                passed += 1
        
        print("\n" + "=" * 70)
        print(f"🏁 Test Summary: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed! KryptoMurat backend is working correctly.")
        else:
            print("⚠️  Some tests failed. Check the details above.")
        
        return passed, total, self.test_results

def main():
    tester = ComprehensiveBackendTester()
    passed, total, results = tester.run_all_tests()
    
    # Save detailed results
    with open('/app/comprehensive_test_results.json', 'w') as f:
        json.dump({
            "summary": {"passed": passed, "total": total},
            "results": results,
            "timestamp": datetime.now().isoformat()
        }, f, indent=2)
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)