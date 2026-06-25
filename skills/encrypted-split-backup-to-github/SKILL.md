---
name: encrypted-split-backup-to-github
description: Split large files into 50 MB parts, create an assembly script, encrypt with GPG symmetric, and push to a private GitHub branch with force-pushed history.
---

# Encrypted Split Backup to GitHub

## When to Use
- You need to back up a large file/directory (>50 MB) where GitHub file size limits prevent direct upload.
- The backup contains sensitive data requiring encryption (e.g., configs, venvs, tokens).
- You want a recoverable, self-contained backup on a private GitHub branch with a simple retrieval flow.
- Use instead of external storage services — no S3, no rsync, no external host needed.

## Steps

### 1. Create the tarball (excluding large/cache dirs)
```bash
tar -czf <name>.tar.gz \
  --exclude='models' \
  --exclude='.venv' \
  --exclude='cache' \
  --exclude='__pycache__' \
  <source_dir>/
```
- Exclude anything that can be re-downloaded or recreated (model weights, venvs, caches).
- Keep configs (`.nanobot/`, `.env`), scripts, source code.

### 2. Split into 50 MB parts
```bash
split -b 50M <name>.tar.gz <name>.tar.gz.part_
```
- GitHub's recommended max file size is 50 MB per file.

### 3. Create the assembly script (`<name>-assemble.sh`)
```bash
#!/usr/bin/env bash
set -euo pipefail
cat <name>.tar.gz.part_* > <name>.tar.gz
gpg -d <name>.tar.gz.gpg | tar -xzf -
```
- This concatenates parts and decrypts+extracts in one pipeline.
- Make the script executable: `chmod +x <name>-assemble.sh`.

### 4. Encrypt the tarball
```bash
gpg --symmetric --cipher-algo AES256 <name>.tar.gz
```
- You will be prompted for a passphrase. Use a strong one and store it securely (e.g., in a password manager or shared verbally).
- The output is `<name>.tar.gz.gpg`.

### 5. Push to a private GitHub branch
```bash
# Create a clean branch
git checkout --orphan <branch-name>
git rm -rf .

# Add split parts and assembly script
git add <name>.tar.gz.part_* <name>-assemble.sh
git commit -m "Backup <name> — split encrypted archive"

# Force push (rewrite history — keeps branch lightweight)
git push origin <branch-name> --force
```
- Use `--orphan` to start from a clean slate (no previous history).
- Use `--force` to rewrite history on subsequent backups of the same branch.

### 6. Clean up local artifacts
```bash
rm -f <name>.tar.gz <name>.tar.gz.part_* <name>-assemble.sh
```
- The remote branch is the single source of truth for the backup.

## Retrieval (Restore) Flow
```bash
git clone --branch <branch-name> <repo-url> <dest-dir>
cd <dest-dir>
chmod +x <name>-assemble.sh
bash <name>-assemble.sh
# Enter GPG passphrase when prompted
```
- The tarball is reconstructed, decrypted, and extracted in one step.
- No manual part concatenation or separate decryption needed.

## Output Format
- A private GitHub branch containing:
  - `<name>.tar.gz.part_aa`, `<name>.tar.gz.part_ab`, … (50 MB chunks)
  - `<name>-assemble.sh` (recovery script)
- After extraction: the original directory structure restored.

## Example
**Scenario**: Backing up the AMI nanobot workspace (269 MB) including `.nanobot` configs and `venvs/dev`.

```bash
# Step 1: tarball
tar -czf ami-home.tar.gz \
  --exclude='models' \
  --exclude='**/__pycache__' \
  /home/ubuntu/AMI/

# Step 2: split
split -b 50M ami-home.tar.gz ami-home.tar.gz.part_

# Step 3: assembly script
cat > ami-assemble.sh << 'SCRIPT'
#!/usr/bin/env bash
set -euo pipefail
cat ami-home.tar.gz.part_* > ami-home.tar.gz
gpg -d ami-home.tar.gz.gpg | tar -xzf -
SCRIPT
chmod +x ami-assemble.sh

# Step 4: encrypt
gpg --symmetric --cipher-algo AES256 ami-home.tar.gz
# → ami-home.tar.gz.gpg created

# Step 5: push to branch
git checkout --orphan ami-home
git rm -rf .
git add ami-home.tar.gz.part_* ami-assemble.sh
git commit -m "Backup AMI home — split encrypted archive"
git push origin ami-home --force

# Step 6: cleanup
rm -f ami-home.tar.gz ami-home.tar.gz.part_* ami-assemble.sh
```