from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
import json
from collections import defaultdict
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# Load API keys from environment variables
HELIUS_API_KEY = os.getenv("HELIUS_API_KEY")
TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")

# Enable CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ContractRequest(BaseModel):
    contract_address: str

class TokenRequest(BaseModel):
    token_name: str

@app.post("/resolve-token")
async def resolve_token(data: ContractRequest):
    address = data.contract_address
    url = f"https://api.helius.xyz/v0/tokens/metadata?api-key={HELIUS_API_KEY}&mint={address}"

    async with httpx.AsyncClient() as client:
        res = await client.get(url)
        if res.status_code != 200:
            raise HTTPException(status_code=400, detail="Could not fetch token metadata")
        metadata = res.json()

    if not metadata:
        raise HTTPException(status_code=404, detail="Token not found")

    return {
        "token_name": metadata[0].get("name"),
        "symbol": metadata[0].get("symbol")
    }

@app.post("/fetch-twitter-accounts")
async def fetch_twitter_accounts(data: TokenRequest):
    query = data.token_name
    headers = {
        "Authorization": f"Bearer {TWITTER_BEARER_TOKEN}"
    }
    tweet_url = (
        f"https://api.twitter.com/2/tweets/search/recent"
        f"?query={query} lang:en -is:retweet"
        f"&max_results=100&tweet.fields=author_id"
    )

    try:
        async with httpx.AsyncClient() as client:
            tweet_res = await client.get(tweet_url, headers=headers)
            if tweet_res.status_code != 200:
                raise HTTPException(status_code=400, detail="Twitter search failed")
            tweets = tweet_res.json().get("data", [])

            author_counts = defaultdict(int)
            for tweet in tweets:
                author_id = tweet["author_id"]
                author_counts[author_id] += 1

            user_ids = list(author_counts.keys())[:10]
            if not user_ids:
                return {"accounts": []}

            user_lookup_url = (
                f"https://api.twitter.com/2/users?ids={','.join(user_ids)}"
                f"&user.fields=public_metrics,username,profile_image_url"
            )
            user_res = await client.get(user_lookup_url, headers=headers)
            if user_res.status_code != 200:
                raise HTTPException(status_code=400, detail="User lookup failed")

            users = user_res.json().get("data", [])
            results = []
            for user in users:
                results.append({
                    "username": f"@{user['username']}",
                    "followers": user["public_metrics"]["followers_count"],
                    "tweets": author_counts[user["id"]],
                    "profilePic": user["profile_image_url"],
                    "url": f"https://x.com/{user['username']}"
                })

            sorted_users = sorted(results, key=lambda x: (-x["tweets"], -x["followers"]))
            return {"accounts": sorted_users}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Twitter API error: {str(e)}")
