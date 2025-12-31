# broll.py
import os, random, requests
from dotenv import load_dotenv
load_dotenv()

PEXELS_KEY = os.getenv("PEXELS_API_KEY")
HEADERS = {"Authorization": PEXELS_KEY}
API = "https://api.pexels.com/videos/search"

os.makedirs("media_cache", exist_ok=True)

# returns list of downloaded file paths (portrait videos when possible)
def fetch_broll(query: str, want: int = 2):
    assert PEXELS_KEY, "Missing PEXELS_API_KEY"
    r = requests.get(API, headers=HEADERS, params={"query": query, "orientation": "portrait", "per_page": 10})
    r.raise_for_status()
    vids = r.json().get("videos", [])
    files = []
    for v in vids[:want]:
        # pick the highest vertical quality link
        vfiles = v.get("video_files", [])
        vfiles.sort(key=lambda x: x.get("height", 0), reverse=True)
        link = vfiles[0]["link"] if vfiles else None
        if not link:
            continue
        name = f"media_cache/{v['id']}_{random.randint(10,99)}.mp4"
        with requests.get(link, stream=True) as s:
            s.raise_for_status()
            with open(name, "wb") as f:
                for chunk in s.iter_content(chunk_size=8192):
                    f.write(chunk)
        files.append(name)
    return files