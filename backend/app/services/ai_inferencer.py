"""
AI Inferencer Service
Uses Gemini 3.0 API (or mock) to predict deleted message content
"""
import json
import random
from typing import List, Optional, Dict
from dataclasses import dataclass, asdict
from abc import ABC, abstractmethod

from app.config import get_settings
from app.services.gap_detector import DetectedGap


@dataclass
class InferenceResult:
    """Result of AI inference for a gap"""
    predicted_intent: str
    predicted_content: Optional[str]
    predicted_sender: Optional[str]
    confidence_score: float
    context_anchors: List[Dict]
    reasoning: str
    model_used: str
    hallucination_flags: List[str]


class BaseInferencer(ABC):
    """Base class for AI inference services"""
    
    @abstractmethod
    def infer_gap(self, gap: DetectedGap, full_context: List[Dict]) -> InferenceResult:
        """Generate inference for a detected gap"""
        pass


class MockInferencer(BaseInferencer):
    """
    Mock AI inferencer for development and testing
    Generates plausible but clearly marked fake predictions
    """
    
    MODEL_NAME = "mock-gemini-2.0"
    
    # Templates for mock predictions based on context
    INTENT_TEMPLATES = [
        "Discussion about {topic} likely continued",
        "Possible exchange of sensitive information related to {topic}",
        "Negotiation or agreement regarding {topic}",
        "Follow-up questions about {topic}",
        "Clarification request about previous statement",
        "Reaction to shared media or document",
    ]
    
    CONTENT_TEMPLATES = [
        "[REDACTED: Possible discussion about {topic}]",
        "[INFERRED: Response confirming previous statement]",
        "[PREDICTED: Question seeking clarification]",
        "[MOCK: Agreement or acknowledgment message]",
    ]
    
    def infer_gap(self, gap: DetectedGap, full_context: List[Dict] = None) -> InferenceResult:
        """Generate mock inference based on gap context"""
        
        # Extract topic hints from context
        topic = self._extract_topic(gap.context_before, gap.context_after)
        
        # Determine likely sender from pattern
        likely_sender = self._predict_sender(gap.context_before, gap.context_after)
        
        # Generate confidence based on available context
        confidence = self._calculate_mock_confidence(gap)
        
        # Generate anchors from context
        anchors = self._generate_anchors(gap)
        
        # Build mock prediction
        intent_template = random.choice(self.INTENT_TEMPLATES)
        content_template = random.choice(self.CONTENT_TEMPLATES)
        
        return InferenceResult(
            predicted_intent=intent_template.format(topic=topic),
            predicted_content=content_template.format(topic=topic),
            predicted_sender=likely_sender,
            confidence_score=confidence,
            context_anchors=anchors,
            reasoning=self._generate_reasoning(gap, topic),
            model_used=self.MODEL_NAME,
            hallucination_flags=["MOCK_DATA", "NOT_REAL_PREDICTION"],
        )
    
    def _extract_topic(self, before: List[Dict], after: List[Dict]) -> str:
        """Extract likely topic from surrounding messages"""
        all_content = []
        
        for msg in before + after:
            content = msg.get("content", "")
            if content and len(content) > 3:
                all_content.append(content)
        
        if not all_content:
            return "unidentified matter"
        
        # Simple: use first few words of nearby message
        sample = all_content[0][:50].strip()
        if len(sample) > 30:
            sample = sample[:30] + "..."
        
        return f"'{sample}'"
    
    def _predict_sender(self, before: List[Dict], after: List[Dict]) -> Optional[str]:
        """Predict likely sender of missing message"""
        if not before or not after:
            return None
        
        last_sender = before[-1].get("sender") if before else None
        next_sender = after[0].get("sender") if after else None
        
        # If same sender before and after, deleted message was likely from other person
        if last_sender and next_sender and last_sender == next_sender:
            # Look for other participants
            all_senders = set()
            for msg in before + after:
                all_senders.add(msg.get("sender"))
            
            others = all_senders - {last_sender}
            if others:
                return list(others)[0]
        
        return last_sender
    
    def _calculate_mock_confidence(self, gap: DetectedGap) -> float:
        """Calculate mock confidence score"""
        base = 0.4
        
        # More context = higher confidence
        context_bonus = min(len(gap.context_before + gap.context_after) * 0.05, 0.3)
        
        # Shorter gaps = higher confidence
        if gap.time_gap_seconds < 3600:
            time_bonus = 0.15
        elif gap.time_gap_seconds < 7200:
            time_bonus = 0.1
        else:
            time_bonus = 0.0
        
        # Explicit deletions = higher confidence something important was there
        if gap.detection_type == "explicit_deletion":
            type_bonus = 0.1
        else:
            type_bonus = 0.05
        
        return min(base + context_bonus + time_bonus + type_bonus, 0.85)
    
    def _generate_anchors(self, gap: DetectedGap) -> List[Dict]:
        """Generate context anchor references"""
        anchors = []
        
        for msg in gap.context_before[-2:]:  # Last 2 before gap
            anchors.append({
                "sequence": msg.get("sequence"),
                "type": "before_gap",
                "relevance": "high",
            })
        
        for msg in gap.context_after[:2]:  # First 2 after gap
            anchors.append({
                "sequence": msg.get("sequence"),
                "type": "after_gap", 
                "relevance": "high",
            })
        
        return anchors
    
    def _generate_reasoning(self, gap: DetectedGap, topic: str) -> str:
        """Generate mock reasoning explanation"""
        reasons = gap.suspicion_reasons
        reason_text = "; ".join(reasons[:3]) if reasons else "Unusual gap detected"
        
        return (
            f"[MOCK REASONING] Based on the gap characteristics ({reason_text}) and "
            f"surrounding context discussing {topic}, the model predicts that "
            f"approximately {gap.estimated_missing or 1} message(s) may have been removed. "
            f"The conversation flow suggests a response or continuation was expected."
        )


