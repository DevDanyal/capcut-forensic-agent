import os
import sys
import re
import uuid
import cv2
import base64
import json
import requests
import numpy as np
import yt_dlp
import threading
import concurrent.futures
from urllib.parse import urlparse
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
from detection_engine import DetectionEngine

app = Flask(__name__)
CORS(app)

IS_VERCEL = os.environ.get('VERCEL', '0') == '1'
UPLOAD_FOLDER = '/tmp/uploads' if IS_VERCEL else os.path.join(os.path.dirname(__file__), 'uploads')
ALLOWED_EXTENSIONS = {'mp4', 'mov', 'avi', 'mkv', 'webm', 'wmv', 'flv', 'm4v'}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024 * 1024

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/api/analyze', methods=['POST'])
def analyze_video():
    if 'video' not in request.files:
        return jsonify({"error": "No video file provided"}), 400

    file = request.files['video']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": f"File type not supported. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"}), 400

    filename = secure_filename(file.filename)
    unique_id = str(uuid.uuid4())
    safe_filename = f"{unique_id}_{filename}"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], safe_filename)
    file.save(filepath)

    try:
        engine = DetectionEngine(filepath, sample_interval=0.5, max_frames=300)
        if not engine.extract_frames():
            err_msg = getattr(engine, '_error', 'Could not extract frames from video')
            os.remove(filepath)
            return jsonify({"error": err_msg}), 400

        analysis = engine.analyze()

        frames_b64 = []
        for ts, frame in engine.get_all_frames()[:60]:
            _, buffer = cv2.imencode('.jpg', cv2.cvtColor(frame, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 60])
            b64 = base64.b64encode(buffer).decode('utf-8')
            frames_b64.append({
                "time": round(ts, 2),
                "data": f"data:image/jpeg;base64,{b64}",
            })

        result = {
            "analysis": analysis,
            "frames": frames_b64,
            "status": "success",
        }

        os.remove(filepath)
        return jsonify(result)

    except Exception as e:
        if os.path.exists(filepath):
            os.remove(filepath)
        return jsonify({"error": str(e)}), 500

PLATFORM_DOMAINS = {
    'youtube.com', 'youtu.be', 'vimeo.com', 'dailymotion.com', 'dai.ly',
    'twitch.tv', 'twitter.com', 'x.com', 'reddit.com', 'redd.it',
    'instagram.com', 'instagr.am', 'facebook.com', 'fb.com', 'fb.watch',
    'tiktok.com', 'vm.tiktok.com', 'ted.com', 'dailymail.co.uk',
    'liveleak.com', 'rumble.com', 'streamable.com', 'vid.me',
}

