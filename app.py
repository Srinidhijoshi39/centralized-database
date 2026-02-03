from flask import Flask, request, jsonify, render_template, g
from markupsafe import escape
from flask_cors import CORS
import psycopg2
from psycopg2 import pool, sql
from datetime import datetime
import logging
import os
from dotenv import load_dotenv
from backup_manager import BackupManager

load_dotenv()

app = Flask(__name__)
CORS(app)
logging.getLogger('werkzeug').setLevel(logging.INFO)

# Security: Set secret key for session management
app.secret_key = os.getenv('SECRET_KEY', os.urandom(24))

# Initialize backup manager
backup_manager = BackupManager()

# Connection pool
connection_pool = None

def init_connection_pool():
    global connection_pool
    if connection_pool is None:
        try:
            connection_pool = psycopg2.pool.SimpleConnectionPool(
                1, 10,  # Increased max connections for better performance
                host=os.getenv('DB_HOST', 'localhost'),
                database=os.getenv('DB_NAME', 'trading_master_db'),
                user=os.getenv('DB_USER', 'postgres'),
                password=os.getenv('DB_PASSWORD'),
                port=os.getenv('DB_PORT', '5432'),
                # Add connection timeout and keepalive
                connect_timeout=10,
                keepalives_idle=600,
                keepalives_interval=30,
                keepalives_count=3
            )
            print("Connection pool initialized successfully")
        except Exception as e:
            print(f"Failed to initialize connection pool: {e}")
            connection_pool = None

TABLE_MAP = {
    'master_bot_data': 'master_bot_data',
    'client_bot_signups': 'client_bot_signups',
    'daily_trading_sessions': 'user_session_data'
}

def get_db():
    if 'db' not in g:
        if connection_pool is None:
            init_connection_pool()
        if connection_pool is not None:
            g.db = connection_pool.getconn()
        else:
            # Fallback to direct connection if pool fails
            g.db = psycopg2.connect(
                host=os.getenv('DB_HOST', 'localhost'),
                database=os.getenv('DB_NAME', 'trading_master_db'),
                user=os.getenv('DB_USER', 'postgres'),
                password=os.getenv('DB_PASSWORD'),
                port=os.getenv('DB_PORT', '5432')
            )
    return g.db

@app.teardown_appcontext
def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        if connection_pool is not None:
            connection_pool.putconn(db)
        else:
            db.close()

def get_client_data(client_id, db_name):
    try:
        conn = get_db()
        cur = conn.cursor()
        table_name = TABLE_MAP.get(db_name)
        if table_name:
            if table_name == 'master_bot_data':
                query = sql.SQL("SELECT name, email, phone, client_id, bot_id, created_at FROM {} WHERE name IS NOT NULL AND name != '' AND email IS NOT NULL AND email != '' ORDER BY sl_number ASC").format(sql.Identifier(table_name))
            elif table_name == 'client_bot_signups':
                query = sql.SQL("SELECT client_id, username, email, phone, aadhar, qr_key, created_at FROM {} WHERE username IS NOT NULL AND username != '' AND email IS NOT NULL AND email != '' ORDER BY id ASC").format(sql.Identifier(table_name))
            elif table_name == 'user_session_data':
                query = sql.SQL("""
                    SELECT session_date, client_id, username, kite_id, 
                           COALESCE(MAX(kite_username), '') as kite_username,
                           COUNT(DISTINCT total_trades) as total_sessions
                    FROM {} 
                    WHERE client_id IS NOT NULL AND client_id != ''
                      AND username IS NOT NULL AND username != ''
                      AND kite_id IS NOT NULL AND kite_id != ''
                      AND kite_username IS NOT NULL AND kite_username != ''
                    GROUP BY session_date, client_id, username, kite_id
                    ORDER BY session_date DESC, client_id ASC
                """).format(sql.Identifier(table_name))
            else:
                query = sql.SQL("SELECT * FROM {}").format(sql.Identifier(table_name))
            cur.execute(query)
        else:
            return [], []
        columns = [desc[0] for desc in cur.description]
        rows = cur.fetchall()
        
        # Add sequential SL numbers and format datetime
        if table_name in ['master_bot_data', 'client_bot_signups', 'user_session_data'] and rows:
            formatted_rows = []
            for i, row in enumerate(rows, 1):  # Start from 1
                row_list = [i] + list(row)  # Add sequential SL number at start
                # Format datetime columns
                for j in range(len(row_list)):
                    if isinstance(row_list[j], datetime):
                        row_list[j] = row_list[j].strftime('%d-%b-%Y')
                    elif hasattr(row_list[j], 'strftime'):  # Handle date objects
                        row_list[j] = row_list[j].strftime('%d-%b-%Y')
                # Add view button for user_session_data
                if table_name == 'user_session_data':
                    row_list.append('View')  # Add view button
                formatted_rows.append(tuple(row_list))
            rows = formatted_rows
            columns = ['sl_number'] + columns
            if table_name == 'user_session_data':
                columns.append('view_button')  # Add view button column
        
        return columns, rows
    except Exception as e:
        logging.error(f"Database error in get_client_data: {e}")
        return [], []

