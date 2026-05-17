from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
from urllib.parse import unquote
import re

app = FastAPI(docs_url=None, redoc_url=None)

@app.get("/Eat")
async def decode_eat_token(eat_token: str = Query(..., description="Eat Token")):
    """Parse Eat Token - Works with your token format"""
    
    try:
        # Your token already has all data
        result = {
            "status": "success",
            "credit": "@CodingWithNexu",
            "data": {
                "account_id": None,
                "nickname": None,
                "region": "IND",
                "eat_token": None
            }
        }
        
        # Parse the query string
        if '&' in eat_token:
            params = eat_token.split('&')
            for param in params:
                if '=' in param:
                    key, value = param.split('=', 1)
                    key = key.strip().lower()
                    value = unquote(value.strip())
                    
                    if key == 'account_id':
                        result["data"]["account_id"] = value
                    elif key == 'nickname':
                        # Handle special chars
                        result["data"]["nickname"] = value
                    elif key == 'region':
                        result["data"]["region"] = value
                    elif key == 'eat':
                        result["data"]["eat_token"] = value[:50] + "..."  # Truncate
        else:
            result["data"]["eat_token"] = eat_token[:50] + "..."
            result["message"] = "Token only - no account info in params"
        
        # Validate we got data
        if not result["data"]["account_id"]:
            result["warning"] = "Account ID not found in token"
        
        return JSONResponse(content=result)
        
    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={"status": "error", "message": str(e)}
        )

@app.get("/")
async def root():
    return {
        "service": "Eat Token Decoder",
        "endpoint": "/Eat?eat_token=YOUR_TOKEN",
        "example": "/Eat?eat_token=eat=xxx&account_id=14345056892&nickname=ZAITU&region=IND",
        "deployed_on": "Vercel"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5030)