def _try_ydl(video_url: str, filepath: str, opts_extra: dict) -> tuple:
    base = {
        'format': 'best[ext=mp4]/worst',
        'quiet': True, 'no_warnings': True,
        'outtmpl': filepath,
        'max_filesize': 500 * 1024 * 1024, 'socket_timeout': 30,
        'retries': 3, 'geo_bypass': True,
        'http_headers': {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'},
    }
    base.update(opts_extra)
    os.remove(filepath) if os.path.exists(filepath) else None

    def _run():
        with yt_dlp.YoutubeDL(base) as ydl:
            ydl.download([video_url])

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        fut = pool.submit(_run)
        try:
            fut.result(timeout=180)
            ok = os.path.exists(filepath) and os.path.getsize(filepath) >= 1000
            return (ok, "" if ok else "Downloaded file is too small or invalid")
        except concurrent.futures.TimeoutError:
            return (False, "Download timed out after 180 seconds")
        except Exception as e:
            msg = str(e)
            if not msg:
                msg = getattr(e, 'msg', 'Unknown yt-dlp error')
            return (False, msg)

def _ydl_strategies():
    ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
    yt_web = {'extractor_args': {'youtube': {'player_client': ['web']}}}
    yt_android = {'extractor_args': {'youtube': {'player_client': ['android']}}}
    yt_mweb = {'extractor_args': {'youtube': {'player_client': ['mweb', 'web']}}}
    yt_skip = {'extractor_args': {'youtube': {'player_skip': ['webpage', 'configs']}}}
    return [
        yt_web,
        {**yt_web, 'format': 'worst'},
        yt_android,
        {**yt_android, 'format': 'worst'},
        yt_mweb,
        {**yt_mweb, 'format': 'worst'},
        yt_skip,
        {**yt_skip, 'format': 'worst'},
        {'format': 'worst'},
        {'format': 'best[ext=mp4]'},
        {'http_headers': {'User-Agent': ua}, 'format': 'worst'},
        {'ignore_no_formats_error': True, 'format': 'worst'},
    ]

def _run_analysis(filepath: str):
    engine = DetectionEngine(filepath, sample_interval=0.5, max_frames=300)
    if not engine.extract_frames():
        err_msg = getattr(engine, '_error', 'Could not extract frames from video')
        os.remove(filepath)
        return jsonify({"error": err_msg}), 400

    analysis = engine.analyze()

    frames_b64 = []
    for ts, frame in engine.get_all_frames()[:60]:
        _, buffer = cv2.imencode('.jpg', cv2.cvtColor(frame, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 60])
        b64 = base64.b64encode(buffer).decode('utf-8')
        frames_b64.append({"time": round(ts, 2), "data": f"data:image/jpeg;base64,{b64}"})

    os.remove(filepath)
    return jsonify({"analysis": analysis, "frames": frames_b64, "status": "success"})

def _extract_youtube_id(url: str) -> str:
    m = re.search(r'(?:v=|/v/|youtu\.be/|/embed/|/shorts/)([a-zA-Z0-9_-]{11})', url)
    return m.group(1) if m else None

def _try_youtube_direct(video_url: str, filepath: str) -> tuple:
    video_id = _extract_youtube_id(video_url)
    if not video_id:
        return (False, "Could not extract YouTube video ID")

    clients = [
        ("ANDROID", "19.09.37", "AIzaSyA8eiZmM1FaDVjRy-df2KTyQ_vz_yYM39w"),
        ("ANDROID", "19.08.35", "AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8"),
        ("WEB", "2.20250101.00.00", "AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8"),
        ("WEB", "2.20240101.00.00", "AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8"),
        ("IOS", "19.09.37", "AIzaSyA8eiZmM1FaDVjRy-df2KTyQ_vz_yYM39w"),
        ("IOS", "19.08.35", "AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8"),
        ("TVHTML5_SIMPLY", "7.20250101", "AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8"),
    ]

    for client_name, client_ver, api_key in clients:
        ctx = {"client": {"clientName": client_name, "clientVersion": client_ver, "hl": "en", "gl": "US"}}
        if "ANDROID" in client_name or "IOS" in client_name:
            ctx["client"]["androidSdkVersion"] = 31
        if "TV" in client_name:
            ctx["client"]["clientScreen"] = "WATCH"
        payload = {"videoId": video_id, "context": ctx}

        ua = {
            "ANDROID": "com.google.android.youtube/19.09.37 (Linux; U; Android 14; en_US)",
            "IOS": "com.google.ios.youtube/19.09.37 (iPhone; U; CPU iOS 17_0 like Mac OS X; en_US)",
            "WEB": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            "TVHTML5_SIMPLY": "Mozilla/5.0 (ChromiumStylePlatform; Linux; en_US) AppleWebKit/537.36",
        }.get(client_name, "Mozilla/5.0")

        try:
            resp = requests.post(
                f"https://www.youtube.com/youtubei/v1/player?key={api_key}",
                headers={"User-Agent": ua, "Content-Type": "application/json"},
                json=payload, timeout=30,
            )
        except Exception:
            continue

        if resp.status_code != 200:
            continue

        data = resp.json()
        playability = data.get("playabilityStatus", {})
        if playability.get("status") != "OK":
            continue

        streaming_data = data.get("streamingData", {})
        if not streaming_data:
            continue

        candidates = streaming_data.get("formats", []) + streaming_data.get("adaptiveFormats", [])
        for fmt in candidates:
            mime = fmt.get("mimeType", "")
            if "mp4" not in mime and "webm" not in mime and "3gp" not in mime:
                continue
            direct_url = fmt.get("url")
            if not direct_url:
                cipher = fmt.get("signatureCipher") or fmt.get("cipher", "")
                if cipher:
                    from urllib.parse import parse_qs
                    qs = parse_qs(cipher)
                    direct_url = qs.get("url", [None])[0]
                    sig = qs.get("s", [None])[0]
                    sp = qs.get("sp", ["sig"])[0]
                    if direct_url and sig:
                        direct_url = f"{direct_url}&{sp}={sig}"
            if not direct_url:
                continue

            os.remove(filepath) if os.path.exists(filepath) else None
            try:
                dl = requests.get(direct_url, stream=True, timeout=120,
                    headers={"User-Agent": "Mozilla/5.0", "Referer": "https://www.youtube.com/"})
            except Exception:
                continue
            if dl.status_code != 200:
                continue

            total = 0
            with open(filepath, "wb") as f:
                for chunk in dl.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        total += len(chunk)
                        if total > 500 * 1024 * 1024:
                            break

            if total >= 1000:
                return (True, "")

    return (False, "No downloadable format found from YouTube")

def _is_platform_url(url: str) -> bool:
    try:
        domain = urlparse(url).netloc.lower()
        if domain.startswith('www.'):
            domain = domain[4:]
        return any(pd in domain for pd in PLATFORM_DOMAINS)
    except Exception:
        return False

@app.route('/api/analyze-url', methods=['POST'])
def analyze_video_url():
    data = request.get_json()
    if not data or 'url' not in data:
        return jsonify({"error": "No URL provided"}), 400

    video_url = data['url'].strip()
    if not video_url:
        return jsonify({"error": "Empty URL"}), 400

    try:
        ext = os.path.splitext(video_url.split('?')[0])[1].lower()
        is_direct_video = ext in ['.' + e for e in ALLOWED_EXTENSIONS]

        if not is_direct_video:
            ext = '.mp4'

        unique_id = str(uuid.uuid4())
        safe_filename = f"{unique_id}_from_url{ext}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], safe_filename)

        domain = urlparse(video_url).netloc.lower()
        if any(d in domain for d in ('tiktok.com', 'vm.tiktok.com')):
            return jsonify({"error": "TikTok does not allow automated video downloads from this server. Please save the video and use the Upload File button instead."}), 400

        if _is_platform_url(video_url) or not is_direct_video:
            last_error = ""
            for strategy in _ydl_strategies():
                ok, err = _try_ydl(video_url, filepath, strategy)
                if ok:
                    return _run_analysis(filepath)
                if err:
                    last_error = err
            if "youtube" in video_url or "youtu.be" in video_url:
                ok, err = _try_youtube_direct(video_url, filepath)
                if ok:
                    return _run_analysis(filepath)
                if err:
                    last_error = err
            os.remove(filepath) if os.path.exists(filepath) else None
            return jsonify({"error": f"Could not download video. {last_error}"}), 400

        resp = requests.get(video_url, stream=True, timeout=60, allow_redirects=True,
                            headers={"User-Agent": "Mozilla/5.0"})
        if resp.status_code != 200:
            resp.close()
            last_error = ""
            for strategy in _ydl_strategies():
                ok, err = _try_ydl(video_url, filepath, strategy)
                if ok:
                    return _run_analysis(filepath)
                if err:
                    last_error = err
            return jsonify({"error": f"Failed to download video (HTTP {resp.status_code}). {last_error}"}), 400

        content_type = (resp.headers.get('content-type', '') or '').lower()
        if 'text/html' in content_type:
            resp.close()
            last_error = ""
            for strategy in _ydl_strategies():
                ok, err = _try_ydl(video_url, filepath, strategy)
                if ok:
                    return _run_analysis(filepath)
                if err:
                    last_error = err
            return jsonify({"error": f"Could not download video. {last_error}"}), 400

        total = 0
        with open(filepath, 'wb') as f:
            for chunk in resp.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    total += len(chunk)
                    if total > 500 * 1024 * 1024:
                        os.remove(filepath)
                        return jsonify({"error": "Video too large (max 500MB)"}), 400

        if total < 1000:
            os.remove(filepath)
            return jsonify({"error": "Downloaded file is too small or invalid"}), 400

        return _run_analysis(filepath)

    except Exception as e:
        if os.path.exists(filepath):
            os.remove(filepath)
        return jsonify({"error": str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "version": "1.0.0"})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True, threaded=True)
