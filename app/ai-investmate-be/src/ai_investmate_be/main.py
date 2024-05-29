from dotenv import load_dotenv

load_dotenv()
from fastapi import FastAPI  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402

from ai_investmate_be.routers import chat, file_ops, kg  # noqa: E402

app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router)
app.include_router(file_ops.router)
app.include_router(kg.router)


@app.get("/")
async def health():
    return {"health": "OK"}
