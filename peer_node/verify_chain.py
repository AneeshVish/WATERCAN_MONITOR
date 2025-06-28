import json
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.exceptions import InvalidSignature

def compute_block_hash(block):
    block_copy = block.copy()
    block_copy.pop('signatures', None)
    block_copy.pop('pubkeys', None)
    import hashlib
    block_str = json.dumps(block_copy, sort_keys=True, separators=(',', ':')).encode()
    return hashlib.sha256(block_str).hexdigest()

def verify_chain(chain_file, pubkey_files, required_signatures=2):
    with open(chain_file, 'r') as f:
        chain = json.load(f)
    pubkeys = [open(pf, 'rb').read() for pf in pubkey_files]
    for idx, block in enumerate(chain):
        block_hash = compute_block_hash(block)
        if block['hash'] != block_hash:
            print(f"Block {idx} hash mismatch!")
            return False
        valid_sigs = 0
        for sig, pubkey_pem in zip(block['signatures'], block['pubkeys']):
            if pubkey_pem.encode() not in pubkeys:
                continue
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
        if valid_sigs < required_signatures:
            print(f"Block {idx} does not have enough valid signatures!")
            return False
    print("Chain verified: All blocks valid and signatures correct.")
    return True

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python verify_chain.py <chain.json> <pubkey1.pem> <pubkey2.pem> [<pubkey3.pem> ...]")
        exit(1)
    chain_file = sys.argv[1]
    pubkey_files = sys.argv[2:]
    verify_chain(chain_file, pubkey_files)
