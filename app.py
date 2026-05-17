import httpx
import warnings
from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
from urllib.parse import urlparse, parse_qs, unquote

warnings.filterwarnings("ignore")

app = FastAPI(docs_url=None, redoc_url=None)

async def exchange_eat_to_access(eat_token: str):
    """Convert Eat Token to Access Token"""
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
                        "region": region
                    }
            
            return {"success": False, "error": "Invalid eat token"}
            
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/Eat")
async def eat_to_access(eat_token: str = Query(..., description="Eat Token from Garena")):
    """Convert Eat Token to Access Token"""
    
    result = await exchange_eat_to_access(eat_token)
    
    if result.get("success"):
        return JSONResponse(content={
            "status": "success",
            "access_token": result["access_token"],
            "account_id": result["account_id"],
            "nickname": result["nickname"],
            "region": result.get("region", "IND"),
            "credit": "@CodingWithNexu"
        })
    else:
        return JSONResponse(
            status_code=400,
            content={
                "status": "error",
                "message": result.get("error", "Failed to exchange token")
            }
        )

@app.get("/")
async def root():
    return {
        "service": "Eat to Access Token Converter",
        "endpoint": "GET /Eat?eat_token=YOUR_EAT_TOKEN",
        "status": "working"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5030)
