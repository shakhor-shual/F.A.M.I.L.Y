---
name: dev-first-deployment
description: Deploy nanobot by trying the dev environment first and automatically rolling back to prod on failure. Use when restarting, deploying, or updating the nanobot service.
---

# Dev-First Deployment

## When to Use

- Restarting the nanobot service after updates or maintenance
- Deploying changes to the nanobot workspace
- Setting up nanobot on a new machine
- The server has both `dev` and `prod` environments configured

## Architecture

- Two Git branches: `dev` (experiments) and `prod` (crystal-copy)
- Two venvs: `~/venvs/dev` and `~/venvs/prod`
- Systemd unit auto-starts with dev-first, automatic rollback to prod on failure

## Deployment Script

The deploy script (`deploy.sh`) follows this logic:

```
1. Check out the dev branch
2. Activate ~/venvs/dev
3. Start nanobot
4. If start fails → check out prod branch → activate ~/venvs/prod → start nanobot
5. Report which environment is running
```

## Manual Deployment Steps

1. **Push changes to dev branch** (or the branch you're working on)
2. **SSH into the server**
3. **Run the deploy script** (or restart systemd)
4. **Verify** — check that nanobot is responding on the expected channel
5. **If dev fails** — rollback happens automatically; check the logs to understand why

## Systemd Configuration

The systemd unit (`/etc/systemd/system/nanobot.service`) should:

```
[Unit]
Description=Nanobot AI Service
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/AMI/My_armors/nanobot
ExecStart=/home/ubuntu/deploy.sh
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

## Troubleshooting

- **Dev fails to start**: Check `journalctl -u nanobot -n 50` for errors; rollback to prod is automatic
- **Both fail**: The server may have stale dependencies; activate each venv and test manually
- **Polling conflict**: If two instances poll Telegram, one gets disabled; set environment variable to distinguish instances or use separate bot tokens

## Example

```bash
# After pushing changes
ssh ubuntu@server
sudo systemctl restart nanobot
# Systemd runs deploy.sh → tries dev → if fail → rolls back to prod
# Check status:
systemctl status nanobot
```