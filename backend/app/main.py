from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.api.v1.endpoints import chat, audio, openai_compat, web
import os

app = FastAPI(title="ESP32-S3 AI Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for audio
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(chat.router, prefix="/api/v1/chat", tags=["Chat"])
app.include_router(audio.router, prefix="/api/v1/audio", tags=["Audio"])
app.include_router(openai_compat.router, prefix="/api/v1/openai", tags=["OpenAI Compat"])
app.include_router(web.router, prefix="", tags=["Web UI"])

import asyncio
from app.services.wyoming_server import start_wyoming_server

@app.on_event("startup")
async def startup_event():
    # Khởi chạy Wyoming Server ngầm khi FastAPI khởi động
    asyncio.create_task(start_wyoming_server(host="0.0.0.0", port=10500))
