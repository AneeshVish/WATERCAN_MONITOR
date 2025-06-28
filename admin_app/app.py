from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import json
import os
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.secret_key = 'supersecretkey'
DATA_FILE = '../watercans.json'
BLOCKCHAIN_FILE = '../blockchain_log.json'

ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD_HASH = generate_password_hash('admin123')

def read_data():
    with open(DATA_FILE, 'r') as f:
        return json.load(f)

def write_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f)

import hashlib
def get_last_block():
    if not os.path.exists(BLOCKCHAIN_FILE):
        return None
    with open(BLOCKCHAIN_FILE, 'r') as f:
        try:
            chain = json.load(f)
        except Exception:
            chain = []
    return chain[-1] if chain else None

def calc_block_hash(block):
    block_str = json.dumps(block, sort_keys=True, separators=(',', ':')).encode()
    return hashlib.sha256(block_str).hexdigest()

def log_update(can_id, old_count, new_count, admin):
    import datetime
    prev_block = get_last_block()
    prev_hash = prev_block['hash'] if prev_block else '0'*64
    block = {
        'timestamp': datetime.datetime.now().isoformat(),
        'can_id': can_id,
        'old_count': old_count,
        'new_count': new_count,
        'admin': admin,
        'prev_hash': prev_hash
    }
    block['hash'] = calc_block_hash({k: v for k, v in block.items() if k != 'hash'})
    if not os.path.exists(BLOCKCHAIN_FILE):
        chain = []
    else:
        with open(BLOCKCHAIN_FILE, 'r') as f:
            try:
                chain = json.load(f)
            except Exception:
                chain = []
    chain.append(block)
    with open(BLOCKCHAIN_FILE, 'w') as f:
        json.dump(chain, f, indent=2)

@app.route('/admin', methods=['GET'])
def admin_page():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    return render_template('admin.html')

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == ADMIN_USERNAME and check_password_hash(ADMIN_PASSWORD_HASH, password):
            session['admin_logged_in'] = True
            return redirect(url_for('admin_page'))
        else:
            error = 'Invalid username or password.'
    return render_template('admin_login.html', error=error)

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin_login'))

@app.route('/api/update_usage', methods=['POST'])
def update_usage():
    if not session.get('admin_logged_in'):
        return jsonify({'success': False, 'msg': 'Unauthorized'}), 401
    can_id = request.json.get('can_id')
    count = request.json.get('count')
    if not can_id or count is None:
        return jsonify({'success': False, 'msg': 'Invalid input'}), 400
    data = read_data()
    old_count = data.get(can_id, 0)
    new_count = int(count)
    if new_count < old_count:
        return jsonify({'success': False, 'msg': 'Cannot decrease usage count!'}), 400
    if new_count == old_count:
        return jsonify({'success': False, 'msg': 'No change in usage count.'}), 400
    data[can_id] = new_count
    write_data(data)
    log_update(can_id, old_count, new_count, ADMIN_USERNAME)
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(port=7000, debug=True)
