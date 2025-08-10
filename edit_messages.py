#!/usr/bin/env python3
"""
Simple interface to edit bot messages.
Run this script to easily modify bot messages without editing Python code.
"""

import json
import os
from message_manager import MessageManager

def print_header():
    """Print a nice header."""
    print("=" * 60)
    print("🤖 BOT MESSAGE EDITOR")
    print("=" * 60)
    print("Edit your bot messages easily without touching Python code!")
    print("=" * 60)

def print_menu():
    """Print the main menu."""
    print("\n📋 MAIN MENU:")
    print("1. 📝 Edit a message")
    print("2. 👀 View all messages")
    print("3. 🔍 Search messages")
    print("4. ➕ Add new message")
    print("5. ❌ Delete a message")
    print("6. 🔄 Reload config")
    print("7. 💾 Save changes")
    print("8. ❓ Help")
    print("0. 🚪 Exit")
    print("-" * 60)

def edit_message(message_manager: MessageManager):
    """Edit a specific message."""
    print("\n📝 EDIT MESSAGE")
    print("-" * 30)
    
    # Show available messages
    messages = message_manager.list_messages()
    if not messages:
        print("❌ No messages available!")
        return
    
    print("Available messages:")
    for i, (key, value) in enumerate(messages.items(), 1):
        preview = value[:50] + "..." if len(value) > 50 else value
        print(f"{i}. {key}: {preview}")
    
    try:
        choice = input("\nEnter message number to edit (or 'back'): ").strip()
        if choice.lower() == 'back':
            return
        
        choice_num = int(choice)
        if choice_num < 1 or choice_num > len(messages):
            print("❌ Invalid choice!")
            return
        
        # Get the key for the selected message
        message_key = list(messages.keys())[choice_num - 1]
        current_message = messages[message_key]
        
        print(f"\n📝 Editing: {message_key}")
        print(f"Current message:\n{current_message}")
        print("\n" + "="*50)
        
        print("Enter new message (or 'cancel' to go back):")
        print("💡 Tip: Use \\n for new lines")
        
        new_message = input("New message: ").strip()
        if new_message.lower() == 'cancel':
            return
        
        # Replace \n with actual newlines
        new_message = new_message.replace('\\n', '\n')
        
        if message_manager.update_message(message_key, new_message):
            print(f"✅ Message '{message_key}' updated successfully!")
        else:
            print("❌ Failed to update message!")
            
    except ValueError:
        print("❌ Please enter a valid number!")
    except KeyboardInterrupt:
        print("\n\n⚠️ Operation cancelled.")
    except Exception as e:
        print(f"❌ Error: {e}")

def view_messages(message_manager: MessageManager):
    """View all messages."""
    print("\n👀 ALL MESSAGES")
    print("-" * 30)
    
    messages = message_manager.list_messages()
    if not messages:
        print("❌ No messages available!")
        return
    
    for i, (key, value) in enumerate(messages.items(), 1):
        print(f"\n{i}. {key}:")
        print("-" * (len(key) + 2))
        print(value)
        print("-" * 50)

def search_messages(message_manager: MessageManager):
    """Search through messages."""
    print("\n🔍 SEARCH MESSAGES")
    print("-" * 30)
    
    search_term = input("Enter search term: ").strip().lower()
    if not search_term:
        print("❌ Please enter a search term!")
        return
    
    messages = message_manager.list_messages()
    found_messages = []
    
    for key, value in messages.items():
        if search_term in key.lower() or search_term in value.lower():
            found_messages.append((key, value))
    
    if not found_messages:
        print(f"❌ No messages found containing '{search_term}'")
        return
    
    print(f"\n✅ Found {len(found_messages)} messages:")
    for i, (key, value) in enumerate(found_messages, 1):
        preview = value[:100] + "..." if len(value) > 100 else value
        print(f"\n{i}. {key}:")
        print(f"   {preview}")

