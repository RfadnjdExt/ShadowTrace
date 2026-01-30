"""
Unit tests for WhatsApp Parser
"""
import pytest
from datetime import datetime
from app.services.parser import WhatsAppParser


class TestWhatsAppParser:
    """Test suite for WhatsApp chat parser"""
    
    def test_parse_standard_format(self):
        """Test parsing standard WhatsApp format"""
        content = """12/01/2024, 10:30 - Alice: Hello Bob!
12/01/2024, 10:31 - Bob: Hey Alice, how are you?
12/01/2024, 10:32 - Alice: I'm good, thanks!"""
        
        parser = WhatsAppParser()
        messages = parser.parse(content)
        
        assert len(messages) == 3
        assert messages[0].sender == "Alice"
        assert messages[0].content == "Hello Bob!"
        assert messages[1].sender == "Bob"
        assert messages[2].sequence_number == 3
    
    def test_detect_deleted_message(self):
        """Test detection of deleted messages"""
        content = """12/01/2024, 10:30 - Alice: Normal message
12/01/2024, 10:31 - Bob: Pesan ini telah dihapus.
12/01/2024, 10:32 - Alice: Another message"""
        
        parser = WhatsAppParser()
        messages = parser.parse(content)
        
        assert len(messages) == 3
        assert messages[1].is_deleted == True
        assert messages[1].message_type == "deleted"
    
    def test_detect_media_omitted(self):
        """Test detection of media messages"""
        content = """12/01/2024, 10:30 - Alice: Check this out
12/01/2024, 10:31 - Alice: <Media omitted>
12/01/2024, 10:32 - Bob: Nice photo!"""
        
        parser = WhatsAppParser()
        messages = parser.parse(content)
        
        assert len(messages) == 3
        assert messages[1].has_media == True
        assert messages[1].message_type == "media"
    
    def test_multiline_messages(self):
        """Test parsing multi-line messages"""
        content = """12/01/2024, 10:30 - Alice: This is a long message
that spans multiple
lines in the chat
12/01/2024, 10:31 - Bob: Got it!"""
        
        parser = WhatsAppParser()
        messages = parser.parse(content)
        
        assert len(messages) == 2
        assert "multiple" in messages[0].content
        assert "lines" in messages[0].content
    
    def test_get_participants(self):
        """Test extracting participants"""
        content = """12/01/2024, 10:30 - Alice: Hello
12/01/2024, 10:31 - Bob: Hi
12/01/2024, 10:32 - Charlie: Hey"""
        
        parser = WhatsAppParser()
        parser.parse(content)
        participants = parser.get_participants()
        
        assert len(participants) == 3
        assert "Alice" in participants
        assert "Bob" in participants
        assert "Charlie" in participants
    
    def test_get_stats(self):
        """Test getting parse statistics"""
        content = """12/01/2024, 10:30 - Alice: Hello
12/01/2024, 10:31 - Bob: Pesan ini telah dihapus.
12/01/2024, 10:32 - Alice: <Media omitted>"""
        
        parser = WhatsAppParser()
        parser.parse(content)
        stats = parser.get_stats()
        
        assert stats["total_messages"] == 3
        assert stats["deleted_count"] == 1
        assert stats["media_count"] == 1
        assert stats["participants"] == 2


class TestGapDetector:
    """Test suite for gap detector"""
    
    def test_detect_time_anomaly(self):
        """Test detection of unusual time gaps"""
        from app.services.parser import ParsedMessage
        from app.services.gap_detector import GapDetector
        
        # Create messages with a large gap
        messages = [
            ParsedMessage(
                timestamp=datetime(2024, 1, 1, 10, 0),
                sender="Alice",
                content="Message 1",
                sequence_number=1,
            ),
            ParsedMessage(
                timestamp=datetime(2024, 1, 1, 10, 5),
                sender="Bob",
                content="Message 2",
                sequence_number=2,
            ),
            # 3 hour gap
            ParsedMessage(
                timestamp=datetime(2024, 1, 1, 13, 5),
                sender="Alice",
                content="Message 3",
                sequence_number=3,
            ),
            ParsedMessage(
                timestamp=datetime(2024, 1, 1, 13, 10),
                sender="Bob",
                content="Message 4",
                sequence_number=4,
            ),
        ]
        
        detector = GapDetector(messages)
        gaps = detector.detect_all()
        
        # Should detect the 3-hour gap
        assert len(gaps) >= 1
        
        # Find the gap between seq 2 and 3
        gap = next((g for g in gaps if g.before_seq == 2), None)
        assert gap is not None
        assert gap.time_gap_seconds == 3 * 3600  # 3 hours in seconds


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
