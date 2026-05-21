# 1️⃣ **Suspicious Login Detection & Response**

---

### 📌 Overview

This playbook automates the detection and response to suspicious login attempts, such as brute-force attacks or logins from malicious IP addresses.

- **Objective:**  
  Detect, analyze, and mitigate unauthorized access attempts.

- **Severity Levels:**  
  Medium → High

---

### 🚨 Trigger

- **Source:** SIEM (Wazuh / Splunk / ELK)  
- **Event:** Multiple failed login attempts or logins from blacklisted IP.

#### Trigger Conditions:
- Failed login attempts > 5 within 5 minutes
- Login from blacklisted IP
- Login from unusual country

---

### 🔍 Step 1: Data Collection

The bot extracts the following details:

- Username
- Source IP address
- Timestamp
- Geolocation
- Number of failed attempts

... (Refer to the PRD or full docs for the rest of the steps)
