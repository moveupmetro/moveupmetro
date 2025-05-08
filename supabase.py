
import os
import json
import requests

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

def upsert_profile(profile):
    url = f"{SUPABASE_URL}/rest/v1/profiles"
    r = requests.post(url, headers=HEADERS, json=profile)
    return r.status_code, r.text

def fetch_profiles():
    url = f"{SUPABASE_URL}/rest/v1/profiles"
    r = requests.get(url, headers=HEADERS)
    return r.json() if r.ok else []

def upsert_leaderboard(entries):
    url = f"{SUPABASE_URL}/rest/v1/leaderboard"
    r = requests.post(url, headers=HEADERS, json=entries)
    return r.status_code, r.text

def fetch_leaderboard():
    url = f"{SUPABASE_URL}/rest/v1/leaderboard?order=money.desc&limit=10"
    r = requests.get(url, headers=HEADERS)
    return r.json() if r.ok else []
