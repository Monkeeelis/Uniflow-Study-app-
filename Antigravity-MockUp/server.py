import os
import time
import math
import io
import base64
import wave
import random
import datetime
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from pypdf import PdfReader
from database import get_db_connection, init_db

app = Flask(__name__)
app.secret_key = "uniflow_secure_academic_key_123987"

# Initialize database tables on load
init_db()

# --- MOTIVATIONAL QUOTES ---
quotes = [
    "Learning is not spectator sport. So let's get active.",
    "The secret of getting ahead is getting started.",
    "Your focus determines your reality. Stay on track.",
    "Small progress every day adds up to big results.",
    "Errors are proof that you are trying. Review them, master them."
]

# --- HELPER: SYNTHESIZE BEEP WAV DATA URI ---
def get_beep_data_uri():
    s_rate = 8000
    freq = 880
    duration = 0.4
    num_samples = int(s_rate * duration)
    
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as wav:
        wav.setnchannels(1)
        wav.setsampwidth(1)
        wav.setframerate(s_rate)
        
        samples = []
        for i in range(num_samples):
            fade = math.exp(-3 * i / num_samples)
            val = int(127 + 127 * fade * math.sin(2 * math.pi * freq * i / s_rate))
            samples.append(val)
        wav.writeframes(bytes(samples))
        
    return "data:audio/wav;base64," + base64.b64encode(buf.getvalue()).decode('utf-8')

# --- SERVER-SIDE CALENDAR OVERLAP ENGINE ---
def calculate_overlaps_for_week(events_and_todos):
    def parse_t(time_str):
        h, m = map(int, time_str.split(':'))
        return h * 60 + m

    # Group items by dayOfWeek (0 to 6)
    grouped = {i: [] for i in range(7)}
    for item in events_and_todos:
        grouped[item['dayOfWeek']].append(item)

    for day, day_items in grouped.items():
        if not day_items:
            continue
        
        sorted_items = sorted(day_items, key=lambda x: (parse_t(x['timeStart']), parse_t(x['timeEnd'])))
        
        columns = []
        for item in sorted_items:
            placed = False
            start_m = parse_t(item['timeStart'])
            for col_idx, col_items in enumerate(columns):
                has_overlap = False
                for other in col_items:
                    other_start = parse_t(other['timeStart'])
                    other_end = parse_t(other['timeEnd'])
                    end_m = parse_t(item['timeEnd'])
                    if start_m < other_end and other_start < end_m:
                        has_overlap = True
                        break
                if not has_overlap:
                    col_items.append(item)
                    item['col_index'] = col_idx
                    placed = True
                    break
            if not placed:
                columns.append([item])
                item['col_index'] = len(columns) - 1

        clusters = []
        for item in sorted_items:
            start_m = parse_t(item['timeStart'])
            end_m = parse_t(item['timeEnd'])
            matching = []
            for c_idx, cluster in enumerate(clusters):
                overlaps = False
                for other in cluster:
                    other_start = parse_t(other['timeStart'])
                    other_end = parse_t(other['timeEnd'])
                    if start_m < other_end and other_start < end_m:
                        overlaps = True
                        break
                if overlaps:
                    matching.append(c_idx)
            
            if not matching:
                clusters.append([item])
            elif len(matching) == 1:
                clusters[matching[0]].append(item)
            else:
                merged = []
                for c_idx in sorted(matching, reverse=True):
                    merged.extend(clusters.pop(c_idx))
                merged.append(item)
                clusters.append(merged)

        for cluster in clusters:
            max_col = max(x['col_index'] for x in cluster)
            total_cols = max_col + 1
            for x in cluster:
                x['total_cols'] = total_cols

    return events_and_todos

# --- DYNAMIC STUDY STREAK ALGORITHM ---
def get_streak_count(sessions):
    if not sessions:
        return 0
    
    dates = set()
    for ts in sessions:
        t_struct = time.localtime(ts)
        dates.add(f"{t_struct.tm_year}-{t_struct.tm_mon:02d}-{t_struct.tm_mday:02d}")

    streak = 0
    day_to_check = time.time()
    
    def get_date_str(t_val):
        ts = time.localtime(t_val)
        return f"{ts.tm_year}-{ts.tm_mon:02d}-{ts.tm_mday:02d}"

    # Check if worked today, if not check yesterday
    if get_date_str(day_to_check) not in dates:
        day_to_check -= 24 * 3600
        if get_date_str(day_to_check) not in dates:
            return 0
            
    while get_date_str(day_to_check) in dates:
        streak += 1
        day_to_check -= 24 * 3600
    return streak

# --- DECORATOR: NAME GATE & ONBOARDING CHECK ---
@app.before_request
def gateway_check():
    # Skip assets, login, onboarding, logout, and focus API logs
    if (request.path.startswith('/static') or 
        request.path in ['/login', '/logout', '/onboarding'] or 
        request.path.startswith('/api/focus/log')):
        return

    # Check session name
    user_name = session.get('user_name')
    if not user_name:
        return redirect(url_for('login_route'))

    # Check onboarding state in database
    conn = get_db_connection()
    profile = conn.execute("SELECT * FROM profile WHERE name = ?", (user_name,)).fetchone()
    conn.close()
    
    if not profile or not profile['onboarded']:
        return redirect(url_for('onboarding_route'))

# --- CONTEXT PROCESSOR FOR GLOBAL VARS ---
@app.context_processor
def inject_global_vars():
    user_name = session.get('user_name')
    if not user_name:
        return {}

    conn = get_db_connection()
    profile = conn.execute("SELECT * FROM profile WHERE name = ?", (user_name,)).fetchone()
    sessions_raw = conn.execute("SELECT timestamp FROM focus_sessions").fetchall()
    conn.close()

    sessions = [s['timestamp'] for s in sessions_raw]
    streak_count = get_streak_count(sessions)

    return {
        "session_name": user_name,
        "profile": profile,
        "streak_count": streak_count,
        "play_beep_data_uri": get_beep_data_uri()
    }

# --- ROUTES ---

@app.route('/')
def root():
    return redirect(url_for('home_route'))

@app.route('/login', methods=['GET', 'POST'])
def login_route():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        if name:
            session['user_name'] = name
            
            # Check if profile exists, otherwise create
            conn = get_db_connection()
            profile = conn.execute("SELECT * FROM profile WHERE name = ?", (name,)).fetchone()
            if not profile:
                conn.execute("INSERT INTO profile (name, year_level, onboarded) VALUES (?, ?, 0)", (name, "College Freshman"))
                conn.commit()
            conn.close()
            
            return redirect(url_for('home_route'))
    return render_template("login.html", active_view="login")

@app.route('/logout')
def logout_route():
    session.pop('user_name', None)
    session.pop('pdf_context', None)
    session.pop('pdf_name', None)
    return redirect(url_for('login_route'))