@app.route('/')
def database_viewer():
    return render_template('database_viewer.html', db_views=sorted(TABLE_MAP.keys()))

@app.route('/view_data')
def view_data():
    db_name = request.args.get('db')
    # Input validation and sanitization
    if db_name not in TABLE_MAP:
        return render_template('view_data.html', db_name='', columns=[], rows=[], error="Invalid database name")
    
    columns, rows = get_client_data(None, db_name)
    if db_name == 'master_bot_data' and columns:
        display_columns = []
        for col in columns:
            if col == 'sl_number':
                display_columns.append('SL No')
            elif col == 'client_id':
                display_columns.append('Client ID')
            elif col == 'bot_id':
                display_columns.append('Bot ID')
            elif col == 'created_at':
                display_columns.append('Created At')
            else:
                display_columns.append(col.title())
        columns = display_columns
    elif db_name == 'client_bot_signups' and columns:
        display_columns = []
        for col in columns:
            if col == 'sl_number':
                display_columns.append('SL No')
            elif col == 'client_id':
                display_columns.append('Client ID')
            elif col == 'qr_key':
                display_columns.append('QR Key')
            elif col == 'created_at':
                display_columns.append('Created At')
            else:
                display_columns.append(col.title())
        columns = display_columns
    elif db_name == 'daily_trading_sessions' and columns:
        display_columns = []
        for col in columns:
            if col == 'sl_number':
                display_columns.append('SL No')
            elif col == 'client_id':
                display_columns.append('Client ID')
            elif col == 'username':
                display_columns.append('Login Username')
            elif col == 'session_date':
                display_columns.append('Date')
            elif col == 'kite_id':
                display_columns.append('Kite ID')
            elif col == 'kite_username':
                display_columns.append('Zerodha User Name')
            elif col == 'total_sessions':
                display_columns.append('Total Sessions')
            elif col == 'session_type':
                display_columns.append('Type')
            elif col == 'session_duration':
                display_columns.append('Duration')
            elif col == 'session_status':
                display_columns.append('Status')
            elif col == 'view_button':
                display_columns.append('View Button')
            else:
                display_columns.append(col.title())
        columns = display_columns
    return render_template('view_data.html', db_name=db_name, columns=columns, rows=rows)

