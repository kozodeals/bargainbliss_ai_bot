import json
import os
from typing import Dict, Any, Optional

class MessageManager:
    """Manages bot messages loaded from configuration file."""
    
    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        self.messages: Dict[str, str] = {}
        self.settings: Dict[str, Any] = {}
        self.load_config()
    
    def load_config(self) -> None:
        """Load configuration from JSON file."""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.messages = config.get('messages', {})
                    self.settings = config.get('settings', {})
                print(f"✅ Loaded {len(self.messages)} messages from {self.config_file}")
            else:
                print(f"⚠️ Config file {self.config_file} not found, using default messages")
                self._set_default_messages()
        except Exception as e:
            print(f"❌ Error loading config: {e}")
            self._set_default_messages()
    
    def reload_config(self) -> None:
        """Reload configuration from file."""
        self.load_config()
    
    def get_message(self, key: str, **kwargs) -> str:
        """Get a message by key, with optional formatting."""
        message = self.messages.get(key, f"Message not found: {key}")
        
        if kwargs:
            try:
                return message.format(**kwargs)
            except KeyError as e:
                print(f"⚠️ Missing format key {e} for message '{key}'")
                return message
        
        return message
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a setting value by key."""
        return self.settings.get(key, default)
    
    def update_message(self, key: str, new_message: str) -> bool:
        """Update a message in memory and save to file."""
        try:
            self.messages[key] = new_message
            self._save_config()
            return True
        except Exception as e:
            print(f"❌ Error updating message: {e}")
            return False
    
    def add_message(self, key: str, message: str) -> bool:
        """Add a new message."""
        return self.update_message(key, message)
    
    def delete_message(self, key: str) -> bool:
        """Delete a message."""
        try:
            if key in self.messages:
                del self.messages[key]
                self._save_config()
                return True
            return False
        except Exception as e:
            print(f"❌ Error deleting message: {e}")
            return False
    
    def list_messages(self) -> Dict[str, str]:
        """Get all messages."""
        return self.messages.copy()
    
    def _save_config(self) -> None:
        """Save current configuration to file."""
        try:
            config = {
                'messages': self.messages,
                'settings': self.settings
            }
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            print(f"✅ Configuration saved to {self.config_file}")
        except Exception as e:
            print(f"❌ Error saving config: {e}")
    
    def _set_default_messages(self) -> None:
        """Set default messages if config file is not available."""
        self.messages = {
            "start": "שלום! אני בוט שמסייע בהמרת קישורי AliExpress לקישורי שותפים.",
            "tips": "💡 טיפים לשימוש יעיל...",
            "help": "🤖 עזרה - בוט AliExpress",
            "invalid_link": "❌ קישור לא תקין!",
            "affiliate_success": "✅ הצלחה! קישור שותפים נוצר: {affiliate_url}"
        }
        self.settings = {
            "max_url_length": 500,
            "rate_limit_seconds": 5,
            "max_requests_per_minute": 12
        }

# Global instance
message_manager = MessageManager() 