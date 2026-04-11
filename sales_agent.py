
import os
import json
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from groq import Groq
import pandas as pd
import numpy as np
from datetime import datetime
from tavily import TavilyClient

# Initialize FastAPI
app = FastAPI(title="Sales Intelligence Agent API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Clients
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

# Mappings for encoded CSV values
SECTOR_MAP = {
    1: "Healthcare",
    2: "Technology",
    3: "Services",
    4: "Agriculture",
    5: "Construction"
}

SIZE_MAP = {
    1: "Micro (1-9 employees)",
    2: "Small (10-49 employees)",
    3: "Medium (50-99 employees)",
    4: "Large Medium (100-249 employees)",
    5: "Enterprise (250+ employees)"
}

# Load SME financial data
SME_DATA_PATH = "sme_financial_decision.csv"
try:
    sme_data = pd.read_csv(SME_DATA_PATH)
    # Clean column names if necessary
    sme_data.columns = [c.strip() for c in sme_data.columns]
except FileNotFoundError:
    print(f"Warning: {SME_DATA_PATH} not found.")
    sme_data = None

# Define request/response models
class ConversationMessage(BaseModel):
    role: str
    content: str

class ClientProfile(BaseModel):
    company_name: Optional[str] = None
    sector: Optional[str] = None
    sme_type: Optional[str] = None
    sme_size: Optional[str] = None
    annual_revenue: Optional[float] = None
    financial_health: Optional[str] = None
    pain_points: Optional[list] = None
    goals: Optional[list] = None
    budget: Optional[float] = None
    decision_timeline: Optional[str] = None

class AgentRequest(BaseModel):
    user_message: str
    conversation_history: list[ConversationMessage]
    client_profile: Optional[ClientProfile] = None
    use_web_search: bool = False

class AgentResponse(BaseModel):
    agent_message: str
    client_profile: Optional[ClientProfile] = None
    recommendations: Optional[list] = None
    next_steps: Optional[list] = None
    trace: Optional[dict] = None
    conversation_turn: int

class ConversationState:
    """Manages conversation state and client qualification"""
    
    def __init__(self):
        self.profile = ClientProfile()
        self.turn_count = 0
        self.qualification_score = 0
        self.identified_needs = []
        self.recommendation_history = []
        
    def update_profile(self, **kwargs):
        """Update client profile with new information"""
        for key, value in kwargs.items():
            if hasattr(self.profile, key):
                setattr(self.profile, key, value)
    
    def calculate_qualification_score(self) -> float:
        """Calculate lead qualification score 0-100"""
        score = 0
        if self.profile.company_name: score += 10
        if self.profile.sector: score += 15
        if self.profile.sme_size: score += 10
        if self.profile.annual_revenue: score += 15
        if self.profile.pain_points and len(self.profile.pain_points) > 0: score += 20
        if self.profile.goals and len(self.profile.goals) > 0: score += 20
        if self.profile.budget: score += 10
        return min(score, 100)

# --- AGENT PROMPTS ---

ANALYZER_PROMPT = """You are the 'Gating Agent' for SalesGenius.
Your job is to decide if the user's message is RELEVANT to sales, business, or the client's current profile.

Decision logic:
1. If the message is irrelevant (e.g., small talk, jokes, personal questions), respond directly and pleasantly, then end with [[[STOP]]].
2. If the message is relevant, provide a 1-sentence 'INTENT SUMMARY' of what the user wants, and end with [[[PROCEED]]].

Do not use emojis."""

VALIDATOR_PROMPT = """You are the 'Validation Agent' for SalesGenius.
Your job is to take the 'INTENT SUMMARY' from the Gatekeeper and the current 'CLIENT PROFILE', and structure it for the Sales Agent.

Actions:
1. Identify any NEW data points.
2. Refine the 'Sales Request' into a high-quality summary for the professional closer.
3. Determine if we have enough info to make a recommendation.

Output MUST end with a JSON block inside ```json ... ``` with keys: 
'refined_input' (string), 'extracted_data' (dict), 'priority' (string: low/med/high)."""

SALES_PROMPT = """You are SalesGenius, a high-performance Sales Intelligence Agent.
Your mission is to qualify prospects, understand their 'Financial DNA', and provide data-backed recommendations.

Use the 'Validated Sales Context' provided by the previous agent to engage.
Your approach:
1. Natural Dialogue: Engage like a human sales expert.
2. Financial DNA Insight: Tailor tone to Literacy, Risk, and Decision style.
3. Market Context: Use web search data and sector benchmarks.
4. Call to Action: Suggest specific solutions and ROI metrics.

Do not use emojis."""

def validate_messages(messages: list) -> list:
    """Ensure all messages are strict dicts with role/content strings to avoid API errors"""
    validated = []
    for msg in messages:
        # Handle dicts
        if isinstance(msg, dict):
            role = str(msg.get("role", "user")).lower()
            content = str(msg.get("content", ""))
            if content:
                validated.append({"role": role, "content": content})
        # Handle Pydantic objects (ConversationMessage)
        elif hasattr(msg, "role") and hasattr(msg, "content"):
            role = str(msg.role).lower()
            content = str(msg.content)
            if content:
                validated.append({"role": role, "content": content})
    return validated

import re
def extract_json_block(text: str) -> dict:
    """Robustly extract a JSON dictionary from a free-text LLM response."""
    # Look for standard markdown JSON blocks
    match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except:
            pass
    
    # Fallback: look for the first { and last }
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except:
            pass
            
    return {}

# SME Financial Insights Cache
SME_INSIGHTS_CACHE = {}

def get_financial_dna(sector: str, sme_size: str) -> dict:
    """Get financial DNA benchmarks (FL, FR, RA, etc.) for SME profile from data"""
    if sme_data is None or not sector or not sme_size:
        return {}
    
    # Try to find numeric codes if labels were passed
    try:
        sector_code = next((k for k, v in SECTOR_MAP.items() if v.lower() == sector.lower()), None)
        size_code = next((k for k, v in SIZE_MAP.items() if v.lower() == sme_size.lower()), None)
    except Exception:
        return {}
    
    if sector_code is None or size_code is None:
        return {}

    cache_key = f"{sector_code}_{size_code}"
    if cache_key in SME_INSIGHTS_CACHE:
        return SME_INSIGHTS_CACHE[cache_key]
    
    try:
        filtered = sme_data[
            (sme_data['Sector'] == sector_code) & 
            (sme_data['SME_Size'] == size_code)
        ]
        
        if len(filtered) == 0:
            return {}
        
        # Calculate scores for DNA domains (averaging 1-5 scales)
        dna = {
            "financial_literacy": float(filtered[[f'FL{i}' for i in range(1, 5)]].mean().mean()),
            "financial_reporting": float(filtered[[f'FR{i}' for i in range(1, 5)]].mean().mean()),
            "risk_attitude": float(filtered[[f'RA{i}' for i in range(1, 5)]].mean().mean()),
            "decision_analysis": float(filtered[[f'MDA{i}' for i in range(1, 5)]].mean().mean()),
            "decision_making": float(filtered[[f'FDM{i}' for i in range(1, 5)]].mean().mean()),
            "financial_awareness": float(filtered[[f'FA{i}' for i in range(1, 5)]].mean().mean()),
            "sample_size": len(filtered)
        }
        
        SME_INSIGHTS_CACHE[cache_key] = dna
        return dna
    except Exception as e:
        print(f"Error calculating DNA: {e}")
        return {}

def search_company_insights(company_name: str, sector: str) -> str:
    """Use Tavily to get real-time insights about a company or sector"""
    try:
        query = f"latest business news and challenges for {company_name} in {sector} sector"
        search_result = tavily_client.search(query=query, search_depth="advanced")
        
        insights = ""
        for result in search_result.get('results', [])[:3]:
            insights += f"- {result['title']}: {result['content'][:200]}...\n"
        
        return insights if insights else "No specific news found."
    except Exception as e:
        print(f"Tavily search error: {e}")
        return "Web search unavailable."

def format_client_context(profile: ClientProfile, web_insights: str = "") -> str:
    """Format client profile and market data for LLM context"""
    context = "### CURRENT CLIENT PROFILE\n"
    if profile.company_name: context += f"- Company: {profile.company_name}\n"
    if profile.sector: context += f"- Sector: {profile.sector}\n"
    if profile.sme_size: context += f"- Size: {profile.sme_size}\n"
    if profile.annual_revenue: context += f"- Revenue: ${profile.annual_revenue:,.0f}\n"
    if profile.pain_points: context += f"- Pain Points: {', '.join(profile.pain_points)}\n"
    if profile.goals: context += f"- Goals: {', '.join(profile.goals)}\n"
    if profile.budget: context += f"- Budget: ${profile.budget:,.0f}\n"
    
    # Add Financial DNA if sector and size are known
    if profile.sector and profile.sme_size:
        dna = get_financial_dna(profile.sector, profile.sme_size)
        if dna:
            context += "\n### MARKET DNA & BENCHMARKS (1-5 Scale)\n"
            context += f"- Financial Literacy: {dna['financial_literacy']:.1f}/5\n"
            context += f"- Risk Attitude (RA): {dna['risk_attitude']:.1f}/5 (Higher = more risk-taking)\n"
            context += f"- Decision Style: {dna['decision_analysis']:.1f} (Analysis) vs {dna['decision_making']:.1f} (Execution)\n"
            context += f"- Representative Sample: Based on {dna['sample_size']} similar firms\n"
    
    if web_insights and web_insights != "No specific news found.":
        context += f"\n### REAL-TIME WEB INSIGHTS\n{web_insights}\n"
    
    return context

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

async def run_agent_step(model: str, system_prompt: str, user_content: str, history: list = None) -> str:
    """Helper to run a single agent step with formatted messages"""
    messages = [{"role": "system", "content": system_prompt}]
    if history:
        for msg in history[-5:]: # Only last 5 for context to save tokens and avoid noise
            messages.append({"role": msg.role, "content": msg.content})
    messages.append({"role": "user", "content": user_content})
    
    response = groq_client.chat.completions.create(
        model=model,
        messages=validate_messages(messages),
        temperature=0.5, # Lower temperature for better reliability
        max_tokens=1024,
    )
    return response.choices[0].message.content

@app.post("/chat", response_model=AgentResponse)
async def chat(request: AgentRequest):
    """
    Multi-Agent Orchestrator: Analyzer -> Validator -> Sales Agent
    """
    try:
        # 1. Global Research & Data Prep
        web_insights = ""
        if request.use_web_search and request.client_profile and request.client_profile.company_name:
            web_insights = search_company_insights(
                request.client_profile.company_name, 
                request.client_profile.sector or "general"
            )
        
        client_context = format_client_context(request.client_profile or ClientProfile(), web_insights)
        
        # 2. STEP 1: ANALYZER (Gating)
        analyzer_input = f"User Input: {request.user_message}\nCurrent Context: {client_context}"
        analyzer_response = await run_agent_step("llama-3.1-8b-instant", ANALYZER_PROMPT, analyzer_input, request.conversation_history)
        
        if "[[[STOP]]]" in analyzer_response:
            return AgentResponse(
                agent_message=analyzer_response.replace("[[[STOP]]]", "").strip(),
                client_profile=request.client_profile,
                recommendations=[],
                next_steps=[],
                trace={"analyzer": analyzer_response, "validator": "Skipped (Gated by Analyzer)"},
                conversation_turn=len(request.conversation_history) // 2 + 1
            )

        # 3. STEP 2: VALIDATOR (Formatting)
        # Feedforward: Validator now receives the Analyzer's approved intent summary
        approved_intent = analyzer_response.replace("[[[PROCEED]]]", "").strip()
        
        try:
            profile_json = request.client_profile.json() if request.client_profile else "{}"
        except AttributeError:
            profile_json = json.dumps(request.client_profile.model_dump()) if request.client_profile else "{}"
            
        validator_input = f"Approved Intent: {approved_intent}\nOriginal Input: {request.user_message}\nCurrent Profile: {profile_json}"
        validator_response = await run_agent_step("llama-3.1-8b-instant", VALIDATOR_PROMPT, validator_input)
        
        validated_data = extract_json_block(validator_response)
        refined_request = validated_data.get("refined_input", request.user_message)

        # 4. STEP 3: SALES AGENT (Expert Response)
        sales_context = f"{client_context}\n\n### VALIDATED SALES CONTEXT\n{validator_response}"
        sales_input = f"User Request: {refined_request}"
        
        # Add JSON extraction instruction for final agent using familiar markdown block
        final_sales_prompt = SALES_PROMPT + "\n\nIMPORTANT: You MUST append a JSON block at the very end of your response inside ```json ... ``` with keys: 'profile_updates' (dict), 'recommendations' (list of strings), 'next_steps' (list of strings)."
        
        final_response_content = await run_agent_step(
            "llama-3.3-70b-versatile", 
            final_sales_prompt + "\n\n" + sales_context, 
            sales_input, 
            request.conversation_history
        )

        # 5. Extraction & Profile Update
        # Hide JSON from user view
        agent_message = re.split(r'```(?:json)?\s*\{', final_response_content, maxsplit=1)[0].strip()
        # Fallback split if they didn't use markdown
        agent_message = re.split(r'\nJSON:', agent_message, flags=re.IGNORECASE)[0].strip()
        
        data = extract_json_block(final_response_content)
        
        recommendations = data.get("recommendations", [])
        next_steps = data.get("next_steps", [])
        # Merge profile updates from both validator and sales agent
        profile_updates = validated_data.get("extracted_data", {})
        if isinstance(profile_updates, dict):
            profile_updates.update(data.get("profile_updates", {}))
        
        if not recommendations or not isinstance(recommendations, list): 
            recommendations = extract_recommendations(agent_message)
        if not next_steps or not isinstance(next_steps, list): 
            next_steps = extract_next_steps(agent_message)
        
        # Robust Profile Validation via Pydantic
        current_profile = request.client_profile or ClientProfile()
        
        # Safe dump to avoid Pydantic serialization errors from corrupted memory
        profile_dict = {}
        # Support both Pydantic V1 and V2 field access
        fields = getattr(current_profile, "model_fields", getattr(current_profile, "__fields__", {}))
        for field in fields:
            profile_dict[field] = getattr(current_profile, field, None)
            
        if profile_updates and isinstance(profile_updates, dict):
            for k, v in profile_updates.items():
                if k in profile_dict and v is not None and str(v).strip():
                    # Type Coercion Safety
                    if k in ["pain_points", "goals"]:
                        if isinstance(v, str):
                            v = [i.strip() for i in v.split(",") if i.strip()]
                        elif not isinstance(v, list):
                            v = [str(v)]
                    elif k in ["annual_revenue", "budget"]:
                        try:
                            v = float(str(v).replace("$", "").replace(",", ""))
                        except ValueError:
                            continue # skip if invalid number
                    # String safety for string fields
                    elif isinstance(v, list) and k not in ["pain_points", "goals"]:
                        v = ", ".join(map(str, v))
                        
                    profile_dict[k] = v
        
        # Create a new validated instance
        try:
            updated_profile = ClientProfile(**profile_dict)
        except Exception as e:
            print(f"Pydantic validation failed, reverting profile: {e}")
            updated_profile = current_profile
        
        return AgentResponse(
            agent_message=agent_message,
            client_profile=updated_profile,
            recommendations=recommendations,
            next_steps=next_steps,
            trace={"analyzer": analyzer_response, "validator": validator_response},
            conversation_turn=len(request.conversation_history) // 2 + 1
        )
        
    except Exception as e:
        print(f"Error in multi-agent chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze-profile")
async def analyze_profile(profile: ClientProfile):
    """
    Analyze a client profile and return insights
    """
    try:
        insights = {
            "qualification_score": calculate_qualification_score(profile),
            "sector_benchmarks": get_sme_insights(profile.sector or "", profile.sme_size or ""),
            "recommended_solutions": generate_solution_recommendations(profile),
            "next_qualification_questions": get_qualification_questions(profile)
        }
        return insights
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def calculate_qualification_score(profile: ClientProfile) -> float:
    """Calculate lead qualification score"""
    score = 0
    weights = {
        'company_name': 10,
        'sector': 15,
        'sme_size': 10,
        'annual_revenue': 15,
        'pain_points': 20,
        'goals': 20,
        'budget': 10,
    }
    
    for field, weight in weights.items():
        if getattr(profile, field, None):
            score += weight
    
    return min(score, 100)

def extract_recommendations(message: str) -> list:
    """Extract recommendations from agent message"""
    recommendations = []
    lines = message.split('\n')
    in_recommendations = False
    
    for line in lines:
        if 'recommend' in line.lower() or 'suggest' in line.lower():
            in_recommendations = True
        if in_recommendations and line.strip().startswith(('-', '•', '*')):
            recommendations.append(line.strip()[1:].strip())
    
    return recommendations[:5]  # Return top 5

def extract_next_steps(message: str) -> list:
    """Extract next steps from agent message"""
    next_steps = []
    lines = message.split('\n')
    in_next_steps = False
    
    for line in lines:
        if 'next step' in line.lower() or 'action item' in line.lower():
            in_next_steps = True
        if in_next_steps and line.strip().startswith(('-', '•', '*')):
            next_steps.append(line.strip()[1:].strip())
    
    return next_steps[:5]

def generate_solution_recommendations(profile: ClientProfile) -> list:
    """Generate solution recommendations based on profile"""
    recommendations = []
    
    if profile.sector and profile.pain_points:
        sector = profile.sector.lower()
        pain_points = [p.lower() for p in profile.pain_points]
        
        solution_map = {
            'healthcare': {
                'efficiency': 'Practice Management System',
                'data': 'Healthcare Analytics Platform',
                'compliance': 'Compliance Management Suite',
            },
            'technology': {
                'scaling': 'Cloud Infrastructure Solution',
                'development': 'DevOps Platform',
                'security': 'Cybersecurity Suite',
            },
            'services': {
                'scheduling': 'Resource Management System',
                'billing': 'Invoicing & Billing Platform',
                'communication': 'Client Communication Tool',
            },
            'agriculture': {
                'yield': 'Agricultural Analytics',
                'supply_chain': 'Supply Chain Management',
                'data': 'IoT Monitoring System',
            },
            'construction': {
                'project': 'Project Management Tool',
                'safety': 'Safety Compliance System',
                'cost': 'Cost Management Software',
            }
        }
        
        sector_solutions = solution_map.get(sector, {})
        for pain, solution in sector_solutions.items():
            if any(pain in pp for pp in pain_points):
                recommendations.append(solution)
    
    return recommendations[:5]

def get_qualification_questions(profile: ClientProfile) -> list:
    """Get next qualification questions based on profile gaps"""
    questions = []
    
    if not profile.company_name:
        questions.append("What's the name of your company?")
    if not profile.sector:
        questions.append("What sector does your business operate in?")
    if not profile.sme_size:
        questions.append("How many employees do you have?")
    if not profile.pain_points:
        questions.append("What are the biggest challenges your business faces today?")
    if not profile.goals:
        questions.append("What are your top 3 business goals for the next 12 months?")
    if not profile.budget:
        questions.append("Do you have a budget allocated for solutions in this area?")
    if not profile.decision_timeline:
        questions.append("What's your timeline for making a decision?")
    
    return questions[:3]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)