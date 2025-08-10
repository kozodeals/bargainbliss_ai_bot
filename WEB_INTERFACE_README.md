# 🌐 Bot Message Editor - Web Interface

A beautiful, user-friendly web interface for managing your Telegram bot messages without touching any code!

## ✨ Features

- **📱 Modern Web Interface** - Clean, responsive design that works on all devices
- **🔍 Search Messages** - Find messages by key or content
- **✏️ Edit Messages** - Easy inline editing with live preview
- **➕ Add New Messages** - Create new bot messages with helpful suggestions
- **🗑️ Delete Messages** - Remove unwanted messages with confirmation
- **👁️ Live Preview** - See how your messages will look before saving
- **💾 Auto-save** - Changes are automatically saved to `config.json`

## 🚀 Quick Start

### 1. Start the Web Interface

```bash
python web_interface.py
```

### 2. Open Your Browser

Navigate to: **http://localhost:5000**

### 3. Start Editing!

- **View All Messages**: See all your bot messages in a card layout
- **Edit Messages**: Click the edit button on any message card
- **Add New Messages**: Use the "Add New Message" button
- **Search**: Use the search bar to find specific messages

## 🎯 How to Use

### Editing Messages

1. Click the **Edit** button (✏️) on any message card
2. Modify the message content in the text area
3. Use `\n` for line breaks
4. See live preview on the right side
5. Click **Save Changes** when done

### Adding New Messages

1. Click **Add New Message** button
2. Enter a descriptive key (e.g., `welcome_message`)
3. Write your message content
4. Use the **Key Suggestions** button for ideas
5. Click **Create Message**

### Searching Messages

1. Use the search bar at the top
2. Search by message key or content
3. Results are highlighted for easy identification

## 🔧 Message Formatting

### Line Breaks
Use `\n` to create new lines:
```
שלום! אני בוט שמסייע בהמרת קישורי AliExpress.\n\n📋 איך להשתמש:\n1. שלח לי קישור
```

### HTML Support
Basic HTML tags are supported:
- `<b>Bold text</b>`
- `<i>Italic text</i>`
- `<code>Code text</code>`

## 📁 File Structure

```
templates/
├── index.html          # Main dashboard
├── edit.html           # Edit message form
├── add.html            # Add new message form
└── search.html         # Search results

web_interface.py        # Flask web application
message_manager.py      # Message management backend
config.json            # Bot messages and settings
```

## 🛠️ Technical Details

- **Backend**: Flask web framework
- **Frontend**: Bootstrap 5 + Font Awesome icons
- **Data Storage**: JSON file (`config.json`)
- **Real-time**: Live preview and character counting
- **Responsive**: Works on desktop, tablet, and mobile

## 🔒 Security Notes

- The web interface runs locally by default
- Change the secret key in production
- Consider adding authentication for production use

## 🚨 Troubleshooting

### Port Already in Use
If you get a port error, change the port in `web_interface.py`:
```python
app.run(debug=True, host='0.0.0.0', port=5001)  # Change 5000 to 5001
```

### Template Errors
Make sure all template files are in the `templates/` folder and the folder name is exactly correct.

### Message Manager Errors
Ensure `message_manager.py` and `config.json` are in the same directory as `web_interface.py`.

## 🎉 Benefits Over Command Line

- **Visual Interface**: See all messages at once
- **Live Preview**: Know exactly how messages will look
- **Easy Navigation**: Click to edit, no need to remember keys
- **Search Functionality**: Find messages quickly
- **Mobile Friendly**: Edit from your phone or tablet
- **No Code Knowledge Required**: Perfect for non-technical users

## 🔄 Integration with Bot

The web interface automatically updates the same `config.json` file that your bot uses. After making changes:

1. Save your changes in the web interface
2. The bot will automatically use the new messages
3. No need to restart the bot (unless you're using the old hardcoded system)

---

**Happy Message Editing! 🎨✨** 