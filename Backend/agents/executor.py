# agents/executor.py - Executes approved actions
from models.schemas import ActionPlan, ExecutionResult
from services.email_service import email_service, EmailMessage, EmailPriority
from datetime import datetime
import uuid
from typing import Dict

class ExecutorAgent:
    """Executes actions with external integrations"""
    
    def __init__(self):
        # In production, initialize real integrations
        self.slack_client = None
        self.jira_client = None
        
        # Email service is now a real integration
        self.email_service = email_service
    
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
        details = plan.action_details
        recipients = details.get("recipients", [])
        
        # Send real emails whenever email service is configured
        if self.email_service.is_configured():
            print(f"📧 Sending REAL merchant notification emails...")
            
            # Build recipient list - we need actual email addresses
            merchant_emails = []
            for merchant_id in recipients:
                # Check if metadata contains merchant email
                merchant_email = details.get("merchant_emails", {}).get(merchant_id)
                if merchant_email:
                    merchant_emails.append(merchant_email)
            
            # Determine if this is critical (for email priority and engineer notification)
            is_critical = plan.priority in ["critical", "high"] and plan.risk_level == "high"
            
            if merchant_emails:
                # Send to merchant(s)
                if is_critical:
                    # Critical: send to merchants AND engineers
                    result = await self.email_service.send_critical_alert(
                        subject=details.get('subject', 'Issue Detected'),
                        body=details.get('body', 'An issue has been detected.'),
                        merchant_email=merchant_emails[0] if merchant_emails else None,
                        include_default_engineers=True
                    )
                else:
                    # Non-critical: send only to merchants
                    from services.email_service import EmailMessage, EmailPriority
                    
                    priority_map = {
                        "low": EmailPriority.LOW,
                        "medium": EmailPriority.NORMAL,
                        "high": EmailPriority.HIGH,
                        "critical": EmailPriority.CRITICAL
                    }
                    
                    message = EmailMessage(
                        to=merchant_emails,
                        subject=details.get('subject', 'Notification from AtherOps'),
                        body=details.get('body', 'You have a notification.'),
                        priority=priority_map.get(plan.priority, EmailPriority.NORMAL)
                    )
                    
                    result = await self.email_service.send_email(message)
                
                return {
                    "emails_sent": len(merchant_emails),
                    "recipients": merchant_emails,
                    "subject": details.get("subject"),
                    "real_email": True,
                    "email_result": result
                }
            else:
                print(f"   ⚠️  No merchant email addresses found in action_details['merchant_emails']")
                print(f"   ℹ️  Recipients (merchant IDs): {recipients}")
                return {
                    "emails_sent": 0,
                    "recipients": recipients,
                    "subject": details.get("subject"),
                    "real_email": False,
                    "error": "No merchant email addresses provided"
                }
        
        # Email service not configured - simulate
        print(f"📧 [SIMULATION] Sending email to {len(recipients)} merchants")
        print(f"   Subject: {details.get('subject')}")
        print(f"   Body preview: {details.get('body')[:100]}...")
        print(f"   ⚠️  To send real emails, configure SMTP_EMAIL and SMTP_PASSWORD in .env")
        
        return {
            "emails_sent": len(recipients),
            "recipients": recipients,
            "subject": details.get("subject"),
            "real_email": False,
            "simulated": True
        }
    
    async def _create_jira_ticket(self, plan: ActionPlan) -> Dict:
        """Create Jira ticket for engineering - also sends email for critical issues"""
        details = plan.action_details
        
        # For critical/high risk issues, send actual email to engineers
        is_critical = plan.priority in ["critical", "high"] and plan.risk_level == "high"
        
        print(f"   📊 Decision check: priority={plan.priority}, risk={plan.risk_level}, is_critical={is_critical}")
        print(f"   📧 Email configured: {self.email_service.is_configured()}")
        print(f"   📧 Engineer emails: {self.email_service.default_engineer_emails}")
        
        email_result = None
        if is_critical and self.email_service.is_configured():
            print(f"📧 Sending REAL engineering escalation email...")
            
            email_result = await self.email_service.send_engineering_escalation(
                subject=details.get('title', 'Engineering Escalation'),
                body=details.get('description', ''),
                severity=plan.priority,
                affected_merchants=details.get('affected_count', 0),
                additional_context={
                    "confidence": details.get("confidence"),
                    "evidence": details.get("evidence", [])[:3],  # Limit evidence items
                    "risk_level": plan.risk_level,
                }
            )
            print(f"   📧 Email result: {email_result}")
        elif is_critical:
            print(f"⚠️  Critical issue but email not configured. Set SMTP_EMAIL and SMTP_PASSWORD env vars.")
        else:
            print(f"   ℹ️  Not sending email: is_critical={is_critical}")
        
        print(f"🎫 [SIMULATION] Creating Jira ticket")
        print(f"   Title: {details.get('title')}")
        print(f"   Affected: {details.get('affected_count')} merchants")
        
        ticket_id = f"PLAT-{uuid.uuid4().hex[:6].upper()}"
        
        return {
            "ticket_id": ticket_id,
            "title": details.get("title"),
            "priority": plan.priority,
            "email_sent": email_result is not None,
            "email_result": email_result
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