import os
import json
from flask import Flask, request, jsonify
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.exceptions import InvalidSignature
from datetime import datetime

app = Flask(__name__)
CHAIN_FILE = 'chain.json'
PUBKEYS_DIR = 'pubkeys'  # Directory to store all admin public keys
REQUIRED_SIGNATURES = 2  # Number of signatures required per block

# --- Key Management ---
PRIVATE_KEY_FILE = 'private_key.pem'
PUBLIC_KEY_FILE = 'public_key.pem'

# Helper to load private key

def load_private_key():
    with open(PRIVATE_KEY_FILE, 'rb') as f:
        return serialization.load_pem_private_key(f.read(), password=None)

def load_public_key(path):
    with open(path, 'rb') as f:
        return serialization.load_pem_public_key(f.read())

def get_pubkey_bytes():
    with open(PUBLIC_KEY_FILE, 'rb') as f:
        return f.read()

# --- Blockchain Logic ---

def get_chain():
    if not os.path.exists(CHAIN_FILE):
        return []
    with open(CHAIN_FILE, 'r') as f:
        return json.load(f)

def write_chain(chain):
    with open(CHAIN_FILE, 'w') as f:
        json.dump(chain, f, indent=2)

def get_last_block():
    chain = get_chain()
    return chain[-1] if chain else None

def block_hash(block):
    block_copy = block.copy()
    block_copy.pop('signatures', None)
    block_copy.pop('pubkeys', None)
    return hashes.Hash(hashes.SHA256())

def compute_block_hash(block):
    block_copy = block.copy()
    block_copy.pop('signatures', None)
    block_copy.pop('pubkeys', None)
    block_str = json.dumps(block_copy, sort_keys=True, separators=(',', ':')).encode()
    from hashlib import sha256
    return sha256(block_str).hexdigest()

# --- API Endpoints ---

@app.route('/api/get_pubkey', methods=['GET'])
def get_pubkey():
    return get_pubkey_bytes(), 200, {'Content-Type': 'application/x-pem-file'}

@app.route('/api/get_chain', methods=['GET'])
def api_get_chain():
    return jsonify(get_chain())

@app.route('/api/add_block', methods=['POST'])
def add_block():
    data = request.json
    chain = get_chain()
    # Verify block structure
    required_fields = ['timestamp', 'can_id', 'old_count', 'new_count', 'admin', 'prev_hash', 'hash', 'signatures', 'pubkeys']
    for field in required_fields:
        if field not in data:
            return jsonify({'success': False, 'error': f'Missing field: {field}'}), 400
    # Verify hash
    expected_hash = compute_block_hash(data)
    if data['hash'] != expected_hash:
        return jsonify({'success': False, 'error': 'Invalid block hash'}), 400
    # Verify previous hash
    last_block = get_last_block()
    if last_block and data['prev_hash'] != last_block['hash']:
        return jsonify({'success': False, 'error': 'prev_hash does not match'}), 400
    # Verify signatures
    valid_sigs = 0
    for sig, pubkey_pem in zip(data['signatures'], data['pubkeys']):
        pubkey = serialization.load_pem_public_key(pubkey_pem.encode())
        try:
            pubkey.verify(
                bytes.fromhex(sig),
                data['hash'].encode(),
                padding.PKCS1v15(),
                hashes.SHA256()
            )
            valid_sigs += 1
        except InvalidSignature:
            continue
    if valid_sigs < REQUIRED_SIGNATURES:
        return jsonify({'success': False, 'error': 'Not enough valid signatures'}), 400
    # Append block
    chain.append(data)
    write_chain(chain)
    return jsonify({'success': True})

@app.route('/api/verify_chain', methods=['GET'])
def verify_chain():
    chain = get_chain()
    if not chain:
        return jsonify({'verified': True, 'length': 0})
    prev_hash = '0'*64
    for idx, block in enumerate(chain):
        block_h = compute_block_hash(block)
        if block['hash'] != block_h or block['prev_hash'] != prev_hash:
            return jsonify({'verified': False, 'at': idx}), 200
        # Verify signatures
        valid_sigs = 0
        for sig, pubkey_pem in zip(block['signatures'], block['pubkeys']):
            pubkey = serialization.load_pem_public_key(pubkey_pem.encode())
            try:
                pubkey.verify(
                    bytes.fromhex(sig),
                    block['hash'].encode(),
                    padding.PKCS1v15(),
                    hashes.SHA256()
                )
                valid_sigs += 1
            except InvalidSignature:
                continue
        if valid_sigs < REQUIRED_SIGNATURES:
            return jsonify({'verified': False, 'at': idx, 'error': 'Not enough valid signatures'}), 200
        prev_hash = block['hash']
    return jsonify({'verified': True, 'length': len(chain)})

# --- Utility: Create and Broadcast Block ---
def create_block(can_id, old_count, new_count, admin, private_key, pubkey_pem, peer_pubkeys):
    chain = get_chain()
    prev_hash = chain[-1]['hash'] if chain else '0'*64
    block = {
        'timestamp': datetime.now().isoformat(),
        'can_id': can_id,
        'old_count': old_count,
        'new_count': new_count,
        'admin': admin,
        'prev_hash': prev_hash
    }
    block['hash'] = compute_block_hash(block)
    # Sign with all available keys (demo: sign with self and simulate others)
    signatures = []
    pubkeys = []
    for pk, pubk in [(private_key, pubkey_pem)] + peer_pubkeys:
        sig = pk.sign(
            block['hash'].encode(),
            padding.PKCS1v15(),
            hashes.SHA256()
        )
        signatures.append(sig.hex())
        pubkeys.append(pubk.decode() if isinstance(pubk, bytes) else pubk)
    block['signatures'] = signatures
    block['pubkeys'] = pubkeys
    return block

if __name__ == '__main__':
    if not os.path.exists(PUBKEYS_DIR):
        os.makedirs(PUBKEYS_DIR)
    app.run(port=8000, debug=True)
