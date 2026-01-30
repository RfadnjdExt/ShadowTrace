"""
Metadata Extraction Engine
Analyzes patterns from chat metadata for forensic insights
"""
from datetime import datetime, timedelta
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from statistics import mean, stdev

from app.services.parser import ParsedMessage


@dataclass
class SenderStats:
    """Statistics for a single sender"""
    name: str
    message_count: int
    avg_message_length: float
    active_hours: List[int]
    most_active_hour: int
    avg_response_time_seconds: Optional[float]
    deleted_message_count: int


@dataclass 
class ConversationPattern:
    """Detected conversation pattern"""
    pattern_type: str  # peak_hours, response_rhythm, topic_clusters
    description: str
    confidence: float
    data: dict


class MetadataEngine:
    """
    Extracts and analyzes metadata patterns from chat messages
    
    Analysis capabilities:
    - Sender behavior profiling
    - Time-based activity patterns
    - Response time analysis
    - Anomaly detection in messaging patterns
    """
    
    def __init__(self, messages: List[ParsedMessage]):
        self.messages = messages
        self.senders: Dict[str, List[ParsedMessage]] = defaultdict(list)
        
        # Group messages by sender
        for msg in messages:
            self.senders[msg.sender].append(msg)
    
    def analyze_sender(self, sender: str) -> Optional[SenderStats]:
        """Analyze a specific sender's messaging patterns"""
        sender_msgs = self.senders.get(sender)
        if not sender_msgs:
            return None
        
        # Calculate message lengths
        lengths = [len(m.content) for m in sender_msgs if m.content]
        avg_length = mean(lengths) if lengths else 0
        
        # Analyze active hours
        hours = [m.timestamp.hour for m in sender_msgs]
        hour_counts = Counter(hours)
        most_active = hour_counts.most_common(1)[0][0] if hour_counts else 12
        
        # Calculate average response time
        response_times = self._calculate_response_times(sender)
        avg_response = mean(response_times) if response_times else None
        
        # Count deleted messages
        deleted_count = sum(1 for m in sender_msgs if m.is_deleted)
        
        return SenderStats(
            name=sender,
            message_count=len(sender_msgs),
            avg_message_length=avg_length,
            active_hours=list(hour_counts.keys()),
            most_active_hour=most_active,
            avg_response_time_seconds=avg_response,
            deleted_message_count=deleted_count,
        )
    
    def _calculate_response_times(self, sender: str) -> List[float]:
        """Calculate response times for a sender"""
        response_times = []
        
        for i, msg in enumerate(self.messages):
            if msg.sender != sender or i == 0:
                continue
            
            prev_msg = self.messages[i - 1]
            
            # Only count if responding to different sender
            if prev_msg.sender != sender:
                response_time = (msg.timestamp - prev_msg.timestamp).total_seconds()
                # Ignore very long gaps (likely not direct responses)
                if response_time < 3600:  # 1 hour max
                    response_times.append(response_time)
        
        return response_times
    
    def analyze_all_senders(self) -> List[SenderStats]:
        """Analyze all senders in the conversation"""
        return [
            self.analyze_sender(sender) 
            for sender in self.senders.keys()
        ]
    
    def detect_activity_patterns(self) -> List[ConversationPattern]:
        """Detect patterns in conversation activity"""
        patterns = []
        
        # Peak hours analysis
        peak_pattern = self._analyze_peak_hours()
        if peak_pattern:
            patterns.append(peak_pattern)
        
        # Daily rhythm analysis  
        rhythm_pattern = self._analyze_daily_rhythm()
        if rhythm_pattern:
            patterns.append(rhythm_pattern)
        
        # Conversation burst detection
        burst_pattern = self._detect_conversation_bursts()
        if burst_pattern:
            patterns.append(burst_pattern)
        
        return patterns
    
    def _analyze_peak_hours(self) -> Optional[ConversationPattern]:
        """Find peak activity hours"""
        if not self.messages:
            return None
        
        hour_counts = Counter(m.timestamp.hour for m in self.messages)
        
        if not hour_counts:
            return None
        
        # Find top 3 peak hours
        peaks = hour_counts.most_common(3)
        peak_hours = [h for h, _ in peaks]
        
        return ConversationPattern(
            pattern_type="peak_hours",
            description=f"Most active hours: {', '.join(f'{h}:00' for h in peak_hours)}",
            confidence=0.9,
            data={
                "peak_hours": peak_hours,
                "hour_distribution": dict(hour_counts),
            }
        )
    
    def _analyze_daily_rhythm(self) -> Optional[ConversationPattern]:
        """Analyze daily messaging rhythm"""
        if len(self.messages) < 10:
            return None
        
        # Group by day
        days = defaultdict(list)
        for msg in self.messages:
            day_key = msg.timestamp.date()
            days[day_key].append(msg)
        
        # Calculate messages per day
        daily_counts = [len(msgs) for msgs in days.values()]
        
        if not daily_counts:
            return None
        
        avg_daily = mean(daily_counts)
        daily_stdev = stdev(daily_counts) if len(daily_counts) > 1 else 0
        
        return ConversationPattern(
            pattern_type="daily_rhythm", 
            description=f"Average {avg_daily:.1f} messages/day (±{daily_stdev:.1f})",
            confidence=0.85,
            data={
                "avg_daily_messages": avg_daily,
                "daily_stdev": daily_stdev,
                "total_days": len(days),
            }
        )
    
    def _detect_conversation_bursts(self) -> Optional[ConversationPattern]:
        """Detect bursts of intense conversation"""
        if len(self.messages) < 5:
            return None
        
        bursts = []
        current_burst = []
        burst_threshold = 120  # 2 minutes between messages = same burst
        
        for i, msg in enumerate(self.messages):
            if i == 0:
                current_burst = [msg]
                continue
            
            gap = (msg.timestamp - self.messages[i-1].timestamp).total_seconds()
            
            if gap <= burst_threshold:
                current_burst.append(msg)
            else:
                if len(current_burst) >= 5:  # Burst = 5+ rapid messages
                    bursts.append({
                        "start": current_burst[0].timestamp.isoformat(),
                        "end": current_burst[-1].timestamp.isoformat(),
                        "message_count": len(current_burst),
                        "participants": list(set(m.sender for m in current_burst)),
                    })
                current_burst = [msg]
        
        # Don't forget last burst
        if len(current_burst) >= 5:
            bursts.append({
                "start": current_burst[0].timestamp.isoformat(),
                "end": current_burst[-1].timestamp.isoformat(),
                "message_count": len(current_burst),
                "participants": list(set(m.sender for m in current_burst)),
            })
        
        if not bursts:
            return None
        
        return ConversationPattern(
            pattern_type="conversation_bursts",
            description=f"Detected {len(bursts)} intense conversation bursts",
            confidence=0.8,
            data={"bursts": bursts[:10]}  # Limit to first 10
        )
    
    def find_anomalies(self) -> List[Dict]:
        """Find anomalous patterns that might indicate tampering"""
        anomalies = []
        
        # Check for unusual silence periods
        silence_anomaly = self._detect_silence_anomalies()
        if silence_anomaly:
            anomalies.extend(silence_anomaly)
        
        # Check for sender behavior changes
        behavior_anomaly = self._detect_behavior_changes()
        if behavior_anomaly:
            anomalies.extend(behavior_anomaly)
        
        return anomalies
    
    def _detect_silence_anomalies(self) -> List[Dict]:
        """Detect unusual silence periods in active conversations"""
        anomalies = []
        
        if len(self.messages) < 10:
            return anomalies
        
        # Calculate typical gaps
        gaps = []
        for i in range(1, len(self.messages)):
            gap = (self.messages[i].timestamp - self.messages[i-1].timestamp).total_seconds()
            gaps.append((i, gap))
        
        if not gaps:
            return anomalies
        
        avg_gap = mean([g[1] for g in gaps])
        gap_stdev = stdev([g[1] for g in gaps]) if len(gaps) > 1 else 0
        
        # Find gaps that are statistical outliers
        for i, gap in gaps:
            if gap_stdev > 0 and gap > avg_gap + 3 * gap_stdev:
                anomalies.append({
                    "type": "unusual_silence",
                    "position": i,
                    "gap_seconds": gap,
                    "expected_avg": avg_gap,
                    "z_score": (gap - avg_gap) / gap_stdev,
                })
        
        return anomalies
    
    def _detect_behavior_changes(self) -> List[Dict]:
        """Detect sudden changes in sender behavior"""
        anomalies = []
        
        for sender, msgs in self.senders.items():
            if len(msgs) < 10:
                continue
            
            # Split messages into two halves and compare patterns
            mid = len(msgs) // 2
            first_half = msgs[:mid]
            second_half = msgs[mid:]
            
            # Compare message lengths
            avg_first = mean(len(m.content) for m in first_half if m.content) or 0
            avg_second = mean(len(m.content) for m in second_half if m.content) or 0
            
            # Significant change in message length
            if avg_first > 0 and abs(avg_second - avg_first) / avg_first > 0.5:
                anomalies.append({
                    "type": "behavior_change",
                    "sender": sender,
                    "metric": "message_length",
                    "before": avg_first,
                    "after": avg_second,
                    "change_percent": ((avg_second - avg_first) / avg_first) * 100,
                })
        
        return anomalies
    
    def get_summary(self) -> Dict:
        """Get overall metadata summary"""
        if not self.messages:
            return {}
        
        return {
            "total_messages": len(self.messages),
            "total_participants": len(self.senders),
            "participants": list(self.senders.keys()),
            "date_range": {
                "start": self.messages[0].timestamp.isoformat(),
                "end": self.messages[-1].timestamp.isoformat(),
            },
            "deleted_count": sum(1 for m in self.messages if m.is_deleted),
            "media_count": sum(1 for m in self.messages if m.has_media),
        }
