import os
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

import requests
from fastapi import FastAPI, UploadFile, File, Form, Query, HTTPException, Header
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles


YANDEX_GEOCODER_API_KEY = "f2965824-94af-415c-90ca-19aecf89f23a"

BASE_DIR = Path(__file__).resolve().parent
WEB_DIR = BASE_DIR / "webapp"
DATA_DIR = BASE_DIR / "data"
UPLOADS_DIR = DATA_DIR / "uploads"
DATA_DIR.mkdir(exist_ok=True)
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

SUBMISSIONS_FILE = DATA_DIR / "submissions.jsonl"
ARTS_FILE = DATA_DIR / "arts.json"
app = FastAPI()


app.mount("/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")
app.mount("/static", StaticFiles(directory=str(WEB_DIR)), name="static")



def append_jsonl(obj: Dict[str, Any], path: Path) -> None:
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")


def read_last_jsonl(path: Path, limit: int = 30) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()
    out = []
    for line in lines[-limit:]:
        if not line.strip():
            continue
        out.append(json.loads(line))
    return out[::-1]

def read_all_jsonl(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        out.append(json.loads(line))
    return out


def rewrite_jsonl(items: List[Dict[str, Any]], path: Path) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        for obj in items:
            f.write(json.dumps(obj, ensure_ascii=False) + "\n")
    tmp.replace(path)

def ensure_ids_in_jsonl(path: Path) -> int:
    items = read_all_jsonl(path)
    changed = 0
    for it in items:
        if not isinstance(it, dict):
            continue
        if not it.get("id"):
            it["id"] = uuid.uuid4().hex
            changed += 1
    if changed:
        rewrite_jsonl(items, path)
    return changed

def require_admin(x_admin_token: Optional[str]) -> None:
    expected = os.getenv("ADMIN_TOKEN", "").strip()
    if not expected:
        raise HTTPException(status_code=500, detail="ADMIN_TOKEN is not set on server")
    if not x_admin_token or x_admin_token.strip() != expected:
        raise HTTPException(status_code=401, detail="Invalid admin token")

def safe_delete_upload(url: str) -> None:
    if not url:
        return

    if not url.startswith("/uploads/"):
        return
    rel = url[len("/uploads/"):]
    p = UPLOADS_DIR / rel
    try:
        if p.exists() and p.is_file():
            p.unlink()
    except Exception:
        pass

def save_upload(upload: UploadFile, subdir: str) -> str:
    ext = Path(upload.filename or "").suffix.lower() or ""
    safe_name = f"{uuid.uuid4().hex}{ext}"
    dst_dir = UPLOADS_DIR / subdir
    dst_dir.mkdir(parents=True, exist_ok=True)
    dst = dst_dir / safe_name
    with dst.open("wb") as f:
        f.write(upload.file.read())
    return f"/uploads/{subdir}/{safe_name}"


def make_address(city: str, district: str, street: str) -> str:
    return ", ".join([x for x in [city, district, street] if x])



@app.get("/", response_class=HTMLResponse)
def index():
    html_path = WEB_DIR / "index.html"
    html = html_path.read_text(encoding="utf-8")

    key = os.getenv("YANDEX_GEOCODER_API_KEY", "").strip()
    if not key:
        return html


    ymaps_src = f"https://api-maps.yandex.ru/2.1/?apikey={key}&lang=ru_RU"
    html = html.replace(
        '<script id="ymapsScript" src=""></script>',
        f'<script id="ymapsScript" src="{ymaps_src}"></script>'
    )
    return html
@app.get("/api/geocode")
def api_geocode(q: str = Query(..., min_length=2)):
    if not YANDEX_GEOCODER_API_KEY:
        raise HTTPException(status_code=500, detail="YANDEX_GEOCODER_API_KEY is not set")

    url = "https://geocode-maps.yandex.ru/1.x/"
    params = {
        "apikey": YANDEX_GEOCODER_API_KEY,
        "geocode": q,
        "format": "json",
        "lang": "ru_RU",
        "results": 1,
    }

    try:
        r = requests.get(url, params=params, timeout=10)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Geocoder request failed: {e}")


    if r.status_code != 200:
        raise HTTPException(
            status_code=502,
            detail=f"Geocoder status={r.status_code}, body={r.text[:500]}"
        )

    data = r.json()
    members = data.get("response", {}).get("GeoObjectCollection", {}).get("featureMember", [])
    if not members:
        return {"found": False}

    obj = members[0]["GeoObject"]
    lon_str, lat_str = obj["Point"]["pos"].split()
    lon = float(lon_str)
    lat = float(lat_str)
    addr = obj.get("metaDataProperty", {}).get("GeocoderMetaData", {}).get("text", "")

    return {"found": True, "lat": lat, "lon": lon, "address": addr}



@app.post("/api/submit")
async def submit(
    is_own_work: str = Form(...),
    author_nickname: str = Form(...),
    city: str = Form(...),
    district: str = Form(...),
    street_and_house: str = Form(""),
    work_type: str = Form(...),
    lat: Optional[str] = Form(None),
    lon: Optional[str] = Form(None),

    material: str = Form(""),
    production_time: str = Form(""),
    emotion: str = Form(""),
    extra: str = Form(""),
    initData: str = Form(""),

    photo: UploadFile = File(...),
    video: Optional[UploadFile] = File(None),
):
    created_at = datetime.utcnow().isoformat()

    photo_url = save_upload(photo, "photos")

    video_url = ""
    if video is not None and video.filename:
        video_url = save_upload(video, "videos")


    lat_f = float(lat) if lat not in (None, "", "nan") else None
    lon_f = float(lon) if lon not in (None, "", "nan") else None

    obj = {
        "id": uuid.uuid4().hex,
        "created_at": created_at,
        "is_own_work": (is_own_work.lower() == "true"),
        "author_nickname": author_nickname,
        "city": city,
        "district": district,
        "street_and_house": street_and_house,
        "address": make_address(city, district, street_and_house),
        "work_type": work_type,
        "lat": lat_f,
        "lon": lon_f,
        "material": material,
        "production_time": production_time,
        "emotion": emotion,
        "extra": extra,
        "photo_url": photo_url,
        "video_url": video_url,
        "initData": initData,
    }

    append_jsonl(obj, SUBMISSIONS_FILE)
    return obj



@app.get("/api/submissions")
def get_submissions(limit: int = 30):
    return read_last_jsonl(SUBMISSIONS_FILE, limit=limit)

@app.post("/api/admin/migrate_submissions_ids")
def admin_migrate_submissions_ids(
    x_admin_token: Optional[str] = Header(default=None, alias="X-Admin-Token"),
):
    require_admin(x_admin_token)
    changed = ensure_ids_in_jsonl(SUBMISSIONS_FILE)
    return {"ok": True, "added_ids": changed}

@app.delete("/api/admin/submissions/{sub_id}")
def admin_delete_submission(
    sub_id: str,
    x_admin_token: Optional[str] = Header(default=None, alias="X-Admin-Token"),
):
    require_admin(x_admin_token)

    items = read_all_jsonl(SUBMISSIONS_FILE)
    if not items:
        return {"ok": True, "deleted": 0}

    kept = []
    deleted_obj = None

    for it in items:
        if it.get("id") == sub_id and deleted_obj is None:
            deleted_obj = it
            continue
        kept.append(it)

    if deleted_obj is None:
        raise HTTPException(status_code=404, detail="submission not found")


    safe_delete_upload(deleted_obj.get("photo_url", ""))
    safe_delete_upload(deleted_obj.get("video_url", ""))

    rewrite_jsonl(kept, SUBMISSIONS_FILE)
    return {"ok": True, "deleted": 1, "id": sub_id}

@app.get("/api/arts")
def get_arts():
    items = read_last_jsonl(SUBMISSIONS_FILE, limit=500)
    out = []
    for it in items:
        if it.get("lat") is None or it.get("lon") is None:
            continue


        extra_raw = it.get("extra")
        if isinstance(extra_raw, dict):
            extra_obj = extra_raw
        else:
            try:
                extra_obj = json.loads(extra_raw) if extra_raw else {}
            except Exception:
                extra_obj = {}

        out.append({
            "lat": it["lat"],
            "lon": it["lon"],

            "work_type": it.get("work_type", ""),
            "author_nickname": it.get("author_nickname", ""),
            "address": it.get("address", ""),

            "city": it.get("city", ""),
            "district": it.get("district", ""),
            "street_and_house": it.get("street_and_house", ""),

            "material": it.get("material", ""),
            "production_time": it.get("production_time", ""),
            "emotion": it.get("emotion", ""),

            "photo_url": it.get("photo_url", ""),
            "video_url": it.get("video_url", ""),

            "is_own_work": it.get("is_own_work", None),
            "created_at": it.get("created_at", ""),
            "source": it.get("source", ""),
            "username": it.get("username", ""),
            "chat_id": it.get("chat_id", None),
            "user_id": it.get("user_id", None),

            "extra": extra_obj,
        })
    return out
