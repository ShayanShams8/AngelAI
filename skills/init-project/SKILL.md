---
name: init-project
description: Initialize the user's project directory for Angel AI runtime use. Creates RESULTS/, tmp/, workflows/, tools/, tools/models/, models.txt, and .env.angel.example if missing. Never overwrites existing secrets.
---

# Angel AI — Init Project

## Purpose
Set up your project directory for Angel AI use.

## Trigger
Use this skill when: the user wants to start using Angel AI, says "initialize", "setup", or "init", or when a required runtime directory is missing.

## Behavior

0. **Verify Python 3.9+** by running `python3 --version`. If Python is not installed or the command is not found, stop immediately and tell the user:
   > "Python 3.9 or higher is required to run Angel AI tools. Please install it from https://www.python.org/downloads/ and re-open this session."
   Do not proceed until Python is confirmed present.

1. Detect the current working directory as USER_PROJECT (unless an explicit path is given).
2. Create these directories if missing (never overwrite existing content):
   - USER_PROJECT/RESULTS/
   - USER_PROJECT/tmp/
   - USER_PROJECT/workflows/
   - USER_PROJECT/tools/
   - USER_PROJECT/tools/models/
3. Create USER_PROJECT/tools/models/models.txt if missing, using the plugin template at templates/models.txt.
4. Create USER_PROJECT/.env.angel.example if missing, copying from plugin template at templates/.env.angel.example.
5. Create an empty USER_PROJECT/.env.angel if it does not yet exist. Never overwrite an existing one.
6. Update USER_PROJECT/.gitignore safely — append only lines that are not already present:
   ```
   .env.angel
   __pycache__/
   *.pyc
   RESULTS/
   tmp/
   system_info.txt
   ```
7. Confirm all directories and files are ready.

## Rules
- Never delete user content.
- Never overwrite .env.angel.
- Never place runtime files in the plugin directory.