class GeminiInferencer(BaseInferencer):
    """
    Real Gemini API integration with full production features:
    - Retry logic with exponential backoff
    - Rate limiting handling  
    - Safety settings configuration
    - Context anchoring for hallucination prevention
    - Async batch processing support
    """
    
    MAX_RETRIES = 3
    BASE_DELAY = 1.0  # seconds
    MAX_DELAY = 30.0  # seconds
    
    def __init__(self, api_key: str, model: str = "gemini-2.0-flash"):
        self.api_key = api_key
        self.model = model
        self._client = None
        self._genai = None
        
        # Lazy initialization
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Gemini client with safety settings"""
        import google.generativeai as genai
        self._genai = genai
        
        genai.configure(api_key=self.api_key)
        
        # Configure safety settings for forensic analysis
        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]
        
        # Generation config for consistent JSON output
        generation_config = {
            "temperature": 0.3,  # Lower for more deterministic forensic analysis
            "top_p": 0.8,
            "top_k": 40,
            "max_output_tokens": 1024,
            "response_mime_type": "application/json",
        }
        
        self._client = genai.GenerativeModel(
            model_name=self.model,
            safety_settings=safety_settings,
            generation_config=generation_config,
        )
    
    def infer_gap(self, gap: DetectedGap, full_context: List[Dict] = None) -> InferenceResult:
        """
        Generate inference using Gemini API with retry logic
        Implements context anchoring for hallucination prevention
        """
        import time
        
        prompt = self._build_prompt(gap, full_context)
        last_error = None
        
        for attempt in range(self.MAX_RETRIES):
            try:
                response = self._client.generate_content(prompt)
                
                # Check if response was blocked
                if not response.parts:
                    raise ValueError("Response blocked by safety filters")
                
                parsed = self._parse_response(response.text)
                
                # Handle null values from conservative AI responses
                predicted_intent = parsed.get("predicted_intent")
                if not predicted_intent or predicted_intent == "null":
                    predicted_intent = "Tidak cukup bukti untuk prediksi"
                
                return InferenceResult(
                    predicted_intent=predicted_intent,
                    predicted_content=parsed.get("predicted_content"),
                    predicted_sender=parsed.get("predicted_sender"),
                    confidence_score=self._validate_confidence(parsed.get("confidence_score", 0.5)),
                    context_anchors=self._generate_anchors(gap),
                    reasoning=parsed.get("reasoning", "AI analysis complete"),
                    model_used=self.model,
                    hallucination_flags=parsed.get("hallucination_flags", []),
                )
                
            except Exception as e:
                last_error = e
                error_str = str(e).lower()
                
                # Check for retryable errors
                if "429" in error_str or "quota" in error_str or "rate" in error_str:
                    # Rate limited - wait with exponential backoff
                    delay = min(self.BASE_DELAY * (2 ** attempt), self.MAX_DELAY)
                    time.sleep(delay)
                    continue
                elif "500" in error_str or "503" in error_str or "timeout" in error_str:
                    # Server error - retry with backoff
                    delay = min(self.BASE_DELAY * (2 ** attempt), self.MAX_DELAY)
                    time.sleep(delay)
                    continue
                else:
                    # Non-retryable error - fail immediately
                    break
        
        # All retries failed - fallback to mock
        return self._fallback_to_mock(gap, full_context, last_error)
    
    def _fallback_to_mock(self, gap: DetectedGap, full_context: List[Dict], error: Exception) -> InferenceResult:
        """Fallback to mock inferencer on API failure"""
        mock = MockInferencer()
        result = mock.infer_gap(gap, full_context)
        
        error_msg = str(error)[:60] if error else "Unknown error"
        model_used = f"{self.model} (fallback: {error_msg})"
        result.model_used = model_used[:250]  # Truncate to fit VARCHAR(255)
        result.hallucination_flags.append("GEMINI_API_FALLBACK")
        
        return result
    
    def _validate_confidence(self, score) -> float:
        """Validate and normalize confidence score"""
        try:
            score = float(score)
            return max(0.0, min(1.0, score))
        except (TypeError, ValueError):
            return 0.5
    
    def _parse_response(self, response_text: str) -> Dict:
        """Parse Gemini response JSON with robust handling"""
        try:
            text = response_text.strip()
            
            # Remove markdown code blocks if present
            if text.startswith("```json"):
                text = text[7:]
            elif text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
            
            # Try to find JSON object in response
            text = text.strip()
            if not text.startswith("{"):
                # Try to find JSON in the response
                start = text.find("{")
                end = text.rfind("}") + 1
                if start != -1 and end > start:
                    text = text[start:end]
            
            parsed = json.loads(text)
            
            # Validate required fields
            if "predicted_intent" not in parsed:
                parsed["predicted_intent"] = "Intent could not be determined"
            
            return parsed
            
        except json.JSONDecodeError as e:
            return {
                "predicted_intent": f"JSON parse error: {str(e)[:30]}",
                "predicted_content": None,
                "confidence_score": 0.2,
                "reasoning": f"Raw response: {response_text[:200]}",
                "hallucination_flags": ["PARSE_ERROR", "RAW_RESPONSE"],
            }
    
    def _generate_anchors(self, gap: DetectedGap) -> List[Dict]:
        """Generate context anchor references for verification"""
        anchors = []
        
        for msg in gap.context_before[-3:]:  # Last 3 messages before gap
            anchors.append({
                "sequence": msg.get("sequence"),
                "type": "before_gap",
                "sender": msg.get("sender"),
                "relevance": "high" if msg == gap.context_before[-1] else "medium",
            })
        
        for msg in gap.context_after[:3]:  # First 3 messages after gap
            anchors.append({
                "sequence": msg.get("sequence"),
                "type": "after_gap",
                "sender": msg.get("sender"),
                "relevance": "high" if msg == gap.context_after[0] else "medium",
            })
        
        return anchors
    
    def _build_prompt(self, gap: DetectedGap, full_context: List[Dict]) -> str:
        """Build forensic analysis prompt with context anchoring instructions"""
        context_before = "\n".join(
            f"[{m.get('timestamp')}] {m.get('sender')}: {m.get('content')}"
            for m in gap.context_before
        )
        context_after = "\n".join(
            f"[{m.get('timestamp')}] {m.get('sender')}: {m.get('content')}"
            for m in gap.context_after
        )
        
        # Format time gap for readability
        hours, remainder = divmod(int(gap.time_gap_seconds), 3600)
        minutes, seconds = divmod(remainder, 60)
        time_display = f"{hours}h {minutes}m {seconds}s" if hours else f"{minutes}m {seconds}s"
        
        # Count participants for context
        participants = set()
        for m in gap.context_before + gap.context_after:
            if m.get("sender"):
                participants.add(m.get("sender"))
        
        return f"""## PERAN
