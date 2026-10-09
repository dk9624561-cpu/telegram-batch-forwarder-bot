import sqlite3
import os
import logging

DB_PATH = "bot_data.db"

def init_db():
    """Initialize SQLite database tables if they don't exist."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Table for storing batch mappings: tag_or_keyword -> target_channel_id, batch_name
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS batch_mappings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tag TEXT UNIQUE NOT NULL,
            target_channel TEXT NOT NULL,
            batch_name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Table for general bot settings (e.g. storage_channel_id, forwarding_mode)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    ''')

    # Table for forwarding logs / statistics
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS forwarding_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            storage_message_id INTEGER,
            tag TEXT,
            target_channel TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Default settings if not set
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('forward_mode', 'copy')")

    conn.commit()
    conn.close()

def set_setting(key: str, value: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, str(value)))
    conn.commit()
    conn.close()

def get_setting(key: str, default: str = None) -> str:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else default

def add_batch_mapping(tag: str, target_channel: str, batch_name: str) -> bool:
    """Add or update a hashtag or keyword mapping to a target channel."""
    tag = tag.strip().lower()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT OR REPLACE INTO batch_mappings (tag, target_channel, batch_name)
            VALUES (?, ?, ?)
        """, (tag, str(target_channel), batch_name))
        conn.commit()
        return True
    except Exception as e:
        logging.error(f"Error adding batch mapping: {e}")
        return False
    finally:
        conn.close()

def remove_batch_mapping(tag: str) -> bool:
    """Remove a batch mapping by tag/keyword."""
    tag = tag.strip().lower()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM batch_mappings WHERE tag = ?", (tag,))
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    return affected > 0

def get_all_batch_mappings() -> list:
    """Return all active batch mappings."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT tag, target_channel, batch_name FROM batch_mappings")
    rows = cursor.fetchall()
    conn.close()
    return [{"tag": r[0], "target_channel": r[1], "batch_name": r[2]} for r in rows]

def get_mapping_by_tag(tag: str) -> dict:
    """Find mapping for a specific tag/keyword."""
    tag = tag.strip().lower()
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT tag, target_channel, batch_name FROM batch_mappings WHERE tag = ?", (tag,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {"tag": row[0], "target_channel": row[1], "batch_name": row[2]}
    return None

def log_forwarding(storage_msg_id: int, tag: str, target_channel: str):
    """Log a successful lecture forward."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO forwarding_logs (storage_message_id, tag, target_channel)
        VALUES (?, ?, ?)
    """, (storage_msg_id, tag, target_channel))
    conn.commit()
    conn.close()

def get_stats() -> dict:
    """Get total forwarded lectures and per-batch breakdown."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM forwarding_logs")
    total_forwarded = cursor.fetchone()[0]

    cursor.execute("""
        SELECT tag, COUNT(*) FROM forwarding_logs GROUP BY tag
    """)
    tag_counts = cursor.fetchall()

    conn.close()
    return {
        "total": total_forwarded,
        "by_tag": {row[0]: row[1] for row in tag_counts}
    }
