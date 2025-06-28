# Water Can Usage Tracker with Blockchain Logging

## Overview
This project is a secure, transparent water can usage tracking system. It consists of two separate web applications:

- **User App**: Allows users to check the usage of water cans and view a tamper-proof blockchain log of all updates.
- **Admin App**: Allows authenticated admins to update water can usage counts, with all changes immutably logged in a blockchain-style audit trail.

All usage updates are stored in a blockchain-style log (`blockchain_log.json`) to ensure data integrity and tamper resistance.

---

## Features

### User App
- Check the current usage count of any water can by ID
- View a detailed, tamper-proof log of all usage updates
- Filter logs by Water Can ID
- Blockchain verification badge (shows if log is untampered)
- **Verify authenticity:** Anyone can check the log's cryptographic signatures for proof of integrity and authenticity

### Admin App
- Secure login (username/password, password hashed)
- Update usage counts for any water can (can only increase, never decrease)
- All updates are permanently logged with timestamp, admin, blockchain hash, and **digital signature**
- Logout functionality
- **Signs each update:** Every block is cryptographically signed with the admin's private key

---

## Folder Structure

```
Iot Project/
│
├── user_app/
│   ├── app.py
│   ├── requirements.txt
│   ├── templates/
│   │   ├── user.html
│   │   └── user_log.html
│   └── static/
│       ├── style.css
│       └── script.js
│
├── admin_app/
│   ├── app.py
│   ├── requirements.txt
│   ├── generate_keys.py         # Script to generate cryptographic keys
│   ├── private_key.pem         # Admin's private key (keep secret!)
│   ├── public_key.pem          # Admin's public key (share for verification)
│   ├── templates/
│   │   ├── admin.html
│   │   └── admin_login.html
│   └── static/
│       ├── style.css
│       └── script.js
│
├── watercans.json           # Shared data file for usage counts
├── blockchain_log.json      # Shared blockchain log for audit trail
└── README.md
```

---

## How It Works

### Blockchain Log & Digital Signatures
- Every admin update creates a new block in `blockchain_log.json`.
- Each block contains:
  - Timestamp
  - Water Can ID
  - Old and new usage counts
  - Admin username
  - Previous block's hash
  - Its own hash (SHA-256)
  - **Digital signature** (proves authenticity and prevents undetected tampering)
- The log is append-only and can be verified for tampering by recalculating hashes and checking signatures.
- **Anyone with the public key can verify the authenticity of every entry.**

### Security & Transparency
- Admin panel is protected by login (username: `admin`, password: `admin123` by default).
- Password is securely hashed using Werkzeug.
- Admins cannot decrease usage.
- All updates are logged and visible to users for transparency.
- **Cryptographic signatures:** Every update is signed with the admin's private key and can be verified by anyone with the public key.
- **Distributed verification:** Multiple nodes can compare logs and signatures to detect tampering and ensure consensus.

---

## Setup & Installation

### 1. Prerequisites
- Python 3.7+
- pip (Python package manager)
- **cryptography** package (for digital signatures)

### 2. Install Dependencies
You must install dependencies for both apps. From the project root:

```
pip install -r user_app/requirements.txt
pip install -r admin_app/requirements.txt
pip install cryptography
```

### 3. Generate Cryptographic Keys (First Time Only)
Go to the `admin_app` directory and run:
```
cd admin_app
python generate_keys.py
```
This will create `private_key.pem` (keep secret!) and `public_key.pem` (share for verification).

### 4. Running the Applications
Open **two terminals**:

#### Terminal 1: Start the User App
```
cd user_app
python app.py
```
- The user app runs at: [http://localhost:5000](http://localhost:5000)

#### Terminal 2: Start the Admin App
```
cd admin_app
python app.py
```
- The admin app runs at: [http://localhost:7000/admin/login](http://localhost:7000/admin/login)

### 5. Using the System

- **User Side:**
  - Go to [http://localhost:5000](http://localhost:5000)
  - Enter a water can ID to check usage.
  - Click "View Usage Log" to see all updates and verify blockchain integrity and signatures.

- **Admin Side:**
  - Go to [http://localhost:7000/admin/login](http://localhost:7000/admin/login)
  - Log in with the admin credentials (`admin` / `admin123` by default).
  - Update water can usage counts. All changes are logged immutably and cryptographically signed.
  - Click "Logout" to end your session.

---

## Customization
- You can change the admin password by updating the `ADMIN_PASSWORD_HASH` in `admin_app/app.py`.
- UI can be restyled via `static/style.css` in each app.
- Data files (`watercans.json`, `blockchain_log.json`) are shared and must be in the project root.
- You can regenerate cryptographic keys with `python generate_keys.py` in `admin_app` (note: this will invalidate previous signatures).
- To enable distributed verification, share your `public_key.pem` with others who wish to audit or verify your log.

---

## Troubleshooting
- **Port in use:** If 5000 or 7000 is busy, change the port in `app.py` for each app (`app.run(port=xxxx, debug=True)`).
- **404 Not Found:** Make sure you use the correct URLs: `/` for user, `/admin/login` for admin.
- **Permission errors:** Run your terminal as administrator if you have file write issues.
- **Dependency errors:** Double-check you installed requirements for both apps and `cryptography`.
- **Signature verification fails:** Make sure you are using the correct `public_key.pem` that matches the admin who created the log.

---

## Security & Production
- This project is for demonstration/educational use. For production, use HTTPS, a real WSGI server, and environment variables for secrets.
- Regularly backup your `blockchain_log.json` for audit and recovery.
- Keep your `private_key.pem` secure and never share it. Only share `public_key.pem` for verification.
- You can distribute your public key to auditors, users, or other nodes for independent log verification.

---

## Verifying Blockchain Authenticity & Transparency

### How to Verify the Log
1. **Obtain the `public_key.pem` from the admin.**
2. **Use the provided verification script (or API endpoint) to check:**
    - Each block's hash matches its contents
    - Each block's signature is valid for its data and hash
    - The chain is unbroken (all `prev_hash` values match the previous block's hash)
3. **If all checks pass, the log is authentic and untampered.**

> You can build or request a simple Python script to load `blockchain_log.json` and `public_key.pem` and verify all signatures and hashes.

---

## Authors
- Created by Aneesh H Vishwamitra

---

Enjoy secure, transparent, and cryptographically verifiable water can usage tracking!
