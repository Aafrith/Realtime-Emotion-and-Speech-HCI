import sqlite3
import json

def update_database_with_new_commands():
    """Add new enhanced commands to the database"""
    
    conn = sqlite3.connect("speech_recognition.db")
    cursor = conn.cursor()
    
    # Create tables if they don't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS commands (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            pattern TEXT NOT NULL,
            type TEXT NOT NULL,
            parameters TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS command_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            command_text TEXT NOT NULL,
            confidence REAL,
            status TEXT DEFAULT 'pending',
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    ''')
    
    # Clear existing commands to avoid duplicates
    cursor.execute("DELETE FROM commands")
    
    # Enhanced commands
    new_commands = [
        # Application Commands
        ("Open Chrome", "open chrome|launch chrome|start chrome", "application", '{"app": "chrome"}'),
        ("Open Firefox", "open firefox|launch firefox|start firefox", "application", '{"app": "firefox"}'),
        ("Open Notepad", "open notepad|launch notepad|start notepad", "application", '{"app": "notepad"}'),
        ("Open Calculator", "open calculator|launch calculator|start calc", "application", '{"app": "calculator"}'),
        ("Open File Explorer", "open explorer|open files|file manager", "application", '{"app": "explorer"}'),
        ("Open Settings", "open settings|launch settings|start settings", "application", '{"app": "settings"}'),
        ("Open Spotify", "open spotify|launch spotify|start spotify", "application", '{"app": "spotify"}'),
        ("Open VS Code", "open vscode|launch vscode|start vscode", "application", '{"app": "vscode"}'),
        
        # System Commands
        ("Volume Up", "volume up|increase volume|louder", "system", '{"action": "volume", "direction": "up"}'),
        ("Volume Down", "volume down|decrease volume|quieter", "system", '{"action": "volume", "direction": "down"}'),
        ("Mute Audio", "mute|unmute|mute audio", "system", '{"action": "mute"}'),
        ("Lock Computer", "lock computer|lock screen", "system", '{"action": "lock"}'),
        ("Shutdown Computer", "shutdown|shut down|power off", "system", '{"action": "shutdown"}'),
        ("Restart Computer", "restart computer|reboot", "system", '{"action": "restart"}'),
        ("Sleep Computer", "sleep computer|hibernate", "system", '{"action": "sleep"}'),
        ("Take Screenshot", "take screenshot|capture screen", "system", '{"action": "screenshot"}'),
        ("What Time", "what time is it|tell me the time", "system", '{"action": "telltime"}'),
        ("What Date", "what date is it|tell me the date", "system", '{"action": "telldate"}'),
        ("Minimize All", "minimize all|show desktop", "system", '{"action": "minimizeall"}'),
        ("Task Manager", "task manager|open task manager", "system", '{"action": "taskmanager"}'),
        ("Check Internet", "check internet|internet connection", "system", '{"action": "checkinternet"}'),
        
        # Web Commands
        ("Search Web", "search for (.+)|google (.+)|look up (.+)", "web", '{"action": "search"}'),
        ("Open YouTube", "open youtube|go to youtube", "web", '{"query": "youtube.com"}'),
        ("Open Gmail", "open gmail|go to gmail", "web", '{"query": "gmail.com"}'),
        ("Open Facebook", "open facebook|go to facebook", "web", '{"query": "facebook.com"}'),
        ("Open Twitter", "open twitter|go to twitter", "web", '{"query": "twitter.com"}'),
        ("Open GitHub", "open github|go to github", "web", '{"query": "github.com"}'),
        ("Check Weather", "check weather|weather forecast", "web", '{"query": "weather forecast"}'),
        ("Check News", "check news|latest news", "web", '{"query": "latest news"}'),
        
        # File Operations
        ("Open Desktop", "open desktop|go to desktop", "file", '{"action": "open_folder", "folder": "desktop"}'),
        ("Open Documents", "open documents|go to documents", "file", '{"action": "open_folder", "folder": "documents"}'),
        ("Open Downloads", "open downloads|go to downloads", "file", '{"action": "open_folder", "folder": "downloads"}'),
        ("Create Folder", "create folder (.+)|make folder (.+)", "file", '{"action": "create_folder"}'),
        
        # Media Controls
        ("Play Music", "play music|start music", "media", '{"action": "play_music"}'),
        ("Pause Music", "pause music|stop music", "media", '{"action": "pause_music"}'),
        ("Next Song", "next song|skip song", "media", '{"action": "next_song"}'),
        ("Previous Song", "previous song|last song", "media", '{"action": "previous_song"}'),
    ]
    
    # Insert new commands
    for command in new_commands:
        cursor.execute('''
            INSERT INTO commands (name, pattern, type, parameters)
            VALUES (?, ?, ?, ?)
        ''', command)
    
    conn.commit()
    conn.close()
    
    print("✅ Database updated with enhanced commands!")
    print(f"Added {len(new_commands)} new voice commands")
    print("\nRun the main application with: python main.py")

if __name__ == "__main__":
    update_database_with_new_commands()
