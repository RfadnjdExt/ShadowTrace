"""
Gap Detection Engine
Detects suspicious gaps and deletions in chat conversations
"""
import json
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import List, Optional
from statistics import mean, stdev

from app.services.parser import ParsedMessage


@dataclass
class DetectedGap:
    """Represents a detected gap in conversation"""
    before_seq: int
    after_seq: int
    before_timestamp: datetime
    after_timestamp: datetime
    time_gap_seconds: int
    detection_type: str
    suspicion_score: float
    suspicion_reasons: List[str]
    context_before: List[dict]
    context_after: List[dict]
    estimated_missing: Optional[int] = None


class GapDetector:
    """
    Detects suspicious gaps in chat conversations
    
    Detection strategies:
    1. Time Anomaly: Unusual time gaps based on conversation patterns
    2. Context Mismatch: Topic shifts that suggest missing messages
    3. Pattern Break: Changes in sender response patterns
    4. Explicit Deletion: Messages marked as deleted
    """
    
    # Thresholds (configurable)
    MIN_SUSPICIOUS_GAP_MINUTES = 30  # Minimum gap to consider suspicious
    MAX_NORMAL_GAP_HOURS = 8  # Maximum "normal" gap (e.g., sleep)
    CONTEXT_WINDOW = 3  # Messages before/after gap for context
    
    def __init__(self, messages: List[ParsedMessage]):
        self.messages = messages
        self.gaps: List[DetectedGap] = []
        self.avg_gap: float = 0
        self.gap_stdev: float = 0
        
        # Calculate baseline metrics
        self._calculate_baseline()
    
    def _calculate_baseline(self):
        """Calculate baseline gap statistics for the conversation"""
        if len(self.messages) < 2:
            return
        
        gaps = []
        for i in range(1, len(self.messages)):
            gap = (self.messages[i].timestamp - self.messages[i-1].timestamp).total_seconds()
            # Only include "normal" gaps (exclude obvious sleep/offline periods)
            if gap < self.MAX_NORMAL_GAP_HOURS * 3600:
                gaps.append(gap)
        
        if gaps:
            self.avg_gap = mean(gaps)
            if len(gaps) > 1:
                self.gap_stdev = stdev(gaps)
    
    def detect_all(self) -> List[DetectedGap]:
        """Run all gap detection strategies"""
        self.gaps = []
        
        if len(self.messages) < 2:
            return self.gaps
        
        for i in range(1, len(self.messages)):
            prev_msg = self.messages[i-1]
            curr_msg = self.messages[i]
            
            gap_seconds = int((curr_msg.timestamp - prev_msg.timestamp).total_seconds())
            
            # Collect all suspicious indicators
            suspicion_reasons = []
            detection_types = []
            
            # Check for time anomaly
            if self._is_time_anomaly(gap_seconds):
                detection_types.append("time_anomaly")
                suspicion_reasons.append(f"Unusual gap of {gap_seconds//60} minutes detected")
            
            # Check for explicit deletions adjacent to gap
            if prev_msg.is_deleted or curr_msg.is_deleted:
                detection_types.append("explicit_deletion")
                suspicion_reasons.append("Adjacent message marked as deleted")
            
            # Check for context mismatch (topic shift)
            if self._has_context_mismatch(i):
                detection_types.append("context_mismatch")
                suspicion_reasons.append("Abrupt topic change suggests missing context")
            
            # Check for pattern break (response pattern changes)
            pattern_break = self._check_pattern_break(i)
            if pattern_break:
                detection_types.append("pattern_break")
                suspicion_reasons.append(pattern_break)
            
            # If any suspicious indicators found, record the gap
            if suspicion_reasons:
                score = self._calculate_suspicion_score(
                    gap_seconds, 
                    detection_types, 
                    len(suspicion_reasons)
                )
                
                gap = DetectedGap(
                    before_seq=prev_msg.sequence_number,
                    after_seq=curr_msg.sequence_number,
                    before_timestamp=prev_msg.timestamp,
                    after_timestamp=curr_msg.timestamp,
                    time_gap_seconds=gap_seconds,
                    detection_type=detection_types[0],  # Primary type
                    suspicion_score=score,
                    suspicion_reasons=suspicion_reasons,
                    context_before=self._get_context(i, before=True),
                    context_after=self._get_context(i, before=False),
                    estimated_missing=self._estimate_missing_messages(gap_seconds),
                )
                self.gaps.append(gap)
        
        return self.gaps
    
    def _is_time_anomaly(self, gap_seconds: int) -> bool:
        """Check if the gap is statistically anomalous"""
        if gap_seconds < self.MIN_SUSPICIOUS_GAP_MINUTES * 60:
            return False
        
        # If within normal hours but significantly above average
        if self.gap_stdev > 0:
            z_score = (gap_seconds - self.avg_gap) / self.gap_stdev
            return z_score > 2.5  # More than 2.5 standard deviations
        
        # Fallback: just check if gap is large
        return gap_seconds > self.MIN_SUSPICIOUS_GAP_MINUTES * 60 * 3
    
    def _has_context_mismatch(self, index: int) -> bool:
        """
        Check if there's an abrupt topic change suggesting missing messages
        Uses simple heuristics - could be enhanced with NLP
        """
        if index < 1 or index >= len(self.messages):
            return False
        
        prev_msg = self.messages[index - 1]
        curr_msg = self.messages[index]
        
        # Heuristic: If current message starts with a greeting after a non-goodbye message
        greetings = ['hi', 'hello', 'hey', 'halo', 'hai', 'pagi', 'siang', 'sore', 'malam']
        goodbyes = ['bye', 'goodbye', 'see you', 'sampai', 'dah', 'dadah']
        
        curr_lower = curr_msg.content.lower().strip()
        prev_lower = prev_msg.content.lower().strip()
        
        # Starts with greeting but previous wasn't a goodbye
        if any(curr_lower.startswith(g) for g in greetings):
            if not any(g in prev_lower for g in goodbyes):
                return True
        
        # Response without question (simplified check)
        if curr_lower.startswith(('ya', 'iya', 'yes', 'no', 'tidak', 'ok', 'oke', 'okay')):
            if '?' not in prev_lower:
                return True
        
        return False
    
    def _check_pattern_break(self, index: int) -> Optional[str]:
        """
        Check for breaks in sender response patterns
        Returns description of pattern break if found
        """
        if index < 3:
            return None
        
        # Get recent sender pattern
        recent_senders = [m.sender for m in self.messages[max(0, index-5):index]]
        prev_sender = self.messages[index-1].sender
        curr_sender = self.messages[index].sender
        
        # Check if same sender messages in a row (unusual in conversation)
        if prev_sender == curr_sender:
            # Count consecutive messages from same sender before gap
            consecutive = 0
            for j in range(index-1, max(0, index-10), -1):
                if self.messages[j].sender == prev_sender:
                    consecutive += 1
                else:
                    break
            
            # If sender had many messages and now continues after gap
            if consecutive >= 3:
                return f"Same sender ({prev_sender}) continues after gap - possible response deleted"
        
        return None
    
    def _calculate_suspicion_score(
        self, 
        gap_seconds: int, 
        detection_types: List[str], 
        reason_count: int
    ) -> float:
        """
        Calculate overall suspicion score (0.0 to 1.0)
        Higher scores indicate more suspicious gaps
        """
        score = 0.0
        
        # Base score from gap duration
        if gap_seconds > 3600 * 4:  # 4+ hours
            score += 0.2
        elif gap_seconds > 3600:  # 1-4 hours
            score += 0.15
        else:
            score += 0.1
        
        # Detection type weights
        type_weights = {
            "explicit_deletion": 0.35,
            "context_mismatch": 0.25,
            "pattern_break": 0.2,
            "time_anomaly": 0.15,
        }
        
        for dt in detection_types:
            score += type_weights.get(dt, 0.1)
        
        # Additional reasons bonus
        score += min(reason_count * 0.05, 0.15)
        
        return min(score, 1.0)
    
    def _get_context(self, index: int, before: bool) -> List[dict]:
        """Get context messages before or after the gap"""
        context = []
        
        if before:
            start = max(0, index - self.CONTEXT_WINDOW)
            end = index
        else:
            start = index
            end = min(len(self.messages), index + self.CONTEXT_WINDOW)
        
        for i in range(start, end):
            msg = self.messages[i]
            context.append({
                "sequence": msg.sequence_number,
                "sender": msg.sender,
                "content": msg.content[:200] if msg.content else "",  # Truncate for storage
                "timestamp": msg.timestamp.isoformat(),
            })
        
        return context
    
    def _estimate_missing_messages(self, gap_seconds: int) -> Optional[int]:
        """Estimate number of missing messages based on average gap"""
        if self.avg_gap <= 0 or gap_seconds <= self.avg_gap:
            return None
        
        # Rough estimate: how many average-gap intervals fit in this gap
        estimated = int(gap_seconds / self.avg_gap) - 1
        return max(1, min(estimated, 50))  # Cap at reasonable number
    
    def get_high_priority_gaps(self, threshold: float = 0.5) -> List[DetectedGap]:
        """Get only gaps above suspicion threshold"""
        return [g for g in self.gaps if g.suspicion_score >= threshold]
    
    def to_json(self) -> str:
        """Serialize gaps to JSON"""
        return json.dumps([asdict(g) for g in self.gaps], default=str)
