import os
import sqlite3

DB_PATH = "uniflow.db"

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS profile (
        id INTEGER PRIMARY KEY,
        name TEXT,
        year_level TEXT,
        focus_hours_today REAL DEFAULT 0.0,
        focus_hours_total REAL DEFAULT 12.5,
        onboarded INTEGER DEFAULT 0,
        api_key TEXT DEFAULT ""
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS subjects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        color TEXT
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        date TEXT,
        timeStart TEXT,
        timeEnd TEXT,
        location TEXT,
        category TEXT
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS todos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        category TEXT,
        date TEXT,
        time TEXT,
        completed INTEGER DEFAULT 0
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS decks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        last_practiced TEXT DEFAULT "Never",
        progress INTEGER DEFAULT 0
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS cards (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        deck_id INTEGER,
        question TEXT,
        answer TEXT,
        incorrect INTEGER DEFAULT 0,
        FOREIGN KEY (deck_id) REFERENCES decks(id) ON DELETE CASCADE
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS focus_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp REAL,
        duration REAL,
        type TEXT
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS chat_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        channel TEXT,
        sender TEXT,
        text TEXT,
        timestamp REAL
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS quizzes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS quiz_questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        quiz_id INTEGER,
        question TEXT,
        correct TEXT,
        opt_a TEXT,
        opt_b TEXT,
        opt_c TEXT,
        opt_d TEXT,
        FOREIGN KEY (quiz_id) REFERENCES quizzes(id) ON DELETE CASCADE
    )
    """)
    
    # Check if empty to populate defaults
    cursor.execute("SELECT COUNT(*) FROM profile")
    if cursor.fetchone()[0] == 0:
        # 1. Profile
        cursor.execute("INSERT INTO profile (id, name, year_level, onboarded) VALUES (1, 'Alex', 'College Freshman', 0)")
        
        # 2. Subjects
        cursor.execute("INSERT OR IGNORE INTO subjects (name, color) VALUES ('Cognitive Psychology', '#D48C70')")
        cursor.execute("INSERT OR IGNORE INTO subjects (name, color) VALUES ('AI Ethics', '#C9A15B')")
        cursor.execute("INSERT OR IGNORE INTO subjects (name, color) VALUES ('Computer Science', '#5A3E22')")
        
        # 3. Events
        cursor.execute("INSERT INTO events (title, date, timeStart, timeEnd, location, category) VALUES (?, ?, ?, ?, ?, ?)", 
                       ("Psychology Lecture", "2026-07-13", "10:00", "11:30", "Room 402 • Hall A", "Cognitive Psychology"))
        cursor.execute("INSERT INTO events (title, date, timeStart, timeEnd, location, category) VALUES (?, ?, ?, ?, ?, ?)", 
                       ("Study Group: AI Ethics", "2026-07-14", "14:00", "15:30", "Library Commons", "AI Ethics"))
        cursor.execute("INSERT INTO events (title, date, timeStart, timeEnd, location, category) VALUES (?, ?, ?, ?, ?, ?)", 
                       ("Focus Revision", "2026-07-16", "17:00", "18:30", "Personal Desk", "Computer Science"))
        
        # 4. To-Dos
        cursor.execute("INSERT INTO todos (title, category, date, time, completed) VALUES (?, ?, ?, ?, 0)", 
                       ("Review Sensory Memory Chapter", "Cognitive Psychology", "2026-07-13", "12:00"))
        cursor.execute("INSERT INTO todos (title, category, date, time, completed) VALUES (?, ?, ?, ?, 0)", 
                       ("Read Algorithmic Bias Guidelines", "AI Ethics", "2026-07-14", "16:00"))
        
        # 5. Decks & Cards
        cursor.execute("INSERT INTO decks (title, last_practiced, progress) VALUES ('Cognitive Bias', '2h ago', 65)")
        deck1_id = cursor.lastrowid
        cursor.execute("INSERT INTO decks (title, last_practiced, progress) VALUES ('Neural Networks', '1d ago', 40)")
        deck2_id = cursor.lastrowid
        
        # Cards for Deck 1
        cards_d1 = [
            ("Confirmation Bias", "The tendency to search for, interpret, favor, and recall information in a way that confirms or supports one's prior beliefs or values.", 0),
            ("Anchor Bias", "The common human tendency to rely too heavily on the first piece of information offered (the 'anchor') when making decisions.", 1),
            ("Availability Heuristic", "A mental shortcut that relies on immediate examples that come to mind when evaluating a specific topic or decision.", 0),
            ("Dunning-Kruger Effect", "A cognitive bias whereby people with low ability or knowledge tend to overestimate their ability or expertise.", 1),
            ("Halo Effect", "The tendency for positive impressions of a person in one area to positively influence one's opinion or feelings in other areas.", 0)
        ]
        for q, a, inc in cards_d1:
            cursor.execute("INSERT INTO cards (deck_id, question, answer, incorrect) VALUES (?, ?, ?, ?)", (deck1_id, q, a, inc))
            
        # Cards for Deck 2
        cards_d2 = [
            ("Activation Function", "A mathematical formula that determines whether a neuron should fire based on the weighted sum of its inputs (e.g. ReLU, Sigmoid).", 0),
            ("Backpropagation", "The algorithm used for training neural networks by calculating the gradient of the loss function with respect to weights, propagating errors backward.", 0),
            ("Overfitting", "A modeling error in machine learning where a model learns training data noise too well, leading to poor generalization on new data.", 0),
            ("Gradient Descent", "An optimization algorithm used to minimize a loss function by iteratively moving in the direction of steepest descent.", 0)
        ]
        for q, a, inc in cards_d2:
            cursor.execute("INSERT INTO cards (deck_id, question, answer, incorrect) VALUES (?, ?, ?, ?)", (deck2_id, q, a, inc))

        # 6. Default Focus Heatmap Sessions
        import time
        t_now = time.time()
        for offset_days in [6, 5, 4, 3, 2, 1, 0]:
            cursor.execute("INSERT INTO focus_sessions (timestamp, duration, type) VALUES (?, ?, ?)",
                           (t_now - offset_days * 24 * 3600, 25.0, "work"))

        # 7. Default Chat Messages
        cursor.execute("INSERT INTO chat_messages (channel, sender, text, timestamp) VALUES (?, ?, ?, ?)",
                       ("general", "ai", "Hey! I am UniFlow Buddy, your study companion. 🚀 Ask me any questions, upload a PDF context, or try out the quizzes!", t_now))
        
        # 8. Quizzes
        cursor.execute("INSERT INTO quizzes (title) VALUES ('Cognitive Memory & Sensory Buffer')")
        quiz1_id = cursor.lastrowid
        cursor.execute("INSERT INTO quizzes (title) VALUES ('AI Ethics & Algorithmic Bias')")
        quiz2_id = cursor.lastrowid
        
        # Quiz 1 questions
        cursor.execute("""
        INSERT INTO quiz_questions (quiz_id, question, correct, opt_a, opt_b, opt_c, opt_d) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (quiz1_id, "How long does visual sensory memory (iconic memory) typically last?", "B", "10-15 seconds", "Under 1 second", "2-3 minutes", "24 hours"))
        cursor.execute("""
        INSERT INTO quiz_questions (quiz_id, question, correct, opt_a, opt_b, opt_c, opt_d) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (quiz1_id, "Which sensory memory store handles auditory information?", "B", "Iconic memory", "Echoic memory", "Haptic memory", "Olfactory memory"))
        cursor.execute("""
        INSERT INTO quiz_questions (quiz_id, question, correct, opt_a, opt_b, opt_c, opt_d) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (quiz1_id, "What is the primary capacity of short-term memory (Miller's Law)?", "B", "Unlimited", "7 ± 2 items", "Exactly 100 items", "1-2 items"))

        # Quiz 2 questions
        cursor.execute("""
        INSERT INTO quiz_questions (quiz_id, question, correct, opt_a, opt_b, opt_c, opt_d) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (quiz2_id, "When an AI replicates previous gender discrimination based on historic hiring datasets, this is:", "B", "Data Augmentation", "Algorithmic Bias", "Overfitting", "Model Pruning"))
        cursor.execute("""
        INSERT INTO quiz_questions (quiz_id, question, correct, opt_a, opt_b, opt_c, opt_d) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (quiz2_id, "What is the main goal of AI alignment?", "B", "Making models train faster", "Ensuring AI actions align with human goals and values", "Scaling parameter count", "Writing code in python"))

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully.")
