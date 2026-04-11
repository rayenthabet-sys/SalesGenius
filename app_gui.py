import gradio as gr
import json
import os
from sales_agent import (
    chat, AgentRequest, ConversationMessage, ClientProfile, 
    SECTOR_MAP, SIZE_MAP, get_financial_dna
)
from dotenv import load_dotenv

load_dotenv()

# Global state for the session
class UIState:
    def __init__(self):
        self.history = []
        self.profile = ClientProfile()
        self.recommendations = []
        self.next_steps = []

state = UIState()

def reset_chat():
    state.history = []
    state.profile = ClientProfile()
    state.recommendations = []
    state.next_steps = []
    return [], "", "No insights yet.", "None", "None", "### 🔍 Agent Trace\nNo logic processed yet."

async def process_chat(message, history, company_name, sector, size, use_search):
    if not message:
        return "", history, "Please enter a message.", "{}", "None", "No message."
        
    # Update initial profile from UI inputs
    state.profile.company_name = company_name
    state.profile.sector = sector
    state.profile.sme_size = size
    
    # Convert Gradio history to API history models and normalize to dicts
    conv_history = []
    normalized_history = []
    for msg in history:
        role = ""
        content = ""
        if isinstance(msg, dict):
            normalized_history.append({
                "role": str(msg.get("role", "user")),
                "content": str(msg.get("content", ""))
            })
        elif hasattr(msg, "role") and hasattr(msg, "content"):
            normalized_history.append({
                "role": str(msg.role),
                "content": str(msg.content)
            })
            
        if normalized_history and normalized_history[-1].get("role") and normalized_history[-1].get("content"):
            conv_history.append(ConversationMessage(role=normalized_history[-1]["role"], content=normalized_history[-1]["content"]))
    
    # Use normalized history for consistency
    history = normalized_history
    
    # Create request
    request = AgentRequest(
        user_message=message,
        conversation_history=conv_history,
        client_profile=state.profile,
        use_web_search=use_search
    )
    
    # Call the chat logic directly (with await)
    try:
        response = await chat(request)
        
        # Update state
        state.profile = response.client_profile or ClientProfile()
        state.recommendations = response.recommendations
        state.next_steps = response.next_steps
        
        # Format metadata for display safely without triggering Pydantic validation errors
        profile_dict = {}
        fields = getattr(state.profile, "model_fields", getattr(state.profile, "__fields__", {}))
        for field in fields:
            profile_dict[field] = getattr(state.profile, field, None)
            
        profile_json = json.dumps(profile_dict, indent=2)
        recommendations_str = "### 💡 Recommendations\n" + "\n".join([f"- {r}" for r in state.recommendations]) if state.recommendations else "### 💡 Recommendations\nNone"
        
        # Calculate DNA for the panel
        dna_str = "No benchmarks available."
        if sector and size:
            dna = get_financial_dna(sector, size)
            if dna:
                dna_str = (
                    f"📊 **Financial DNA Benchmarks**\n"
                    f"- Literacy: {dna['financial_literacy']:.1f}/5\n"
                    f"- Risk Attitude (RA): {dna['risk_attitude']:.1f}/5\n"
                    f"- Decision Execution: {dna['decision_making']:.1f}/5\n"
                    f"*(Based on {dna['sample_size']} similar firms)*"
                )

        new_history = history + [
            {"role": "user", "content": message},
            {"role": "assistant", "content": response.agent_message}
        ]
        
        # Format Trace
        trace = response.trace or {}
        trace_str = (
            f"### 🛡️ Analyzer (Gatekeeper)\n{trace.get('analyzer', 'N/A')}\n\n"
            f"### 📝 Validator (Strategist)\n{trace.get('validator', 'N/A')}"
        )
        
        return "", new_history, dna_str, profile_json, recommendations_str, trace_str
    except Exception as e:
        error_msg = f"⚠️ **Error:** {str(e)}"
        new_history = history + [
            {"role": "user", "content": message},
            {"role": "assistant", "content": error_msg}
        ]
        return "", new_history, "Error loading benchmarks.", "{}", "Error", f"Error: {e}"

# Define Interface
with gr.Blocks(title="Sales Intelligence Agent") as demo:
    gr.Markdown("# SalesGenius Intelligence Agent")
    gr.Markdown("Engage with prospects, qualify needs, and view data-backed 'Financial DNA' insights.")
    
    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### 🏢 Prospect Details")
            company_input = gr.Textbox(label="Company Name", placeholder="e.g. TechFlow Solutions")
            sector_input = gr.Dropdown(label="Sector", choices=list(SECTOR_MAP.values()))
            size_input = gr.Dropdown(label="Company Size", choices=list(SIZE_MAP.values()))
            use_search = gr.Checkbox(label="Use Web Search (Tavily)", value=True)
            
            dna_panel = gr.Markdown("📊 **Financial DNA Benchmarks**\n*Select sector and size to see benchmarks*")
            reset_btn = gr.Button("Reset Conversation", variant="secondary")

        with gr.Column(scale=2):
            chatbot = gr.Chatbot(label="SalesGenius Chat", height=500)
            msg = gr.Textbox(label="Your Message", placeholder="Type your response here...", show_label=False)
        
        with gr.Column(scale=1):
            gr.Markdown("### 🔍 Live Intel")
            profile_display = gr.Code(label="Dynamic Client Profile", language="json", interactive=False)
            recs_display = gr.Markdown("### 💡 Recommendations\nNone")
            
            with gr.Accordion("🕵️ Behind the Scenes (Intelligence Trace)", open=False):
                trace_display = gr.Markdown("### 🔍 Agent Trace\nNo logic processed yet.")

    # Connect components
    msg.submit(process_chat, [msg, chatbot, company_input, sector_input, size_input, use_search], 
               [msg, chatbot, dna_panel, profile_display, recs_display, trace_display])
    
    reset_btn.click(reset_chat, None, [chatbot, msg, dna_panel, profile_display, recs_display, trace_display])

if __name__ == "__main__":
    demo.launch(theme=gr.themes.Soft(), share=True)
