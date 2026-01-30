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
    Real Gemini 3.0 API integration
    Uses context anchoring to minimize hallucination
    """
    
    def __init__(self, api_key: str, model: str = "gemini-2.0-flash"):
        self.api_key = api_key
        self.model = model
        # TODO: Initialize actual Gemini client when needed
        # from google import generativeai as genai
        # genai.configure(api_key=api_key)
        # self.client = genai.GenerativeModel(model)
    
    def infer_gap(self, gap: DetectedGap, full_context: List[Dict] = None) -> InferenceResult:
        """
        Generate inference using Gemini API
        Implements context anchoring for hallucination prevention
        """
        # Build forensic analysis prompt
        prompt = self._build_prompt(gap, full_context)
        
        # TODO: Actual API call
        # response = self.client.generate_content(prompt)
        # parsed = self._parse_response(response.text)
        
        # For now, fall back to mock
        mock = MockInferencer()
        result = mock.infer_gap(gap, full_context)
        result.model_used = f"{self.model} (fallback to mock)"
        result.hallucination_flags.append("GEMINI_NOT_CONFIGURED")
        
        return result
    
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
        
        return f"""You are a forensic chat analyst helping to reconstruct deleted messages.

CONTEXT BEFORE GAP:
{context_before}

[GAP DETECTED - {gap.time_gap_seconds} seconds, estimated {gap.estimated_missing or 'unknown'} missing messages]
Detection reason: {', '.join(gap.suspicion_reasons)}

CONTEXT AFTER GAP:
{context_after}

INSTRUCTIONS:
1. Analyze the conversation flow before and after the gap
2. Predict what was likely discussed in the missing message(s)
3. IMPORTANT: Only make predictions that can be directly anchored to the surrounding context
4. Assign a confidence score (0.0-1.0) based on how strongly the context supports your prediction
5. Flag any aspects of your prediction that could be hallucination

Respond in JSON format:
{{
    "predicted_intent": "Brief description of what was likely discussed",
    "predicted_content": "Possible message content (or null if too speculative)",
    "predicted_sender": "Most likely sender",
    "confidence_score": 0.0-1.0,
    "reasoning": "Explanation of your analysis",
    "hallucination_flags": ["List any aspects that are speculative"]
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
