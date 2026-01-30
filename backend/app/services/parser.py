"""
WhatsApp Chat Parser
Parses WhatsApp exported .txt chat files into structured data
"""
import re
from datetime import datetime
from dataclasses import dataclass
from typing import List, Optional, Tuple


@dataclass
class ParsedMessage:
    """Represents a parsed message from WhatsApp export"""
    timestamp: datetime
    sender: str
    content: str
    sequence_number: int
    message_type: str = "text"
    is_deleted: bool = False
    has_media: bool = False


class WhatsAppParser:
    """
    Parser for WhatsApp exported chat files (.txt format)
    
    Supports formats:
    - DD/MM/YYYY, HH:MM - Sender: Message
    - MM/DD/YY, HH:MM AM/PM - Sender: Message
    - [DD/MM/YYYY, HH:MM:SS] Sender: Message
    """
    
    # Multiple regex patterns for different WhatsApp export formats
    PATTERNS = [
        # Format: DD/MM/YYYY, HH:MM - Sender: Message
        re.compile(
            r'^(\d{1,2}/\d{1,2}/\d{2,4}),?\s+(\d{1,2}:\d{2}(?::\d{2})?(?:\s*[APap][Mm])?)\s*[-–]\s*([^:]+):\s*(.*)$'
        ),
        # Format: [DD/MM/YYYY, HH:MM:SS] Sender: Message
        re.compile(
            r'^\[(\d{1,2}/\d{1,2}/\d{2,4}),?\s+(\d{1,2}:\d{2}:\d{2})\]\s*([^:]+):\s*(.*)$'
        ),
        # Format: YYYY-MM-DD HH:MM:SS - Sender: Message
        re.compile(
            r'^(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2}:\d{2})\s*[-–]\s*([^:]+):\s*(.*)$'
        ),
    ]
    
    # System message patterns (not from a sender)
    SYSTEM_PATTERNS = [
        re.compile(r'Messages and calls are end-to-end encrypted', re.IGNORECASE),
        re.compile(r'created group', re.IGNORECASE),
        re.compile(r'added you', re.IGNORECASE),
        re.compile(r'changed the subject', re.IGNORECASE),
        re.compile(r'left the group', re.IGNORECASE),
        re.compile(r'removed \w+', re.IGNORECASE),
    ]
    
    # Deleted message patterns
    DELETED_PATTERNS = [
        re.compile(r'^This message was deleted\.?$', re.IGNORECASE),
        re.compile(r'^You deleted this message\.?$', re.IGNORECASE),
        re.compile(r'^Pesan ini telah dihapus\.?$', re.IGNORECASE),  # Indonesian
    ]
    
    # Media patterns
    MEDIA_PATTERNS = [
        re.compile(r'<Media omitted>', re.IGNORECASE),
        re.compile(r'\(file attached\)', re.IGNORECASE),
        re.compile(r'image omitted', re.IGNORECASE),
        re.compile(r'video omitted', re.IGNORECASE),
        re.compile(r'audio omitted', re.IGNORECASE),
        re.compile(r'GIF omitted', re.IGNORECASE),
        re.compile(r'sticker omitted', re.IGNORECASE),
    ]
    
    def __init__(self):
        self.messages: List[ParsedMessage] = []
        self.participants: set = set()
        self.parse_errors: List[Tuple[int, str]] = []
    
    def parse(self, content: str) -> List[ParsedMessage]:
        """
        Parse WhatsApp export content into structured messages
        
        Args:
            content: Raw text content from WhatsApp export file
            
        Returns:
            List of ParsedMessage objects
        """
        self.messages = []
        self.participants = set()
        self.parse_errors = []
        
        lines = content.strip().split('\n')
        current_message = None
        sequence = 0
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line:
                continue
            
            # Try to parse as new message
            parsed = self._try_parse_line(line)
            
            if parsed:
                # Save previous message if exists
                if current_message:
                    self.messages.append(current_message)
                
                sequence += 1
                timestamp, sender, content_text = parsed
                
                # Detect message type
                msg_type, is_deleted, has_media = self._classify_message(content_text)
                
                current_message = ParsedMessage(
                    timestamp=timestamp,
                    sender=sender,
                    content=content_text,
                    sequence_number=sequence,
                    message_type=msg_type,
                    is_deleted=is_deleted,
                    has_media=has_media,
                )
                self.participants.add(sender)
            else:
                # Continuation of previous message (multi-line)
                if current_message:
                    current_message.content += f"\n{line}"
                else:
                    # Line at start that doesn't match pattern
                    self.parse_errors.append((line_num, line))
        
        # Don't forget the last message
        if current_message:
            self.messages.append(current_message)
        
        return self.messages
    
    def _try_parse_line(self, line: str) -> Optional[Tuple[datetime, str, str]]:
        """Try to parse a line using various patterns"""
        for pattern in self.PATTERNS:
            match = pattern.match(line)
            if match:
                groups = match.groups()
                date_str = groups[0]
                time_str = groups[1]
                sender = groups[2].strip()
                content = groups[3] if len(groups) > 3 else ""
                
                timestamp = self._parse_datetime(date_str, time_str)
                if timestamp:
                    return timestamp, sender, content
        
        return None
    
    def _parse_datetime(self, date_str: str, time_str: str) -> Optional[datetime]:
        """Parse date and time strings into datetime object"""
        formats = [
            ("%d/%m/%Y %H:%M", f"{date_str} {time_str}"),
            ("%d/%m/%y %H:%M", f"{date_str} {time_str}"),
            ("%m/%d/%Y %I:%M %p", f"{date_str} {time_str}"),
            ("%m/%d/%y %I:%M %p", f"{date_str} {time_str}"),
            ("%Y-%m-%d %H:%M:%S", f"{date_str} {time_str}"),
            ("%d/%m/%Y %H:%M:%S", f"{date_str} {time_str}"),
        ]
        
        for fmt, dt_str in formats:
            try:
                return datetime.strptime(dt_str.strip(), fmt)
            except ValueError:
                continue
        
        return None
    
    def _classify_message(self, content: str) -> Tuple[str, bool, bool]:
        """
        Classify message type, deletion status, and media presence
        
        Returns:
            Tuple of (message_type, is_deleted, has_media)
        """
        # Check for deleted messages
        for pattern in self.DELETED_PATTERNS:
            if pattern.search(content):
                return "deleted", True, False
        
        # Check for system messages
        for pattern in self.SYSTEM_PATTERNS:
            if pattern.search(content):
                return "system", False, False
        
        # Check for media
        for pattern in self.MEDIA_PATTERNS:
            if pattern.search(content):
                return "media", False, True
        
        return "text", False, False
    
    def get_participants(self) -> List[str]:
        """Get list of unique participants"""
        return list(self.participants)
    
    def get_time_range(self) -> Tuple[Optional[datetime], Optional[datetime]]:
        """Get start and end timestamps of the chat"""
        if not self.messages:
            return None, None
        return self.messages[0].timestamp, self.messages[-1].timestamp
    
    def get_stats(self) -> dict:
        """Get parsing statistics"""
        return {
            "total_messages": len(self.messages),
            "participants": len(self.participants),
            "deleted_count": sum(1 for m in self.messages if m.is_deleted),
            "media_count": sum(1 for m in self.messages if m.has_media),
            "parse_errors": len(self.parse_errors),
        }