def add_message(message_manager: MessageManager):
    """Add a new message."""
    print("\n➕ ADD NEW MESSAGE")
    print("-" * 30)
    
    key = input("Enter message key (e.g., 'welcome'): ").strip()
    if not key:
        print("❌ Message key cannot be empty!")
        return
    
    messages = message_manager.list_messages()
    if key in messages:
        print(f"❌ Message key '{key}' already exists!")
        return
    
    print("Enter message content (or 'cancel' to go back):")
    print("💡 Tip: Use \\n for new lines")
    
    content = input("Message content: ").strip()
    if content.lower() == 'cancel':
        return
    
    # Replace \n with actual newlines
    content = content.replace('\\n', '\n')
    
    if message_manager.add_message(key, content):
        print(f"✅ Message '{key}' added successfully!")
    else:
        print("❌ Failed to add message!")

def delete_message(message_manager: MessageManager):
    """Delete a message."""
    print("\n❌ DELETE MESSAGE")
    print("-" * 30)
    
    messages = message_manager.list_messages()
    if not messages:
        print("❌ No messages available!")
        return
    
    print("Available messages:")
    for i, (key, value) in enumerate(messages.items(), 1):
        preview = value[:50] + "..." if len(value) > 50 else value
        print(f"{i}. {key}: {preview}")
    
    try:
        choice = input("\nEnter message number to delete (or 'back'): ").strip()
        if choice.lower() == 'back':
            return
        
        choice_num = int(choice)
        if choice_num < 1 or choice_num > len(messages):
            print("❌ Invalid choice!")
            return
        
        # Get the key for the selected message
        message_key = list(messages.keys())[choice_num - 1]
        
        # Confirm deletion
        confirm = input(f"\n⚠️ Are you sure you want to delete '{message_key}'? (yes/no): ").strip().lower()
        if confirm in ['yes', 'y']:
            if message_manager.delete_message(message_key):
                print(f"✅ Message '{message_key}' deleted successfully!")
            else:
                print("❌ Failed to delete message!")
        else:
            print("❌ Deletion cancelled.")
            
    except ValueError:
        print("❌ Please enter a valid number!")
    except KeyboardInterrupt:
        print("\n\n⚠️ Operation cancelled.")
    except Exception as e:
        print(f"❌ Error: {e}")

def show_help():
    """Show help information."""
    print("\n❓ HELP")
    print("-" * 30)
    print("This tool helps you edit bot messages without touching Python code.")
    print("\n📝 EDIT MESSAGE:")
    print("  • Choose a message to edit")
    print("  • Type your new message")
    print("  • Use \\n for new lines")
    print("  • Changes are saved automatically")
    print("\n🔍 SEARCH:")
    print("  • Search by message key or content")
    print("  • Useful for finding specific messages")
    print("\n➕ ADD MESSAGE:")
    print("  • Create new message keys")
    print("  • Use descriptive keys like 'welcome' or 'error_404'")
    print("\n❌ DELETE MESSAGE:")
    print("  • Remove unused messages")
    print("  • Requires confirmation")
    print("\n💾 SAVE:")
    print("  • Changes are saved automatically")
    print("  • Use 'Reload config' if you edit config.json manually")

def main():
    """Main function."""
    try:
        # Initialize message manager
        message_manager = MessageManager()
        
        while True:
            print_header()
            print_menu()
            
            choice = input("\nEnter your choice (0-8): ").strip()
            
            if choice == '0':
                print("\n👋 Goodbye! Your changes have been saved.")
                break
            elif choice == '1':
                edit_message(message_manager)
            elif choice == '2':
                view_messages(message_manager)
            elif choice == '3':
                search_messages(message_manager)
            elif choice == '4':
                add_message(message_manager)
            elif choice == '5':
                delete_message(message_manager)
            elif choice == '6':
                message_manager.reload_config()
                print("✅ Configuration reloaded!")
            elif choice == '7':
                print("💾 Changes are saved automatically!")
            elif choice == '8':
                show_help()
            else:
                print("❌ Invalid choice! Please enter 0-8.")
            
            input("\nPress Enter to continue...")
            os.system('cls' if os.name == 'nt' else 'clear')
            
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye! Your changes have been saved.")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        input("Press Enter to exit...")

if __name__ == "__main__":
    main() 