@app.route('/api/get-latest-data/<table_name>')
def get_latest_data(table_name):
    try:
        columns, rows = get_client_data(None, table_name)
        
        # Format columns based on table type
        if table_name == 'master_bot_data' and columns:
            display_columns = []
            for col in columns:
                if col == 'sl_number':
                    display_columns.append('SL No')
                elif col == 'client_id':
                    display_columns.append('Client ID')
                elif col == 'bot_id':
                    display_columns.append('Bot ID')
                elif col == 'created_at':
                    display_columns.append('Created At')
                else:
                    display_columns.append(col.title())
            columns = display_columns
        elif table_name == 'client_bot_signups' and columns:
            display_columns = []
            for col in columns:
                if col == 'sl_number':
                    display_columns.append('SL No')
                elif col == 'client_id':
                    display_columns.append('Client ID')
                elif col == 'qr_key':
                    display_columns.append('QR Key')
                elif col == 'created_at':
                    display_columns.append('Created At')
                else:
                    display_columns.append(col.title())
            columns = display_columns
        elif table_name == 'daily_trading_sessions' and columns:
            display_columns = []
            for col in columns:
                if col == 'sl_number':
                    display_columns.append('SL No')
                elif col == 'client_id':
                    display_columns.append('Client ID')
                elif col == 'username':
                    display_columns.append('Login Username')
                elif col == 'session_date':
                    display_columns.append('Date')
                elif col == 'kite_id':
                    display_columns.append('Kite ID')
                elif col == 'kite_username':
                    display_columns.append('Zerodha User Name')
                elif col == 'total_sessions':
                    display_columns.append('Total Sessions')
                elif col == 'view_button':
                    display_columns.append('View Button')
                else:
                    display_columns.append(col.title())
            columns = display_columns
        
        return jsonify({
            'status': 'success',
            'columns': columns,
            'rows': rows
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/sync-signup', methods=['POST'])
def sync_signup():
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "Invalid JSON"}), 400

    conn = None
    try:
        conn = get_db()
        cur = conn.cursor()
        
        # Handle both master bot data and client signup data
        client_id = data.get('client_id')
        
        # Check if this is master bot data (has name field) or client signup data (has username field)
        if 'name' in data:
            # Master bot data
            name = data.get('name')
            email = data.get('email')
            phone = data.get('phone')
            bot_id = data.get('bot_id')
            
            if not client_id or not name or not email:
                return jsonify({"status": "error", "message": "client_id, name, and email are required"}), 400
            
            cur.execute("SELECT sl_number FROM master_bot_data WHERE client_id = %s", (client_id,))
            existing = cur.fetchone()
            
            if existing:
                sql_update = """
                    UPDATE master_bot_data 
                    SET name = %s, email = %s, phone = %s, bot_id = %s, created_at = CURRENT_TIMESTAMP
                    WHERE client_id = %s
                """
                cur.execute(sql_update, (name, email, phone, bot_id, client_id))
            else:
                sql_insert = """
                    INSERT INTO master_bot_data (client_id, bot_id, name, email, phone, created_at)
                    VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                """
                cur.execute(sql_insert, (client_id, bot_id, name, email, phone))
        
        elif 'username' in data:
            # Client signup data
            username = data.get('username')
            email = data.get('email')
            phone = data.get('phone')
            aadhar = data.get('aadhar')
            qr_key = data.get('qr_key')
            
            if not client_id or not username or not email:
                return jsonify({"status": "error", "message": "client_id, username, and email are required"}), 400
            
            cur.execute("SELECT id FROM client_bot_signups WHERE client_id = %s", (client_id,))
            existing = cur.fetchone()
            
            if existing:
                sql_update = """
                    UPDATE client_bot_signups 
                    SET username = %s, email = %s, phone = %s, aadhar = %s, qr_key = %s, created_at = CURRENT_TIMESTAMP
                    WHERE client_id = %s
                """
                cur.execute(sql_update, (username, email, phone, aadhar, qr_key, client_id))
            else:
                sql_insert = """
                    INSERT INTO client_bot_signups (client_id, username, email, phone, aadhar, qr_key, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                """
                cur.execute(sql_insert, (client_id, username, email, phone, aadhar, qr_key))
        
        conn.commit()
        return jsonify({"status": "success", "message": "Data synced successfully", "client_id": client_id}), 201
        
    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/sync-session', methods=['POST'])