@app.route('/onboarding', methods=['GET', 'POST'])
def onboarding_route():
    user_name = session.get('user_name')
    if not user_name:
        return redirect(url_for('login_route'))

    if request.method == 'POST':
        year_level = request.form.get('year_level')
        subjects_raw = request.form.get('subjects', '')
        
        parsed_subjects = [s.strip() for s in subjects_raw.split(',') if s.strip()]
        colors = ["#D48C70", "#C9A15B", "#5A3E22", "#8A4F37", "#00f5d4", "#9b5de5"]
        
        conn = get_db_connection()
        conn.execute("UPDATE profile SET year_level = ?, onboarded = 1 WHERE name = ?", (year_level, user_name))
        
        for i, sub_name in enumerate(parsed_subjects):
            color = colors[i % len(colors)]
            conn.execute("INSERT OR IGNORE INTO subjects (name, color) VALUES (?, ?)", (sub_name, color))
            # Create a default flashcard deck for each subject
            conn.execute("INSERT INTO decks (title, last_practiced, progress) VALUES (?, 'Never', 0)", (sub_name,))
            deck_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            conn.execute("INSERT INTO cards (deck_id, question, answer) VALUES (?, ?, ?)", 
                         (deck_id, f"Core Concept in {sub_name}", f"Enter study terms or details for {sub_name} here."))
        
        conn.commit()
        conn.close()
        return redirect(url_for('home_route'))

    return render_template("onboarding.html", active_view="onboarding")

@app.route('/home')
def home_route():
    user_name = session.get('user_name')
    conn = get_db_connection()
    
    profile = conn.execute("SELECT * FROM profile WHERE name = ?", (user_name,)).fetchone()
    quote = random.choice(quotes)
    
    # Get subjects
    subjects = conn.execute("SELECT * FROM subjects").fetchall()
    subjects_dict = {s['name'].lower(): s['color'] for s in subjects}

    # Daily Schedule Events
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    events_raw = conn.execute("SELECT * FROM events WHERE date = ?", (today_str,)).fetchall()
    
    today_events = []
    for evt in events_raw:
        h, m = map(int, evt['timeStart'].split(':'))
        ampm = "AM" if h < 12 else "PM"
        h_12 = h % 12 or 12
        timeStart12h = f"{h_12}:{m:02d} {ampm}"
        
        h2, m2 = map(int, evt['timeEnd'].split(':'))
        ampm2 = "AM" if h2 < 12 else "PM"
        h_12_2 = h2 % 12 or 12
        timeEnd12h = f"{h_12_2}:{m2:02d} {ampm2}"

        today_events.append({
            "id": evt['id'],
            "title": evt['title'],
            "location": evt['location'],
            "category": evt['category'],
            "color": subjects_dict.get(evt['category'].lower(), "#5A3E22"),
            "timeStart12h": timeStart12h,
            "timeEnd12h": timeEnd12h,
            "timeStart": evt['timeStart']
        })
    today_events.sort(key=lambda x: x['timeStart'])

    # Recommended Deck (first deck)
    decks_raw = conn.execute("SELECT * FROM decks").fetchall()
    decks = []
    for d in decks_raw:
        cards_cnt = conn.execute("SELECT COUNT(*) FROM cards WHERE deck_id = ?", (d['id'],)).fetchone()[0]
        inc_cnt = conn.execute("SELECT COUNT(*) FROM cards WHERE deck_id = ? AND incorrect = 1", (d['id'],)).fetchone()[0]
        decks.append({
            "id": d['id'],
            "title": d['title'],
            "lastPracticed": d['last_practiced'],
            "progress": d['progress'],
            "cards_count": cards_cnt,
            "incorrect_count": inc_cnt
        })

    recommended_deck = decks[0] if decks else None

    # Filter To-Dos for today
    todos_raw = conn.execute("SELECT * FROM todos WHERE date = ?", (today_str,)).fetchall()
    todos = []
    for td in todos_raw:
        todos.append({
            "id": td['id'],
            "title": td['title'],
            "category": td['category'],
            "date": td['date'],
            "time": td['time'],
            "completed": bool(td['completed']),
            "color": subjects_dict.get(td['category'].lower(), "#5A3E22")
        })

    t_struct = time.localtime()
    months = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
    today_date_label = f"{months[t_struct.tm_mon-1]} {t_struct.tm_mday}"

    # Render focus settings defaults
    timer_settings = {
        "mode": "pomodoro",
        "status": "paused",
        "type": "work",
        "work_minutes": 25,
        "break_minutes": 5,
        "duration": 1500,
        "timer_display": "25:00",
        "svg_offset": 0
    }

    conn.close()

    return render_template(
        "home.html",
        active_view="home",
        profile=profile,
        quote=quote,
        schedule=today_events,
        decks=decks,
        recommended_deck=recommended_deck,
        today_date_label=today_date_label,
        todos=todos,
        subjects=subjects,
        timer_mode=timer_settings['mode'],
        timer_status=timer_settings['status'],
        timer_type=timer_settings['type'],
        timer_work_minutes=timer_settings['work_minutes'],
        timer_break_minutes=timer_settings['break_minutes'],
        timer_display=timer_settings['timer_display'],
        timer_svg_offset=timer_settings['svg_offset']
    )

