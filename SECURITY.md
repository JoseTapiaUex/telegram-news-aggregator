# Security and Secrets

This document explains how to handle secrets, sensitive data and backups for the project.

## Keep secrets out of the repository

- Do not commit `.env` or any file containing real credentials (API keys, tokens, passwords).
- Only commit `.env.example` with placeholder values.
- Ensure `.gitignore` contains at least: `data/`, `.env`, `.venv/`, `*.log`, `*.db`.

## Use GitHub Secrets

1. Go to your GitHub repository -> Settings -> Secrets and variables -> Actions -> New repository secret.
2. Add keys like `TG_APP_ID`, `TG_API_HASH`, `TG_PHONE`, `IMAGE_API_KEY` as secrets.
3. In GitHub Actions, reference them as `${{ secrets.TG_APP_ID }}`.

## Backup strategy (recommended)

- Use a private storage bucket (S3, Azure Blob or GCS) and upload encrypted backups of `data/posts.db`.
- Alternatively, push a compressed and encrypted copy to a private repo.
- Rotating keys and limiting access is recommended.

## Removing sensitive data from history

If you accidentally committed secrets, remove them with either:

### Option A: BFG Repo-Cleaner (easier)

1. Install BFG: https://rtyley.github.io/bfg-repo-cleaner/
2. Run:

```bash
java -jar bfg.jar --delete-files .env
git reflog expire --expire=now --all
git gc --prune=now --aggressive
git push --force
```

### Option B: git filter-repo (recommended for advanced users)

1. Install `git-filter-repo`.
2. Example command to remove `data/posts.db` from history:

```bash
git filter-repo --path data/posts.db --invert-paths
git push --force
```

> WARNING: rewriting history will change commit SHAs. Coordinate with collaborators and keep a local backup before proceeding.

## Need help?

If you want, I can:

- Add a small PowerShell script to create encrypted backups of `data/posts.db` and upload them to a private S3 bucket.
- Walk you through cleaning the git history if secrets were committed.
- Add a GitHub Action to periodically create encrypted backups.

Contact me in the repo issues or request the specific assistance above and I will implement it.