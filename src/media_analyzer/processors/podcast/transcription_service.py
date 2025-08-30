"""Streaming transcription service for podcast audio."""

import io
import logging
import tempfile
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, Union
from pathlib import Path

import aiohttp
import whisper
from pydub import AudioSegment

from media_analyzer.models.audio.transcription import TranscriptionResult
from media_analyzer.core.exceptions import AudioProcessingError

logger = logging.getLogger(__name__)


class StreamingTranscriptionService(ABC):
    """Abstract base class for streaming transcription services."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize transcription service."""
        self.config = config or {}
    
    @abstractmethod
    async def transcribe_stream(self, audio_url: str, options: Optional[Dict[str, Any]] = None) -> TranscriptionResult:
        """Transcribe audio from streaming URL.
        
        Args:
            audio_url: Direct URL to audio stream
            options: Optional transcription parameters
            
        Returns:
            TranscriptionResult with transcription and metadata
        """
        pass


class WhisperStreamingService(StreamingTranscriptionService):
    """Whisper-based streaming transcription service."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize Whisper streaming service."""
        super().__init__(config)
        self._model: Optional[Any] = None
        self.session: Optional[aiohttp.ClientSession] = None
    
    @property
    def model(self):
        """Lazy load the whisper model."""
        if self._model is None:
            try:
                model_size = self.config.get('model_size', 'base')
                self._model = whisper.load_model(model_size)
                logger.info(f"Loaded Whisper model: {model_size}")
            except Exception as e:
                raise AudioProcessingError(f"Failed to load Whisper model: {str(e)}")
        return self._model
    
    async def transcribe_stream(self, audio_url: str, options: Optional[Dict[str, Any]] = None) -> TranscriptionResult:
        """Transcribe audio from streaming URL using Whisper.
        
        Args:
            audio_url: Direct URL to audio stream
            options: Optional transcription parameters:
                - language: Target language (default: 'en')
                - task: 'transcribe' or 'translate'
                - segment_length: Chunk size in seconds for large files
                
        Returns:
            TranscriptionResult with transcription and metadata
        """
        options = options or {}
        
        try:
            # Download and process audio
            audio_data = await self._download_audio(audio_url)
            
            # Process with chunking for large files
            segment_length = options.get('segment_length', 300)  # 5 minutes default
            
            if len(audio_data) / 1000 > segment_length:
                logger.info(f"Processing large audio file in chunks of {segment_length}s")
                return await self._transcribe_chunked(audio_data, options, segment_length)
            else:
                return await self._transcribe_single(audio_data, options)
                
        except Exception as e:
            logger.error(f"Transcription failed: {str(e)}")
            raise AudioProcessingError(f"Failed to transcribe audio: {str(e)}")
    
    async def _download_audio(self, audio_url: str) -> AudioSegment:
        """Download audio from URL and return as AudioSegment.
        
        Args:
            audio_url: URL to download audio from
            
        Returns:
            AudioSegment with the downloaded audio
        """
        session = await self._get_session()
        
        try:
            logger.info(f"Downloading audio from: {audio_url}")
            
            async with session.get(audio_url, timeout=300) as response:  # 5 minute timeout
                if response.status != 200:
                    raise ConnectionError(f"Failed to download audio: HTTP {response.status}")
                
                # Read audio data in chunks to avoid memory issues
                audio_data = io.BytesIO()
                chunk_size = 1024 * 1024  # 1MB chunks
                
                async for chunk in response.content.iter_chunked(chunk_size):
                    audio_data.write(chunk)
                
                # Reset to beginning and load with pydub
                audio_data.seek(0)
                
                # Determine format from content type or URL
                content_type = response.headers.get('content-type', '').lower()
                format_hint = self._guess_audio_format(content_type, audio_url)
                
                logger.info(f"Loading audio data, format: {format_hint}")
                return AudioSegment.from_file(audio_data, format=format_hint)
                
        except aiohttp.ClientError as e:
            raise ConnectionError(f"Failed to download audio: {str(e)}")
        except Exception as e:
            raise AudioProcessingError(f"Failed to process downloaded audio: {str(e)}")
    
    async def _transcribe_single(self, audio_data: AudioSegment, options: Dict[str, Any]) -> TranscriptionResult:
        """Transcribe a single audio segment.
        
        Args:
            audio_data: AudioSegment to transcribe
            options: Transcription options
            
        Returns:
            TranscriptionResult
        """
        # Prepare whisper options
        transcribe_kwargs = {
            "language": options.get("language", "en"),
            "task": options.get("task", "transcribe"),
            "fp16": False
        }
        
        # Save to temporary file for whisper
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            try:
                # Preprocess audio (16kHz, mono for Whisper)
                processed_audio = audio_data.set_frame_rate(16000).set_channels(1)
                processed_audio.export(temp_file.name, format="wav")
                
                logger.info("Starting Whisper transcription...")
                result = self.model.transcribe(temp_file.name, **transcribe_kwargs)
                
                # Extract text and metadata
                text = result.get("text", "")
                if not text:
                    raise AudioProcessingError("No transcription returned")
                
                # Calculate confidence from segments
                segments = result.get("segments", [])
                confidence = self._calculate_confidence(segments)
                
                # Prepare metadata
                metadata = {
                    "language": result.get("language", transcribe_kwargs["language"]),
                    "model": "whisper-streaming",
                    "task": transcribe_kwargs["task"],
                    "duration": len(audio_data) / 1000.0,
                    "service": "whisper"
                }
                
                return TranscriptionResult(
                    text=text.strip(),
                    language=metadata["language"],
                    segments=segments,
                    confidence=confidence,
                    metadata=metadata
                )
                
            finally:
                # Clean up temp file
                Path(temp_file.name).unlink(missing_ok=True)
    
    async def _transcribe_chunked(self, audio_data: AudioSegment, options: Dict[str, Any], segment_length: int) -> TranscriptionResult:
        """Transcribe large audio file in chunks.
        
        Args:
            audio_data: AudioSegment to transcribe
            options: Transcription options
            segment_length: Length of each chunk in seconds
            
        Returns:
            Combined TranscriptionResult
        """
        segment_length_ms = segment_length * 1000
        total_length = len(audio_data)
        
        all_text = []
        all_segments = []
        all_confidences = []
        
        logger.info(f"Processing {total_length/1000:.1f}s audio in {segment_length}s chunks")
        
        for start_ms in range(0, total_length, segment_length_ms):
            end_ms = min(start_ms + segment_length_ms, total_length)
            chunk = audio_data[start_ms:end_ms]  # type: ignore[assignment]
            
            logger.info(f"Processing chunk {start_ms/1000:.1f}s - {end_ms/1000:.1f}s")
            
            try:
                result = await self._transcribe_single(chunk, options)  # type: ignore[arg-type]
                all_text.append(result.text)
                all_confidences.append(result.confidence)
                
                # Adjust segment timestamps for this chunk
                chunk_start_seconds = start_ms / 1000.0
                for segment in result.segments:
                    if isinstance(segment, dict):
                        segment['start'] += chunk_start_seconds
                        segment['end'] += chunk_start_seconds
                all_segments.extend(result.segments)
                
            except Exception as e:
                logger.warning(f"Failed to process chunk {start_ms/1000:.1f}s: {e}")
                # Continue with other chunks
                all_text.append(f"[CHUNK_ERROR: {str(e)}]")
                all_confidences.append(0.0)
        
        # Combine results
        combined_text = " ".join(filter(None, all_text))
        overall_confidence = sum(all_confidences) / len(all_confidences) if all_confidences else 0.0
        
        metadata = {
            "language": options.get("language", "en"),
            "model": "whisper-streaming-chunked", 
            "task": options.get("task", "transcribe"),
            "duration": total_length / 1000.0,
            "chunks_processed": len(all_text),
            "service": "whisper"
        }
        
        return TranscriptionResult(
            text=combined_text,
            language=metadata["language"],
            segments=all_segments,
            confidence=overall_confidence,
            metadata=metadata
        )
    
    def _calculate_confidence(self, segments: list) -> float:
        """Calculate overall confidence from segment log probabilities."""
        if not segments:
            return 0.5  # Default confidence
        
        try:
            valid_logprobs = []
            for segment in segments:
                if isinstance(segment, dict) and 'avg_logprob' in segment:
                    logprob = float(segment['avg_logprob'])
                    valid_logprobs.append(logprob)
            
            if valid_logprobs:
                avg_logprob = sum(valid_logprobs) / len(valid_logprobs)
                # Convert log probability to confidence (0-1 range)
                return min(1.0, max(0.0, 1 + avg_logprob))
        except Exception as e:
            logger.warning(f"Failed to calculate confidence: {e}")
        
        return 0.5  # Fallback confidence
    
    def _guess_audio_format(self, content_type: str, url: str) -> str:
        """Guess audio format from content type or URL."""
        # Check content type first
        if 'mp3' in content_type or 'mpeg' in content_type:
            return 'mp3'
        elif 'mp4' in content_type or 'm4a' in content_type:
            return 'm4a'
        elif 'wav' in content_type:
            return 'wav'
        elif 'aac' in content_type:
            return 'aac'
        
        # Check URL extension
        url_lower = url.lower()
        if url_lower.endswith('.mp3'):
            return 'mp3'
        elif url_lower.endswith('.m4a'):
            return 'm4a'
        elif url_lower.endswith('.wav'):
            return 'wav'
        elif url_lower.endswith('.aac'):
            return 'aac'
        
        # Default to mp3 (most common podcast format)
        return 'mp3'
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session."""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=600)  # 10 minute timeout for large downloads
            headers = {
                'User-Agent': 'Story-Curator-Podcast-Analyzer/1.0'
            }
            self.session = aiohttp.ClientSession(timeout=timeout, headers=headers)
        return self.session
    
    async def cleanup(self):
        """Cleanup resources."""
        if self.session and not self.session.closed:
            await self.session.close()
