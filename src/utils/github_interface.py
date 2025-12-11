import os
import requests
import json

def create_pr(branch_name, title, body):
    """
    Opens a Pull Request from 'branch_name' to 'main'.
    """
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        print(">> ⚠️  ERROR: GITHUB_TOKEN not found. Cannot open PR.")
        return

    # Extract owner/repo from remote URL or env var
    # For now, hardcoding based on your previous logs, but ideally dynamic
    owner = "made-it-so"
    repo = "MISO-Phoenix"
    
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    data = {
        "title": title,
        "body": body,
        "head": branch_name,
        "base": "main"
    }
    
    try:
        resp = requests.post(url, headers=headers, json=data)
        if resp.status_code == 201:
            pr_url = resp.json().get('html_url')
            print(f">> 🚀 SUCCESS: Pull Request Open! {pr_url}")
            return pr_url
        else:
            print(f">> ❌ PR ERROR: {resp.status_code} - {resp.text}")
    except Exception as e:
        print(f">> ❌ PR EXCEPTION: {e}")
