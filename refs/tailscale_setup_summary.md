# 📝 Summary: Tailscale Setup on Mac Mini (`tesla`)

## Overview
We configured **Tailscale** on your Mac Mini (`tesla`) so you can securely access it (SSH + web apps) from your laptop and iPhone, without exposing it to the public internet.

---

## Steps Completed

### 1. Installed Tailscale
- On Mac Mini (`tesla`):
  ```bash
  brew install tailscale
  sudo brew services start tailscale
  ```
  This runs the Tailscale daemon (`tailscaled`) at boot.

---

### 2. Joined Tailnet with SSH Enabled
- One-time authentication:
  ```bash
  sudo tailscale up --ssh
  ```
- Result: `tesla` is visible in your tailnet and reachable by Tailscale IP (`100.115.62.30`).

---

### 3. Verified Devices
- Using:
  ```bash
  tailscale status
  ```
- Devices in tailnet:
  - `kepler` (your dev Mac)
  - `iphone-15-pro`
  - `tesla` (Mac Mini)

---

### 4. MagicDNS Setup
- Tailnet domain: `tail19187e.ts.net` (can be renamed to something cleaner).  
- Hostname for Mac Mini:
  ```
  100.115.62.30
  ```

---

### 5. DNS Resolution Issue
- `dig @100.100.100.100 100.115.62.30` worked (MagicDNS functional).  
- But `ping 100.115.62.30` failed → macOS/iPhone weren’t using Tailscale DNS.  
- Cause: **Override local DNS** is a Premium feature (greyed out on Free plan).

---

### 6. Workaround: Manual DNS Override
#### macOS
1. System Settings → **Network → DNS**.  
2. Add `100.100.100.100` as first nameserver.  
3. Flush cache:
   ```bash
   sudo dscacheutil -flushcache
   sudo killall -HUP mDNSResponder
   ```

#### iPhone
1. Settings → **Wi-Fi → (your network) → Configure DNS → Manual**.  
2. Add `100.100.100.100`.  
3. Toggle Airplane mode to refresh.

Result: `100.115.62.30` resolves correctly.

---

### 7. Access Methods
- **SSH**:
  ```bash
  ssh egs@100.115.62.30
  ```
- **Web app** (example Streamlit):
  ```
  http://100.115.62.30:8501
  ```
- **Fallback (by IP)**:
  ```
  ssh egs@100.115.62.30
  http://100.115.62.30:8501
  ```

---

### 8. Security Hardening
- SSH password logins disabled (`/etc/ssh/sshd_config`):
  ```
  PermitRootLogin no
  PasswordAuthentication no
  ChallengeResponseAuthentication no
  UsePAM yes
  PubkeyAuthentication yes
  AllowUsers egs
  ```
- Restarted SSH service to apply changes.

- Tailscale ACLs recommended to restrict access to only your account:
  ```json
  {
    "acls": [
      {
        "action": "accept",
        "src": ["you@domain.com"],
        "dst": ["tesla:22", "tesla:8501"]
      }
    ]
  }
  ```

---

## ✅ Final State
- `tesla` auto-joins Tailscale at boot (`brew services`).  
- Reachable securely via `100.115.62.30` (or IP).  
- Accessible from iPhone and Kepler with manual DNS override.  
- SSH hardened (keys only, no passwords).  
- Web apps reachable inside tailnet without public exposure.

---

## Next Steps (Optional)
- Rename tailnet to something memorable (e.g. `suchanek.ts.net`).  
- Add ACLs to strictly control access.  
- Consider Premium plan if you want automatic DNS override.  

---
