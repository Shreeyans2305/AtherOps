# services/email_service.py - Email service using smtplib
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional, Dict
from dataclasses import dataclass
import os
from enum import Enum

# Load environment variables early - before any config is read
from dotenv import load_dotenv
load_dotenv()


class EmailPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class EmailConfig:
    """Email configuration - can be loaded from environment variables"""
    smtp_server: str
    smtp_port: int
    sender_email: str
    sender_password: str
    use_tls: bool = True
    use_ssl: bool = False
    
    @classmethod
    def from_env(cls) -> 'EmailConfig':
        """Load configuration from environment variables"""
        config = cls(
            smtp_server=os.getenv("SMTP_SERVER", "smtp.gmail.com"),
            smtp_port=int(os.getenv("SMTP_PORT", "587")),
            sender_email=os.getenv("SMTP_EMAIL", ""),
            sender_password=os.getenv("SMTP_PASSWORD", ""),
            use_tls=os.getenv("SMTP_USE_TLS", "true").lower() == "true",
            use_ssl=os.getenv("SMTP_USE_SSL", "false").lower() == "true",
        )
        # Debug: print config status
        if config.sender_email:
            print(f"📧 Email config loaded: {config.sender_email[:3]}***@{config.sender_email.split('@')[1] if '@' in config.sender_email else '...'}")
        else:
            print("⚠️  Email config: SMTP_EMAIL not set")
        return config


@dataclass
class EmailMessage:
    """Email message structure"""
    to: List[str]
    subject: str
    body: str
    cc: Optional[List[str]] = None
    bcc: Optional[List[str]] = None
    priority: EmailPriority = EmailPriority.NORMAL
    is_html: bool = False
    reply_to: Optional[str] = None