@app.route('/calendar')
def calendar_route():
    week_offset = int(request.args.get('week_offset', 0))

    # Calculate dates for the week
    today = datetime.date.today()
    start_of_week = today - datetime.timedelta(days=(today.weekday() + 1) if today.weekday() != 6 else 0)
    start_of_week += datetime.timedelta(weeks=week_offset)
    
    week_days = []
    week_date_strings = []
    day_names = ["SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT"]
    
    for i in range(7):
        day_date = start_of_week + datetime.timedelta(days=i)
        date_str = day_date.strftime("%Y-%m-%d")
        week_date_strings.append(date_str)
        is_today = date_str == today.strftime("%Y-%m-%d")
        week_days.append({
            "name": day_names[i],
            "num": day_date.day,
            "is_today": is_today
        })

    end_of_week = start_of_week + datetime.timedelta(days=6)
    range_label = f"{start_of_week.strftime('%B')} {start_of_week.day}-{end_of_week.day}"
    if start_of_week.month != end_of_week.month:
        range_label = f"{start_of_week.strftime('%b')} {start_of_week.day} - {end_of_week.strftime('%b')} {end_of_week.day}"

    conn = get_db_connection()
    subjects = conn.execute("SELECT * FROM subjects").fetchall()
    subjects_dict = {s['name'].lower(): s['color'] for s in subjects}

    # Fetch events and to-dos inside this week
    events_raw = conn.execute("SELECT * FROM events WHERE date BETWEEN ? AND ?", 
                              (week_date_strings[0], week_date_strings[-1])).fetchall()
    todos_raw = conn.execute("SELECT * FROM todos WHERE completed = 0 AND date BETWEEN ? AND ?", 
                             (week_date_strings[0], week_date_strings[-1])).fetchall()

    grid_items = []
    
    # 1. Add Events
    for evt in events_raw:
        day_idx = week_date_strings.index(evt['date'])
        sh, sm = map(int, evt['timeStart'].split(':'))
        eh, em = map(int, evt['timeEnd'].split(':'))
        start_m = sh * 60 + sm - 480
        end_m = eh * 60 + em - 480
        
        top = max(0, start_m)
        height = max(30, end_m - start_m)

        grid_items.append({
            "type": "event",
            "id": evt['id'],
            "title": evt['title'],
            "location": evt['location'],
            "date": evt['date'],
            "timeStart": evt['timeStart'],
            "timeEnd": evt['timeEnd'],
            "category": evt['category'],
            "dayOfWeek": day_idx,
            "color": subjects_dict.get(evt['category'].lower(), "#5A3E22"),
            "top": top,
            "height": height
        })

    # 2. Add To-Dos with due times to Calendar
    for todo in todos_raw:
        day_idx = week_date_strings.index(todo['date'])
        th, tm = map(int, todo['time'].split(':'))
        start_m = th * 60 + tm - 480
        top = max(0, start_m)
        height = 35

        grid_items.append({
            "type": "todo",
            "id": todo['id'],
            "title": todo['title'],
            "date": todo['date'],
            "timeStart": todo['time'],
            "completed": bool(todo['completed']),
            "dayOfWeek": day_idx,
            "color": subjects_dict.get(todo['category'].lower(), "#5A3E22"),
            "top": top,
            "height": height,
            "timeEnd": f"{int((th * 60 + tm + 45) // 60):02d}:{int((th * 60 + tm + 45) % 60):02d}"
        })

    grid_items = calculate_overlaps_for_week(grid_items)

    # Current Time Indicator
    show_time_indicator = False
    current_time_top = 0
    now_struct = time.localtime()
    now_date_str = f"{now_struct.tm_year}-{now_struct.tm_mon:02d}-{now_struct.tm_mday:02d}"
    if now_date_str in week_date_strings:
        now_m = now_struct.tm_hour * 60 + now_struct.tm_min - 480
        if 0 <= now_m <= 720:
            show_time_indicator = True
            current_time_top = now_m

    conn.close()

    return render_template(
        "calendar.html",
        active_view="calendar",
        range_label=range_label,
        week_days=week_days,
        prev_offset=week_offset - 1,
        next_offset=week_offset + 1,
        grid_items=grid_items,
        show_time_indicator=show_time_indicator,
        current_time_top=current_time_top,
        subjects=subjects
    )

@app.route('/calendar/add', methods=['POST'])
def add_event():
    title = request.form.get('title')
    date = request.form.get('date')
    category = request.form.get('category').strip()
    timeStart = request.form.get('timeStart')
    timeEnd = request.form.get('timeEnd')
    location = request.form.get('location')

    conn = get_db_connection()
    # Check if category subject exists, if not add it
    sub = conn.execute("SELECT * FROM subjects WHERE name = ?", (category,)).fetchone()
    if not sub and category:
        colors = ["#D48C70", "#C9A15B", "#5A3E22", "#8A4F37", "#00f5d4", "#9b5de5"]
        conn.execute("INSERT INTO subjects (name, color) VALUES (?, ?)", (category, random.choice(colors)))
        
    conn.execute("INSERT INTO events (title, date, timeStart, timeEnd, location, category) VALUES (?, ?, ?, ?, ?, ?)",
                 (title, date, timeStart, timeEnd, location, category))
    conn.commit()
    conn.close()
    return redirect(url_for('calendar_route'))

@app.route('/calendar/edit', methods=['POST'])
def edit_event():
    evt_id = request.form.get('id')
    action = request.form.get('action')

    conn = get_db_connection()
    if action == 'delete':
        conn.execute("DELETE FROM events WHERE id = ?", (evt_id,))
    else:
        title = request.form.get('title')
        date = request.form.get('date')
        category = request.form.get('category')
        timeStart = request.form.get('timeStart')
        timeEnd = request.form.get('timeEnd')
        location = request.form.get('location')
        
        conn.execute("UPDATE events SET title=?, date=?, category=?, timeStart=?, timeEnd=?, location=? WHERE id=?",
                     (title, date, category, timeStart, timeEnd, location, evt_id))
    conn.commit()
    conn.close()
    return redirect(url_for('calendar_route'))

# --- TO-DO LIST ROUTES ---

@app.route('/todo/add', methods=['POST'])
def add_todo():
    title = request.form.get('title')
    category = request.form.get('category').strip()
    date = request.form.get('date')
    todo_time = request.form.get('time')
    redirect_to = request.args.get('redirect', 'home')

    conn = get_db_connection()
    sub = conn.execute("SELECT * FROM subjects WHERE name = ?", (category,)).fetchone()
    if not sub and category:
        colors = ["#D48C70", "#C9A15B", "#5A3E22", "#8A4F37", "#00f5d4", "#9b5de5"]
        conn.execute("INSERT INTO subjects (name, color) VALUES (?, ?)", (category, random.choice(colors)))

    conn.execute("INSERT INTO todos (title, category, date, time, completed) VALUES (?, ?, ?, ?, 0)",
                 (title, category, date, todo_time))
    conn.commit()
    conn.close()
    
    return redirect(url_for('home_route') if redirect_to == 'home' else url_for('calendar_route'))

@app.route('/todo/toggle/<todo_id>', methods=['POST'])
def toggle_todo(todo_id):
    redirect_to = request.args.get('redirect', 'home')
    conn = get_db_connection()
    todo = conn.execute("SELECT completed FROM todos WHERE id = ?", (todo_id,)).fetchone()
    if todo:
        new_val = 0 if todo['completed'] else 1
        conn.execute("UPDATE todos SET completed = ? WHERE id = ?", (new_val, todo_id))
        conn.commit()
    conn.close()
    return redirect(url_for('home_route') if redirect_to == 'home' else url_for('calendar_route'))

