#!/usr/bin/env python3
"""
Web Interface for editing Telegram Bot messages
"""

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import json
import os
from message_manager import MessageManager

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Change this in production

# Initialize message manager
message_manager = MessageManager()

@app.route('/')
def index():
    """Main page showing all messages"""
    messages = message_manager.list_messages()
    return render_template('index.html', messages=messages)

@app.route('/edit/<key>')
def edit_message(key):
    """Edit a specific message"""
    messages = message_manager.list_messages()
    if key not in messages:
        flash(f'Message key "{key}" not found!', 'error')
        return redirect(url_for('index'))
    
    return render_template('edit.html', key=key, message=messages[key])

@app.route('/update/<key>', methods=['POST'])
def update_message(key):
    """Update a message"""
    try:
        new_message = request.form.get('message', '').strip()
        if not new_message:
            flash('Message cannot be empty!', 'error')
            return redirect(url_for('edit_message', key=key))
        
        # Update the message
        if message_manager.update_message(key, new_message):
            flash(f'Message "{key}" updated successfully!', 'success')
        else:
            flash(f'Failed to update message "{key}"!', 'error')
        
        return redirect(url_for('index'))
    except Exception as e:
        flash(f'Error updating message: {str(e)}', 'error')
        return redirect(url_for('edit_message', key=key))

@app.route('/add', methods=['GET', 'POST'])
def add_message():
    """Add a new message"""
    if request.method == 'POST':
        key = request.form.get('key', '').strip()
        message = request.form.get('message', '').strip()
        
        if not key or not message:
            flash('Both key and message are required!', 'error')
            return redirect(url_for('add_message'))
        
        if key in message_manager.list_messages():
            flash(f'Message key "{key}" already exists!', 'error')
            return redirect(url_for('add_message'))
        
        if message_manager.add_message(key, message):
            flash(f'Message "{key}" added successfully!', 'success')
            return redirect(url_for('index'))
        else:
            flash(f'Failed to add message "{key}"!', 'error')
    
    return render_template('add.html')

@app.route('/delete/<key>', methods=['POST'])
def delete_message(key):
    """Delete a message"""
    try:
        if message_manager.delete_message(key):
            flash(f'Message "{key}" deleted successfully!', 'success')
        else:
            flash(f'Failed to delete message "{key}"!', 'error')
    except Exception as e:
        flash(f'Error deleting message: {str(e)}', 'error')
    
    return redirect(url_for('index'))

@app.route('/search')
def search_messages():
    """Search messages"""
    query = request.args.get('q', '').strip()
    if not query:
        return redirect(url_for('index'))
    
    messages = message_manager.list_messages()
    results = {}
    
    for key, message in messages.items():
        if query.lower() in key.lower() or query.lower() in message.lower():
            results[key] = message
    
    return render_template('search.html', results=results, query=query)

@app.route('/preview/<key>')
def preview_message(key):
    """Preview a message with formatting"""
    messages = message_manager.list_messages()
    if key not in messages:
        return jsonify({'error': 'Message not found'}), 404
    
    message = messages[key]
    # Convert \n to <br> for HTML display
    html_message = message.replace('\n', '<br>')
    
    return jsonify({
        'key': key,
        'message': message,
        'html_message': html_message
    })

if __name__ == '__main__':
    print("🌐 Starting Web Interface for Bot Message Editor...")
    print("📱 Open your browser and go to: http://localhost:5001")
    print("🔧 You can now edit bot messages through a web interface!")
    print("⏹️  Press Ctrl+C to stop the server")
    print()
    
    app.run(debug=True, host='0.0.0.0', port=5001) 