class EmailService:
    """
    Email service for sending notifications.
    Uses smtplib for actual email delivery.
    """
    
    def __init__(self, config: Optional[EmailConfig] = None):
        self.config = config or EmailConfig.from_env()
        self._is_configured = bool(self.config.sender_email and self.config.sender_password)
        
        # Default recipients for critical alerts
        self.default_engineer_emails: List[str] = []
        self.default_merchant_support_email: Optional[str] = None
        
        # Load from environment
        engineer_emails = os.getenv("ENGINEER_EMAILS", "")
        if engineer_emails:
            self.default_engineer_emails = [e.strip() for e in engineer_emails.split(",")]
        
        self.default_merchant_support_email = os.getenv("MERCHANT_SUPPORT_EMAIL")
    
    def is_configured(self) -> bool:
        """Check if email service is properly configured"""
        return self._is_configured
    
    def set_engineer_emails(self, emails: List[str]):
        """Set default engineer email addresses for escalations"""
        self.default_engineer_emails = emails
    
    def set_merchant_support_email(self, email: str):
        """Set default merchant support email"""
        self.default_merchant_support_email = email
    
    async def send_email(self, message: EmailMessage) -> Dict:
        """
        Send an email using smtplib.
        Returns a dict with status and details.
        """
        if not self._is_configured:
            print("⚠️  Email service not configured. Set SMTP_EMAIL and SMTP_PASSWORD environment variables.")
            return {
                "success": False,
                "error": "Email service not configured",
                "simulated": True,
                "recipients": message.to,
                "subject": message.subject
            }
        
        try:
            # Create the email
            msg = MIMEMultipart("alternative")
            msg["Subject"] = message.subject
            msg["From"] = self.config.sender_email
            msg["To"] = ", ".join(message.to)
            
            if message.cc:
                msg["Cc"] = ", ".join(message.cc)
            
            if message.reply_to:
                msg["Reply-To"] = message.reply_to
            
            # Set priority headers
            if message.priority == EmailPriority.HIGH:
                msg["X-Priority"] = "2"
                msg["X-MSMail-Priority"] = "High"
            elif message.priority == EmailPriority.CRITICAL:
                msg["X-Priority"] = "1"
                msg["X-MSMail-Priority"] = "High"
                msg["Importance"] = "High"
            
            # Create body
            if message.is_html:
                part = MIMEText(message.body, "html")
            else:
                part = MIMEText(message.body, "plain")
            
            msg.attach(part)
            
            # Calculate all recipients
            all_recipients = list(message.to)
            if message.cc:
                all_recipients.extend(message.cc)
            if message.bcc:
                all_recipients.extend(message.bcc)
            
            # Send the email
            context = ssl.create_default_context()
            
            if self.config.use_ssl:
                # Use SSL from the start (port 465)
                with smtplib.SMTP_SSL(
                    self.config.smtp_server, 
                    self.config.smtp_port, 
                    context=context
                ) as server:
                    server.login(self.config.sender_email, self.config.sender_password)
                    server.sendmail(
                        self.config.sender_email,
                        all_recipients,
                        msg.as_string()
                    )
            else:
                # Use STARTTLS (port 587)
                with smtplib.SMTP(self.config.smtp_server, self.config.smtp_port) as server:
                    if self.config.use_tls:
                        server.starttls(context=context)
                    server.login(self.config.sender_email, self.config.sender_password)
                    server.sendmail(
                        self.config.sender_email,
                        all_recipients,
                        msg.as_string()
                    )
            
            print(f"📧 Email sent successfully to {len(all_recipients)} recipient(s)")
            print(f"   Subject: {message.subject}")
            
            return {
                "success": True,
                "recipients": all_recipients,
                "subject": message.subject,
                "simulated": False
            }
            
        except smtplib.SMTPAuthenticationError as e:
            print(f"❌ SMTP Authentication failed: {e}")
            return {
                "success": False,
                "error": f"Authentication failed: {str(e)}",
                "simulated": False
            }
        except smtplib.SMTPException as e:
            print(f"❌ SMTP error: {e}")
            return {
                "success": False,
                "error": f"SMTP error: {str(e)}",
                "simulated": False
            }
        except Exception as e:
            print(f"❌ Failed to send email: {e}")
            return {
                "success": False,
                "error": str(e),
                "simulated": False
            }
    
    async def send_critical_alert(
        self,
        subject: str,
        body: str,
        merchant_email: Optional[str] = None,
        engineer_emails: Optional[List[str]] = None,
        include_default_engineers: bool = True
    ) -> Dict:
        """
        Send a critical alert to merchants and/or engineers.
        This is specifically for HIGH risk, CRITICAL priority issues.
        """
        recipients = []
        
        # Add merchant email if provided
        if merchant_email:
            recipients.append(merchant_email)
        
        # Add specified engineer emails
        if engineer_emails:
            recipients.extend(engineer_emails)
        
        # Add default engineer emails
        if include_default_engineers and self.default_engineer_emails:
            for email in self.default_engineer_emails:
                if email not in recipients:
                    recipients.append(email)
        
        if not recipients:
            print("⚠️  No recipients specified for critical alert")
            return {
                "success": False,
                "error": "No recipients specified"
            }
        
        # Format the critical alert
        critical_subject = f"🚨 CRITICAL ALERT: {subject}"
        
        critical_body = f"""
╔══════════════════════════════════════════════════════════════╗
║                    🚨 CRITICAL ALERT 🚨                      ║
╚══════════════════════════════════════════════════════════════╝

{body}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
This is an automated alert from the AtherOps Healing System.
Priority: CRITICAL | Risk Level: HIGH
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        
        message = EmailMessage(
            to=recipients,
            subject=critical_subject,
            body=critical_body,
            priority=EmailPriority.CRITICAL
        )
        
        result = await self.send_email(message)
        result["alert_type"] = "critical"
        result["recipients_count"] = len(recipients)
        
        return result
    
    async def send_merchant_notification(
        self,
        merchant_email: str,
        subject: str,
        body: str,
        priority: EmailPriority = EmailPriority.NORMAL
    ) -> Dict:
        """Send a notification to a specific merchant"""
        message = EmailMessage(
            to=[merchant_email],
            subject=subject,
            body=body,
            priority=priority
        )
        
        return await self.send_email(message)
    
    async def send_engineering_escalation(
        self,
        subject: str,
        body: str,
        severity: str = "high",
        affected_merchants: int = 0,
        additional_context: Optional[Dict] = None
    ) -> Dict:
        """
        Send an engineering escalation email.
        Used for platform bugs and issues requiring engineering attention.
        """
        if not self.default_engineer_emails:
            print("⚠️  No engineer emails configured for escalation")
            return {
                "success": False,
                "error": "No engineer emails configured"
            }
        
        escalation_body = f"""
Engineering Escalation Alert
============================

Severity: {severity.upper()}
Affected Merchants: {affected_merchants}

Issue Details:
{body}

"""
        
        if additional_context:
            escalation_body += "\nAdditional Context:\n"
            for key, value in additional_context.items():
                escalation_body += f"  - {key}: {value}\n"
        
        escalation_body += """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Automated escalation from AtherOps Healing System
"""
        
        message = EmailMessage(
            to=self.default_engineer_emails,
            subject=f"[ESCALATION] {subject}",
            body=escalation_body,
            priority=EmailPriority.HIGH if severity in ["high", "critical"] else EmailPriority.NORMAL
        )
        
        return await self.send_email(message)


# Global email service instance
email_service = EmailService()
