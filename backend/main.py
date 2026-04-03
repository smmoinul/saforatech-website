from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
import os, json

app = FastAPI(title="SaforaTech Website API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── SCHEMAS ─────────────────────────────────────────────────────────────────

class ContactForm(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    service: Optional[str] = None
    message: str

class NewsletterForm(BaseModel):
    email: EmailStr

# ─── SIMPLE FILE-BASED STORAGE (replace with DB in production) ───────────────

CONTACTS_FILE = "contacts.json"
NEWSLETTER_FILE = "newsletter.json"

def load_json(path):
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return []

def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=str)

# ─── ROUTES ──────────────────────────────────────────────────────────────────

@app.post("/api/contact")
async def contact(data: ContactForm):
    contacts = load_json(CONTACTS_FILE)
    entry = {
        "id": len(contacts) + 1,
        "name": data.name,
        "email": data.email,
        "phone": data.phone,
        "service": data.service,
        "message": data.message,
        "created_at": datetime.now().isoformat(),
        "status": "new"
    }
    contacts.append(entry)
    save_json(CONTACTS_FILE, contacts)

    # TODO: Send email notification via SendGrid/SMTP
    # send_email(to="hello@saforatech.com", subject=f"New Contact: {data.name}", body=...)

    return {"success": True, "message": "Message received. We'll reply within 24 hours."}


@app.post("/api/newsletter")
async def newsletter(data: NewsletterForm):
    subs = load_json(NEWSLETTER_FILE)
    if any(s["email"] == data.email for s in subs):
        raise HTTPException(400, "Already subscribed")
    subs.append({"email": data.email, "subscribed_at": datetime.now().isoformat()})
    save_json(NEWSLETTER_FILE, subs)
    return {"success": True, "message": "Subscribed successfully!"}


@app.get("/api/contacts")
async def list_contacts(secret: str = ""):
    # Simple admin protection — use proper auth in production
    if secret != os.getenv("ADMIN_SECRET", "saforatech-admin-2025"):
        raise HTTPException(403, "Forbidden")
    return load_json(CONTACTS_FILE)


@app.get("/api/health")
async def health():
    return {"status": "healthy", "service": "SaforaTech Website"}


# Serve static frontend files
if os.path.exists("../frontend"):
    app.mount("/", StaticFiles(directory="../frontend", html=True), name="static")

@app.get("/")
async def root():
    return FileResponse("../frontend/index.html")
