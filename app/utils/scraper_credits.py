import os
import requests
import pandas as pd
from typing import Dict, Optional
import streamlit as st
from datetime import datetime


# API Configuration
API_KEYS = {
    "apify_facebook": os.getenv("APIFY_FACEBOOK_API_KEY"),
    "apify_instagram": os.getenv("APIFY_INSTAGRAM_API_KEY"),
    "twitter_x": os.getenv("TWITTER_X_API_KEY"),
    "tikapi": os.getenv("TIKAPI_API_KEY"),
    "youtube": os.getenv("YOUTUBE_API_KEY"),
}

# API Endpoints
APIFY_USER_ENDPOINT = "https://api.apify.com/v2/users/me"
APIFY_USAGE_ENDPOINT = "https://api.apify.com/v2/users/me/usage/monthly"
TWITTER_X_ENDPOINT = "https://api.twitter.com/2/usage/tweets"
TIKAPI_ENDPOINT = "https://api.tiktok.com/v1/user/info"
YOUTUBE_ENDPOINT = "https://www.googleapis.com/youtube/v3/channels"


@st.cache_data(ttl=300)  # Cache for 5 minutes
def fetch_apify_facebook_credits() -> Optional[Dict]:
    """
    Fetch Apify Facebook account credits and usage limits
    Uses separate APIFY_FACEBOOK_API_KEY
    
    Endpoint: https://api.apify.com/v2/users/me/usage/monthly
    Response includes monthly usage details and costs
    """
    try:
        if not API_KEYS.get("apify_facebook"):
            return None
        
        headers = {
            "Authorization": f"Bearer {API_KEYS['apify_facebook']}"
        }
        
        # Get user info for plan details
        user_response = requests.get(
            APIFY_USER_ENDPOINT,
            headers=headers,
            timeout=5
        )
        
        if user_response.status_code != 200:
            return None
        
        user_data = user_response.json().get("data", {})
        plan_data = user_data.get("plan", {})
        monthly_budget = plan_data.get("maxMonthlyUsageUsd", 250)
        
        # Get usage data
        usage_response = requests.get(
            APIFY_USAGE_ENDPOINT,
            headers=headers,
            timeout=5
        )
        
        if usage_response.status_code == 200:
            usage_data = usage_response.json().get("data", {})
            
            # Extract usage information
            total_used = usage_data.get("totalUsageCreditsUsdAfterVolumeDiscount", 0)
            daily_average = total_used / 30  # Rough daily average
            
            return {
                "daily_limit": int(monthly_budget),
                "used_today": round(daily_average, 2),
                "used_month": round(total_used, 2),
                "remaining": round(monthly_budget - total_used, 2),
                "status": "Active ✅"
            }
        return None
        
    except Exception as e:
        st.warning(f"⚠️ Could not fetch Apify Facebook credits: {str(e)}")
        return None


@st.cache_data(ttl=300)  # Cache for 5 minutes
def fetch_apify_instagram_credits() -> Optional[Dict]:
    """
    Fetch Apify Instagram account credits and usage limits
    Uses separate APIFY_INSTAGRAM_API_KEY
    
    Endpoint: https://api.apify.com/v2/users/me/usage/monthly
    Response includes monthly usage details and costs
    """
    try:
        if not API_KEYS.get("apify_instagram"):
            return None
        
        headers = {
            "Authorization": f"Bearer {API_KEYS['apify_instagram']}"
        }
        
        # Get user info for plan details
        user_response = requests.get(
            APIFY_USER_ENDPOINT,
            headers=headers,
            timeout=5
        )
        
        if user_response.status_code != 200:
            return None
        
        user_data = user_response.json().get("data", {})
        plan_data = user_data.get("plan", {})
        monthly_budget = plan_data.get("maxMonthlyUsageUsd", 250)
        
        # Get usage data
        usage_response = requests.get(
            APIFY_USAGE_ENDPOINT,
            headers=headers,
            timeout=5
        )
        
        if usage_response.status_code == 200:
            usage_data = usage_response.json().get("data", {})
            
            # Extract usage information
            total_used = usage_data.get("totalUsageCreditsUsdAfterVolumeDiscount", 0)
            daily_average = total_used / 30  # Rough daily average
            
            return {
                "daily_limit": int(monthly_budget),
                "used_today": round(daily_average, 2),
                "used_month": round(total_used, 2),
                "remaining": round(monthly_budget - total_used, 2),
                "status": "Active ✅"
            }
        return None
        
    except Exception as e:
        st.warning(f"⚠️ Could not fetch Apify Instagram credits: {str(e)}")
        return None


