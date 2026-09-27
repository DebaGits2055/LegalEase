import sqlite3
import os
import json
import time
from typing import List, Dict, Any, Optional

try:
    from vault import EncryptedDocumentVault
except ImportError:
    from backend.vault import EncryptedDocumentVault

if os.environ.get("VERCEL"):
    DB_PATH = "/tmp/legaltech.db"
else:
    DB_PATH = os.path.join(os.path.dirname(__file__), "legaltech.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    # Users table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        full_name TEXT DEFAULT '',
        phone_number TEXT DEFAULT '',
        age INTEGER DEFAULT 24,
        profession TEXT DEFAULT 'Student',
        org_name TEXT DEFAULT '',
        avatar_url TEXT DEFAULT '',
        is_subscribed BOOLEAN DEFAULT 0,
        subscription_plan TEXT DEFAULT 'Free Tier',
        doc_upload_count INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Pending OTP verifications table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS pending_otps (
        email TEXT PRIMARY KEY,
        otp_code TEXT NOT NULL,
        captcha_text TEXT NOT NULL,
        created_at REAL NOT NULL
    )
    """)
    
    # Revenue Ledger / Subscriptions table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS revenue_ledger (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        transaction_id TEXT UNIQUE NOT NULL,
        email TEXT NOT NULL,
        plan_name TEXT NOT NULL,
        amount_inr REAL NOT NULL,
        payment_method TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        status TEXT DEFAULT 'COMPLETED'
    )
    """)
    
    # Audits history table (with AES-256-GCM encryption metadata)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS document_audits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        filename TEXT NOT NULL,
        language TEXT DEFAULT 'English',
        report_text TEXT NOT NULL,
        audio_url TEXT,
        vault_id TEXT,
        sha256_fingerprint TEXT,
        cipher_algorithm TEXT DEFAULT 'AES-256-GCM',
        category TEXT DEFAULT 'General Legal',
        is_ephemeral BOOLEAN DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    """)
    
    # Dynamic column migration for existing databases
    cursor.execute("PRAGMA table_info(document_audits)")
    columns = [col["name"] for col in cursor.fetchall()]
    new_cols = [
        ("vault_id", "TEXT"),
        ("sha256_fingerprint", "TEXT"),
        ("cipher_algorithm", "TEXT DEFAULT 'AES-256-GCM'"),
        ("category", "TEXT DEFAULT 'General Legal'"),
        ("is_ephemeral", "BOOLEAN DEFAULT 0")
    ]
    for col_name, col_type in new_cols:
        if col_name not in columns:
            try:
                cursor.execute(f"ALTER TABLE document_audits ADD COLUMN {col_name} {col_type}")
            except Exception as e:
                print(f"Migration note ({col_name}): {e}")
                
    conn.commit()
    conn.close()

def save_encrypted_audit(
    user_id: int,
    filename: str,
    language: str,
    plain_report_text: str,
    audio_url: Optional[str] = None,
    vault_id: Optional[str] = None,
    sha256_fingerprint: Optional[str] = None,
    category: str = "General Legal",
    is_ephemeral: bool = False
) -> int:
    """
    Encrypts report_text with 256-Bit AES-GCM before persisting to database.
    """
    encrypted_report = EncryptedDocumentVault.encrypt_field(plain_report_text)
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO document_audits (
            user_id, filename, language, report_text, audio_url,
            vault_id, sha256_fingerprint, cipher_algorithm, category, is_ephemeral
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, 'AES-256-GCM', ?, ?)
    """, (
        user_id, filename, language, encrypted_report, audio_url,
        vault_id, sha256_fingerprint, category, 1 if is_ephemeral else 0
    ))
    conn.commit()
    audit_id = cursor.lastrowid
    conn.close()
    return audit_id

def get_user_audits(user_id: int) -> List[Dict[str, Any]]:
    """
    Fetches user's audit history and decrypts report_text for authorized user.
    """
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM document_audits 
        WHERE user_id = ? 
        ORDER BY created_at DESC
    """, (user_id,))
    rows = cursor.fetchall()
    conn.close()
    
    audits = []
    for row in rows:
        item = dict(row)
        # Transparently decrypt report text
        item["report_text"] = EncryptedDocumentVault.decrypt_field(item.get("report_text", ""))
        audits.append(item)
    return audits

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully with AES-256-GCM at", DB_PATH)
