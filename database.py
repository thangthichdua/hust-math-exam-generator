import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "maclaurin_app.db")

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Exercises (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            week_id INTEGER NOT NULL,          
            topic_id INTEGER NOT NULL,         
            difficulty INTEGER NOT NULL,       
            function_text TEXT NOT NULL,       
            has_parameter BOOLEAN NOT NULL,    
            latex_template TEXT NOT NULL,      
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    # Thêm các cột mới (Bao gồm bad_seeds)
    try: cursor.execute("ALTER TABLE Exercises ADD COLUMN question_type TEXT DEFAULT 'Tự luận'")
    except: pass
    try: cursor.execute("ALTER TABLE Exercises ADD COLUMN options_template TEXT DEFAULT ''")
    except: pass
    try: cursor.execute("ALTER TABLE Exercises ADD COLUMN solution_logic TEXT DEFAULT ''")
    except: pass
    try: cursor.execute("ALTER TABLE Exercises ADD COLUMN bad_seeds TEXT DEFAULT ''")
    except: pass
    
    conn.commit()
    conn.close()

def insert_exercise(week_id, topic_id, difficulty, function_text, has_parameter, latex_template, q_type="Tự luận", options="", logic="", bad_seeds=""):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO Exercises (week_id, topic_id, difficulty, function_text, has_parameter, latex_template, question_type, options_template, solution_logic, bad_seeds)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (week_id, topic_id, difficulty, function_text, has_parameter, latex_template, q_type, options, logic, bad_seeds))
    conn.commit()
    conn.close()

def get_exercises_by_custom_filter(filter_type, selected_ids, diff):
    # LƯU Ý: Đã bỏ LIMIT và ORDER BY RANDOM(). Trả về toàn bộ danh sách để Python dùng random.seed() chọn.
    if not selected_ids: return []
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    placeholders = ",".join(["?"] * len(selected_ids))
    params = selected_ids.copy() 
    base_col = "id, function_text, has_parameter, latex_template, question_type, options_template, solution_logic, bad_seeds"
    
    if filter_type == "topic":
        query = f"SELECT {base_col} FROM Exercises WHERE topic_id IN ({placeholders})"
    else: 
        query = f"SELECT {base_col} FROM Exercises WHERE week_id IN ({placeholders})"

    if diff != "Tất cả":
        diff_val = int(diff.split(" - ")[0])
        query += " AND difficulty = ?"
        params.append(diff_val)

    cursor.execute(query, params)
    results = cursor.fetchall()
    conn.close()
    return results

def get_all_exercises():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT id, week_id, topic_id, difficulty, question_type, function_text FROM Exercises ORDER BY id DESC')
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_filtered_exercises(week="Tất cả", topic="Tất cả", diff="Tất cả", sort_by="Mới nhất"):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    query = "SELECT id, week_id, topic_id, difficulty, question_type, function_text, latex_template FROM Exercises WHERE 1=1"
    params = []
    
    if week != "Tất cả":
        query += " AND week_id = ?"
        params.append(int(week))
    if topic != "Tất cả":
        # Tách lấy ID từ chuỗi "1 - Đại cương về..."
        query += " AND topic_id = ?"
        params.append(int(topic.split(" - ")[0]))
    if diff != "Tất cả":
        diff_val = int(diff.split(" - ")[0])
        query += " AND difficulty = ?"
        params.append(diff_val)
        
    if sort_by == "Mới nhất": query += " ORDER BY id DESC"
    elif sort_by == "Cũ nhất": query += " ORDER BY id ASC"
    elif sort_by == "Tuần (Tăng dần)": query += " ORDER BY week_id ASC, topic_id ASC"
    elif sort_by == "Độ khó (Tăng dần)": query += " ORDER BY difficulty ASC, week_id ASC"
        
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_exercise_by_id(ex_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT week_id, topic_id, difficulty, latex_template, question_type, options_template, solution_logic, bad_seeds FROM Exercises WHERE id = ?', (ex_id,))
    row = cursor.fetchone()
    conn.close()
    return row

def update_exercise(ex_id, week_id, topic_id, difficulty, func_text, latex_template, q_type, options, logic, bad_seeds):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE Exercises 
        SET week_id = ?, topic_id = ?, difficulty = ?, function_text = ?, latex_template = ?, question_type = ?, options_template = ?, solution_logic = ?, bad_seeds = ?
        WHERE id = ?
    ''', (week_id, topic_id, difficulty, func_text, latex_template, q_type, options, logic, bad_seeds, ex_id))
    conn.commit()
    conn.close()

def delete_exercise(ex_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM Exercises WHERE id = ?', (ex_id,))
    conn.commit()
    conn.close()

def get_exercise_by_id_full(ex_id):
    """Lấy đầy đủ 8 trường dữ liệu để phục vụ việc sinh đề thủ công"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT id, function_text, has_parameter, latex_template, question_type, options_template, solution_logic, bad_seeds FROM Exercises WHERE id = ?', (ex_id,))
    row = cursor.fetchone()
    conn.close()
    return row

def get_exercises_excluding(exclude_ids, week="Tất cả", diff="Tất cả", topic="Tất cả", limit=None):
    """Lấy danh sách câu hỏi nhưng BỎ QUA những câu đã được chọn"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    query = "SELECT id, week_id, topic_id, difficulty, question_type, function_text, latex_template FROM Exercises WHERE 1=1"
    params = []
    
    if exclude_ids:
        placeholders = ",".join(["?"] * len(exclude_ids))
        query += f" AND id NOT IN ({placeholders})"
        params.extend(exclude_ids)
        
    if week != "Tất cả":
        query += " AND week_id = ?"
        params.append(int(week))
    if topic != "Tất cả":
        query += " AND topic_id = ?"
        params.append(int(topic.split(" - ")[0]))
    if diff != "Tất cả":
        diff_val = int(diff.split(" - ")[0])
        query += " AND difficulty = ?"
        params.append(diff_val)
        
    query += " ORDER BY id DESC"
    if limit:
        query += " LIMIT ?"
        params.append(limit)
        
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return rows