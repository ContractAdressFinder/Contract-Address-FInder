# Solana Twitter Backend

A FastAPI service that fetches top Twitter accounts discussing a Solana token using its contract address.

## 🛠 Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create `.env` file with:
```
HELIUS_API_KEY=your_helius_api_key
TWITTER_BEARER_TOKEN=your_twitter_bearer_token
```

3. Run the app:
```bash
uvicorn main:app --reload
```

## 🧪 Endpoints

- `POST /resolve-token` — input: `{ contract_address }`
- `POST /fetch-twitter-accounts` — input: `{ token_name }`
