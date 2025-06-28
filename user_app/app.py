from flask import Flask, render_template, request, jsonify
import json
import os

app = Flask(__name__)
DATA_FILE = '../watercans.json'
BLOCKCHAIN_FILE = '../blockchain_log.json'

# Read can usage data
def read_data():
    with open(DATA_FILE, 'r') as f:
        return json.load(f)

# Blockchain verification
def calc_block_hash(block):
    import hashlib
    block_str = json.dumps(block, sort_keys=True, separators=(',', ':')).encode()
    return hashlib.sha256(block_str).hexdigest()

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

@app.route('/api/get_usage', methods=['POST'])
def get_usage():
    can_id = request.json.get('can_id')
    data = read_data()
    count = data.get(can_id)
    if count is None:
        return jsonify({'status': 'not_found'}), 404
    status = 'Good' if count <= 40 else 'Bad'
    return jsonify({'status': status, 'count': count})

@app.route('/api/get_logs', methods=['GET'])
def get_logs():
    if not os.path.exists(BLOCKCHAIN_FILE):
        return jsonify([])
    with open(BLOCKCHAIN_FILE, 'r') as f:
        try:
            logs = json.load(f)
        except Exception:
            logs = []
    for log in logs:
        log.pop('hash', None)
        log.pop('prev_hash', None)
    return jsonify(logs)

@app.route('/api/verify_blockchain', methods=['GET'])
def verify_chain():
    ok, idx = verify_blockchain()
    return jsonify({'verified': ok, 'checked_blocks': idx})

if __name__ == '__main__':
    app.run(port=5000, debug=True)
