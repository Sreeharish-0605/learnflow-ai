# LearnFlow AI

LearnFlow AI is a public learning tracker for freshers. Users create an account, select a learning path, complete tasks, and monitor their progress. An admin dashboard helps mentors see who needs support.

The first version runs locally with SQLite. It is designed to move to Oracle Autonomous Database by changing `DATABASE_URL`; no application code needs to change.

## Local run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000`.

Set `ADMIN_EMAIL` in `.env` to your own email before registering. That account will receive mentor/admin access.

## OCI deployment target

- OCI Compute: Docker container running this FastAPI app.
- OCI Autonomous Database: user accounts, paths, tasks, and progress.
- OCI Object Storage: optional certificates and project-evidence uploads.
- OCI VCN and NSG: public HTTPS access only to the application.

Never commit `.env`, database wallets, API keys, or OCI credentials.

## OCI Autonomous Database

For production deployment, set `ORACLE_USER`, `ORACLE_PASSWORD`, and the
service alias from the wallet's `tnsnames.ora` file (for example,
`learnflowdb_tp`) in the VM's `.env`. Set `WALLET_HOST_DIR` to the secure
directory that contains the unzipped wallet. Docker mounts this directory at
`/app/wallet` as read-only. Keep `DATABASE_URL` as SQLite for local work.
