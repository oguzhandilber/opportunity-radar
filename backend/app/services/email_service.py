"""Email service for sending alerts and notifications."""

import logging
from datetime import datetime, timezone
from typing import List, Optional
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Template

from app.config import get_settings
from app.database import Opportunity

logger = logging.getLogger(__name__)

settings = get_settings()


# Email templates
OPPORTUNITY_ALERT_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px 10px 0 0; }
        .content { background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }
        .opportunity { background: white; padding: 20px; margin: 20px 0; border-radius: 8px; border-left: 4px solid #667eea; }
        .score { font-size: 24px; font-weight: bold; color: #667eea; }
        .score-label { font-size: 12px; color: #666; text-transform: uppercase; }
        .btn { display: inline-block; background: #667eea; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; margin-top: 15px; }
        .footer { text-align: center; margin-top: 30px; font-size: 12px; color: #999; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎯 New High-Value Opportunity Alert</h1>
            <p>Based on your alert criteria</p>
        </div>
        <div class="content">
            <div class="opportunity">
                <h2>{{ opportunity.title }}</h2>
                <p>{{ opportunity.summary[:200] }}{% if opportunity.summary|length > 200 %}...{% endif %}</p>
                
                <div style="display: flex; gap: 20px; margin: 20px 0;">
                    <div>
                        <div class="score-label">Total Score</div>
                        <div class="score">{{ "%.1f"|format(opportunity.total_score) }}/10</div>
                    </div>
                    <div>
                        <div class="score-label">Sector</div>
                        <div style="font-size: 18px; font-weight: bold;">{{ opportunity.sector or "Unknown" }}</div>
                    </div>
                    <div>
                        <div class="score-label">Source</div>
                        <div style="font-size: 18px; font-weight: bold;">{{ opportunity.source or "Internal" }}</div>
                    </div>
                </div>
                
                <a href="https://opportunityradar.io/opportunities/{{ opportunity.id }}" class="btn">View Full Analysis</a>
            </div>
            
            <div class="footer">
                <p>You're receiving this because you set up an alert for high-value opportunities.</p>
                <p><a href="https://opportunityradar.io/alerts">Manage your alerts</a> | <a href="https://opportunityradar.io/unsubscribe">Unsubscribe</a></p>
            </div>
        </div>
    </div>
</body>
</html>
"""

DAILY_DIGEST_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px 10px 0 0; }
        .content { background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }
        .opportunity { background: white; padding: 15px; margin: 10px 0; border-radius: 8px; border-left: 4px solid #667eea; }
        .score { font-size: 20px; font-weight: bold; color: #667eea; }
        .btn { display: inline-block; background: #667eea; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin-top: 10px; }
        .footer { text-align: center; margin-top: 30px; font-size: 12px; color: #999; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Daily Opportunity Digest</h1>
            <p>{{ date.strftime('%B %d, %Y') }}</p>
        </div>
        <div class="content">
            <p>Found {{ opportunities|length }} new opportunities matching your saved searches.</p>
            
            {% for opp in opportunities[:5] %}
            <div class="opportunity">
                <h3>{{ opp.title }}</h3>
                <p>{{ opp.summary[:150] }}{% if opp.summary|length > 150 %}...{% endif %}</p>
                <div style="display: flex; gap: 15px; align-items: center;">
                    <span class="score">{{ "%.1f"|format(opp.total_score) }}/10</span>
                    <span>{{ opp.sector or "Unknown" }}</span>
                </div>
                <a href="https://opportunityradar.io/opportunities/{{ opp.id }}" class="btn">View Details</a>
            </div>
            {% endfor %}
            
            {% if opportunities|length > 5 %}
            <div style="text-align: center; margin: 20px 0;">
                <a href="https://opportunityradar.io/dashboard" class="btn">View All {{ opportunities|length }} Opportunities</a>
            </div>
            {% endif %}
            
            <div class="footer">
                <p><a href="https://opportunityradar.io/saved-searches">Manage your saved searches</a></p>
            </div>
        </div>
    </div>
</body>
</html>
"""


class EmailService:
    """Service for sending email notifications."""

    def __init__(self):
        self.smtp_host = settings.smtp_host
        self.smtp_port = settings.smtp_port
        self.smtp_user = settings.smtp_user
        self.smtp_password = settings.smtp_password
        self.from_email = settings.smtp_from_email
        self.from_name = settings.smtp_from_name

    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
    ) -> bool:
        """Send an email to a recipient."""
        if not all([self.smtp_host, self.smtp_user, self.smtp_password]):
            logger.warning("SMTP not configured, skipping email send")
            return False

        try:
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = f"{self.from_name} <{self.from_email}>"
            message["To"] = to_email

            # Add text part
            if text_content:
                message.attach(MIMEText(text_content, "plain"))

            # Add HTML part
            message.attach(MIMEText(html_content, "html"))

            # Send email
            await aiosmtplib.send(
                message,
                hostname=self.smtp_host,
                port=self.smtp_port,
                username=self.smtp_user,
                password=self.smtp_password,
                start_tls=True,
            )

            logger.info(f"Email sent successfully to {to_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False

    async def send_opportunity_alert(
        self, to_email: str, opportunity: Opportunity, alert_name: str
    ) -> bool:
        """Send an opportunity alert email."""
        template = Template(OPPORTUNITY_ALERT_TEMPLATE)
        html_content = template.render(opportunity=opportunity, alert_name=alert_name)

        subject = f"🎯 {alert_name}: {opportunity.title[:50]}{'...' if len(opportunity.title) > 50 else ''}"

        return await self.send_email(
            to_email=to_email,
            subject=subject,
            html_content=html_content,
            text_content=f"New opportunity: {opportunity.title}\nScore: {opportunity.total_score}/10\nView at: https://opportunityradar.io/opportunities/{opportunity.id}",
        )

    async def send_daily_digest(
        self, to_email: str, opportunities: List[Opportunity]
    ) -> bool:
        """Send a daily digest email."""
        if not opportunities:
            return False

        template = Template(DAILY_DIGEST_TEMPLATE)
        html_content = template.render(
            opportunities=opportunities, date=datetime.now(timezone.utc)
        )

        subject = (
            f"📊 Daily Opportunity Digest - {len(opportunities)} new opportunities"
        )

        return await self.send_email(
            to_email=to_email,
            subject=subject,
            html_content=html_content,
            text_content=f"Found {len(opportunities)} new opportunities. View them at https://opportunityradar.io/dashboard",
        )


# Global email service instance
email_service = EmailService()
