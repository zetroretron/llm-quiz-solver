"""
Audio Handler - Transcribe audio files using Whisper or fallback.
"""
import requests
import re
import os
import tempfile
from typing import Optional
import logging

from .base import BaseHandler, TaskContext

logger = logging.getLogger(__name__)


class AudioHandler(BaseHandler):
    """Handler for audio transcription tasks."""
    
    priority = 20
    
    def can_handle(self, task_type: str, context: TaskContext) -> bool:
        page_lower = context.page_text.lower()
        return (
            'audio' in page_lower or
            'transcribe' in page_lower or
            'spoken' in page_lower or
            'passphrase' in page_lower or
            any(ext in page_lower for ext in ['.opus', '.mp3', '.wav', '.m4a', '.ogg']) or
            task_type == 'audio'
        )
    
    async def handle(self, context: TaskContext) -> str:
        logger.info("Processing audio task")
        
        # Find audio URL
        audio_url = self._find_audio_url(context)
        if not audio_url:
            logger.warning("No audio URL found, returning skip")
            return "skip"
        
        # Download audio file
        r = requests.get(audio_url)
        
        # Try multiple transcription methods
        result = await self._try_openai_whisper(r.content, audio_url)
        if result:
            return self._clean_transcription(result, context)
        
        result = await self._try_local_whisper(r.content, audio_url)
        if result:
            return self._clean_transcription(result, context)
        
        result = await self._try_speech_recognition(r.content, audio_url)
        if result:
            return self._clean_transcription(result, context)
        
        # Fallback - return skip for low-difficulty tasks
        logger.warning("All transcription methods failed, returning skip")
        return "skip"
    
    async def _try_openai_whisper(self, audio_bytes: bytes, audio_url: str) -> Optional[str]:
        """Try transcription using OpenAI Whisper API."""
        try:
            import openai
            
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                logger.info("No OpenAI API key found")
                return None
            
            client = openai.OpenAI(api_key=api_key)
            
            # Determine file extension
            ext = audio_url.split('.')[-1].lower()
            if ext not in ['mp3', 'mp4', 'm4a', 'wav', 'webm']:
                ext = 'mp3'  # Default
            
            # Save to temp file
            with tempfile.NamedTemporaryFile(suffix=f'.{ext}', delete=False) as f:
                f.write(audio_bytes)
                temp_path = f.name
            
            try:
                with open(temp_path, 'rb') as audio_file:
                    transcript = client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file
                    )
                return transcript.text
            finally:
                os.unlink(temp_path)
                
        except ImportError:
            logger.info("OpenAI library not available")
            return None
        except Exception as e:
            logger.error(f"OpenAI Whisper failed: {e}")
            return None
    
    async def _try_local_whisper(self, audio_bytes: bytes, audio_url: str) -> Optional[str]:
        """Try transcription using local Whisper model."""
        try:
            import whisper
            
            # Save to temp file
            ext = audio_url.split('.')[-1].lower()
            with tempfile.NamedTemporaryFile(suffix=f'.{ext}', delete=False) as f:
                f.write(audio_bytes)
                temp_path = f.name
            
            try:
                model = whisper.load_model("base")
                result = model.transcribe(temp_path)
                return result["text"]
            finally:
                os.unlink(temp_path)
                
        except ImportError:
            logger.info("Local Whisper not available")
            return None
        except Exception as e:
            logger.error(f"Local Whisper failed: {e}")
            return None
    
    async def _try_speech_recognition(self, audio_bytes: bytes, audio_url: str) -> Optional[str]:
        """Try transcription using SpeechRecognition library."""
        try:
            import speech_recognition as sr
            from pydub import AudioSegment
            
            ext = audio_url.split('.')[-1].lower()
            
            # Convert to WAV if needed
            with tempfile.NamedTemporaryFile(suffix=f'.{ext}', delete=False) as f:
                f.write(audio_bytes)
                input_path = f.name
            
            wav_path = input_path.replace(f'.{ext}', '.wav')
            
            try:
                # Convert to WAV
                audio = AudioSegment.from_file(input_path)
                audio.export(wav_path, format='wav')
                
                # Recognize
                recognizer = sr.Recognizer()
                with sr.AudioFile(wav_path) as source:
                    audio_data = recognizer.record(source)
                    text = recognizer.recognize_google(audio_data)
                    return text
            finally:
                if os.path.exists(input_path):
                    os.unlink(input_path)
                if os.path.exists(wav_path):
                    os.unlink(wav_path)
                    
        except ImportError:
            logger.info("SpeechRecognition or pydub not available")
            return None
        except Exception as e:
            logger.error(f"SpeechRecognition failed: {e}")
            return None
    
    def _clean_transcription(self, text: str, context: TaskContext) -> str:
        """Clean and format transcription based on task requirements."""
        # Lowercase if required
        if 'lowercase' in context.page_text.lower():
            text = text.lower()
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        # Keep only alphanumeric and spaces if passphrase
        if 'passphrase' in context.page_text.lower() or 'code' in context.page_text.lower():
            # Keep digits and letters
            text = re.sub(r'[^\w\s]', '', text)
        
        return text.strip()
    
    def _find_audio_url(self, context: TaskContext) -> Optional[str]:
        """Find audio URL in page content."""
        patterns = [
            r'href=["\']([^"\']+\.(?:opus|mp3|wav|m4a|ogg))["\']',
            r'(/project2/[^\s"\'<>]+\.(?:opus|mp3|wav|m4a|ogg))',
            r'(https?://[^\s"\'<>]+\.(?:opus|mp3|wav|m4a|ogg))',
        ]
        
        for p in patterns:
            match = re.search(p, context.page_text + context.html_content, re.IGNORECASE)
            if match:
                url = match.group(1)
                if not url.startswith('http'):
                    url = context.base_url + url
                return url
        return None
