import threading
import os
import tempfile
from flask import Blueprint, request, flash, redirect, url_for, render_template, jsonify
from flask_babel import gettext as _
from pikaraoke.lib.current_app import get_karaoke_instance
from pikaraoke import import_bookmark

import_songs_bp = Blueprint("import_songs", __name__)

@import_songs_bp.route("/import", methods=["GET"])
def import_page():
    return render_template("import.html")

@import_songs_bp.route("/import/youtube_playlist", methods=["POST"])
def import_youtube_playlist():
    k = get_karaoke_instance()
    d = request.form.to_dict()
    playlist_url = d["playlist_url"]
    user = d["playlist-added-by"]
    if "queue" in d and d["queue"] == "on":
        queue = True
    else:
        queue = False
    if not playlist_url:
        flash(_("No playlist URL provided."), "is-danger")
        return redirect(url_for("import_songs.import_page"))

    # download in the background since this can take a few minutes
    t = threading.Thread(target=k.download_video_playlist, args=[playlist_url, queue, user])
    t.daemon = True
    t.start()

    flash(_("Started downloading YouTube playlist. This may take a while."), "is-info")
    return redirect(url_for("import_songs.import_page"))

@import_songs_bp.route("/import/bookmark_upload", methods=["POST"])
def bookmark_upload():
    if 'bookmark_file' not in request.files:
        return {"success": False, "message": "No file part"}
    file = request.files['bookmark_file']
    if file.filename == '':
        return {"success": False, "message": "No selected file"}

    tmp_dir = tempfile.mkdtemp()
    file_path = os.path.join(tmp_dir, file.filename)
    file.save(file_path)

    try:
        bookmarks = import_bookmark.parse(file_path)
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        try:
            os.remove(file_path)
            os.rmdir(tmp_dir)
        except Exception:
            pass

    return jsonify({"success": True, "bookmarks": bookmarks})

@import_songs_bp.route("/import/bookmark_import", methods=["POST"])
def bookmark_import():
    data = request.get_json()
    folder = data.get("folder")
    user = data.get("user", "")
    queue = data.get("queue", False)

    if not folder:
        return {"success": False, "message": "No folder selected"}

    k = get_karaoke_instance()

    def background_import():
        def collect_urls(node):
            urls = []
            if isinstance(node, list):
                for item in node:
                    urls.extend(collect_urls(item))
            elif isinstance(node, dict):
                if node.get('type') == 'bookmark' and node.get('url', '').startswith('https://www.youtube.com/'):
                    urls.append(node['url'])
                for child in node.get('children', []):
                    urls.extend(collect_urls(child))
            return urls

        urls = collect_urls(folder)
        for url in urls:
            k.download_video(url, queue, user)

    t = threading.Thread(target=background_import)
    t.daemon = True
    t.start()


    return {"success": True, "message": "Started importing bookmarks."}