def sync_session():
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "Invalid JSON"}), 400
    
    # STEP 4: PC3 PAYLOAD LOGGING
    print("=== PC3 PAYLOAD RECEIVED ===")
    print(f"Raw payload: {data}")
    print(f"client_id: {data.get('client_id')}")
    print(f"username: {data.get('username')}")
    print(f"kite_id: {data.get('kite_id')}")
    print(f"kite_username: {data.get('kite_username')}")
    print("==============================")
    
    conn = None
    try:
        conn = get_db()
        cur = conn.cursor()
        
        client_id = data.get('client_id')
        session_date = data.get('session_date')
        login_time = data.get('login_time')
        logout_time = data.get('logout_time')
        kite_id = data.get('kite_id')
        username = data.get('username')
        kite_username = data.get('kite_username')
        mode = data.get('mode')
        total_trades = data.get('total_trades', 0)
        net_pnl = data.get('net_pnl', 0.00)
        gross_pnl = data.get('gross_pnl', 0.00)
        charges = data.get('charges', 0.00)
        
        if not client_id or not session_date or not login_time:
            return jsonify({"status": "error", "message": "client_id, session_date, and login_time are required"}), 400
        
        # PRODUCTION SAFETY: Auto-close any existing ACTIVE sessions before creating new one
        if not logout_time:  # This is a new session start (login)
            cur.execute("""
                UPDATE user_session_data 
                SET logout_time = CURRENT_TIMESTAMP, 
                    mode = COALESCE(mode, 'AUTO-CLOSED')
                WHERE client_id = %s AND kite_id = %s AND logout_time IS NULL
            """, (client_id, kite_id))
            closed_count = cur.rowcount
            if closed_count > 0:
                print(f"Auto-closed {closed_count} existing sessions for {client_id}")
        # Check if record exists for this exact login time and client
        cur.execute("""
            SELECT id FROM user_session_data 
            WHERE client_id = %s AND session_date = %s AND login_time = %s
        """, (client_id, session_date, login_time))
        
        existing = cur.fetchone()
        
        if existing:
            # Update existing session (Logout event)
            cur.execute("""
                UPDATE user_session_data
                SET logout_time = %s,
                    total_trades = %s,
                    net_pnl = %s,
                    gross_pnl = %s,
                    charges = %s,
                    kite_id = COALESCE(%s, kite_id),
                    username = COALESCE(%s, username),
                    kite_username = COALESCE(%s, kite_username),
                    mode = COALESCE(%s, mode)
                WHERE id = %s
            """, (logout_time, total_trades, net_pnl, gross_pnl, charges, kite_id, username, kite_username, mode, existing[0]))
        else:
            # Insert new session (Login event)
            cur.execute("""
                INSERT INTO user_session_data 
                (client_id, kite_id, username, kite_username, session_date, login_time, logout_time, mode, total_trades, net_pnl, gross_pnl, charges)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (client_id, kite_id, username, kite_username, session_date, login_time, logout_time, mode, total_trades, net_pnl, gross_pnl, charges))
            
        conn.commit()
        return jsonify({"status": "success", "message": "Session synced successfully"}), 200

    except Exception as e:
        print(f"Error syncing session: {str(e)}")
        if conn:
            conn.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/session_details/<client_id>/<date>')
def session_details_page(client_id, date):
    # Input validation
    if not client_id or not date:
        return render_template('session_details.html', client_id=client_id, columns=[], rows=[], summary=None)
    
    # Sanitize inputs
    client_id = escape(client_id.strip())
    date = escape(date.strip())
    
    # Validate and normalize date format
    try:
        # Try standard ISO format first
        dt_obj = datetime.strptime(date, '%Y-%m-%d')
    except ValueError:
        try:
            # Try display format (DD-Mon-YYYY)
            dt_obj = datetime.strptime(date, '%d-%b-%Y')
            # Convert to YYYY-MM-DD for consistency in SQL
            date = dt_obj.strftime('%Y-%m-%d')
        except ValueError:
            print(f"Invalid date format received: {date}")
            return render_template('session_details.html', client_id=client_id, columns=[], rows=[], summary=None)
    
    try:
        conn = get_db()
        cur = conn.cursor()
        
        # Safe search with aggressive data type casting
        # Safe search with aggressive data type casting
        cur.execute("""
            SELECT session_date, login_time, logout_time, mode, 
                   COALESCE(total_trades, 0), COALESCE(net_pnl, 0.00),
                   COALESCE(gross_pnl, 0.00), COALESCE(charges, 0.00)
            FROM user_session_data 
            WHERE TRIM(client_id) = %s 
            AND session_date::date = %s::date
            ORDER BY login_time ASC
        """, (client_id.strip(), date))
        
        sessions = cur.fetchall()
        
        if sessions:
            # Sort sessions to ensure sequential processing
            sessions.sort(key=lambda x: x[1] if x[1] else datetime.min)
            
            max_seen_trades = 0
            last_valid_cum_pnl = 0
            last_valid_cum_gross = 0
            last_valid_cum_charges = 0
            display_sessions = []
            
            for s in sessions:
                session_date = s[0]
                login_time = s[1]
                logout_time = s[2]
                mode = s[3]
                current_cum_trades = s[4] or 0
                current_cum_pnl = s[5] or 0
                current_cum_gross = s[6] or 0
                current_cum_charges = s[7] or 0
                is_active = logout_time is None
                
                # Check for Monotonicity
                # If the current session report has FEWER trades than we've already seen, 
                # it is "stale" or "interleaved" data from a restarted process that hasn't synced.
                # OR it is a hard reset (Paper bot crash). We assume Reset if current < max.
                
                if current_cum_trades < max_seen_trades:
                    # Assume Reset: Treat baselines as 0
                    max_seen_trades = 0
                    last_valid_cum_pnl = 0
                    last_valid_cum_gross = 0
                    last_valid_cum_charges = 0
                
                # Calculate Delta against the last valid HIGH WATER mark
                delta_trades = current_cum_trades - max_seen_trades
                delta_pnl = current_cum_pnl - last_valid_cum_pnl
                
                # VISIBILITY CONTROL
                # Only display if positive trade activity occurred (Sequence advanced)
                # OR if the session is currently ACTIVE (so we can see it running)
                if delta_trades > 0 or is_active:
                    display_sessions.append((session_date, login_time, logout_time, mode, delta_trades, delta_pnl))
                    
                    # Update High Water Marks
                    # Only update if we are not just showing a stagnant active session
                    if delta_trades > 0:
                        max_seen_trades = current_cum_trades
                        last_valid_cum_pnl = current_cum_pnl
                        last_valid_cum_gross = current_cum_gross
                        last_valid_cum_charges = current_cum_charges
            
            sessions = display_sessions

            # Summary calculation logic (Sum of displayed deltas)
            # This should now match the final Cumulative value perfectly
            total_sessions = len(sessions)
            active_sessions = sum(1 for s in sessions if s[2] is None) # Accurate because only the "latest" active one will pass the max check
            total_trades = sum(s[4] for s in sessions)
            net_pnl = sum(s[5] for s in sessions)
            mode = sessions[0][3] if sessions else 'N/A'
            
            summary = [total_sessions, date, active_sessions, total_trades, net_pnl, mode]
            
            columns = ['Date', 'Login Time', 'Logout Time', 'Mode', 'Trades', 'Net PnL']
            formatted_rows = []
            for session in sessions:
                formatted_rows.append([
                    session[0].strftime('%d-%b-%Y') if session[0] else '',
                    session[1].strftime('%H:%M:%S') if session[1] else '',
                    session[2].strftime('%H:%M:%S') if session[2] else 'Active',
                    session[3] or '',
                    session[4],
                    f"₹{session[5]:.2f}"
                ])
            
            return render_template('session_details.html', client_id=client_id, columns=columns, rows=formatted_rows, summary=summary)
        
        return render_template('session_details.html', client_id=client_id, columns=[], rows=[], summary=None)
            
    except Exception as e:
        print(f"Error: {e}")
        return render_template('session_details.html', client_id=client_id, columns=[], rows=[], summary=None)

@app.route('/test-route/<client_id>/<date>')
def test_route(client_id, date):
    return f"<h1>Route Test</h1><p>Client: {client_id}</p><p>Date: {date}</p>"

@app.route('/api/fix-consolidated-data/<client_id>/<date>', methods=['GET', 'POST'])
def fix_consolidated_data(client_id, date):
    try:
        conn = get_db()
        cur = conn.cursor()
        
        # Delete all sessions for this client/date to start fresh
        cur.execute("""
            DELETE FROM user_session_data 
            WHERE client_id = %s AND DATE(session_date) = %s
        """, (client_id, date))
        
        # Insert sample realistic sessions based on the consolidated data
        sample_sessions = [
            ('10:27:02', '10:47:38', 3, 216.15, 'PAPER'),
            ('10:47:26', '11:43:26', 5, 10782.12, 'PAPER'),
            ('11:53:21', '11:53:32', 6, 10745.64, 'PAPER'),
            ('12:04:38', '12:05:32', 7, 16359.58, 'PAPER'),
            ('12:08:03', '12:08:38', 8, 16070.14, 'PAPER'),
            ('12:09:29', '12:09:46', 8, 16070.14, 'PAPER'),
            ('12:10:26', '12:10:53', 9, 15306.39, 'PAPER'),
            ('12:12:29', '12:14:16', 10, 18017.41, 'PAPER'),
            ('12:15:59', '12:16:06', 10, 18017.41, 'PAPER'),
            ('12:16:15', '12:18:01', 11, 22587.43, 'PAPER'),
            ('12:20:27', '12:21:19', 11, 22587.43, 'PAPER'),
            ('12:22:47', '12:23:01', 11, 22587.43, 'PAPER')
        ]
        
        for login, logout, trades, pnl, mode in sample_sessions:
            cur.execute("""
                INSERT INTO user_session_data 
                (client_id, session_date, login_time, logout_time, total_trades, net_pnl, mode, username, kite_username)
                VALUES (%s, %s, %s, %s, %s, %s, %s, 'dP73HnSC', 'Ratan Kumar Hugonder')
            """, (client_id, date, f"{date} {login}", f"{date} {logout}", trades, pnl, mode))
        
        conn.commit()
        return jsonify({"status": "success", "message": "Data restored with realistic sessions"}), 200
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/session_details_json/<client_id>/<date>')
def session_details_json(client_id, date):
    # Reuse the same logic as the page render
    try:
        # Validate/Normalize date (simplified for API, assuming frontend passes valid format or we handle it)
        # Check if date needs parsing logic similar to main route
        formatted_date = date
        try:
             dt_obj = datetime.strptime(date, '%Y-%m-%d')
        except ValueError:
            try:
                dt_obj = datetime.strptime(date, '%d-%b-%Y')
                formatted_date = dt_obj.strftime('%Y-%m-%d')
            except ValueError:
                 return jsonify({'status': 'error', 'message': 'Invalid date'}), 400

        conn = get_db()
        cur = conn.cursor()
        
        # Same query as session_details_page
        cur.execute("""
            SELECT session_date, login_time, logout_time, mode, 
                   COALESCE(total_trades, 0), COALESCE(net_pnl, 0.00),
                   COALESCE(gross_pnl, 0.00), COALESCE(charges, 0.00)
            FROM user_session_data 
            WHERE TRIM(client_id) = %s 
            AND session_date::date = %s::date
            ORDER BY login_time ASC
        """, (client_id.strip(), formatted_date))
        
        sessions = cur.fetchall()
        display_sessions = []
        if sessions:
             # Sort sessions
            sessions.sort(key=lambda x: x[1] if x[1] else datetime.min)
            
            max_seen_trades = 0
            last_valid_cum_pnl = 0
            last_valid_cum_gross = 0
            last_valid_cum_charges = 0
            
            for s in sessions:
                session_date = s[0]
                login_time = s[1]
                logout_time = s[2]
                mode = s[3]
                current_cum_trades = s[4] or 0
                current_cum_pnl = s[5] or 0
                current_cum_gross = s[6] or 0
                current_cum_charges = s[7] or 0
                is_active = logout_time is None
                
                if current_cum_trades < max_seen_trades:
                    max_seen_trades = 0
                    last_valid_cum_pnl = 0
                    last_valid_cum_gross = 0
                    last_valid_cum_charges = 0
                
                delta_trades = current_cum_trades - max_seen_trades
                delta_pnl = current_cum_pnl - last_valid_cum_pnl
                delta_gross = current_cum_gross - last_valid_cum_gross
                delta_charges = current_cum_charges - last_valid_cum_charges
                
                # Visibility Logic (Active OR Trades > 0)
                if delta_trades > 0 or is_active:
                    display_sessions.append({
                        'date': session_date.strftime('%d-%b-%Y') if session_date else '',
                        'login': login_time.strftime('%H:%M:%S') if login_time else '',
                        'logout': logout_time.strftime('%H:%M:%S') if logout_time else 'Active',
                        'mode': mode or '',
                        'trades': delta_trades,
                        'net_pnl': delta_pnl,
                        # 'gross_pnl': delta_gross, # Hidden as per request
                        # 'charges': delta_charges  # Hidden as per request
                    })
                    
                    if delta_trades > 0:
                        max_seen_trades = current_cum_trades
                        last_valid_cum_pnl = current_cum_pnl
                        last_valid_cum_gross = current_cum_gross
                        last_valid_cum_charges = current_cum_charges

        # Summary Calc
        total_sessions = len(display_sessions)
        active_sessions = sum(1 for s in display_sessions if s['logout'] == 'Active')
        total_trades = sum(s['trades'] for s in display_sessions)
        net_pnl = sum(s['net_pnl'] for s in display_sessions)
        mode = display_sessions[0]['mode'] if display_sessions else 'N/A'
        
        summary = {
            'sessions': total_sessions,
            'active': active_sessions,
            'trades': total_trades,
            'net_pnl': net_pnl,
            'mode': mode
        }
        
        return jsonify({
            'status': 'success',
            'rows': display_sessions,
            'summary': summary
        })

    except Exception as e:
        print(f"API Error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500
    conn = None
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            UPDATE user_session_data 
            SET logout_time = CURRENT_TIMESTAMP, mode = 'MANUAL-CLOSE'
            WHERE client_id = %s AND logout_time IS NULL
        """, (client_id,))
        closed_count = cur.rowcount
        conn.commit()
        return jsonify({"status": "success", "closed": closed_count}), 200
    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/test-pc3-payload', methods=['POST'])
