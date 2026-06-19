import os
import uuid
import requests
import numpy as np
import threading
import concurrent.futures
from urllib.parse import urlparse
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = '/tmp/uploads' if os.environ.get('VERCEL') else os.path.join(os.path.dirname(__file__), 'uploads')
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
        import cv2, base64
        from detection_engine import DetectionEngine

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

def _try_ydl(video_url: str, filepath: str, opts_extra: dict) -> bool:
    import yt_dlp

    base = {
        'format': 'best[ext=mp4]/best[height<=1080]/worst',
        'quiet': True, 'no_warnings': True,
        'outtmpl': filepath,
        'max_filesize': 500 * 1024 * 1024, 'socket_timeout': 15,
        'retries': 2, 'geo_bypass': True,
    }
    base.update(opts_extra)
    os.remove(filepath) if os.path.exists(filepath) else None

    def _run():
        with yt_dlp.YoutubeDL(base) as ydl:
            ydl.download([video_url])

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        fut = pool.submit(_run)
        try:
            fut.result(timeout=120)
            return os.path.exists(filepath) and os.path.getsize(filepath) >= 1000
        except Exception:
            return False

def _ydl_strategies():
    s = [{}, {'extractor_args': {'tiktok': {'app_api': ['1']}}}]
    s.append({'extractor_args': {'tiktok': {'app_api': ['1'], 'api_hostname': ['api16-normal-c-useast1a.tiktokv.com']}}})
    for browser in ['chrome', 'brave', 'edge', 'opera', 'firefox']:
        try:
            s.append({'cookiesfrombrowser': (browser,)})
            s.append({'cookiesfrombrowser': (browser,), 'extractor_args': {'tiktok': {'app_api': ['1']}}})
        except Exception:
            pass
    return s

def _run_analysis(filepath: str):
    import cv2, base64
    from detection_engine import DetectionEngine

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

        # TikTok known-blocked: fast-fail with clear message
        domain = urlparse(video_url).netloc.lower()
        if any(d in domain for d in ('tiktok.com', 'vm.tiktok.com')):
            return jsonify({"error": "TikTok does not allow automated video downloads from this server. Please save the video and use the Upload File button instead."}), 400

        # Known platform → yt-dlp first
        if _is_platform_url(video_url) or not is_direct_video:
            success = any(_try_ydl(video_url, filepath, s) for s in _ydl_strategies())
            if success and os.path.exists(filepath) and os.path.getsize(filepath) >= 1000:
                return _run_analysis(filepath)
            os.remove(filepath) if os.path.exists(filepath) else None
            return jsonify({"error": "Could not download video from this platform. Download the file and upload directly."}), 400

        # Direct video URL → try requests, fall back to yt-dlp
        resp = requests.get(video_url, stream=True, timeout=60, allow_redirects=True,
                            headers={"User-Agent": "Mozilla/5.0"})
        if resp.status_code != 200:
            resp.close()
            success = any(_try_ydl(video_url, filepath, s) for s in _ydl_strategies())
            if success and os.path.exists(filepath) and os.path.getsize(filepath) >= 1000:
                return _run_analysis(filepath)
            return jsonify({"error": f"Failed to download video (HTTP {resp.status_code})"}), 400

        content_type = (resp.headers.get('content-type', '') or '').lower()
        if 'text/html' in content_type:
            resp.close()
            success = any(_try_ydl(video_url, filepath, s) for s in _ydl_strategies())
            if not success:
                return jsonify({"error": "Could not download video from this platform. Download the file and upload directly."}), 400
            if not os.path.exists(filepath) or os.path.getsize(filepath) < 1000:
                os.remove(filepath)
                return jsonify({"error": "Downloaded file is too small or invalid"}), 400
            return _run_analysis(filepath)

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

@app.errorhandler(500)
def handle_500(e):
    return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.errorhandler(Exception)
def handle_all(e):
    return jsonify({"error": str(e)}), 500

@app.route('/api/compare', methods=['POST'])
def compare_videos_endpoint():
    orig_path = edit_path = None
    try:
        if 'original' not in request.files or 'edited' not in request.files:
            return jsonify({"error": "Both original and edited video files required"}), 400
        orig_file = request.files['original']
        edit_file = request.files['edited']
        if orig_file.filename == '' or edit_file.filename == '':
            return jsonify({"error": "Both files must be selected"}), 400
        for f in [orig_file, edit_file]:
            if not allowed_file(f.filename):
                return jsonify({"error": f"File type not supported for {f.filename}"}), 400
        uid = str(uuid.uuid4())
        orig_path = os.path.join(UPLOAD_FOLDER, f"{uid}_orig_{secure_filename(orig_file.filename)}")
        edit_path = os.path.join(UPLOAD_FOLDER, f"{uid}_edit_{secure_filename(edit_file.filename)}")
        orig_file.save(orig_path)
        edit_file.save(edit_path)
        from detection_engine import compare_videos
        result = compare_videos(orig_path, edit_path)
        result["status"] = "success"
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        for p in [orig_path, edit_path]:
            if p and os.path.exists(p):
                os.remove(p)

@app.route('/api/apply-edits', methods=['POST'])
def apply_edits_endpoint():
    orig_path = ref_path = out_path = None
    try:
        if 'original' not in request.files or 'reference' not in request.files:
            return jsonify({"error": "Both original and reference video files required"}), 400
        orig_file = request.files['original']
        ref_file = request.files['reference']
        if orig_file.filename == '' or ref_file.filename == '':
            return jsonify({"error": "Both files must be selected"}), 400
        for f in [orig_file, ref_file]:
            if not allowed_file(f.filename):
                return jsonify({"error": f"File type not supported for {f.filename}"}), 400
        uid = str(uuid.uuid4())
        orig_path = os.path.join(UPLOAD_FOLDER, f"{uid}_orig_{secure_filename(orig_file.filename)}")
        ref_path = os.path.join(UPLOAD_FOLDER, f"{uid}_ref_{secure_filename(ref_file.filename)}")
        out_path = os.path.join(UPLOAD_FOLDER, f"{uid}_output.mp4")
        orig_file.save(orig_path)
        ref_file.save(ref_path)

        from detection_engine import compare_videos
        from edit_applier import apply_edits_to_video

        result = compare_videos(orig_path, ref_path)
        adjustments = result.get("adjustments", {})

        success = apply_edits_to_video(orig_path, out_path, adjustments)
        if not success:
            return jsonify({"error": "Failed to process video"}), 500

        import base64
        with open(out_path, 'rb') as f:
            video_b64 = base64.b64encode(f.read()).decode('utf-8')

        return jsonify({
            "status": "success",
            "adjustments": adjustments,
            "filters": result.get("filters", []),
            "effects": result.get("effects", []),
            "video_data": video_b64,
            "video_mime": "video/mp4",
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        for p in [orig_path, ref_path, out_path]:
            if p and os.path.exists(p):
                try:
                    os.remove(p)
                except Exception:
                    pass

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "version": "1.0.0"})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True, threaded=True)
