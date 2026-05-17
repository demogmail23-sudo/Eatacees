import httpx
import asyncio
import warnings
from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from urllib.parse import urlparse, parse_qs
from typing import Optional
import json

warnings.filterwarnings("ignore")

app = FastAPI(title="India FreeFire Token Decoder", description="FreeFire India Eat Token Decoder")

async def get_open_id_from_shop2game(account_id: str):
    """Get Open ID using shop2game.com API (Works for India)"""
    try:
        async with httpx.AsyncClient(verify=False, timeout=15.0) as client:
            url = "https://shop2game.com/api/auth/player_id_login"
            
            headers = {
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "en-IN,en;q=0.9,hi;q=0.8",
                "Content-Type": "application/json",
                "Origin": "https://shop2game.com",
                "Referer": "https://shop2game.com/",
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "same-origin",
                "User-Agent": "Mozilla/5.0 (Linux; Android 13; SM-S23) AppleWebKit/537.36",
                "Cookie": "region=IN; source=mb; language=en"
            }
            
            payload = {
                "app_id": 100067,
                "login_id": str(account_id)
            }
            
            response = await client.post(url, headers=headers, json=payload)
            
            if response.status_code == 200:
                data = response.json()
                open_id = data.get("open_id")
                if open_id:
                    return open_id
            
            return None
            
    except Exception as e:
        print(f"Shop2Game error: {e}")
        return None

async def get_open_id_from_topup(account_id: str):
    """Fallback: Get Open ID using topup.pk API"""
    try:
        async with httpx.AsyncClient(verify=False, timeout=15.0) as client:
            url = "https://topup.pk/api/auth/player_id_login"
            
            headers = {
                "Accept": "application/json, text/plain, */*",
                "Content-Type": "application/json",
                "Origin": "https://topup.pk",
                "Referer": "https://topup.pk/",
                "User-Agent": "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36",
                "Cookie": "region=PK; source=mb"
            }
            
            payload = {
                "app_id": 100067,
                "login_id": str(account_id)
            }
            
            response = await client.post(url, headers=headers, json=payload)
            
            if response.status_code == 200:
                data = response.json()
                open_id = data.get("open_id")
                if open_id:
                    return open_id
            
            return None
            
    except Exception as e:
        print(f"Topup error: {e}")
        return None

async def get_garena_data_india(eat_token: str):
    """Main function to decode Eat Token for India region"""
    try:
        async with httpx.AsyncClient(verify=False, timeout=15.0) as client:
            # Step 1: Garena Callback
            callback_url = f"https://api-otrss.garena.com/support/callback/?access_token={eat_token}"
            response = await client.get(callback_url, follow_redirects=False)

            if 300 <= response.status_code < 400 and "Location" in response.headers:
                redirect_url = response.headers["Location"]
                parsed_url = urlparse(redirect_url)
                query_params = parse_qs(parsed_url.query)

                token_value = query_params.get("access_token", [None])[0]
                account_id = query_params.get("account_id", [None])[0]
                account_nickname = query_params.get("nickname", [None])[0]
                region = query_params.get("region", [None])[0]

                if not token_value or not account_id:
                    return {
                        "status": "error", 
                        "message": "Failed to extract data from Garena callback"
                    }
            else:
                return {
                    "status": "error", 
                    "message": "Invalid access token or session expired",
                    "http_code": response.status_code
                }

            # Step 2: Try to get Open ID (India first)
            open_id = await get_open_id_from_shop2game(account_id)
            
            # Fallback to topup.pk if shop2game fails
            if not open_id:
                open_id = await get_open_id_from_topup(account_id)
            
            if not open_id:
                return {
                    "status": "error",
                    "message": "Failed to fetch Open ID from all sources",
                    "account_id": account_id
                }

            # Step 3: Try to get India region specific info (optional)
            india_info = {}
            try:
                # India specific endpoint check
                india_url = "https://client.ind.freefiremobile.com/GetPlayerPersonalShow"
                # This requires proper encryption, so it's optional
                india_info = {"note": "Use India endpoint for full details"}
            except:
                pass

            return {
                "status": "success",
                "region_detected": "INDIA" if region == "IN" else region,
                "data": {
                    "account_id": account_id,
                    "account_nickname": account_nickname,
                    "open_id": open_id,
                    "access_token": token_value,
                    "region": region if region else "IN"
                },
                "credit": "@CodingWithNexu",
                "powered_by": "@Parrahex"
            }

    except httpx.TimeoutException:
        return {"status": "error", "message": "Request timeout - server slow response"}
    except httpx.ConnectError:
        return {"status": "error", "message": "Connection error - check your internet"}
    except Exception as e:
        return {"status": "error", "message": "Internal server error", "details": str(e)}

