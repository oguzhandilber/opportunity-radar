from app.websockets.dashboard import (
    manager,
    notify_app_updated,
    notify_score_changed,
    notify_new_match,
    notify_viral_alert,
    notify_trend_forecast,
)
from app.analyzers.pipeline import OpportunityPipeline
from app.models.appstore import App
from app.models.opportunity import Opportunity
from app.scheduler import TaskScheduler
from sqlalchemy.orm import Session
from typing import Dict, Any, List
import logging
import asyncio

logger = logging.getLogger(__name__)


class WebSocketIntegration:
    def __init__(self, db: Session, pipeline: OpportunityPipeline):
        self.db = db
        self.pipeline = pipeline
        self.scheduler = TaskScheduler()

    async def start_monitoring(self):
        self.scheduler.add_task(
            self._monitor_score_changes, interval=30, name="score_changes_monitor"
        )

        self.scheduler.add_task(
            self._monitor_new_opportunities,
            interval=60,
            name="new_opportunities_monitor",
        )

        self.scheduler.add_task(
            self._monitor_viral_alerts, interval=120, name="viral_alerts_monitor"
        )

        self.scheduler.add_task(
            self._monitor_forecast_updates,
            interval=300,
            name="forecast_updates_monitor",
        )

        await self.scheduler.start_async()
        logger.info("WebSocket monitoring started")

    async def stop_monitoring(self):
        await self.scheduler.stop_async()
        logger.info("WebSocket monitoring stopped")

    async def _monitor_score_changes(self):
        try:
            apps = self.db.query(App).all()
            for app in apps:
                if hasattr(app, 'current_score') and hasattr(app, 'previous_score'):
                    if app.current_score != app.previous_score:
                        await notify_score_changed(
                            app_id=app.id,
                            new_score=app.current_score,
                            previous_score=app.previous_score
                        )
                        
        except Exception as e:
            logger.error(f"Error monitoring score changes: {e}")
    
    async def _monitor_new_opportunities(self):
        try:
            recent_opportunities = self.db.query(Opportunity).filter(
                Opportunity.status == 'new'
            ).limit(10).all()
            
            for opportunity in recent_opportunities:
                match_data = {
                    "opportunity_id": opportunity.id,
                    "title": opportunity.title,
                    "score": opportunity.score,
                    "revenue_potential": getattr(opportunity, 'revenue_potential', 0),
                    "created_at": opportunity.created_at.isoformat() if opportunity.created_at else None
                }
                await notify_new_match(match_data)
                
        except Exception as e:
            logger.error(f"Error monitoring new opportunities: {e}")
    
    async def _monitor_viral_alerts(self):
        try:
            viral_opportunities = self.db.query(Opportunity).filter(
                Opportunity.score >= 80,
                Opportunity.status == 'new'
            ).limit(5).all()
            
            for opportunity in viral_opportunities:
                alert_data = {
                    "alert_id": f"viral_{opportunity.id}",
                    "opportunity_id": opportunity.id,
                    "title": opportunity.title,
                    "score": opportunity.score,
                    "alert_type": "viral_opportunity",
                    "urgency": "high" if opportunity.score >= 90 else "medium",
                    "created_at": opportunity.created_at.isoformat() if opportunity.created_at else None
                }
                await notify_viral_alert(alert_data)
                
        except Exception as e:
            logger.error(f"Error monitoring viral alerts: {e}")
    
    async def _monitor_forecast_updates(self):
        try:
            opportunities = self.db.query(Opportunity).all()
            
            if opportunities:
                high_score_count = len([op for op in opportunities if op.score >= 70])
                total_revenue_potential = sum(
                    getattr(op, 'revenue_potential', 0) for op in opportunities
                )
                
                forecast_data = {
                    "forecast_type": "opportunity_trend",
                    "period": "next_30_days",
                    "high_score_opportunities": high_score_count,
                    "total_revenue_potential": total_revenue_potential,
                    "trend_direction": "increasing" if high_score_count > 5 else "stable",
                    "confidence_score": min(95, 60 + high_score_count * 2),
                    "generated_at": "now"
                }
                await notify_trend_forecast(forecast_data)
                
        except Exception as e:
            logger.error(f"Error monitoring forecast updates: {e}")
    
    async def trigger_app_update(self, app_id: int, app_data: Dict[str, Any]):
        await notify_app_updated(app_id, app_data)
    
    async def trigger_score_change(self, app_id: int, new_score: float, previous_score: float = None):
        await notify_score_changed(app_id, new_score, previous_score)
    
    async def trigger_new_match(self, match_data: Dict[str, Any]):
        await notify_new_match(match_data)
    
    async def trigger_viral_alert(self, alert_data: Dict[str, Any]):
        await notify_viral_alert(alert_data)
    
    async def trigger_forecast_update(self, forecast_data: Dict[str, Any]):
        await notify_trend_forecast(forecast_data)
    
    def get_connection_stats(self) -> Dict[str, int]:
        return {
            "total_dashboard_clients": len(manager.active_connections),
            "total_app_subscribers": sum(len(conns) for conns in manager.app_connections.values()),
            "total_alert_subscribers": len(manager.alert_connections),
            "total_connections": (
                len(manager.active_connections) +
                sum(len(conns) for conns in manager.app_connections.values()) +
                len(manager.alert_connections)
            )
        }

