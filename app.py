import httpx
import jwt
import warnings
from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
from urllib.parse import urlparse, parse_qs, unquote
from datetime import datetime, timedelta

warnings.filterwarnings("ignore")

app = FastAPI(docs_url=None, redoc_url=None)

JWT_SECRET = "zainu_bhai_secret_key_2024"
JWT_ALGORITHM = "HS256"

def generate_jwt_token(account_id: str, nickname: str, region: str):
    """Generate JWT token from account info"""
    payload = {
        "account_id": account_id,
        "nickname": nickname,
        "region": region,
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(days=7)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

async def exchange_eat_to_access(eat_token: str):
    """Convert Eat Token to Access Token - REAL WORKING"""
    try:
        async with httpx.AsyncClient(verify=False, timeout=15.0) as client:
            callback_url = f"https://api-otrss.garena.com/support/callback/?access_token={eat_token}"
            response = await client.get(callback_url, follow_redirects=False)

            if 300 <= response.status_code < 400 and "Location" in response.headers:
                redirect_url = response.headers["Location"]
                parsed_url = urlparse(redirect_url)
                query_params = parse_qs(parsed_url.query)

                access_token = query_params.get("access_token", [None])[0]
                account_id = query_params.get("account_id", [None])[0]
                nickname = query_params.get("nickname", [None])[0]
                region = query_params.get("region", [None])[0]

                if access_token and account_id:
                    return {
                        "success": True,
                        "access_token": access_token,
                        "account_id": account_id,
                        "nickname": unquote(nickname) if nickname else None,
                        "region": region if region else "IND"
                    }
            
            return {"success": False, "error": "Invalid or expired eat token"}
            
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/Eat")
async def eat_to_access(eat_token: str = Query(..., description="Eat Token from Garena")):
    """Convert Eat Token to Access Token + Generate JWT"""
    
    result = await exchange_eat_to_access(eat_token)
    
    if not result.get("success"):
        return JSONResponse(
            status_code=400,
            content={
                "status": "error",
                "message": result.get("error"),
                "credit": "ZAINU BHAI"
            }
        )
    
    # Generate JWT token
    jwt_token = generate_jwt_token(
        result["account_id"],
        result["nickname"],
        result["region"]
    )
    
    return JSONResponse(content={
        "status": "success",
        "credit": "ZAINU BHAI",
        "data": {
            "account_id": result["account_id"],
            "nickname": result["nickname"],
            "region": result["region"],
            "access_token": result["access_token"],
            "jwt_token": jwt_token
        }
    })

@app.get("/verify-jwt")
async def verify_jwt(jwt_token: str = Query(..., description="JWT Token to verify")):
    """Verify JWT token"""
    try:
        decoded = jwt.decode(jwt_token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return JSONResponse(content={
            "status": "success",
            "credit": "ZAINU BHAI",
            "decoded": {
                "account_id": decoded.get("account_id"),
                "nickname": decoded.get("nickname"),
                "region": decoded.get("region"),
                "issued_at": decoded.get("iat"),
                "expires_at": decoded.get("exp")
            }
        })
    except jwt.ExpiredSignatureError:
        return JSONResponse(
            status_code=400,
            content={"status": "error", "message": "JWT token expired", "credit": "ZAINU BHAI"}
        )
    except:
        return JSONResponse(
            status_code=400,
            content={"status": "error", "message": "Invalid JWT token", "credit": "ZAINU BHAI"}
        )

@app.get("/")
async def root():
    return {
        "service": "Eat Token Decoder - ZAINU BHAI",
        "credit": "ZAINU BHAI",
        "working_endpoints": [
            "GET /Eat?eat_token=YOUR_TOKEN - Get Access Token + JWT",
            "GET /verify-jwt?jwt_token=YOUR_JWT - Verify JWT Token"
        ],
        "what_you_get": [
            "✅ Account ID",
            "✅ Nickname",
            "✅ Region", 
            "✅ Access Token",
            "✅ JWT Token"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5030)
