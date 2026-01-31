# agent_langgraph.py - The healing agent using LangGraph
from typing import TypedDict, Annotated, List, Dict
from langgraph.graph import StateGraph, END
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage
from collections import defaultdict
import json

# Define the agent's state (what it remembers during the workflow)
class AgentState(TypedDict):
    signals: List[Dict]  # Input: merchant errors
    grouped_patterns: Dict[str, List[Dict]]  # After observation
    analyzed_issues: List[Dict]  # After reasoning
    decisions: List[Dict]  # After decision-making
    current_step: str  # Track where we are

# Initialize the local Llama model
llm = ChatOllama(
    model="llama3.1:8b",  # Change to llama3.1:8b for better quality
    temperature=0.3,  # Lower = more consistent
)

# Step 1: OBSERVE - Group similar errors
def observe_node(state: AgentState) -> AgentState:
    """Groups similar error patterns together"""
    print("\n🔍 OBSERVE: Analyzing incoming signals...")
    
    signals = state["signals"]
    grouped = defaultdict(list)
    
    for signal in signals:
        # Group by error message (in production, use embedding similarity)
        key = signal['message']
        grouped[key].append(signal)
    
    state["grouped_patterns"] = dict(grouped)
    state["current_step"] = "observed"
    
    print(f"   Found {len(grouped)} unique error patterns")
    return state

# Step 2: REASON - Use LLM to analyze each pattern
def reason_node(state: AgentState) -> AgentState:
    """Uses Llama to analyze root causes"""
    print("\n🧠 REASON: Analyzing patterns with Llama...")
    
    analyzed = []
    
    for error_msg, occurrences in state["grouped_patterns"].items():
        # Skip single occurrences for demo
        if len(occurrences) < 2:
            continue
        
        # Build context for Llama
        merchant_ids = [s['merchant_id'] for s in occurrences]
        
        prompt = f"""You are analyzing errors during an e-commerce platform migration.

ERROR PATTERN:
- Message: {error_msg}
- Affected merchants: {len(occurrences)}
- Merchant IDs: {merchant_ids}

Analyze this pattern and provide:
1. ROOT CAUSE (merchant config / platform bug / external service / migration issue)
2. CONFIDENCE (0-100%)
3. RECOMMENDED ACTION (specific action to take)
4. RISK LEVEL (low / medium / high)
5. REASONING (brief explanation)

Format your response EXACTLY like this:
ROOT_CAUSE: [your answer]
CONFIDENCE: [number]%
RECOMMENDED_ACTION: [specific action]
RISK_LEVEL: [low/medium/high]
REASONING: [1-2 sentences]
"""
        
        # Call local Llama model
        messages = [
            SystemMessage(content="You are a technical support AI analyzing e-commerce platform issues."),
            HumanMessage(content=prompt)
        ]
        
        print(f"   Analyzing: '{error_msg[:50]}...' ({len(occurrences)} occurrences)")
        response = llm.invoke(messages)
        
        analyzed.append({
            "error_pattern": error_msg,
            "affected_count": len(occurrences),
            "merchants": merchant_ids,
            "analysis": response.content,
            "status": "pending_review"
        })
    
    state["analyzed_issues"] = analyzed
    state["current_step"] = "reasoned"
    
    print(f"   Completed analysis of {len(analyzed)} patterns")
    return state

# Step 3: DECIDE - Categorize actions by risk
def decide_node(state: AgentState) -> AgentState:
    """Decides which actions need human approval"""
    print("\n⚖️  DECIDE: Categorizing actions by risk...")
    
    decisions = []
    
    for issue in state["analyzed_issues"]:
        analysis = issue['analysis'].lower()
        
        # Parse risk level from LLM response
        if "risk_level: low" in analysis or "risk level: low" in analysis:
            decision_type = "auto_execute"
            action_detail = "Send proactive email to affected merchants"
        elif "risk_level: medium" in analysis or "risk level: medium" in analysis:
            decision_type = "needs_approval"
            action_detail = "Update documentation and notify support team"
        else:
            decision_type = "escalate"
            action_detail = "Escalate to engineering for investigation"
        
        decisions.append({
            **issue,
            "decision": decision_type,
            "action_detail": action_detail
        })
        
        print(f"   Pattern: {issue['error_pattern'][:40]}... → {decision_type}")
    
    state["decisions"] = decisions
    state["current_step"] = "decided"
    return state

# Step 4: ACT - Execute or prepare actions
def act_node(state: AgentState) -> AgentState:
    """Executes approved actions or prepares them for human review"""
    print("\n✅ ACT: Preparing actions...")
    
    for decision in state["decisions"]:
        if decision["decision"] == "auto_execute":
            print(f"   ✉️  AUTO: Sending email to {decision['affected_count']} merchants")
        elif decision["decision"] == "needs_approval":
            print(f"   ⏳ PENDING: Action requires human approval")
        else:
            print(f"   🚨 ESCALATED: Engineering review needed")
    
    state["current_step"] = "completed"
    return state

# Build the LangGraph workflow
def create_agent():
    """Creates the LangGraph agent workflow"""
    workflow = StateGraph(AgentState)
    
    # Add nodes (steps in the agent loop)
    workflow.add_node("observe", observe_node)
    workflow.add_node("reason", reason_node)
    workflow.add_node("decide", decide_node)
    workflow.add_node("act", act_node)
    
    # Define the flow: observe → reason → decide → act → end
    workflow.set_entry_point("observe")
    workflow.add_edge("observe", "reason")
    workflow.add_edge("reason", "decide")
    workflow.add_edge("decide", "act")
    workflow.add_edge("act", END)
    
    return workflow.compile()

# Main execution
class HealingAgent:
    def __init__(self):
        self.graph = create_agent()
    
    def run(self, signals):
        """Runs the complete agent workflow"""
        print("\n" + "="*60)
        print("🤖 SELF-HEALING AGENT STARTING")
        print("="*60)
        
        # Initial state
        initial_state = {
            "signals": signals,
            "grouped_patterns": {},
            "analyzed_issues": [],
            "decisions": [],
            "current_step": "initializing"
        }
        
        # Run the graph
        final_state = self.graph.invoke(initial_state)
        
        print("\n" + "="*60)
        print("🎉 AGENT WORKFLOW COMPLETED")
        print("="*60)
        
        return final_state["decisions"]

# Test the agent
if __name__ == "__main__":
    from fake_data import MOCK_SIGNALS
    
    agent = HealingAgent()
    decisions = agent.run(MOCK_SIGNALS)
    
    # Print results
    print("\n📊 FINAL DECISIONS:")
    for i, d in enumerate(decisions, 1):
        print(f"\n--- Issue #{i} ---")
        print(f"Pattern: {d['error_pattern']}")
        print(f"Affected: {d['affected_count']} merchants")
        print(f"Decision: {d['decision']}")
        print(f"Action: {d['action_detail']}")
        print(f"\nFull Analysis:\n{d['analysis']}")