_websocket_integration: WebSocketIntegration = None

async def initialize_websocket_integration(db: Session, pipeline: OpportunityPipeline) -> WebSocketIntegration:
    global _websocket_integration
    _websocket_integration = WebSocketIntegration(db, pipeline)
    await _websocket_integration.start_monitoring()
    return _websocket_integration

def get_websocket_integration() -> WebSocketIntegration:
    return _websocket_integration

async def broadcast_system_event(event_type: str, data: Dict[str, Any]):
    message = {
        "type": event_type,
        "payload": data,
        "timestamp": "now"
    }
    await manager.broadcast_to_all(message)

async def broadcast_custom_alert(title: str, message: str, severity: str = "info"):
    alert_data = {
        "title": title,
        "message": message,
        "severity": severity,
        "source": "system",
        "created_at": "now"
    }
    await notify_viral_alert(alert_data)

        except Exception as e:
            logger.error(f"Error monitoring viral alerts: {e}")

    async def _monitor_forecast_updates(self):
        """Monitor for trend forecast updates"""
        try:
            # Generate forecast data based on current opportunities
            opportunities = self.db.query(Opportunity).all()

            if opportunities:
                # Simple forecast based on recent opportunity trends
                high_score_count = len([op for op in opportunities if op.score >= 70])
                total_revenue_potential = sum(
                    getattr(op, "revenue_potential", 0) for op in opportunities
                )

                forecast_data = {
                    "forecast_type": "opportunity_trend",
                    "period": "next_30_days",
                    "high_score_opportunities": high_score_count,
                    "total_revenue_potential": total_revenue_potential,
                    "trend_direction": "increasing"
                    if high_score_count > 5
                    else "stable",
                    "confidence_score": min(95, 60 + high_score_count * 2),
                    "generated_at": "now",
                }
                await notify_trend_forecast(forecast_data)

        except Exception as e:
            logger.error(f"Error monitoring forecast updates: {e}")

    async def trigger_app_update(self, app_id: int, app_data: Dict[str, Any]):
        """Manually trigger an app update notification"""
        await notify_app_updated(app_id, app_data)

    async def trigger_score_change(
        self, app_id: int, new_score: float, previous_score: float = None
    ):
        """Manually trigger a score change notification"""
        await notify_score_changed(app_id, new_score, previous_score)

    async def trigger_new_match(self, match_data: Dict[str, Any]):
        """Manually trigger a new match notification"""
        await notify_new_match(match_data)

    async def trigger_viral_alert(self, alert_data: Dict[str, Any]):
        """Manually trigger a viral alert notification"""
        await notify_viral_alert(alert_data)

    async def trigger_forecast_update(self, forecast_data: Dict[str, Any]):
        """Manually trigger a forecast update notification"""
        await notify_trend_forecast(forecast_data)

    def get_connection_stats(self) -> Dict[str, int]:
        """Get current connection statistics"""
        return {
            "total_dashboard_clients": len(manager.active_connections),
            "total_app_subscribers": sum(
                len(conns) for conns in manager.app_connections.values()
            ),
            "total_alert_subscribers": len(manager.alert_connections),
            "total_connections": (
                len(manager.active_connections)
                + sum(len(conns) for conns in manager.app_connections.values())
                + len(manager.alert_connections)
            ),
        }


# Global WebSocket integration instance
_websocket_integration: WebSocketIntegration = None


async def initialize_websocket_integration(
    db: Session, pipeline: OpportunityPipeline
) -> WebSocketIntegration:
    """Initialize the global WebSocket integration instance"""
    global _websocket_integration
    _websocket_integration = WebSocketIntegration(db, pipeline)
    await _websocket_integration.start_monitoring()
    return _websocket_integration


def get_websocket_integration() -> WebSocketIntegration:
    """Get the global WebSocket integration instance"""
    return _websocket_integration


async def broadcast_system_event(event_type: str, data: Dict[str, Any]):
    """Broadcast a system-wide event to all connected clients"""
    message = {"type": event_type, "payload": data, "timestamp": "now"}
    await manager.broadcast_to_all(message)


async def broadcast_custom_alert(title: str, message: str, severity: str = "info"):
    """Broadcast a custom alert to all connected clients"""
    alert_data = {
        "title": title,
        "message": message,
        "severity": severity,
        "source": "system",
        "created_at": "now",
    }
    await notify_viral_alert(alert_data)
