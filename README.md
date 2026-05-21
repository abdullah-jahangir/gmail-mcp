# gmail-mcp

A Gmail MCP server for Claude Code built on Google's official Python SDK.

**Bring your own credentials.** You register your own Google Cloud app — your token is stored locally on your machine and never touches anyone else's servers.

## Tools

| Tool | Description |
|------|-------------|
| `send_email` | Send an email with optional CC, BCC, and reply threading |
| `create_draft` | Save a draft without sending |
| `list_emails` | List emails from inbox or any label |
| `search_emails` | Search using Gmail query syntax |
| `get_email` | Read the full content of an email by ID |
| `reply_to_email` | Reply to an existing thread |

---

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Create a Google Cloud project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Go to **APIs & Services > Library**, search for **Gmail API**, click **Enable**

### 3. Create OAuth credentials

1. Go to **APIs & Services > OAuth consent screen**
   - User type: **External**
   - Fill in app name (anything), your email for support and developer contact
   - Click through Scopes and Test Users without changing anything
2. Go to **APIs & Services > Credentials**
   - Click **+ Create Credentials > OAuth client ID**
   - Application type: **Desktop app**
   - Click **Create**, then **Download JSON**

### 4. Add yourself as a test user

1. Go back to **OAuth consent screen**
2. Under **Test users**, click **+ Add Users**
3. Add your Gmail address

### 5. Save your credentials

```bash
mkdir -p ~/.gmail-mcp
mv ~/Downloads/client_secret_*.json ~/.gmail-mcp/credentials.json
```

### 6. Authenticate

```bash
python3 server.py --auth
```

This opens a browser, you log in with Google, and your token is saved to `~/.gmail-mcp/token.json`. You only do this once.

### 7. Register with Claude Code

```bash
claude mcp add -s user gmail -- python3 /path/to/gmail-mcp/server.py
```

---

## How it works

Your credentials are yours. The OAuth flow uses the `client_id` and `client_secret` from the Google Cloud app **you** created — not a shared app. Google sees all requests as coming from your own registered application.

The access token is stored at `~/.gmail-mcp/token.json` and automatically refreshed when it expires. Nothing is transmitted to any third party.

```
credentials.json   →   your Google Cloud app identity
token.json         →   your personal access token (auto-refreshed)
server.py          →   MCP server that connects Claude Code to Gmail API
```

## Security

- `credentials.json` and `token.json` are listed in `.gitignore` — they will never be committed
- All Gmail API calls go directly from your machine to Google
- The server runs locally as a subprocess of Claude Code over stdin/stdout

## License

MIT
