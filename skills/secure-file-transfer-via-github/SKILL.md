---
name: secure-file-transfer-via-github
description: Transfer files using a private GitHub repository and GPG encryption when Telegram bot cannot send attachments. Use when sharing sensitive files between server and local machine or when the primary channel (Telegram) cannot handle attachments.
---

# Secure File Transfer via GitHub

## When to Use

- Telegram bot cannot send or receive file attachments (polling mode limitation)
- Need to transfer sensitive files (backups, configuration, datasets) between server and local machine
- File is too large for Telegram's attachment limit (~50 MB)
- Need an encrypted transfer channel

## Prerequisites

- GitHub account authenticated via `gh` CLI (token scopes: `repo`, `workflow`)
- Private repository with write access (e.g., `shakhor-shual/F.A.M.I.L.Y`)
- GPG installed on both machines
- Git configured on both machines

## Workflow

### Sending Files (Server → Local)

1. **Encrypt the file**:
   ```bash
   gpg -c --cipher-algo AES256 file.tar.gz
   # Enter passphrase when prompted
   ```

2. **Split if large** (optional, for files > 50 MB):
   ```bash
   split -b 50M file.tar.gz.gpg part_
   # Create assembly script (ami-assemble.sh):
   # cat part_* > file.tar.gz.gpg
   ```

3. **Push to private branch**:
   ```bash
   git checkout -b transfer-branch
   git add file.tar.gz.gpg ami-assemble.sh
   git commit -m "transfer: description"
   git push origin transfer-branch --force
   ```

### Receiving Files (Local → Server)

1. **Clone the branch**:
   ```bash
   git clone -b transfer-branch git@github.com:user/repo.git temp_dir
   ```

2. **Assemble if split**:
   ```bash
   bash ami-assemble.sh
   ```

3. **Decrypt**:
   ```bash
   gpg -d file.tar.gz.gpg | tar -xzf -
   # Enter passphrase when prompted
   ```

4. **Clean up**: Delete the branch after successful transfer

## Security Notes

- Use strong GPG passphrases (shared via separate channel)
- Delete the branch after transfer to minimize exposure
- The GPG encryption protects content even if the repository is compromised
- Do not commit unencrypted sensitive files to any branch
- Force-push to avoid leaving history traces on the remote

## Example

```bash
# On server:
gpg -c config_backup.tar.gz
git checkout -b transfer-config
git add config_backup.tar.gz.gpg
git commit -m "transfer: config backup 2026-06-23"
git push origin transfer-config --force

# On local machine:
git clone -b transfer-config git@github.com:shakhor-shual/F.A.M.I.L.Y.git tmp
gpg -d tmp/config_backup.tar.gz.gpg | tar -xzf -
# Clean up:
git push origin --delete transfer-config
rm -rf tmp
```