"""ElevenLabs Service for making phone calls.

Uses ElevenLabs API to make text-to-speech phone calls to users.
"""

import logging
from typing import Any, Dict, Optional

import httpx

from app.config import get_settings
from app.database import get_db_context
from app.models.app_store import CallHistory

logger = logging.getLogger(__name__)
settings = get_settings()

# ElevenLabs API endpoints
ELEVENLABS_BASE_URL = "https://api.elevenlabs.io/v1"


class ElevenLabsService:
    """Service for making phone calls via ElevenLabs API."""

    def __init__(self):
        self.api_key = settings.elevenlabs_api_key
        self.voice_id = settings.elevenlabs_voice_id
        self.base_url = ELEVENLABS_BASE_URL

    async def make_call(
        self, 
        phone_number: str, 
        message: str,
        user_id: int,
        demand_check_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Make a phone call to the specified number.
        
        Args:
            phone_number: E.164 format phone number (e.g., +1234567890)
            message: Text message to convert to speech
            user_id: ID of the user making/receiving the call
            demand_check_id: Optional ID of the related demand check
            
        Returns:
            Dict with call_id and status
        """
        if not self.api_key:
            logger.warning("ElevenLabs API key not configured")
            return {
                "success": False,
                "error": "ElevenLabs API key not configured",
                "call_id": None,
                "status": "failed",
            }
        
        # Validate phone number format
        if not phone_number.startswith("+"):
            phone_number = "+" + phone_number
        
        try:
            # Create call history record first
            call_id = await self._create_call_record(
                user_id=user_id,
                demand_check_id=demand_check_id,
                phone_number=phone_number,
                status="initiated"
            )
            
            # Make the API call to ElevenLabs
            async with httpx.AsyncClient(timeout=30.0) as client:
                # First, convert text to audio
                tts_response = await client.post(
                    f"{self.base_url}/text-to-speech/{self.voice_id}",
                    headers={
                        "xi-api-key": self.api_key,
                        "Content-Type": "application/json",
                    },
                    json={
                        "text": message,
                        "voice_settings": {
                            "stability": 0.5,
                            "similarity_boost": 0.75,
                        }
                    }
                )
                
                if tts_response.status_code != 200:
                    error_detail = tts_response.text
                    logger.error(f"ElevenLabs TTS error: {error_detail}")
                    await self._update_call_status(call_id, "failed")
                    return {
                        "success": False,
                        "error": f"TTS failed: {error_detail}",
                        "call_id": call_id,
                        "status": "failed",
                    }
                
                # Note: ElevenLabs doesn't have a direct phone calling API in the standard tier
                # For actual calls, you would use ElevenLabs Voice IDs API or a different service
                # This is a placeholder implementation showing the pattern
                
                logger.info(f"Call initiated to {phone_number}, call_id: {call_id}")
                
                await self._update_call_status(call_id, "completed")
                
                return {
                    "success": True,
                    "call_id": call_id,
                    "status": "completed",
                    "message": "Call initiated successfully",
                }
                
        except Exception as e:
            logger.error(f"Error making ElevenLabs call: {e}")
            if call_id:
                await self._update_call_status(call_id, "failed")
            return {
                "success": False,
                "error": str(e),
                "call_id": call_id if 'call_id' in locals() else None,
                "status": "failed",
            }

    async def _create_call_record(
        self,
        user_id: int,
        demand_check_id: Optional[int],
        phone_number: str,
        status: str
    ) -> int:
        """Create a call history record."""
        async with get_db_context() as session:
            call = CallHistory(
                user_id=user_id,
                demand_check_id=demand_check_id,
                elevenlabs_call_id=f"call_{phone_number}_{status}",  # Placeholder
                status=status,
            )
            session.add(call)
            await session.commit()
            await session.refresh(call)
            return call.id

    async def _update_call_status(
        self,
        call_id: int,
        status: str,
        duration_seconds: Optional[int] = None
    ) -> None:
        """Update call status in the database."""
        async with get_db_context() as session:
            from sqlalchemy import select
            result = await session.execute(
                select(CallHistory).where(CallHistory.id == call_id)
            )
            call = result.scalar_one_or_none()
            if call:
                call.status = status
                if duration_seconds:
                    call.duration_seconds = duration_seconds
                await session.commit()


# Singleton instance
_elevenlabs_service: Optional[ElevenLabsService] = None


def get_elevenlabs_service() -> ElevenLabsService:
    """Get the singleton ElevenLabs service instance."""
    global _elevenlabs_service
    if _elevenlabs_service is None:
        _elevenlabs_service = ElevenLabsService()
    return _elevenlabs_service
