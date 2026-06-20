import os
import requests
import uuid
import mimetypes

BLOB_ENDPOINT = "https://blob.vercel-storage.com"
ALLOWED_EXTENSIONS = {'mp4', 'mov', 'avi', 'mkv', 'webm', 'wmv', 'flv', 'm4v'}


def download_from_blob(blob_url: str, save_dir: str) -> str | None:
    try:
        resp = requests.get(blob_url, stream=True, timeout=120)
        if resp.status_code != 200:
            return None

        content_type = (resp.headers.get('content-type', '') or '').lower()
        ext = '.mp4'
        if 'quicktime' in content_type:
            ext = '.mov'
        elif 'webm' in content_type:
            ext = '.webm'
        elif 'x-msvideo' in content_type or 'avi' in content_type:
            ext = '.avi'
        elif 'matroska' in content_type:
            ext = '.mkv'
        elif 'x-ms-wmv' in content_type:
            ext = '.wmv'
        elif 'x-flv' in content_type or 'flv' in content_type:
            ext = '.flv'

        filename = f"{uuid.uuid4()}{ext}"
        local_path = os.path.join(save_dir, filename)

        with open(local_path, 'wb') as f:
            for chunk in resp.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        if os.path.getsize(local_path) < 1000:
            os.remove(local_path)
            return None

        return local_path
    except Exception:
        return None


def upload_to_blob(local_path: str, content_type: str | None = None) -> str | None:
    token = os.environ.get('BLOB_READ_WRITE_TOKEN')
    if not token:
        return None

    if content_type is None:
        content_type, _ = mimetypes.guess_type(local_path)
        if not content_type:
            content_type = 'video/mp4'

    filename = os.path.basename(local_path)
    pathname = f"results/{uuid.uuid4()}_{filename}"

    try:
        with open(local_path, 'rb') as f:
            resp = requests.put(
                f"{BLOB_ENDPOINT}/{pathname}",
                data=f,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": content_type,
                    "x-blob-add-random-suffix": "1",
                },
                timeout=300,
            )

        if resp.status_code == 200:
            data = resp.json()
            return data.get("url")

        return None
    except Exception:
        return None