@st.cache_data(ttl=300)  # Cache for 5 minutes
def fetch_twitter_x_credits() -> Optional[Dict]:
    """
    Fetch Twitter X API usage and limits
    """
    try:
        if not API_KEYS.get("twitter_x"):
            return None
        
        headers = {
            "Authorization": f"Bearer {API_KEYS['twitter_x']}",
            "User-Agent": "Alpha-Scraper-Dashboard"
        }
        
        response = requests.get(
            TWITTER_X_ENDPOINT,
            headers=headers,
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            # Twitter has different rate limits per endpoint
            # Adjust based on actual response structure
            return {
                "daily_limit": 500,  # Example limit
                "used_today": data.get("usage", {}).get("tweets", 0),
                "remaining": 500 - data.get("usage", {}).get("tweets", 0),
                "status": "Active ✅"
            }
        return None
        
    except Exception as e:
        st.warning(f"⚠️ Could not fetch Twitter X credits: {str(e)}")
        return None


@st.cache_data(ttl=300)  # Cache for 5 minutes
def fetch_tikapi_credits() -> Optional[Dict]:
    """
    Fetch TikTok API credits via TIKAPI
    """
    try:
        if not API_KEYS.get("tikapi"):
            return None
        
        headers = {
            "Authorization": f"Bearer {API_KEYS['tikapi']}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(
            TIKAPI_ENDPOINT,
            headers=headers,
            json={"get_credits": True},
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            credits = data.get("credits", {})
            daily_limit = credits.get("daily_limit", 2000)
            used = credits.get("used_today", 0)
            
            return {
                "daily_limit": daily_limit,
                "used_today": used,
                "remaining": daily_limit - used,
                "status": "Active ✅"
            }
        return None
        
    except Exception as e:
        st.warning(f"⚠️ Could not fetch TikApi credits: {str(e)}")
        return None


@st.cache_data(ttl=300)  # Cache for 5 minutes
def fetch_youtube_credits() -> Optional[Dict]:
    """
    Fetch YouTube API quota usage
    """
    try:
        if not API_KEYS.get("youtube"):
            return None
        
        params = {
            "key": API_KEYS["youtube"],
            "part": "statistics",
            "forUsername": "your_channel_username"  # Set dynamically as needed
        }
        
        response = requests.get(
            YOUTUBE_ENDPOINT,
            params=params,
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            # YouTube has a unit quota system (typically 10,000 units per day)
            # Adjust based on actual quota tracking
            return {
                "daily_limit": 100,  # Example API call limit
                "used_today": data.get("usage", 0),
                "remaining": 100 - data.get("usage", 0),
                "status": "Active ✅"
            }
        return None
        
    except Exception as e:
        st.warning(f"⚠️ Could not fetch YouTube credits: {str(e)}")
        return None


def get_all_platform_credits() -> pd.DataFrame:
    """
    Fetch credits for all platforms and return as DataFrame
    Falls back to placeholder data if APIs are unavailable
    """
    
    platform_credits = {
        "Facebook": {
            "api": "APIFY",
            "daily_limit": 1000,
            "used_today": 0,
            "remaining": 1000,
            "status": "⏳ Fetching..."
        },
        "Twitter": {
            "api": "X API",
            "daily_limit": 500,
            "used_today": 0,
            "remaining": 500,
            "status": "⏳ Fetching..."
        },
        "Instagram": {
            "api": "APIFY",
            "daily_limit": 800,
            "used_today": 0,
            "remaining": 800,
            "status": "⏳ Fetching..."
        },
        "TikTok": {
            "api": "TIKAPI",
            "daily_limit": 2000,
            "used_today": 0,
            "remaining": 2000,
            "status": "⏳ Fetching..."
        },
        "YouTube": {
            "api": "YOUTUBE API",
            "daily_limit": 100,
            "used_today": 0,
            "remaining": 100,
            "status": "⏳ Fetching..."
        }
    }
    
    # Fetch Apify data (separate accounts for Facebook & Instagram)
    facebook_data = fetch_apify_facebook_credits()
    if facebook_data:
        platform_credits["Facebook"].update(facebook_data)
    
    instagram_data = fetch_apify_instagram_credits()
    if instagram_data:
        platform_credits["Instagram"].update(instagram_data)
    
    # Fetch Twitter X data
    twitter_data = fetch_twitter_x_credits()
    if twitter_data:
        platform_credits["Twitter"].update(twitter_data)
    
    # Fetch TikTok data
    tikapi_data = fetch_tikapi_credits()
    if tikapi_data:
        platform_credits["TikTok"].update(tikapi_data)
    
    # Fetch YouTube data
    youtube_data = fetch_youtube_credits()
    if youtube_data:
        platform_credits["YouTube"].update(youtube_data)
    
    # Convert to DataFrame
    df = pd.DataFrame([
        {
            "Platform": platform,
            "API": data["api"],
            "Daily Limit": data["daily_limit"],
            "Used Today": data["used_today"],
            "Remaining": data["remaining"],
            "Usage %": round((data["used_today"] / data["daily_limit"] * 100) if data["daily_limit"] > 0 else 0, 1),
            "Status": data["status"]
        }
        for platform, data in platform_credits.items()
    ])
    
    return df


def get_credit_status_message(usage_percent: float) -> tuple[str, str]:
    """
    Get status message and color based on usage percentage
    Returns: (status_text, color_code)
    """
    if usage_percent >= 90:
        return "⛔ Critical", "#FF0000"
    elif usage_percent >= 75:
        return "⚠️ High", "#FF6B6B"
    elif usage_percent >= 50:
        return "⚡ Medium", "#FFA500"
    else:
        return "✅ Low", "#51CF66"


def log_credit_check():
    """
    Log credit check for monitoring and debugging
    """
    try:
        log_message = f"{datetime.now().isoformat()} - Credit check performed"
        # You can store this in a file, database, or log service as needed
        print(log_message)
    except Exception as e:
        print(f"Error logging credit check: {str(e)}")