@app.get("/", response_class=HTMLResponse)
async def home():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>🇮🇳 India FreeFire Token Decoder</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;
                background: linear-gradient(135deg, #FF9933 0%, #FFFFFF 50%, #138808 100%);
                min-height: 100vh;
                display: flex;
                justify-content: center;
                align-items: center;
                padding: 20px;
            }
            .container {
                background: rgba(255, 255, 255, 0.95);
                border-radius: 20px;
                padding: 40px;
                max-width: 650px;
                width: 100%;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                text-align: center;
            }
            .flag {
                font-size: 50px;
                margin-bottom: 10px;
            }
            h1 {
                color: #FF9933;
                margin-bottom: 5px;
            }
            .india-text {
                color: #138808;
                font-weight: bold;
            }
            .credit {
                background: linear-gradient(135deg, #FF9933 0%, #FFFFFF 50%, #138808 100%);
                padding: 15px;
                border-radius: 10px;
                margin: 20px 0;
                color: white;
                font-weight: bold;
            }
            .endpoint {
                background: #2c3e50;
                color: #ecf0f1;
                padding: 15px;
                border-radius: 10px;
                font-family: monospace;
                word-break: break-all;
                font-size: 14px;
            }
            .status {
                color: #27ae60;
                font-weight: bold;
                display: inline-block;
                animation: pulse 1.5s infinite;
            }
            @keyframes pulse {
                0% { opacity: 1; }
                50% { opacity: 0.5; }
                100% { opacity: 1; }
            }
            hr {
                margin: 20px 0;
                border: none;
                border-top: 2px solid #FF9933;
            }
            input {
                width: 85%;
                padding: 12px;
                margin: 15px 0;
                border: 2px solid #FF9933;
                border-radius: 8px;
                font-family: monospace;
                font-size: 14px;
            }
            button {
                background: #FF9933;
                color: white;
                border: none;
                padding: 12px 30px;
                border-radius: 8px;
                cursor: pointer;
                font-size: 16px;
                font-weight: bold;
                transition: transform 0.2s;
            }
            button:hover {
                background: #138808;
                transform: scale(1.05);
            }
            pre {
                text-align: left;
                background: #1e1e1e;
                color: #d4d4d4;
                padding: 15px;
                border-radius: 10px;
                overflow-x: auto;
                font-size: 12px;
                max-height: 300px;
                overflow-y: auto;
            }
            .feature {
                display: inline-block;
                margin: 5px;
                padding: 5px 10px;
                background: #e0e0e0;
                border-radius: 20px;
                font-size: 12px;
            }
            .region-badge {
                background: #FF9933;
                color: white;
                padding: 5px 15px;
                border-radius: 20px;
                display: inline-block;
                margin: 10px 0;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="flag">🇮🇳</div>
            <h1>India FreeFire</h1>
            <h3 class="india-text">Eat Token Decoder API</h3>
            
            <div class="region-badge">🇮🇍 INDIA REGION ONLY 🇮🇳</div>
            
            <div class="credit">
                🎮 Credit: @CodingWithNexu | ⚡ Powered By: @Parrahex
            </div>
            
            <hr>
            
            <h3>📖 How to Use</h3>
            <div class="endpoint">
                GET /Eat?eat_token=YOUR_EAT_TOKEN_HERE
            </div>
            
            <h3>🧪 Try it Now</h3>
            <input type="text" id="tokenInput" placeholder="Enter your Eat Token..." style="width: 90%;">
            <br>
            <button onclick="testToken()">🇮🇳 Decode Token 🇮🇳</button>
            
            <h3>📤 Response</h3>
            <pre id="response">Click the button to see response...</pre>
            
            <div style="margin-top: 15px;">
                <span class="feature">✅ India Region Support</span>
                <span class="feature">✅ Shop2Game API</span>
                <span class="feature">✅ Auto Fallback</span>
                <span class="feature">✅ Fast Response</span>
            </div>
        </div>
        
        <script>
            async function testToken() {
                const token = document.getElementById('tokenInput').value;
                const responseDiv = document.getElementById('response');
                
                if (!token) {
                    responseDiv.textContent = '❌ Please enter an Eat Token!';
                    return;
                }
                
                responseDiv.textContent = '⏳ Loading... Please wait...';
                
                try {
                    const res = await fetch(`/Eat?eat_token=${encodeURIComponent(token)}`);
                    const data = await res.json();
                    responseDiv.textContent = JSON.stringify(data, null, 2);
                } catch (error) {
                    responseDiv.textContent = '❌ Error: ' + error.message;
                }
            }
            
            // Enter key support
            document.getElementById('tokenInput').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    testToken();
                }
            });
        </script>
    </body>
    </html>
    """

@app.get("/Eat")
async def decode_eat_token(eat_token: str = Query(..., description="Garena Eat Token / Access Token")):
    """Decode Garena Eat Token for India region"""
    result = await get_garena_data_india(eat_token)
    
    if result.get("status") == "error":
        return JSONResponse(status_code=400, content=result)
    
    return result

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "India FreeFire Token Decoder",
        "region": "INDIA",
        "version": "2.0"
    }

@app.get("/api/docs")
async def api_docs():
    return {
        "endpoints": [
            {
                "path": "/",
                "method": "GET",
                "description": "Home page with UI"
            },
            {
                "path": "/Eat",
                "method": "GET",
                "params": {"eat_token": "string"},
                "description": "Decode Eat Token"
            },
            {
                "path": "/api/health",
                "method": "GET",
                "description": "Health check"
            }
        ],
        "example": "curl 'https://your-domain.vercel.app/Eat?eat_token=YOUR_TOKEN'",
        "india_specific": True
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5030)