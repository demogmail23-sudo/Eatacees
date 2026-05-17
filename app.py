import httpx
import warnings
from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import JSONResponse
from urllib.parse import urlparse, parse_qs

warnings.filterwarnings("ignore")

app = FastAPI(title="India FreeFire Token Decoder API", docs_url=None, redoc_url=None)

async def get_open_id(account_id: str):
    """Get Open ID from API"""
    try:
        async with httpx.AsyncClient(verify=False, timeout=15.0) as client:
            # Primary: Shop2Game
            url = "https://shop2game.com/api/auth/player_id_login"
            headers = {
                "Accept": "application/json",
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36",
                "Cookie": "region=IN; source=mb"
            }
            payload = {"app_id": 100067, "login_id": str(account_id)}
            
            response = await client.post(url, headers=headers, json=payload)
            if response.status_code == 200:
                data = response.json()
                if data.get("open_id"):
                    return data.get("open_id")
            
            # Fallback: Topup
            url2 = "https://topup.pk/api/auth/player_id_login"
            response2 = await client.post(url2, headers=headers, json=payload)
            if response2.status_code == 200:
                data2 = response2.json()
                if data2.get("open_id"):
                    return data2.get("open_id")
            
            return None
    except:
        return None

@app.get("/Eat")
async def decode_eat_token(eat_token: str = Query(..., description="Garena Eat Token")):
    """Decode Eat Token - India Region"""
    
    if not eat_token or len(eat_token) < 10:
        return JSONResponse(
            status_code=400,
            content={"status": "error", "message": "Invalid eat_token"}
        )
    
    try:
        async with httpx.AsyncClient(verify=False, timeout=15.0) as client:
            # Get user data from Garena
            callback_url = f"https://api-otrss.garena.com/support/callback/?access_token={eat_token}"
            response = await client.get(callback_url, follow_redirects=False)

            if not (300 <= response.status_code < 400 and "Location" in response.headers):
                return JSONResponse(
                    status_code=400,
                    content={"status": "error", "message": "Invalid or expired token"}
                )
            
            redirect_url = response.headers["Location"]
            parsed_url = urlparse(redirect_url)
            query_params = parse_qs(parsed_url.query)
            
            token_value = query_params.get("access_token", [None])[0]
            account_id = query_params.get("account_id", [None])[0]
            account_nickname = query_params.get("nickname", [None])[0]
            region = query_params.get("region", [None])[0]
            
            if not token_value or not account_id:
                return JSONResponse(
                    status_code=400,
                    content={"status": "error", "message": "Failed to extract user data"}
                )
            
            # Get Open ID
            open_id = await get_open_id(account_id)
            
            if not open_id:
                open_id = "Not available"
            
            return {
                "status": "success",
                "region": region if region else "IN",
                "data": {
                    "account_id": account_id,
                    "nickname": account_nickname,
                    "open_id": open_id,
                    "access_token": token_value
                }
            }
            
    except httpx.TimeoutException:
        return JSONResponse(
            status_code=504,
            content={"status": "error", "message": "Request timeout"}
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )

@app.get("/health")
async def health():
    return {"status": "ok", "service": "India FF Token Decoder"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5030)