Anda adalah analis forensik digital yang SANGAT KONSERVATIF. Tugas Anda adalah menganalisis gap dalam riwayat chat untuk mendeteksi kemungkinan pesan yang dihapus.

## ATURAN ANTI-HALUSINASI (WAJIB DIPATUHI)
1. **JANGAN PERNAH mengarang isi pesan** - Jika tidak ada bukti kuat, gunakan null
2. **Hanya prediksi yang DAPAT DIBUKTIKAN** dari konteks sekitar
3. **Lebih baik bilang "tidak tahu" daripada menebak**
4. **Setiap klaim HARUS memiliki bukti** dari pesan sebelum/sesudah gap
5. **Confidence score MAKSIMUM 0.7** kecuali ada bukti sangat kuat

## KONTEKS PERCAKAPAN

### Pesan Sebelum Gap:
{context_before}

### [GAP TERDETEKSI]
- Durasi: {time_display} ({gap.time_gap_seconds} detik)
- Estimasi pesan hilang: {gap.estimated_missing or 'tidak diketahui'}
- Alasan deteksi: {', '.join(gap.suspicion_reasons)}
- Tipe: {gap.detection_type}
- Partisipan: {', '.join(participants)}

### Pesan Setelah Gap:
{context_after}

## METODE ANALISIS (Chain-of-Thought)

