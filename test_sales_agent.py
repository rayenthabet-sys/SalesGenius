import os
import json
from fastapi.testclient import TestClient
from sales_agent import app, ClientProfile, AgentRequest, ConversationMessage
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

client = TestClient(app)

def test_sales_intelligence_flow():
    """
    Test the multi-turn sales intelligence flow with different personas
    """
    print("\nStarting Sales Intelligence Agent Verification...")
    
    # Persona 1: Technology SME with low risk appetite
    print("\n--- TEST CASE 1: Technology SME (Conservative) ---")
    request_data = {
        "user_message": "Hello, I'm the CEO of TechFlow, a software firm. We're looking to upgrade our cloud infra but we're worried about cost stability.",
        "conversation_history": [],
        "client_profile": {
            "company_name": "TechFlow",
            "sector": "Technology",
            "sme_size": "Medium (50-99 employees)"
        },
        "use_web_search": True
    }
    
    response = client.post("/chat", json=request_data)
    assert response.status_code == 200
    data = response.json()
    
    print(f"Agent Message:\n{data['agent_message']}")
    print(f"\nUpdated Profile: {data['client_profile']}")
    print(f"Recommendations: {data['recommendations']}")
    print(f"Next Steps: {data['next_steps']}")
    
    # Verify Financial DNA Benchmark check
    # (Since it's in the system prompt, we check if the agent mentions ROI or stability)
    content = data['agent_message'].lower()
    has_stability_vibe = any(word in content for word in ["roi", "stable", "security", "proven", "predictable"])
    print(f"DNA Tone Check (Security focused?): {'[PASS]' if has_stability_vibe else '[FAIL]'}")

    # Persona 2: Healthcare SME with low literacy (needs simple explanation)
    print("\n--- TEST CASE 2: Healthcare Clinic (Simplicity needed) ---")
    request_data = {
        "user_message": "Hi, I run a small clinic. I keep hearing about 'data-driven practice management' but I don't really get how it helps me.",
        "conversation_history": [],
        "client_profile": {
            "company_name": "City Care Clinic",
            "sector": "Healthcare",
            "sme_size": "Micro (1-9 employees)"
        },
        "use_web_search": False
    }
    
    response = client.post("/chat", json=request_data)
    assert response.status_code == 200
    data = response.json()
    
    print(f"Agent Message:\n{data['agent_message'][:300]}...")
    
    # Check for simplified tone
    agent_msg = data['agent_message'].lower()
    is_simple = any(word in agent_msg for word in ["simple", "basics", "help you understand", "manage your clinic"])
    print(f"DNA Tone Check (Simplicity?): {'[PASS]' if is_simple else '[FAIL]'}")

    # Persona 3: Irrelevant Query (Testing Analyzer Agent)
    print("\n--- TEST CASE 3: Irrelevant Query (Testing Analyzer) ---")
    request_data = {
        "user_message": "Can you tell me a joke about space?",
        "conversation_history": [],
        "client_profile": None,
        "use_web_search": False
    }
    
    response = client.post("/chat", json=request_data)
    assert response.status_code == 200
    data = response.json()
    
    print(f"Agent Message: {data['agent_message']}")
    
    # Analyzer should handle this directly without going to Sales Agent
    is_gated = "genius" not in data['agent_message'].lower()
    print(f"Analyzer Gating Check: {'[PASS]' if is_gated else '[WARNING]'}")

if __name__ == "__main__":
    try:
        test_sales_intelligence_flow()
    except Exception as e:
        print(f"Test Failed: {e}")
