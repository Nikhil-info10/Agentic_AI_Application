# This file handles the database side of the app.
# It stores the company knowledge articles and all IT support tickets.
# In simple terms: this file is the memory of the system.

import sqlite3
import random
from typing import Dict, List, Any

# Name of the SQLite database file.
# This file is created automatically when the app starts.
DB_FILE = "it_support.db"

# ---------------------------------------------------------------------------
# Set up the database when the app is first loaded.
# ---------------------------------------------------------------------------
def init_db():
    """Initializes the SQLite database with required tables and seed data."""
    # Connect to the database file.
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Create the knowledge base table if it does not already exist.
    # This table stores IT help articles.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS knowledge_base (
            id TEXT PRIMARY KEY,
            content TEXT
        )
    """)

    # Create the tickets table if it does not already exist.
    # This table stores support tickets for employees.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tickets (
            ticket_id TEXT PRIMARY KEY,
            employee_id TEXT,
            issue TEXT,
            status TEXT
        )
    """)

    # If the knowledge base is empty, add a few sample IT articles.
    cursor.execute("SELECT COUNT(*) FROM knowledge_base")
    if cursor.fetchone()[0] == 0:
        seed_data = [
            ("vpn_reset", "To reset your VPN password, navigate to ://company.com, click 'Forgot Password', and complete the MFA prompt. New passwords must be 16+ characters."),
            ("wifi_guest", "The guest Wi-Fi network password changes every Monday. You can find this week's password on the physical bulletin board in the cafeteria."),
            ("software_request", "To request approved software like Adobe Acrobat, submit a form via the HR Procurement Portal. Approval takes 2 business days.")
        ]
        cursor.executemany("INSERT INTO knowledge_base VALUES (?, ?)", seed_data)

    # If there are no tickets yet, add one example ticket for demonstration.
    cursor.execute("SELECT COUNT(*) FROM tickets")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO tickets VALUES (?, ?, ?, ?)", ("TIC-1001", "EMP1024", "MacBook overheating and fan runs constantly.", "In Progress"))

    # Save all changes and close the database connection.
    conn.commit()
    conn.close()

# Run the database setup as soon as this file is imported.
init_db()

# ---------------------------------------------------------------------------
# Read all ticket records from the database.
# This is used by the sidebar in the UI to display the live ticket list.
# ---------------------------------------------------------------------------
def get_all_tickets() -> List[Dict[str, Any]]:
    """Helper function to fetch all tickets in real-time for the UI sidebar."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT ticket_id, employee_id, issue, status FROM tickets")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

# ---------------------------------------------------------------------------
# Search the knowledge base for relevant IT articles.
# It checks keywords from the user's question and returns matching articles.
# ---------------------------------------------------------------------------
def search_knowledge_base(query: str) -> str:
    """Search the local IT knowledge base using SQLite keyword matching."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Split the user request into words.
    query_words = query.lower().split()
    results = []

    # Look through each word in the question.
    # If a word matches article text or ID, add that article to the results.
    for word in query_words:
        cursor.execute("SELECT content FROM knowledge_base WHERE id LIKE ? OR content LIKE ?", (f"%{word}%", f"%{word}%"))
        for row in cursor.fetchall():
            if row[0] not in results:
                results.append(row[0])

    conn.close()

    # If matching articles were found, return them together.
    if results:
        return "[Found Article]: " + " | ".join(results)

    # If nothing matches, give a polite fallback response.
    return "No highly relevant knowledge base articles found for this issue."

# ---------------------------------------------------------------------------
# Look for existing tickets for one employee.
# ---------------------------------------------------------------------------
def lookup_ticket(employee_id: str) -> str:
    """Find existing support tickets for a given employee ID from SQLite."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Search the database using the employee ID.
    cursor.execute("SELECT * FROM tickets WHERE UPPER(employee_id) = UPPER(?)", (employee_id.strip(),))
    rows = cursor.fetchall()
    conn.close()

    # If there are no records, say so clearly.
    if not rows:
        return f"No active tickets found for Employee ID: {employee_id}"

    # Convert database rows into a readable JSON-like structure.
    tickets_list = [dict(row) for row in rows]
    import json
    return json.dumps(tickets_list, indent=2)

# ---------------------------------------------------------------------------
# Create a new ticket in the database.
# It checks whether the same ticket already exists before inserting a new one.
# ---------------------------------------------------------------------------
def create_ticket(employee_id: str, issue: str) -> str:
    """Create a new IT support ticket securely with duplicate checks in SQLite."""
    # Do not allow empty values.
    if not employee_id or not issue:
        return "Error: Missing employee ID or issue description."

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Safety check: stop duplicate tickets from being created.
    cursor.execute(
        "SELECT ticket_id, status FROM tickets WHERE UPPER(employee_id) = UPPER(?) AND LOWER(issue) = LOWER(?)",
        (employee_id.strip(), issue.strip())
    )
    duplicate = cursor.fetchone()
    if duplicate:
        conn.close()
        return f"Duplicate Ticket Prevention: An identical ticket already exists ({duplicate[0]}) with status: {duplicate[1]}."

    # Create a new ticket ID like TIC-1234.
    new_id = f"TIC-{random.randint(1002, 9999)}"

    # Insert the new ticket with status Open.
    cursor.execute("INSERT INTO tickets VALUES (?, ?, ?, 'Open')", (new_id, employee_id.strip().upper(), issue.strip()))

    conn.commit()
    conn.close()
    return f"Success! Generated Ticket ID: {new_id}. Status: Open."