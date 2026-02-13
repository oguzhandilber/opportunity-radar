"""Alert processor - checks opportunities against user alerts and sends notifications."""

import logging
from datetime import datetime, timezone
from typing import List
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db_context, Alert, User, Opportunity, SavedSearch
from app.services.email_service import email_service

logger = logging.getLogger(__name__)


class AlertProcessor:
    """Process alerts and send notifications when opportunities match criteria."""

    async def check_alerts_for_opportunity(self, opportunity: Opportunity) -> int:
        """Check an opportunity against all active alerts and send notifications."""
        notifications_sent = 0

        try:
            async with get_db_context() as session:
                # Get all active alerts
                alerts = await self._get_active_alerts(session)

                for alert in alerts:
                    if await self._matches_alert_criteria(opportunity, alert):
                        await self._send_alert_notification(session, alert, opportunity)
                        notifications_sent += 1

                        # Update last_alert_at
                        alert.last_alert_at = datetime.now(timezone.utc)
                        await session.commit()

        except Exception as e:
            logger.error(f"Error checking alerts for opportunity {opportunity.id}: {e}")

        return notifications_sent

    async def _get_active_alerts(self, session: AsyncSession) -> List[Alert]:
        """Get all active alerts with their associated users."""
        from sqlalchemy.orm import selectinload

        stmt = (
            select(Alert)
            .options(selectinload(Alert.user))
            .where(
                and_(
                    Alert.email_enabled == True, Alert.user.has(User.is_active == True)
                )
            )
        )

        result = await session.execute(stmt)
        return result.scalars().all()

    async def _matches_alert_criteria(
        self, opportunity: Opportunity, alert: Alert
    ) -> bool:
        """Check if an opportunity matches an alert's criteria."""
        # Check minimum score
        if alert.min_total_score is not None:
            if (
                opportunity.total_score is None
                or opportunity.total_score < alert.min_total_score
            ):
                return False

        # Check sectors
        if alert.sectors:
            if not opportunity.sector or opportunity.sector.lower() not in [
                s.lower() for s in alert.sectors
            ]:
                return False

        # Check product types
        if alert.product_types:
            if not opportunity.product_type or opportunity.product_type.lower() not in [
                p.lower() for p in alert.product_types
            ]:
                return False

        # Check keywords
        if alert.keywords:
            content = f"{opportunity.title} {opportunity.summary or ''}".lower()
            if not any(keyword.lower() in content for keyword in alert.keywords):
                return False

        return True

    async def _send_alert_notification(
        self, session: AsyncSession, alert: Alert, opportunity: Opportunity
    ):
        """Send notification for a matched alert."""
        user = alert.user

        if not user or not user.email:
            logger.warning(f"Alert {alert.id} has no associated user email")
            return

        # Send email notification
        if alert.email_enabled:
            success = await email_service.send_opportunity_alert(
                to_email=user.email, opportunity=opportunity, alert_name=alert.name
            )

            if success:
                logger.info(
                    f"Sent email alert to {user.email} for opportunity {opportunity.id}"
                )
            else:
                logger.error(f"Failed to send email alert to {user.email}")

        # Send Slack notification if webhook configured
        if alert.slack_webhook:
            await self._send_slack_notification(alert.slack_webhook, opportunity)

    async def _send_slack_notification(
        self, webhook_url: str, opportunity: Opportunity
    ):
        """Send Slack notification via webhook."""
        import httpx

        try:
            payload = {
                "blocks": [
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": f"🎯 New Opportunity: {opportunity.title[:50]}",
                        },
                    },
                    {
                        "type": "section",
                        "fields": [
                            {
                                "type": "mrkdwn",
                                "text": f"*Score:* {opportunity.total_score}/10",
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Sector:* {opportunity.sector or 'Unknown'}",
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Revenue Potential:* {opportunity.revenue_potential_score or 'N/A'}/10",
                            },
                        ],
                    },
                    {
                        "type": "actions",
                        "elements": [
                            {
                                "type": "button",
                                "text": {"type": "plain_text", "text": "View Details"},
                                "url": f"https://opportunityradar.io/opportunities/{opportunity.id}",
                            }
                        ],
                    },
                ]
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(webhook_url, json=payload)
                response.raise_for_status()

            logger.info(f"Sent Slack notification for opportunity {opportunity.id}")

        except Exception as e:
            logger.error(f"Failed to send Slack notification: {e}")

    async def process_saved_search_matches(self):
        """Update saved searches with new opportunity matches."""
        try:
            async with get_db_context() as session:
                # Get all saved searches
                stmt = select(SavedSearch)
                result = await session.execute(stmt)
                saved_searches = result.scalars().all()

                for saved_search in saved_searches:
                    # Count opportunities matching criteria
                    count = await self._count_matching_opportunities(
                        session, saved_search
                    )

                    # Update counts
                    saved_search.total_matches = count
                    saved_search.new_matches_today = count - (
                        saved_search.total_matches or 0
                    )
                    saved_search.updated_at = datetime.now(timezone.utc)

                await session.commit()

        except Exception as e:
            logger.error(f"Error processing saved search matches: {e}")

    async def _count_matching_opportunities(
        self, session: AsyncSession, saved_search: SavedSearch
    ) -> int:
        """Count opportunities matching a saved search criteria."""
        stmt = select(Opportunity)

        # Build filters
        filters = []

        if saved_search.sectors:
            filters.append(Opportunity.sector.in_(saved_search.sectors))

        if saved_search.product_types:
            filters.append(Opportunity.product_type.in_(saved_search.product_types))

        if saved_search.min_score is not None:
            filters.append(Opportunity.total_score >= saved_search.min_score)

        if saved_search.source:
            filters.append(Opportunity.raw_post.has(source=saved_search.source))

        if filters:
            stmt = stmt.where(and_(*filters))

        result = await session.execute(stmt)
        return len(result.scalars().all())


# Global alert processor instance
alert_processor = AlertProcessor()
