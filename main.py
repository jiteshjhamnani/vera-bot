from contextlib import asynccontextmanager
from datetime import datetime
import traceback
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from store import Store
from composer import Composer


# ==========================================================
# Global Objects
# ==========================================================

SERVER_START_TIME = datetime.utcnow()

store = Store()

composer = Composer(store)


# ==========================================================
# Lifespan
# ==========================================================

@asynccontextmanager
async def lifespan(app: FastAPI):

    print("\n===================================")
    print(" Vera Bot Started ")
    print("===================================\n")

    yield

    print("\n===================================")
    print(" Vera Bot Stopped ")
    print("===================================\n")


# ==========================================================
# App
# ==========================================================

app = FastAPI(

    title="Vera Bot",

    version="1.0.0",

    lifespan=lifespan

)

@app.get("/")
def root():

    return {

        "message": "Vera Bot Running",

        "docs": "/docs"

    }

@app.get("/v1/healthz")
def health():

    uptime = int(

        (

            datetime.utcnow()

            - SERVER_START_TIME

        ).total_seconds()

    )

    return {

        "status": "ok",

        "uptime_seconds": uptime,

        "contexts_loaded": store.get_counts()

    }

@app.get("/v1/metadata")
def metadata():

    return {

        "team_name": "PeakyBlends",

        "team_members": [

            "Jitesh Jhamnani"

        ],

        "version": "1.0.0",

        "model": "gemini-2.5-flash"

    }

@app.post("/v1/context")
def context(request: dict):

    result, status = store.add_context(

        request

    )

    return JSONResponse(

        status_code=status,

        content=result

    )

# ==========================================================
# Tick Endpoint
# ==========================================================

@app.post("/v1/tick")
def tick(request: dict):

    try:

        actions = composer.tick(request)

        return {

            "actions": actions

        }

    except Exception as e:

        traceback.print_exc()

        return JSONResponse(

            status_code=500,

            content={

                "error": str(e)

            }

        )
    # ==========================================================
# Reply Endpoint
# ==========================================================

@app.post("/v1/reply")
def reply(request: dict):

    
    try:

        response = composer.reply(

            request

        )

        return response

    except Exception as e:

        return JSONResponse(

            status_code=500,

            content={

                "error": str(e)

            }

        )
    