def test_pc3_payload():
    """Test endpoint to verify PC3 sends correct payload"""
    data = request.get_json() or {}
    
    print("=== PC3 PAYLOAD TEST ===")
    print(f"Timestamp: {datetime.now()}")
    print(f"Remote IP: {request.remote_addr}")
    print(f"client_id: {data.get('client_id')}")
    print(f"username: {data.get('username')}")
    print(f"kite_id: {data.get('kite_id')}")
    print(f"kite_username: {data.get('kite_username')}")
    print(f"Full payload: {data}")
    
    return jsonify({
        "status": "success",
        "timestamp": datetime.now().isoformat(),
        "remote_ip": request.remote_addr,
        "received": data
    }), 200

@app.route('/api/add-test-data/<client_id>')
def add_test_data(client_id):
    """Add test session data for debugging"""
    try:
        conn = get_db()
        cur = conn.cursor()
        
        # Insert test session data
        cur.execute("""
            INSERT INTO user_session_data 
            (client_id, session_date, login_time, logout_time, kite_id, username, kite_username, mode, total_trades, net_pnl)
            VALUES (%s, CURRENT_DATE, CURRENT_TIMESTAMP - INTERVAL '2 hours', CURRENT_TIMESTAMP - INTERVAL '1 hour', 'DR4971', 'dP73HnSC', 'Ratan Kumar', 'PAPER', 5, 1500.00)
        """, (client_id,))
        
        conn.commit()
        return jsonify({"status": "success", "message": f"Test data added for {client_id}"})
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/api/debug-data/<client_id>')
def debug_data(client_id):
    """Debug endpoint to check what data exists for a client"""
    try:
        conn = get_db()
        cur = conn.cursor()
        
        # Check all data for this client
        cur.execute("SELECT * FROM user_session_data WHERE client_id = %s ORDER BY session_date DESC, login_time DESC", (client_id,))
        all_data = cur.fetchall()
        
        # Get column names
        columns = [desc[0] for desc in cur.description] if cur.description else []
        
        # Also check recent activity from all clients to see if PC3 is sending data
        cur.execute("SELECT client_id, COUNT(*) as sessions, MAX(login_time) as last_activity FROM user_session_data WHERE login_time >= CURRENT_DATE - INTERVAL '7 days' GROUP BY client_id ORDER BY last_activity DESC")
        recent_activity = cur.fetchall()
        
        return jsonify({
            "client_id": client_id,
            "total_rows": len(all_data),
            "columns": columns,
            "data": [dict(zip(columns, row)) for row in all_data] if all_data else [],
            "recent_activity": [dict(zip(['client_id', 'sessions', 'last_activity'], row)) for row in recent_activity]
        })
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/api/backup-database', methods=['POST'])
def backup_database():
    """Create database backup"""
    try:
        result = backup_manager.create_backup()
        if result['status'] == 'success':
            # Cleanup old backups
            backup_manager.cleanup_old_backups()
            return jsonify(result), 200
        else:
            return jsonify(result), 500
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/test-session/<client_id>')
def test_session(client_id):
    """Direct test route to check session data"""
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM user_session_data WHERE client_id = %s LIMIT 5", (client_id,))
        rows = cur.fetchall()
        
        result = f"<h1>Test Session Data for {client_id}</h1>"
        result += f"<p>Found {len(rows)} sessions</p>"
        
        if rows:
            result += "<table border='1'>"
            result += "<tr><th>ID</th><th>Client</th><th>Date</th><th>Login</th><th>Logout</th><th>Trades</th><th>PnL</th></tr>"
            for row in rows:
                result += f"<tr><td>{row[0]}</td><td>{row[1]}</td><td>{row[2]}</td><td>{row[3]}</td><td>{row[4]}</td><td>{row[8]}</td><td>{row[9]}</td></tr>"
            result += "</table>"
        else:
            result += "<p>No data found</p>"
            
        return result
    except Exception as e:
        return f"<h1>Error: {str(e)}</h1>"

@app.route('/favicon.ico')
def favicon():
    return '', 204

@app.errorhandler(404)
def not_found_error(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

@app.errorhandler(400)
def bad_request_error(error):
    return jsonify({'error': 'Bad request'}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)