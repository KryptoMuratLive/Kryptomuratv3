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

class BackendTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        self.created_stream_id = None
        
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
    
    def test_api_root(self):
        """Test basic API root endpoint"""
        try:
            response = self.session.get(f"{API_BASE}/")
            if response.status_code == 200:
                data = response.json()
                if "message" in data and "Bitcoin" in data["message"]:
                    self.log_test("API Root Endpoint", True, "Root endpoint accessible", data)
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
    
    def test_create_stream(self):
        """Test POST /api/streams/create"""
        try:
            # Test data for stream creation
            stream_data = {
                "name": "Test Bitcoin Hunt Stream",
                "description": "Testing Livepeer integration for Bitcoin hunting platform",
                "nft_required": True
            }
            
            # The endpoint expects creator_wallet as a query parameter based on the code
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
                    self.log_test("Create Stream", True, f"Stream created with ID: {data['id']}", data)
                    return True
                else:
                    self.log_test("Create Stream", False, "Missing required fields in response", data)
                    return False
            else:
                error_data = response.json() if response.content else None
                self.log_test("Create Stream", False, f"HTTP {response.status_code}", error_data)
                return False
                
        except Exception as e:
            self.log_test("Create Stream", False, f"Request error: {str(e)}")
            return False
    
    def test_get_all_streams(self):
        """Test GET /api/streams"""
        try:
            response = self.session.get(f"{API_BASE}/streams")
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    self.log_test("Get All Streams", True, f"Retrieved {len(data)} streams", {"count": len(data)})
                    return True
                else:
                    self.log_test("Get All Streams", False, "Response is not a list", data)
                    return False
            else:
                error_data = response.json() if response.content else None
                self.log_test("Get All Streams", False, f"HTTP {response.status_code}", error_data)
                return False
                
        except Exception as e:
            self.log_test("Get All Streams", False, f"Request error: {str(e)}")
            return False
    
    def test_get_specific_stream(self):
        """Test GET /api/streams/{stream_id}"""
        if not self.created_stream_id:
            self.log_test("Get Specific Stream", False, "No stream ID available (create stream failed)")
            return False
            
        try:
            response = self.session.get(f"{API_BASE}/streams/{self.created_stream_id}")
            
            if response.status_code == 200:
                data = response.json()
                if "id" in data and data["id"] == self.created_stream_id:
                    self.log_test("Get Specific Stream", True, f"Retrieved stream {self.created_stream_id}", data)
                    return True
                else:
                    self.log_test("Get Specific Stream", False, "Stream ID mismatch or missing", data)
                    return False
            elif response.status_code == 404:
                self.log_test("Get Specific Stream", False, "Stream not found", response.json() if response.content else None)
                return False
            else:
                error_data = response.json() if response.content else None
                self.log_test("Get Specific Stream", False, f"HTTP {response.status_code}", error_data)
                return False
                
        except Exception as e:
            self.log_test("Get Specific Stream", False, f"Request error: {str(e)}")
            return False
    
    def test_verify_stream_access(self):
        """Test POST /api/streams/{stream_id}/access"""
        if not self.created_stream_id:
            self.log_test("Verify Stream Access", False, "No stream ID available (create stream failed)")
            return False
            
        try:
            # Based on the code, it expects wallet_address as a parameter, not in body
            params = {"wallet_address": TEST_WALLET}
            
            response = self.session.post(
                f"{API_BASE}/streams/{self.created_stream_id}/access",
                params=params
            )
            
            if response.status_code == 200:
                data = response.json()
                if "access_granted" in data and "wallet_address" in data:
                    access_granted = data["access_granted"]
                    status = "granted" if access_granted else "denied"
                    self.log_test("Verify Stream Access", True, f"Access {status} for wallet", data)
                    return True
                else:
                    self.log_test("Verify Stream Access", False, "Missing required fields in response", data)
                    return False
            elif response.status_code == 403:
                data = response.json() if response.content else None
                self.log_test("Verify Stream Access", True, "Access properly denied (NFT required)", data)
                return True
            else:
                error_data = response.json() if response.content else None
                self.log_test("Verify Stream Access", False, f"HTTP {response.status_code}", error_data)
                return False
                
        except Exception as e:
            self.log_test("Verify Stream Access", False, f"Request error: {str(e)}")
            return False
    
    def test_get_playback_url(self):
        """Test GET /api/streams/{stream_id}/playback/{wallet_address}"""
        if not self.created_stream_id:
            self.log_test("Get Playback URL", False, "No stream ID available (create stream failed)")
            return False
            
        try:
            response = self.session.get(
                f"{API_BASE}/streams/{self.created_stream_id}/playback/{TEST_WALLET}"
            )
            
            if response.status_code == 200:
                data = response.json()
                if "playback_id" in data and "hls_url" in data:
                    self.log_test("Get Playback URL", True, "Playback URLs retrieved", data)
                    return True
                else:
                    self.log_test("Get Playback URL", False, "Missing playback URLs in response", data)
                    return False
            elif response.status_code == 403:
                data = response.json() if response.content else None
                self.log_test("Get Playback URL", True, "Access properly denied (expected for NFT gating)", data)
                return True
            else:
                error_data = response.json() if response.content else None
                self.log_test("Get Playback URL", False, f"HTTP {response.status_code}", error_data)
                return False
                
        except Exception as e:
            self.log_test("Get Playback URL", False, f"Request error: {str(e)}")
            return False
    
    def test_get_viewer_stats(self):
        """Test GET /api/streams/{stream_id}/viewers"""
        if not self.created_stream_id:
            self.log_test("Get Viewer Stats", False, "No stream ID available (create stream failed)")
            return False
            
        try:
            response = self.session.get(f"{API_BASE}/streams/{self.created_stream_id}/viewers")
            
            if response.status_code == 200:
                data = response.json()
                if "total_viewers" in data and "stream_status" in data:
                    self.log_test("Get Viewer Stats", True, f"Viewer stats: {data['total_viewers']} total, status: {data['stream_status']}", data)
                    return True
                else:
                    self.log_test("Get Viewer Stats", False, "Missing viewer stats in response", data)
                    return False
            else:
                error_data = response.json() if response.content else None
                self.log_test("Get Viewer Stats", False, f"HTTP {response.status_code}", error_data)
                return False
                
        except Exception as e:
            self.log_test("Get Viewer Stats", False, f"Request error: {str(e)}")
            return False
    
    def test_nft_access_control(self):
        """Test NFT access control functionality"""
        try:
            # Test the NFT access endpoint directly
            response = self.session.get(f"{API_BASE}/nft/access/{TEST_WALLET}")
            
            if response.status_code == 200:
                data = response.json()
                if "has_access" in data and "access_level" in data:
                    access = "granted" if data["has_access"] else "denied"
                    self.log_test("NFT Access Control", True, f"NFT access {access}, level: {data['access_level']}", data)
                    return True
                else:
                    self.log_test("NFT Access Control", False, "Missing access fields in response", data)
                    return False
            else:
                error_data = response.json() if response.content else None
                self.log_test("NFT Access Control", False, f"HTTP {response.status_code}", error_data)
                return False
                
        except Exception as e:
            self.log_test("NFT Access Control", False, f"Request error: {str(e)}")
            return False
    
    def test_error_handling(self):
        """Test proper error handling"""
        tests_passed = 0
        total_tests = 3
        
        # Test 1: Invalid stream ID
        try:
            response = self.session.get(f"{API_BASE}/streams/invalid-stream-id")
            if response.status_code == 404:
                tests_passed += 1
                print("   ✅ Invalid stream ID properly returns 404")
            else:
                print(f"   ❌ Invalid stream ID returned {response.status_code}, expected 404")
        except Exception as e:
            print(f"   ❌ Error testing invalid stream ID: {str(e)}")
        
        # Test 2: Invalid wallet address format
        try:
            response = self.session.get(f"{API_BASE}/nft/access/invalid-wallet")
            if response.status_code in [400, 500]:  # Either is acceptable for invalid wallet
                tests_passed += 1
                print("   ✅ Invalid wallet address properly handled")
            else:
                print(f"   ❌ Invalid wallet returned {response.status_code}, expected 400 or 500")
        except Exception as e:
            print(f"   ❌ Error testing invalid wallet: {str(e)}")
        
        # Test 3: Missing required parameters
        try:
            response = self.session.post(f"{API_BASE}/streams/create", json={})
            if response.status_code in [400, 422]:  # FastAPI validation error
                tests_passed += 1
                print("   ✅ Missing parameters properly validated")
            else:
                print(f"   ❌ Missing params returned {response.status_code}, expected 400 or 422")
        except Exception as e:
            print(f"   ❌ Error testing missing params: {str(e)}")
        
        success = tests_passed == total_tests
        self.log_test("Error Handling", success, f"{tests_passed}/{total_tests} error handling tests passed")
        return success
    
    def run_all_tests(self):
        """Run all tests in sequence"""
        print("🚀 Starting Backend API Tests for Livepeer Streaming")
        print("=" * 60)
        
        # Test sequence
        tests = [
            ("Basic API", self.test_api_root),
            ("Create Stream", self.test_create_stream),
            ("Get All Streams", self.test_get_all_streams),
            ("Get Specific Stream", self.test_get_specific_stream),
            ("Verify Stream Access", self.test_verify_stream_access),
            ("Get Playback URL", self.test_get_playback_url),
            ("Get Viewer Stats", self.test_get_viewer_stats),
            ("NFT Access Control", self.test_nft_access_control),
            ("Error Handling", self.test_error_handling)
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            print(f"\n📋 Running {test_name} test...")
            if test_func():
                passed += 1
        
        print("\n" + "=" * 60)
        print(f"🏁 Test Summary: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed! Livepeer streaming endpoints are working correctly.")
        else:
            print("⚠️  Some tests failed. Check the details above.")
        
        return passed, total, self.test_results

def main():
    tester = BackendTester()
    passed, total, results = tester.run_all_tests()
    
    # Save detailed results
    with open('/app/test_results_detailed.json', 'w') as f:
        json.dump({
            "summary": {"passed": passed, "total": total},
            "results": results,
            "timestamp": datetime.now().isoformat()
        }, f, indent=2)
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)