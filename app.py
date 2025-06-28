from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import json
import os
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.secret_key = 'supersecretkey' 
DATA_FILE = 'watercans.json'

ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD_HASH = generate_password_hash('admin123') 


def init_data_file():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'w') as f:
            json.dump({}, f)

def read_data():
    with open(DATA_FILE, 'r') as f:
        return json.load(f)

def write_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f)

import hashlib
BLOCKCHAIN_FILE = 'blockchain_log.json'

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

def verify_blockchain():
    if not os.path.exists(BLOCKCHAIN_FILE):
        return True, 0
    with open(BLOCKCHAIN_FILE, 'r') as f:
        try:
            chain = json.load(f)
        except Exception:
            return False, 0
    prev_hash = '0'*64
    for idx, block in enumerate(chain):
        block_no_hash = {k: v for k, v in block.items() if k != 'hash'}
        expected_hash = calc_block_hash(block_no_hash)
        if block['prev_hash'] != prev_hash or block['hash'] != expected_hash:
            return False, idx
        prev_hash = block['hash']
    return True, len(chain)

@app.route('/')
def user_page():
    return render_template('user.html')

@app.route('/user/log')
def user_log():
    return render_template('user_log.html')

@app.route('/admin')
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

@app.route('/api/get_usage', methods=['POST'])
def get_usage():
    can_id = request.json.get('can_id')
    data = read_data()
    count = data.get(can_id)
    if count is None:
        return jsonify({'status': 'not_found'}), 404
    status = 'Good' if count <= 40 else 'Bad'
    return jsonify({'status': status, 'count': count})

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

@app.route('/api/get_logs', methods=['GET'])
def get_logs():
    if not os.path.exists(BLOCKCHAIN_FILE):
        return jsonify([])
    with open(BLOCKCHAIN_FILE, 'r') as f:
        try:
            logs = json.load(f)
        except Exception:
            logs = []
    # Remove hash fields for user display
    for log in logs:
        log.pop('hash', None)
        log.pop('prev_hash', None)
    return jsonify(logs)

@app.route('/api/verify_blockchain', methods=['GET'])
def verify_chain():
    ok, idx = verify_blockchain()
    return jsonify({'verified': ok, 'checked_blocks': idx})

if __name__ == '__main__':
    init_data_file()
    app.run(debug=True)
