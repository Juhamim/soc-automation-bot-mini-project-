# 2️⃣ **Phishing Response Playbook**

---

### 📌 Overview

This playbook automates the response to phishing attacks by verifying suspicious emails, blocking malicious URLs, and notifying users.

- **Objective:**  
  Automatically detect and mitigate phishing attacks by analyzing email content and URLs.

- **Severity Levels:**  
  Medium → High

---

### 🚨 Trigger

- **Source:** Email Security System / SIEM  
- **Event:** Email flagged as phishing or contains suspicious URL.

#### Trigger Conditions:
- Email contains a suspicious URL
- Subject line contains “urgent” or “update”
- Sender is from a new or suspicious domain

---

### 🔍 Step 1: Data Collection

The bot extracts the following details from the email:

- Sender email address
- Email subject and body
- Suspicious URL
- Timestamp

... (Refer to the full docs for the rest of the steps)
