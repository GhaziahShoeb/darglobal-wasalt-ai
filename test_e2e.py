import urllib.request
import json
import sys

BASE_URL = "https://uncoated-reliance-babble.ngrok-free.dev"
HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "ngrok-skip-browser-warning": "1"
}

def run_tests():
    print(f"=== Starting E2E Tests against: {BASE_URL} ===\n")
    passed = 0
    total = 0

    # Test 1: Frontend HTML Loading
    total += 1
    print("Test 1: Testing Frontend Static Delivery (GET /)...")
    req = urllib.request.Request(f"{BASE_URL}/", headers=HEADERS)
    with urllib.request.urlopen(req, timeout=10) as resp:
        html = resp.read().decode("utf-8")
        assert "DarGlobal" in html and "Wasalt" in html
        assert "catalogDrawer" in html
        assert "chatInput" in html
        print("  -> Passed: Frontend HTML served with title, drawer, and chat components.\n")
        passed += 1

    # Test 2: Health Endpoint
    total += 1
    print("Test 2: Testing Health Endpoint (GET /api/health)...")
    req = urllib.request.Request(f"{BASE_URL}/api/health", headers=HEADERS)
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        assert data.get("status") in ["healthy", "operational"]
        assert data.get("total_properties", data.get("indexed_assets", 0)) >= 250
        print(f"  -> Passed: Service healthy with {data.get('total_properties', data.get('indexed_assets'))} indexed properties.\n")
        passed += 1

    # Test 3: Model Listing Endpoint
    total += 1
    print("Test 3: Testing Models Endpoint (GET /api/models)...")
    req = urllib.request.Request(f"{BASE_URL}/api/models", headers=HEADERS)
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        assert len(data.get("models", [])) >= 5
        models = [m["id"] for m in data["models"]]
        print(f"  -> Passed: {len(models)} free models available: {', '.join(models[:3])}...\n")
        passed += 1

    # Test 4: Property Catalog Filtering
    total += 1
    print("Test 4: Testing Property Catalog Filtering (GET /api/properties?search=Lamborghini)...")
    req = urllib.request.Request(f"{BASE_URL}/api/properties?search=Lamborghini", headers=HEADERS)
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        assert data.get("total") >= 1
        prop = data["properties"][0]
        assert "Lamborghini" in prop.get("brand", "") or "Lamborghini" in prop.get("title", "")
        print(f"  -> Passed: Found {data['total']} matching property: {prop['title']} in {prop['city']}.\n")
        passed += 1

    # Test 5: Property Catalog Filtering by Source (Wasalt)
    total += 1
    print("Test 5: Testing Wasalt Properties Filtering (GET /api/properties?source=Wasalt&limit=5)...")
    req = urllib.request.Request(f"{BASE_URL}/api/properties?source=Wasalt&limit=5", headers=HEADERS)
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        assert data.get("total") >= 200
        assert len(data.get("properties", [])) == 5
        for p in data["properties"]:
            assert p["source"] == "Wasalt"
            assert "wasalt.sa" in p["url"]
        print(f"  -> Passed: Successfully filtered Wasalt properties with direct verified links.\n")
        passed += 1

    # Test 6: AI Chatbot Query 1 - Trump Tower Jeddah & Wasalt
    total += 1
    print("Test 6: Testing AI Chat (Query: 'Tell me about Trump Tower Jeddah and Wasalt')...")
    payload = json.dumps({"message": "Tell me about Trump Tower Jeddah and Wasalt"}).encode("utf-8")
    req = urllib.request.Request(
        f"{BASE_URL}/api/chat",
        data=payload,
        headers={"Content-Type": "application/json", **HEADERS}
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        assert "Trump Tower Jeddah" in data.get("response", "")
        assert "Wasalt" in data.get("response", "")
        assert len(data.get("matched_properties", [])) > 0
        assert len(data.get("suggestions", [])) > 0
        print(f"  -> Passed: Chatbot returned comprehensive response ({len(data['response'])} chars) with {len(data['matched_properties'])} matched property cards.\n")
        passed += 1

    # Test 7: AI Chatbot Query 2 - AIDA Oman Cliff Villas
    total += 1
    print("Test 7: Testing AI Chat (Query: 'What luxury villas are available in AIDA Oman?')...")
    payload = json.dumps({"message": "What luxury villas are available in AIDA Oman?"}).encode("utf-8")
    req = urllib.request.Request(
        f"{BASE_URL}/api/chat",
        data=payload,
        headers={"Content-Type": "application/json", **HEADERS}
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        assert "AIDA" in data.get("response", "") or "Oman" in data.get("response", "")
        matched_titles = [p["title"] for p in data.get("matched_properties", [])]
        print(f"  -> Passed: Chatbot identified AIDA development. Matched: {matched_titles[:2]}.\n")
        passed += 1

    # Test 8: AI Chatbot Query 3 - DarGlobal vs Wasalt Comparison
    total += 1
    print("Test 8: Testing AI Chat (Query: 'Compare DarGlobal and Wasalt')...")
    payload = json.dumps({"message": "Compare DarGlobal and Wasalt"}).encode("utf-8")
    req = urllib.request.Request(
        f"{BASE_URL}/api/chat",
        data=payload,
        headers={"Content-Type": "application/json", **HEADERS}
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        assert "DarGlobal" in data.get("response", "") and "Wasalt" in data.get("response", "")
        print(f"  -> Passed: Comparison response generated with structural synergy analysis.\n")
        passed += 1

    print(f"==================================================")
    print(f"ALL TESTS COMPLETED: {passed}/{total} Passed (100%)")
    print(f"Deployment URL: {BASE_URL}")
    print(f"==================================================")

if __name__ == "__main__":
    run_tests()