@app.route('/todo/delete/<todo_id>', methods=['POST'])
def delete_todo(todo_id):
    redirect_to = request.args.get('redirect', 'home')
    conn = get_db_connection()
    conn.execute("DELETE FROM todos WHERE id = ?", (todo_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('home_route') if redirect_to == 'home' else url_for('calendar_route'))

# --- AI CHAT, NOTEBOOK & INTEGRATION ---

@app.route('/chat')
def chat_route():
    channel = request.args.get('channel', 'general')
    
    conn = get_db_connection()
    subjects = conn.execute("SELECT * FROM subjects").fetchall()
    messages_raw = conn.execute("SELECT * FROM chat_messages WHERE channel = ? ORDER BY id ASC LIMIT 50", (channel,)).fetchall()
    conn.close()

    messages = [{"sender": m['sender'], "text": m['text']} for m in messages_raw]
    
    channel_name = channel
    for s in subjects:
        if s['name'].lower().replace(' ', '-') == channel:
            channel_name = f"{s['name'].lower()}-study"
            break

    # Get API Key from profile
    user_name = session.get('user_name')
    conn = get_db_connection()
    profile = conn.execute("SELECT api_key FROM profile WHERE name = ?", (user_name,)).fetchone()
    conn.close()
    api_key_set = bool(profile['api_key'] if profile else False)

    return render_template(
        "chat.html",
        active_view="chat",
        active_channel=channel,
        active_channel_name=channel_name,
        messages=messages,
        subjects=subjects,
        active_pdf=session.get('pdf_name'),
        api_key_set=api_key_set
    )

@app.route('/chat/clear-pdf', methods=['POST'])
def clear_pdf():
    channel = request.form.get('channel', 'general')
    session.pop('pdf_context', None)
    session.pop('pdf_name', None)
    return redirect(url_for('chat_route', channel=channel))

@app.route('/chat/send', methods=['GET', 'POST'])
def chat_send():
    channel = request.form.get('channel', 'general') if request.method == 'POST' else request.args.get('channel', 'general')
    message = request.form.get('message', '').strip() if request.method == 'POST' else request.args.get('msg', '').strip()
    pdf_file = request.files.get('pdf_file') if request.method == 'POST' else None
    
    conn = get_db_connection()

    # 1. Handles PDF Upload
    if pdf_file and pdf_file.filename:
        try:
            reader = PdfReader(pdf_file)
            pdf_text = ""
            for page in reader.pages:
                pdf_text += page.extract_text() or ""
            
            session['pdf_context'] = pdf_text[:15000]
            session['pdf_name'] = pdf_file.filename
            
            welcome_text = f"📁 Loaded PDF Source: *{pdf_file.filename}* ({len(pdf_text)} characters extracted). Ask me to summarize or explain concepts from this document!"
            conn.execute("INSERT INTO chat_messages (channel, sender, text, timestamp) VALUES (?, 'ai', ?, ?)",
                         (channel, welcome_text, time.time()))
            conn.commit()
        except Exception as e:
            conn.execute("INSERT INTO chat_messages (channel, sender, text, timestamp) VALUES (?, 'ai', ?, ?)",
                         (channel, f"❌ Error reading PDF: {str(e)}", time.time()))
            conn.commit()
            
        if not message:
            conn.close()
            return redirect(url_for('chat_route', channel=channel))

    if not message:
        conn.close()
        return redirect(url_for('chat_route', channel=channel))
        
    # Log user message
    conn.execute("INSERT INTO chat_messages (channel, sender, text, timestamp) VALUES (?, 'user', ?, ?)",
                 (channel, message, time.time()))
    conn.commit()

    # Get API Key
    user_name = session.get('user_name')
    profile = conn.execute("SELECT api_key FROM profile WHERE name = ?", (user_name,)).fetchone()
    api_key = profile['api_key'] if profile else ""
    if not api_key:
        api_key = os.environ.get('GEMINI_API_KEY', "")

    bot_reply = query_gemini_ai(message, channel, api_key)
    
    # Save bot response
    conn.execute("INSERT INTO chat_messages (channel, sender, text, timestamp) VALUES (?, 'ai', ?, ?)",
                 (channel, bot_reply, time.time()))
    conn.commit()
    conn.close()
    
    return redirect(url_for('chat_route', channel=channel))

def query_gemini_ai(prompt, channel, api_key):
    sys_prompt = "You are a friendly study buddy AI named UniFlow Buddy. Help the user study academic topics."
    if channel != 'general':
        sys_prompt = f"You are the study assistant for the channel: #{channel}. Answer questions specifically relating to this academic subject."
    
    pdf_ctx = session.get('pdf_context')
    context_prefix = ""
    if pdf_ctx:
        context_prefix = f"[STUDY SOURCE DOCUMENT CONTEXT: {pdf_ctx}]\n\n"

    if api_key:
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            full_query = f"{sys_prompt}\n\n{context_prefix}User query: {prompt}"
            response = model.generate_content(full_query)
            return response.text
        except Exception as e:
            return f"⚠️ Gemini API Error: {str(e)}\n\n(Fallback Active) Try re-entering your key in Settings."

    # Fallback Responder
    clean = prompt.lower()
    if "sensory memory" in clean or "iconic" in clean:
        return "👀 **Sensory Memory Context:**\nIt stores sensory inputs for fractions of a second. Iconic memory (visual) decays in under 1 second, while Echoic memory (auditory) lasts 3-4 seconds before entering Short-Term Memory buffer."
    elif "bias" in clean or "ethical" in clean:
        return "⚖️ **AI Bias:**\nAlgorithms replicate patterns present in historical training datasets. If dataset values represent biased historical hiring decisions, the output models replicate those system biases."
    elif "quiz" in clean:
        return "📝 Let's do a quick quiz! Head over to the **Quizzes** tab at the top navbar. You can take multi-question tests or upload source texts to generate custom quizzes!"
    elif "tips" in clean or "study" in clean:
        return "💡 **UniFlow Study Tips:**\n1. Use **Active Recall**: Test your memory instead of just highlighting text.\n2. Apply **Spaced Repetition** on your flashcard decks.\n3. Cycle Pomodoros to maintain focus."
    
    return f"Hello! I am your study buddy. 💡 (Offline Mock Mode). You asked about: '{prompt}'.\n\nTo unlock fully intelligent answers, add a Gemini API Key in Settings!"

# --- AI NOTEBOOK ACTIONS ---

@app.route('/api/ai/notebook', methods=['POST'])
def ai_notebook():
    data = request.get_json() or {}
    notes = data.get('notes', '').strip()
    action = data.get('action', 'summarize')
    
    if not notes:
        return jsonify({"result": "Write some notes in the editor panel first!"})

    # Fetch API Key
    user_name = session.get('user_name')
    conn = get_db_connection()
    profile = conn.execute("SELECT api_key FROM profile WHERE name = ?", (user_name,)).fetchone()
    conn.close()
    
    api_key = profile['api_key'] if profile else ""
    if not api_key:
        api_key = os.environ.get('GEMINI_API_KEY', "")

    # Define dynamic prompt action
    if action == 'summarize':
        prompt = f"Summarize the following study notes in structured bullet points, highlighting key takeaways:\n\n{notes}"
    elif action == 'explain':
        prompt = f"Identify core academic terms from these notes and explain them in simple terms:\n\n{notes}"
    elif action == 'bullets':
        prompt = f"Convert these messy notes into a clean, hierarchical outline format:\n\n{notes}"
    elif action == 'deck':
        # Create a flashcard deck
        return create_flashcards_from_notes(notes, api_key)
    elif action == 'quiz':
        # Create a quiz
        return create_quiz_from_notes(notes, api_key)
    else:
        prompt = f"Help me analyze and improve these notes:\n\n{notes}"

    if api_key:
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content(prompt)
            return jsonify({"result": response.text})
        except Exception as e:
            return jsonify({"result": f"⚠️ Gemini API Error: {str(e)}\n\n(Fallback active: please configure your API key in settings.)"})

    # Fallback response
    mock_responses = {
        "summarize": f"### 💡 Mock Summary of Notes\n- Your notes cover topics with approximately {len(notes)} characters.\n- Key Concept 1: Active Recall is highly encouraged.\n- Key Concept 2: Take structured breaks to avoid mental fatigue.",
        "explain": f"### 🔑 Key Term Explanations\n- **Active Recall**: The practice of actively testing yourself instead of passive reading.\n- **Spaced Repetition**: Reviewing cards at increasing intervals to move information to long-term memory.",
        "bullets": f"### 📌 Hierarchical Notes Outline\n* Introduction to Academic Success\n  * Active Study Strategies\n    * Flashcard revision\n    * Multiple question testing\n  * Focus and Endurance\n    * pomodoro cycles\n    * stopwatch lap trackings"
    }
    return jsonify({"result": mock_responses.get(action, "Detailed study assistant offline. Enter a Gemini Key in Settings to get live completions!")})

def create_flashcards_from_notes(notes, api_key):
    deck_title = f"Notes Deck ({datetime.date.today().strftime('%b %d')})"
    cards = []
    
    if api_key:
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            prompt = (
                "Based on the following notes, generate 3 to 5 clear flashcards. "
                "Format your response EXACTLY as a JSON list of objects containing 'q' (question) and 'a' (answer). "
                "Do not include markdown tags like ```json or anything else. Just the raw JSON array string.\n\n"
                f"Notes: {notes}"
            )
            response = model.generate_content(prompt)
            import json
            clean_text = response.text.replace("```json", "").replace("```", "").strip()
            cards_raw = json.loads(clean_text)
            for item in cards_raw:
                if 'q' in item and 'a' in item:
                    cards.append((item['q'], item['a']))
        except Exception as e:
            print("Gemini Flashcard Generator Error:", e)
            
    if not cards:
        # Fallback cards
        cards = [
            ("Core Notes Concept 1", f"Summary facts: {notes[:60]}..."),
            ("Core Notes Concept 2", "Review this card for spaced repetition practice."),
            ("Core Notes Concept 3", "Test your active recall on details of this notebook page.")
        ]
        
    conn = get_db_connection()
    conn.execute("INSERT INTO decks (title, last_practiced, progress) VALUES (?, 'Never', 0)", (deck_title,))
    deck_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    for q, a in cards:
        conn.execute("INSERT INTO cards (deck_id, question, answer) VALUES (?, ?, ?)", (deck_id, q, a))
    conn.commit()
    conn.close()
    
    return jsonify({"result": f"✨ Successfully generated and saved flashcard deck: **{deck_title}** with {len(cards)} cards! You can study them in the Revise tab."})

def create_quiz_from_notes(notes, api_key):
    quiz_title = f"Notes Quiz ({datetime.date.today().strftime('%b %d')})"
    questions = []
    
    if api_key:
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            prompt = (
                "Based on the following notes, generate a quiz with 3 to 5 multiple-choice questions. "
                "Format your response EXACTLY as a JSON list of objects containing: "
                "'question' (question text), 'correct' (correct option letter: A, B, C, or D), "
                "'opt_a', 'opt_b', 'opt_c', 'opt_d' (option texts). "
                "Do not include markdown tags like ```json or anything else. Just the raw JSON array string.\n\n"
                f"Notes: {notes}"
            )
            response = model.generate_content(prompt)
            import json
            clean_text = response.text.replace("```json", "").replace("```", "").strip()
            qs_raw = json.loads(clean_text)
            for item in qs_raw:
                if all(k in item for k in ['question', 'correct', 'opt_a', 'opt_b', 'opt_c', 'opt_d']):
                    questions.append(item)
        except Exception as e:
            print("Gemini Quiz Generator Error:", e)

    if not questions:
        # Fallback questions
        questions = [
            {
                "question": f"What is the primary topic of the notes starting with: '{notes[:30]}...'?",
                "correct": "B",
                "opt_a": "Irrelevant Topics",
                "opt_b": "Your study notes content",
                "opt_c": "General Knowledge",
                "opt_d": "Unrelated sciences"
            },
            {
                "question": "Which of these is the best way to study this notebook section?",
                "correct": "B",
                "opt_a": "Highlighting everything",
                "opt_b": "Active recall & taking mock quizzes",
                "opt_c": "Rereading text passively",
                "opt_d": "Skimming pages quickly"
            }
        ]

    conn = get_db_connection()
    conn.execute("INSERT INTO quizzes (title) VALUES (?)", (quiz_title,))
    quiz_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    for q in questions:
        conn.execute("""
        INSERT INTO quiz_questions (quiz_id, question, correct, opt_a, opt_b, opt_c, opt_d) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (quiz_id, q['question'], q['correct'], q['opt_a'], q['opt_b'], q['opt_c'], q['opt_d']))
    conn.commit()
    conn.close()

    return jsonify({"result": f"✨ Successfully generated and saved multiple-question quiz: **{quiz_title}** with {len(questions)} questions! Try it out in the Quizzes tab."})

# --- REVISE FLASHCARDS MODULE ---

@app.route('/revise')
def revise_route():
    conn = get_db_connection()
    decks_raw = conn.execute("SELECT * FROM decks").fetchall()
    
    decks = []
    for d in decks_raw:
        cards_cnt = conn.execute("SELECT COUNT(*) FROM cards WHERE deck_id = ?", (d['id'],)).fetchone()[0]
        inc_cnt = conn.execute("SELECT COUNT(*) FROM cards WHERE deck_id = ? AND incorrect = 1", (d['id'],)).fetchone()[0]
        decks.append({
            "id": d['id'],
            "title": d['title'],
            "lastPracticed": d['last_practiced'],
            "progress": d['progress'],
            "cards_count": cards_cnt,
            "incorrect_count": inc_cnt
        })
    conn.close()
    return render_template("revise.html", active_view="revise", decks=decks)

@app.route('/revise/study/<deck_id>')
def study_deck(deck_id):
    incorrect_only = request.args.get('incorrect_only') == 'true'
    card_idx = int(request.args.get('card_idx', 0))

    conn = get_db_connection()
    deck = conn.execute("SELECT * FROM decks WHERE id = ?", (deck_id,)).fetchone()
    
    if not deck:
        conn.close()
        return redirect(url_for('revise_route'))

    # Retrieve cards
    if incorrect_only:
        cards_raw = conn.execute("SELECT * FROM cards WHERE deck_id = ? AND incorrect = 1", (deck_id,)).fetchall()
    else:
        cards_raw = conn.execute("SELECT * FROM cards WHERE deck_id = ?", (deck_id,)).fetchall()

    if not cards_raw:
        conn.close()
        return redirect(url_for('revise_route'))

    # If completed all cards in this study session
    if card_idx >= len(cards_raw):
        # Update last practiced time
        conn.execute("UPDATE decks SET last_practiced = 'Just now' WHERE id = ?", (deck_id,))
        
        # Calculate deck mastery progress: percentage of correct cards
        total_cards = conn.execute("SELECT COUNT(*) FROM cards WHERE deck_id = ?", (deck_id,)).fetchone()[0]
        correct_cards = conn.execute("SELECT COUNT(*) FROM cards WHERE deck_id = ? AND incorrect = 0", (deck_id,)).fetchone()[0]
        progress = int((correct_cards / total_cards * 100) if total_cards > 0 else 0)
        conn.execute("UPDATE decks SET progress = ? WHERE id = ?", (progress, deck_id))
        conn.commit()
        conn.close()
        
        return render_template("revise.html", study_mode=False, summary_mode=True, deck=deck, score=correct_cards, total=total_cards)

    card = cards_raw[card_idx]
    conn.close()

    return render_template(
        "revise.html",
        study_mode=True,
        summary_mode=False,
        deck=deck,
        card={"q": card['question'], "a": card['answer'], "id": card['id']},
        card_idx=card_idx,
        current_display_idx=card_idx + 1,
        total_cards=len(cards_raw),
        incorrect_only=incorrect_only
    )

@app.route('/revise/study/<deck_id>/rate', methods=['POST'])
def rate_card(deck_id):
    card_idx = int(request.form.get('card_idx', 0))
    incorrect_only = request.form.get('incorrect_only') == 'true'
    rating = request.form.get('rating') # need_review, got_it

    conn = get_db_connection()
    if incorrect_only:
        cards_raw = conn.execute("SELECT id FROM cards WHERE deck_id = ? AND incorrect = 1", (deck_id,)).fetchall()
    else:
        cards_raw = conn.execute("SELECT id FROM cards WHERE deck_id = ?", (deck_id,)).fetchall()

    if cards_raw and card_idx < len(cards_raw):
        card_id = cards_raw[card_idx]['id']
        inc_val = 1 if rating == 'need_review' else 0
        conn.execute("UPDATE cards SET incorrect = ? WHERE id = ?", (inc_val, card_id))
        conn.commit()
    conn.close()

    return redirect(url_for('study_deck', deck_id=deck_id, card_idx=card_idx + 1, incorrect_only='true' if incorrect_only else 'false'))

@app.route('/revise/deck/<deck_id>/add-card', methods=['POST'])
def add_card_to_deck(deck_id):
    q = request.form.get('q').strip()
    a = request.form.get('a').strip()

    if q and a:
        conn = get_db_connection()
        conn.execute("INSERT INTO cards (deck_id, question, answer, incorrect) VALUES (?, ?, ?, 0)", (deck_id, q, a))
        # Recalculate deck progress
        total_cards = conn.execute("SELECT COUNT(*) FROM cards WHERE deck_id = ?", (deck_id,)).fetchone()[0]
        correct_cards = conn.execute("SELECT COUNT(*) FROM cards WHERE deck_id = ? AND incorrect = 0", (deck_id,)).fetchone()[0]
        progress = int((correct_cards / total_cards * 100) if total_cards > 0 else 0)
        conn.execute("UPDATE decks SET progress = ? WHERE id = ?", (progress, deck_id))
        conn.commit()
        conn.close()

    return redirect(url_for('revise_route'))

@app.route('/revise/create-deck', methods=['POST'])
def create_deck():
    title = request.form.get('title').strip()
    
    if title:
        conn = get_db_connection()
        conn.execute("INSERT INTO decks (title, last_practiced, progress) VALUES (?, 'Never', 0)", (title,))
        deck_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        
        # Add the 3 card fields if filled
        for idx in range(1, 4):
            q = request.form.get(f"q_{idx}", "").strip()
            a = request.form.get(f"a_{idx}", "").strip()
            if q and a:
                conn.execute("INSERT INTO cards (deck_id, question, answer, incorrect) VALUES (?, ?, ?, 0)", (deck_id, q, a))
        
        # Recalculate deck progress
        total_cards = conn.execute("SELECT COUNT(*) FROM cards WHERE deck_id = ?", (deck_id,)).fetchone()[0]
        correct_cards = conn.execute("SELECT COUNT(*) FROM cards WHERE deck_id = ? AND incorrect = 0", (deck_id,)).fetchone()[0]
        progress = int((correct_cards / total_cards * 100) if total_cards > 0 else 0)
        conn.execute("UPDATE decks SET progress = ? WHERE id = ?", (progress, deck_id))
        conn.commit()
        conn.close()

    return redirect(url_for('revise_route'))

# --- FOCUS TIMERS & HEATMAP LOGGER ---

@app.route('/focus')
def focus_route():
    user_name = session.get('user_name')
    conn = get_db_connection()
    profile = conn.execute("SELECT * FROM profile WHERE name = ?", (user_name,)).fetchone()
    sessions_raw = conn.execute("SELECT * FROM focus_sessions").fetchall()
    conn.close()

    sessions = [s['timestamp'] for s in sessions_raw]
    streak_count = get_streak_count(sessions)

    # heatmap days calculation
    active_heatmap_days = []
    now_struct = time.localtime()
    cur_year = now_struct.tm_year
    cur_mon = now_struct.tm_mon
    for ts in sessions:
        t_struct = time.localtime(ts)
        if t_struct.tm_year == cur_year and t_struct.tm_mon == cur_mon:
            active_heatmap_days.append(t_struct.tm_mday)
    active_heatmap_days = list(set(active_heatmap_days))

    # calendar layout settings
    import calendar
    months_names = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
    month_label = f"{months_names[cur_mon-1]} {cur_year}"
    first_weekday, days_in_month = calendar.monthrange(cur_year, cur_mon)
    first_day_idx = (first_weekday + 1) % 7 # align Sun=0

    # read customizable timers settings
    timer_settings = session.get('timer_settings', {
        "mode": "pomodoro",
        "work_minutes": 25,
        "break_minutes": 5,
        "custom_minutes": 25
    })

    return render_template(
        "focus.html",
        active_view="focus",
        profile=profile,
        focus_sessions=sessions,
        streak_count=streak_count,
        active_heatmap_days=active_heatmap_days,
        month_label=month_label,
        first_day_idx=first_day_idx,
        days_in_month=days_in_month,
        timer_mode=timer_settings['mode'],
        timer_work_minutes=timer_settings['work_minutes'],
        timer_break_minutes=timer_settings['break_minutes'],
        timer_custom_minutes=timer_settings['custom_minutes']
    )

@app.route('/focus/set-mode', methods=['POST'])
def focus_set_mode():
    mode = request.form.get('mode', 'pomodoro')
    timer_settings = session.get('timer_settings', {
        "mode": "pomodoro",
        "work_minutes": 25,
        "break_minutes": 5,
        "custom_minutes": 25
    })
    timer_settings['mode'] = mode
    session['timer_settings'] = timer_settings
    return redirect(url_for('focus_route'))

@app.route('/focus/set-custom-duration', methods=['POST'])
def focus_set_custom_duration():
    hours = int(request.form.get('hours', 0))
    minutes = int(request.form.get('minutes', 25))
    total_mins = hours * 60 + minutes
    
    timer_settings = session.get('timer_settings', {
        "mode": "pomodoro",
        "work_minutes": 25,
        "break_minutes": 5,
        "custom_minutes": 25
    })
    timer_settings['custom_minutes'] = total_mins
    session['timer_settings'] = timer_settings
    return redirect(url_for('focus_route'))

@app.route('/focus/set-pomodoro-times', methods=['POST'])
def focus_set_pomodoro_times():
    work_min = int(request.form.get('work_min', 25))
    break_min = int(request.form.get('break_min', 5))
    
    timer_settings = session.get('timer_settings', {
        "mode": "pomodoro",
        "work_minutes": 25,
        "break_minutes": 5,
        "custom_minutes": 25
    })
    timer_settings['work_minutes'] = work_min
    timer_settings['break_minutes'] = break_min
    session['timer_settings'] = timer_settings
    return redirect(url_for('focus_route'))

@app.route('/api/focus/log', methods=['POST'])
def api_log_focus_session():
    # JSON endpoint to record completed focus hours
    data = request.get_json() or {}
    duration = float(data.get('duration', 25.0)) # duration in minutes
    session_type = data.get('type', 'work')

    user_name = session.get('user_name')
    if not user_name:
        return jsonify({"error": "Unauthorized"}), 401

    conn = get_db_connection()
    
    # Log session
    conn.execute("INSERT INTO focus_sessions (timestamp, duration, type) VALUES (?, ?, ?)",
                 (time.time(), duration, session_type))
    
    # Update profile work hours if it is work session
    if session_type == 'work':
        hrs = duration / 60.0
        conn.execute("UPDATE profile SET focus_hours_today = focus_hours_today + ?, focus_hours_total = focus_hours_total + ? WHERE name = ?",
                     (hrs, hrs, user_name))
        
    conn.commit()

    # Recalculate streak
    sessions_raw = conn.execute("SELECT timestamp FROM focus_sessions").fetchall()
    profile = conn.execute("SELECT * FROM profile WHERE name = ?", (user_name,)).fetchone()
    conn.close()

    sessions = [s['timestamp'] for s in sessions_raw]
    streak = get_streak_count(sessions)

    return jsonify({
        "success": True,
        "streak": streak,
        "focus_hours_today": profile['focus_hours_today'],
        "focus_hours_total": profile['focus_hours_total']
    })

# --- QUIZZES ARENA & CREATOR MODULE ---

@app.route('/quizzes')
def quizzes_route():
    conn = get_db_connection()
    quizzes_raw = conn.execute("SELECT * FROM quizzes").fetchall()
    
    quizzes = []
    for qz in quizzes_raw:
        questions_cnt = conn.execute("SELECT COUNT(*) FROM quiz_questions WHERE quiz_id = ?", (qz['id'],)).fetchone()[0]
        quizzes.append({
            "id": qz['id'],
            "title": qz['title'],
            "questions_count": questions_cnt
        })
    conn.close()

    # Get API Key from profile
    user_name = session.get('user_name')
    conn = get_db_connection()
    profile = conn.execute("SELECT api_key FROM profile WHERE name = ?", (user_name,)).fetchone()
    conn.close()
    api_key_set = bool(profile['api_key'] if profile else False)

    return render_template(
        "quizzes.html",
        active_view="quizzes",
        quizzes=quizzes,
        api_key_set=api_key_set
    )

@app.route('/quizzes/take/<quiz_id>')
def take_quiz(quiz_id):
    q_idx = int(request.args.get('q_idx', 0))

    conn = get_db_connection()
    quiz = conn.execute("SELECT * FROM quizzes WHERE id = ?", (quiz_id,)).fetchone()
    if not quiz:
        conn.close()
        return redirect(url_for('quizzes_route'))

    questions = conn.execute("SELECT * FROM quiz_questions WHERE quiz_id = ?", (quiz_id,)).fetchall()
    conn.close()

    if not questions:
        return redirect(url_for('quizzes_route'))

    # If completed all questions, show scorecard
    if q_idx >= len(questions):
        # Calculate scorecard
        answers = session.get(f'quiz_ans_{quiz_id}', {})
        score = 0
        reviews = []
        
        conn = get_db_connection()
        for idx, q in enumerate(questions):
            user_ans = answers.get(str(idx), "")
            correct_ans = q['correct']
            is_correct = user_ans == correct_ans
            if is_correct:
                score += 1
            else:
                # Add to incorrect flashcards deck! Create a "Quiz Failures" deck
                deck_title = "Quiz Reviews"
                deck = conn.execute("SELECT id FROM decks WHERE title = ?", (deck_title,)).fetchone()
                if not deck:
                    conn.execute("INSERT INTO decks (title, last_practiced, progress) VALUES (?, 'Never', 0)", (deck_title,))
                    deck_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
                else:
                    deck_id = deck['id']
                
                # Check if card already exists
                card_exists = conn.execute("SELECT id FROM cards WHERE deck_id = ? AND question = ?", (deck_id, q['question'])).fetchone()
                if not card_exists:
                    # Retrieve correct answer option text
                    correct_opt_text = q['opt_a'] if correct_ans == 'A' else q['opt_b'] if correct_ans == 'B' else q['opt_c'] if correct_ans == 'C' else q['opt_d']
                    conn.execute("INSERT INTO cards (deck_id, question, answer, incorrect) VALUES (?, ?, ?, 1)",
                                 (deck_id, q['question'], f"Correct Option: {correct_ans}. Details: {correct_opt_text}",))

            # Option text resolution
            opt_texts = {'A': q['opt_a'], 'B': q['opt_b'], 'C': q['opt_c'], 'D': q['opt_d']}
            reviews.append({
                "question": q['question'],
                "correct_key": correct_ans,
                "correct_text": opt_texts.get(correct_ans, ""),
                "user_key": user_ans,
                "user_text": opt_texts.get(user_ans, "No Answer"),
                "is_correct": is_correct
            })
        
        # Save updates to database
        conn.commit()
        conn.close()

        score_pct = int((score / len(questions) * 100) if questions else 0)
        session.pop(f'quiz_ans_{quiz_id}', None) # Clear answers cache

        return render_template(
            "quizzes.html",
            active_view="quizzes",
            taking_quiz_mode=False,
            summary_mode=True,
            quiz=quiz,
            score=score,
            total=len(questions),
            score_pct=score_pct,
            reviews=reviews
        )

    q = questions[q_idx]
    pct_progress = int((q_idx / len(questions)) * 100)
    
    return render_template(
        "quizzes.html",
        active_view="quizzes",
        taking_quiz_mode=True,
        summary_mode=False,
        quiz=quiz,
        question={
            "q": q['question'],
            "options": [
                {"key": "A", "text": q['opt_a']},
                {"key": "B", "text": q['opt_b']},
                {"key": "C", "text": q['opt_c']},
                {"key": "D", "text": q['opt_d']}
            ]
        },
        q_idx=q_idx,
        current_display_idx=q_idx + 1,
        total_questions=len(questions),
        pct_progress=pct_progress
    )

@app.route('/quizzes/submit', methods=['POST'])
def submit_quiz_answer():
    quiz_id = request.form.get('quiz_id')
    q_idx = int(request.form.get('q_idx'))
    answer = request.form.get('answer') # A, B, C, D

    answers = session.get(f'quiz_ans_{quiz_id}', {})
    answers[str(q_idx)] = answer
    session[f'quiz_ans_{quiz_id}'] = answers

    return redirect(url_for('take_quiz', quiz_id=quiz_id, q_idx=q_idx + 1))

@app.route('/quizzes/generate', methods=['POST'])
def generate_quiz_or_cards():
    generate_type = request.form.get('generate_type') # quiz, flashcards
    source_text = request.form.get('source_text', '').strip()
    source_file = request.files.get('source_file')

    # Read text
    study_text = source_text
    if source_file and source_file.filename:
        try:
            if source_file.filename.endswith('.pdf'):
                reader = PdfReader(source_file)
                pdf_text = ""
                for page in reader.pages:
                    pdf_text += page.extract_text() or ""
                study_text += "\n" + pdf_text
            else:
                study_text += "\n" + source_file.read().decode('utf-8')
        except Exception as e:
            flash(f"Error parsing file: {str(e)}", "error")
            return redirect(url_for('quizzes_route'))

    if not study_text.strip():
        flash("Please enter some study text or upload a study file first!", "warning")
        return redirect(url_for('quizzes_route'))

    # Fetch API key
    user_name = session.get('user_name')
    conn = get_db_connection()
    profile = conn.execute("SELECT api_key FROM profile WHERE name = ?", (user_name,)).fetchone()
    conn.close()
    
    api_key = profile['api_key'] if profile else ""
    if not api_key:
        api_key = os.environ.get('GEMINI_API_KEY', "")

    if generate_type == 'quiz':
        # Generate Quiz
        res = create_quiz_from_notes(study_text[:12000], api_key)
        flash("✨ Generated study quiz successfully! Check the Quizzes list below.", "success")
    else:
        # Generate flashcards
        res = create_flashcards_from_notes(study_text[:12000], api_key)
        flash("✨ Generated flashcard deck successfully! Head to the Revise page to study them.", "success")

    return redirect(url_for('quizzes_route'))

@app.route('/quizzes/create-manual', methods=['POST'])
def create_quiz_manual():
    title = request.form.get('title').strip()
    
    if title:
        conn = get_db_connection()
        conn.execute("INSERT INTO quizzes (title) VALUES (?)", (title,))
        quiz_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        
        # Add 3 questions if filled
        for idx in range(1, 4):
            q_text = request.form.get(f"q_{idx}_text", "").strip()
            opt_a = request.form.get(f"q_{idx}_a", "").strip()
            opt_b = request.form.get(f"q_{idx}_b", "").strip()
            opt_c = request.form.get(f"q_{idx}_c", "").strip()
            opt_d = request.form.get(f"q_{idx}_d", "").strip()
            correct = request.form.get(f"q_{idx}_correct", "A")
            
            if q_text and opt_a and opt_b:
                conn.execute("""
                INSERT INTO quiz_questions (quiz_id, question, correct, opt_a, opt_b, opt_c, opt_d) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (quiz_id, q_text, correct, opt_a, opt_b, opt_c, opt_d))
        conn.commit()
        conn.close()
        flash("Quiz created successfully!", "success")
        
    return redirect(url_for('quizzes_route'))

# --- SETTINGS CONFIGURATOR ---

@app.route('/settings')
def settings_route():
    user_name = session.get('user_name')
    conn = get_db_connection()
    profile = conn.execute("SELECT * FROM profile WHERE name = ?", (user_name,)).fetchone()
    subjects = conn.execute("SELECT * FROM subjects").fetchall()
    conn.close()
    
    api_key = profile['api_key'] if profile else ""
    return render_template("settings.html", active_view="settings", api_key=api_key, subjects=subjects)

@app.route('/settings/save-api-key', methods=['POST'])
def save_api_key():
    api_key = request.form.get('api_key', '').strip()
    user_name = session.get('user_name')
    
    conn = get_db_connection()
    conn.execute("UPDATE profile SET api_key = ? WHERE name = ?", (api_key, user_name))
    conn.commit()
    conn.close()
    
    flash("API Key saved successfully!", "success")
    return redirect(url_for('settings_route'))

@app.route('/settings/add-subject', methods=['POST'])
def add_subject():
    name = request.form.get('name', '').strip()
    color = request.form.get('color', '#D48C70')

    if name:
        conn = get_db_connection()
        conn.execute("INSERT OR IGNORE INTO subjects (name, color) VALUES (?, ?)", (name, color))
        # Create a default flashcard deck for each subject
        conn.execute("INSERT INTO decks (title, last_practiced, progress) VALUES (?, 'Never', 0)", (name,))
        deck_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.execute("INSERT INTO cards (deck_id, question, answer) VALUES (?, ?, ?)", 
                     (deck_id, f"Core Concept in {name}", f"Enter study terms or details for {name} here."))
        conn.commit()
        conn.close()
        flash(f"Subject '{name}' added successfully!", "success")

    return redirect(url_for('settings_route'))

@app.route('/settings/edit-subject/<old_name>', methods=['POST'])
def edit_subject(old_name):
    new_name = request.form.get('new_name', '').strip()
    color = request.form.get('color')

    if new_name:
        conn = get_db_connection()
        conn.execute("UPDATE subjects SET name = ?, color = ? WHERE name = ?", (new_name, color, old_name))
        conn.execute("UPDATE events SET category = ? WHERE category = ?", (new_name, old_name))
        conn.execute("UPDATE todos SET category = ? WHERE category = ?", (new_name, old_name))
        conn.commit()
        conn.close()
        flash("Subject updated successfully!", "success")

    return redirect(url_for('settings_route'))

@app.route('/settings/delete-subject/<name>', methods=['POST'])
def delete_subject(name):
    conn = get_db_connection()
    conn.execute("DELETE FROM subjects WHERE name = ?", (name,))
    # Delete related event/todos or map them to general
    conn.execute("UPDATE events SET category = 'General' WHERE category = ?", (name,))
    conn.execute("UPDATE todos SET category = 'General' WHERE category = ?", (name,))
    conn.commit()
    conn.close()
    flash(f"Subject '{name}' deleted successfully!", "success")
    return redirect(url_for('settings_route'))

@app.route('/settings/reset', methods=['POST'])
def reset_db():
    # Remove existing SQLite file and reinitialize
    if os.path.exists("uniflow.db"):
        os.remove("uniflow.db")
    init_db()
    session.clear()
    flash("Database successfully reset to original defaults!", "success")
    return redirect(url_for('login_route'))

if __name__ == '__main__':
    # Retrieve port from env or default
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