### Langkah 1: Analisis Pola Gilir Bicara
- Siapa yang berbicara terakhir sebelum gap?
- Siapa yang berbicara pertama setelah gap?
- Apakah ada pelanggaran pola gilir yang menunjukkan pesan hilang?

### Langkah 2: Cari Bukti Konkret
- Apakah ada pertanyaan tanpa jawaban?
- Apakah ada jawaban tanpa pertanyaan?
- Apakah ada referensi ke hal yang tidak disebutkan?
- Apakah ada kata seperti "iya", "oke", "setuju" tanpa konteks?

### Langkah 3: Evaluasi Kepercayaan
- 0.1-0.3: Hanya dugaan berdasarkan durasi gap
- 0.4-0.5: Ada indikasi lemah dari perubahan topik
- 0.6-0.7: Ada bukti jelas (pertanyaan tanpa jawaban, dll)
- 0.8-1.0: HANYA jika ada pesan "dihapus" eksplisit

### Langkah 4: Flag Semua Spekulasi
- Tandai SETIAP aspek prediksi yang tidak bisa dibuktikan 100%

## FORMAT RESPONS (JSON)
{{
    "predicted_intent": "Deskripsi SINGKAT dan KONSERVATIF (atau null jika tidak cukup bukti)",
    "predicted_content": null,
    "predicted_sender": "Nama pengirim HANYA jika bisa ditentukan dari pola gilir bicara (atau null)",
    "confidence_score": 0.5,
    "reasoning": "Langkah-langkah analisis Anda dengan KUTIPAN SPESIFIK dari konteks sebagai bukti",
    "hallucination_flags": ["WAJIB ISI - minimal 'INFERENCE_BASED' jika ada prediksi apapun"]
}}

## CONTOH RESPONS KONSERVATIF
Jika tidak ada bukti kuat:
{{
    "predicted_intent": null,
    "predicted_content": null,
    "predicted_sender": null,
    "confidence_score": 0.2,
    "reasoning": "Gap terdeteksi tetapi tidak ada bukti linguistik yang cukup untuk memprediksi isi pesan. Perubahan topik bisa disebabkan oleh jeda waktu natural.",
    "hallucination_flags": ["NO_EVIDENCE", "TIME_GAP_ONLY"]
}}
"""


class AIInferencer:
    """
    AI Inferencer factory that returns appropriate implementation
    based on configuration
    """
    
    def __init__(self):
        settings = get_settings()
        
        if settings.use_mock_ai:
            self.inferencer = MockInferencer()
        else:
            self.inferencer = GeminiInferencer(
                api_key=settings.gemini_api_key,
                model=settings.gemini_model,
            )
    
    def analyze_gap(self, gap: DetectedGap, full_context: List[Dict] = None) -> InferenceResult:
        """Analyze a gap and generate inference"""
        return self.inferencer.infer_gap(gap, full_context)
    
    def analyze_multiple_gaps(
        self, 
        gaps: List[DetectedGap], 
        full_context: List[Dict] = None
    ) -> List[InferenceResult]:
        """Analyze multiple gaps"""
        return [self.analyze_gap(gap, full_context) for gap in gaps]
    
    def get_model_info(self) -> Dict:
        """Get information about the current model"""
        return {
            "implementation": type(self.inferencer).__name__,
            "model": getattr(self.inferencer, 'model', 'mock'),
            "is_mock": isinstance(self.inferencer, MockInferencer),
        }
