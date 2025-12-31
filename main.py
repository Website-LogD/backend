from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

import logging
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Configure Logging
logging.basicConfig(
    filename="server.log",
    level=logging.INFO,
    format="[%(asctime)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger(__name__)

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")


# Enable CORS
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class UserLogin(BaseModel):
    username: str
    password: str

class UserRegister(BaseModel):
    email: str
    username: str
    password: str

@app.get("/")
def read_root():
    return {"message": "Welcome to the Auth API"}

@app.post("/api/login")
def login(user: UserLogin):
    # Simulated login logic
    if user.username == "admin" and user.password == "password":
        logger.info(f"User '{user.username}' logged in successfully.")
        return {"status": "success", "message": "Login successful", "user": user.username}
    else:
        # For demo purposes, we accept any login if it's not the hardcoded check failure
        # But let's make it a bit realistic
        if len(user.password) < 4:
             logger.warning(f"Failed login attempt for '{user.username}': Password too short.")
             raise HTTPException(status_code=400, detail="Password too short")
        logger.info(f"User '{user.username}' logged in (demo mode).")
        return {"status": "success", "message": f"Welcome back, {user.username}!"}

@app.post("/api/register")
def register(user: UserRegister):
    # Simulated registration logic
    return {
        "status": "success", 
        "message": "Account created successfully", 
        "data": {"username": user.username, "email": user.email}
    }

# --- CI/CD Dashboard Endpoints ---
import random
from datetime import datetime

@app.get("/api/dashboard/stats")
def get_stats():
    """Returns simulated environment status and build stats"""
    return {
        "production": {"status": "healthy", "uptime": "99.9%", "version": "v2.4.0"},
        "staging": {"status": "deploying", "uptime": "98.5%", "version": "v2.4.1-rc"},
        "build_success_rate": 94,
        "active_deployments": 1
    }

@app.get("/api/dashboard/logs")
def get_logs():
    """Returns the last 50 lines from the server log file"""
    try:
        if not os.path.exists("server.log"):
            return {"logs": ["Waiting for logs..."]}
        
        with open("server.log", "r") as f:
            # Read all lines and take the last 50
            lines = f.readlines()
            last_logs = [line.strip() for line in lines[-50:]]
            return {"logs": last_logs}
    except Exception as e:
        return {"logs": [f"Error reading logs: {str(e)}"]}

@app.post("/api/dashboard/trigger")
def trigger_build():
    """Simulates triggering a new build"""
    logger.info("Manual build triggered by user.")
    return {
        "status": "success",
        "message": "Build #4021 triggered successfully",
        "timestamp": datetime.now().isoformat()
    }

class SocialLogin(BaseModel):
    provider: str

@app.post("/api/login/social")
def social_login(login: SocialLogin):
    """Simulates a social login (Google/GitHub)"""
    # specific simulated delays or checks could go here
    return {
        "status": "success",
        "message": f"Successfully authenticated with {login.provider}",
        "user": "Social User"
    }

# --- Real OAuth Redirects ---
from fastapi.responses import RedirectResponse
import httpx

# Update these to match your actual backend callback URLs
GOOGLE_REDIRECT_URI = "http://localhost:8000/api/auth/callback/google"
GITHUB_REDIRECT_URI = "http://localhost:8000/api/auth/callback/github"
FRONTEND_URL = "http://localhost:5173/dashboard"

@app.get("/api/auth/google")
def auth_google():
    """Redirects to Google for OAuth authentication"""
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
    
    if not GOOGLE_CLIENT_ID:
         raise HTTPException(status_code=500, detail="Missing GOOGLE_CLIENT_ID in server configuration")

    url = (
        f"https://accounts.google.com/o/oauth2/v2/auth?"
        f"response_type=code&"
        f"client_id={GOOGLE_CLIENT_ID}&"
        f"redirect_uri={GOOGLE_REDIRECT_URI}&"
        f"scope=openid%20email%20profile"
    )
    return RedirectResponse(url, status_code=308)

@app.get("/api/auth/github")
def auth_github():
    """Redirects to GitHub for OAuth authentication"""
    GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
    
    if not GITHUB_CLIENT_ID:
         raise HTTPException(status_code=500, detail="Missing GITHUB_CLIENT_ID in server configuration")

    url = (
        f"https://github.com/login/oauth/authorize?"
        f"client_id={GITHUB_CLIENT_ID}&"
        f"redirect_uri={GITHUB_REDIRECT_URI}&"
        f"scope=user:email"
    )
    return RedirectResponse(url, status_code=308)

@app.get("/api/auth/callback/github")
async def callback_github(code: str):
    """Handles callback from GitHub, exchanges code for token"""
    GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
    GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")
    
    if not GITHUB_CLIENT_ID or not GITHUB_CLIENT_SECRET:
        raise HTTPException(status_code=500, detail="Missing GitHub credentials")

    async with httpx.AsyncClient() as client:
        # Exchange code for access token
        headers = {"Accept": "application/json"}
        data = {
            "client_id": GITHUB_CLIENT_ID,
            "client_secret": GITHUB_CLIENT_SECRET,
            "code": code,
            "redirect_uri": GITHUB_REDIRECT_URI
        }
        response = await client.post("https://github.com/login/oauth/access_token", headers=headers, json=data)
        token_data = response.json()
        
        if "error" in token_data:
             raise HTTPException(status_code=400, detail=f"GitHub Login Failed: {token_data.get('error_description')}")

        access_token = token_data.get("access_token")
        
        # Get User Info
        user_response = await client.get("https://api.github.com/user", headers={
            "Authorization": f"Bearer {access_token}"
        })
        user_info = user_response.json()
        
    # In a real app, you would create a session/JWT here
    # For now, we redirect to dashboard with a query param (simple demo)
    return RedirectResponse(f"{FRONTEND_URL}?user={user_info.get('login')}", status_code=302)

@app.get("/api/auth/callback/google")
async def callback_google(code: str):
    """Handles callback from Google, exchanges code for token"""
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        raise HTTPException(status_code=500, detail="Missing Google credentials")

    async with httpx.AsyncClient() as client:
        # Exchange code for access token
        data = {
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": GOOGLE_REDIRECT_URI
        }
        response = await client.post("https://oauth2.googleapis.com/token", data=data)
        token_data = response.json()
        
        if "error" in token_data:
             raise HTTPException(status_code=400, detail=f"Google Login Failed: {token_data.get('error_description')}")
             
        access_token = token_data.get("access_token")
        
        # Get User Info
        user_response = await client.get("https://www.googleapis.com/oauth2/v2/userinfo", headers={
            "Authorization": f"Bearer {access_token}"
        })
        user_info = user_response.json()
        
    # Redirect to dashboard
    logger.info(f"Google login successful for {user_info.get('email')}")
    return RedirectResponse(f"{FRONTEND_URL}?user={user_info.get('email')}", status_code=302)

# Make sure this mount is AFTER all API routes
# Mount the frontend static files (Production Mode)
if os.path.exists("../frontend/dist"):
    app.mount("/assets", StaticFiles(directory="../frontend/dist/assets"), name="assets")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        # API requests are already handled above, so this catches everything else
        # Check if file exists in dist, otherwise serve index.html
        possible_path = os.path.join("../frontend/dist", full_path)
        if os.path.isfile(possible_path):
             return FileResponse(possible_path)
        return FileResponse("../frontend/dist/index.html")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
