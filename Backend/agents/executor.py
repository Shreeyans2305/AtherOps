# agents/executor.py - Executes approved actions
from models.schemas import ActionPlan, ExecutionResult
from datetime import datetime
import uuid
from typing import Dict

class ExecutorAgent:
    """Executes actions with external integrations"""
    
    def __init__(self):
        # In production, initialize real integrations
        self.slack_client = None
        self.email_service = None
        self.jira_client = None
    
    async def execute(self, plan: ActionPlan, approved: bool = False) -> ExecutionResult:
        """
        Execute action plan (if approved or auto-executable)
        """
        if plan.requires_approval and not approved:
            return ExecutionResult(
                execution_id=str(uuid.uuid4()),
                plan_id=plan.plan_id,
                status="pending_approval",
                result_details={"message": "Awaiting human approval"}
            )
        
        # Route to appropriate executor
        try:
            if plan.action_type == "merchant_communication":
                result = await self._send_merchant_emails(plan)
            elif plan.action_type == "engineering_escalation":
                result = await self._create_jira_ticket(plan)
            elif plan.action_type == "support_guidance":
                result = await self._post_to_slack(plan)
            elif plan.action_type == "documentation_update":
                result = await self._update_docs(plan)
            else:
                result = {"message": "Action type not implemented"}
            
            return ExecutionResult(
                execution_id=str(uuid.uuid4()),
                plan_id=plan.plan_id,
                status="success",
                executed_at=datetime.now(),
                result_details=result
            )
        
        except Exception as e:
            return ExecutionResult(
                execution_id=str(uuid.uuid4()),
                plan_id=plan.plan_id,
                status="failed",
                executed_at=datetime.now(),
                error=str(e)
            )
    
    async def _send_merchant_emails(self, plan: ActionPlan) -> Dict:
        """Send emails to affected merchants"""
        # In production: integrate with SendGrid/SES
        details = plan.action_details
        recipients = details.get("recipients", [])
        
        print(f"📧 [SIMULATION] Sending email to {len(recipients)} merchants")
        print(f"   Subject: {details.get('subject')}")
        print(f"   Body preview: {details.get('body')[:100]}...")
        
        return {
            "emails_sent": len(recipients),
            "recipients": recipients,
            "subject": details.get("subject")
        }
    
    async def _create_jira_ticket(self, plan: ActionPlan) -> Dict:
        """Create Jira ticket for engineering"""
        # In production: use Jira API
        details = plan.action_details
        
        print(f"🎫 [SIMULATION] Creating Jira ticket")
        print(f"   Title: {details.get('title')}")
        print(f"   Affected: {details.get('affected_count')} merchants")
        
        return {
            "ticket_id": f"PLAT-{uuid.uuid4().hex[:6].upper()}",
            "title": details.get("title"),
            "priority": plan.priority
        }
    
    async def _post_to_slack(self, plan: ActionPlan) -> Dict:
        """Post guidance to Slack"""
        # In production: use Slack API
        details = plan.action_details
        
        print(f"💬 [SIMULATION] Posting to Slack #support")
        print(f"   Message: {details.get('guidance')}")
        
        return {
            "channel": "#support",
            "message": details.get("guidance")
        }
    
    async def _update_docs(self, plan: ActionPlan) -> Dict:
        """Update documentation (placeholder)"""
        print(f"📝 [SIMULATION] Documentation update queued")
        
        return {
            "status": "queued",
            "type": "documentation_update"
        }