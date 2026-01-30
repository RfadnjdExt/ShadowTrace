"""
Test Data Generator
Creates synthetic WhatsApp chat exports for testing gap detection
"""
import random
from datetime import datetime, timedelta


class SyntheticChatGenerator:
    """Generates synthetic WhatsApp chat exports with controllable gaps"""
    
    SENDERS = ["Alice", "Bob", "Charlie", "Diana"]
    
    TOPICS = {
        "negotiation": [
            "Kita perlu bicarakan angka ini",
            "Berapa yang bisa kamu tawarkan?",
            "Saya rasa 500 juta terlalu rendah",
            "Mari kita temui di tengah",
            "Oke, saya setuju dengan syaratnya",
            "Kirimkan kontraknya nanti",
        ],
        "planning": [
            "Kapan kita bisa meeting?",
            "Bagaimana kalau Jumat?",
            "Jam 3 sore bisa?",
            "Oke fix, kita ketemu di kantor",
            "Jangan lupa bawa dokumennya",
            "Sudah saya siapkan semuanya",
        ],
        "casual": [
            "Halo, apa kabar?",
            "Baik, kamu gimana?",
            "Sibuk banget minggu ini",
            "Sama, deadline mepet",
            "Semangat ya!",
            "Thanks, kamu juga",
        ],
        "suspicious": [
            "Jangan bicarakan ini di telepon",
            "Hapus semua chat setelah ini",
            "Kita ketemu langsung saja",
            "Pastikan tidak ada yang tahu",
            "Ini harus rahasia",
            "Oke, saya mengerti",
        ],
    }
    
    def __init__(self, seed: int = None):
        if seed:
            random.seed(seed)
    
    def generate(
        self,
        num_messages: int = 100,
        num_gaps: int = 5,
        include_deletions: bool = True,
        include_suspicious: bool = True,
        start_date: datetime = None,
    ) -> str:
        """
        Generate synthetic WhatsApp chat export
        
        Args:
            num_messages: Number of messages to generate
            num_gaps: Number of suspicious gaps to insert
            include_deletions: Include "This message was deleted" markers
            include_suspicious: Include suspicious conversation patterns
            start_date: Starting timestamp (defaults to 30 days ago)
        
        Returns:
            WhatsApp export formatted string
        """
        if start_date is None:
            start_date = datetime.now() - timedelta(days=30)
        
        messages = []
        current_time = start_date
        senders = random.sample(self.SENDERS, min(3, len(self.SENDERS)))
        
        # Determine gap positions
        gap_positions = sorted(random.sample(
            range(10, num_messages - 10), 
            min(num_gaps, num_messages - 20)
        ))
        
        # Generate messages
        for i in range(num_messages):
            # Check if we should insert a gap
            if i in gap_positions:
                # Insert suspicious gap (2-6 hours)
                gap_minutes = random.randint(120, 360)
                current_time += timedelta(minutes=gap_minutes)
                
                # Maybe insert a deleted message marker
                if include_deletions and random.random() > 0.5:
                    deleted_msg = self._format_message(
                        current_time,
                        random.choice(senders),
                        "Pesan ini telah dihapus."
                    )
                    messages.append(deleted_msg)
                    current_time += timedelta(seconds=random.randint(5, 30))
            else:
                # Normal gap (30 seconds to 15 minutes)
                gap_seconds = random.randint(30, 900)
                current_time += timedelta(seconds=gap_seconds)
            
            # Select topic
            if include_suspicious and i in gap_positions:
                topic = "suspicious"
            else:
                topic = random.choice(["negotiation", "planning", "casual"])
            
            # Generate message
            sender = random.choice(senders)
            content = random.choice(self.TOPICS[topic])
            
            # Sometimes add longer messages
            if random.random() > 0.7:
                content += " " + random.choice(self.TOPICS[topic])
            
            messages.append(self._format_message(current_time, sender, content))
        
        # Add WhatsApp header
        header = "Messages and calls are end-to-end encrypted. No one outside of this chat can read or listen to them.\n"
        
        return header + "\n".join(messages)
    
    def _format_message(self, timestamp: datetime, sender: str, content: str) -> str:
        """Format a single message in WhatsApp export format"""
        date_str = timestamp.strftime("%d/%m/%Y")
        time_str = timestamp.strftime("%H:%M")
        return f"{date_str}, {time_str} - {sender}: {content}"
    
    def generate_with_explicit_deletions(
        self,
        num_messages: int = 50,
        deletion_count: int = 5,
    ) -> str:
        """Generate chat with explicit deletion markers at specific positions"""
        start_date = datetime.now() - timedelta(days=7)
        messages = []
        current_time = start_date
        senders = ["Pejabat A", "Pejabat B"]
        
        # Positions where deletions happened
        deletion_positions = sorted(random.sample(
            range(5, num_messages - 5),
            min(deletion_count, num_messages - 10)
        ))
        
        msg_index = 0
        for i in range(num_messages):
            current_time += timedelta(seconds=random.randint(60, 300))
            sender = senders[i % 2]
            
            if i in deletion_positions:
                # This is a deleted message
                messages.append(self._format_message(
                    current_time,
                    sender,
                    "Pesan ini telah dihapus."
                ))
            else:
                # Normal message
                topic = random.choice(["negotiation", "planning"])
                content = random.choice(self.TOPICS[topic])
                messages.append(self._format_message(current_time, sender, content))
        
        return "\n".join(messages)


def generate_test_file(output_path: str = "test_chat.txt"):
    """Generate and save a test chat file"""
    generator = SyntheticChatGenerator(seed=42)
    content = generator.generate(
        num_messages=150,
        num_gaps=8,
        include_deletions=True,
        include_suspicious=True,
    )
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Generated test chat: {output_path}")
    return output_path


if __name__ == "__main__":
    generate_test_file()
