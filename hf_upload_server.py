#!/usr/bin/env python3
"""Hugging Face 文件上传/下载服务器 (HF Space 部署版)

用于 HF Spaces Docker 部署，H5 网页可通过 /upload 和 /download 访问。

服务器不预设任何 HF Token，由 H5 前端每次请求时直接传入。

启动：
    python app.py
"""

import os
import sys

# 确保可以导入同目录下的 hf_upload_core
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import requests
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from hf_upload_core import delete_from_hf, upload_to_hf

app = Flask(__name__)
CORS(app, resources={r"/upload": {"origins": "*"}, r"/download": {"origins": "*"}, r"/delete": {"origins": "*"}})


@app.route("/upload", methods=["POST", "OPTIONS"])
def upload():
    if request.method == "OPTIONS":
        return jsonify({}), 200

    file = request.files.get("file")
    repo = request.form.get("repo")
    path = request.form.get("path")
    token = request.form.get("token")

    if not file:
        return jsonify({"error": "missing file"}), 400
    if not repo:
        return jsonify({"error": "missing repo"}), 400
    if not path:
        return jsonify({"error": "missing path"}), 400
    if not token:
        return jsonify({"error": "missing token"}), 400

    try:
        file_bytes = file.read()
        result = upload_to_hf(
            file_bytes=file_bytes,
            filename=file.filename or "unnamed",
            repo=repo,
            path=path,
            token=token,
        )
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/download", methods=["GET", "OPTIONS"])
def download():
    if request.method == "OPTIONS":
        return jsonify({}), 200

    url = request.args.get("url")
    token = request.args.get("token")

    if not url:
        return jsonify({"error": "missing url"}), 400
    if not token:
        return jsonify({"error": "missing token"}), 400

    try:
        resp = requests.get(
            url,
            headers={"Authorization": f"Bearer {token}"},
            stream=True,
            timeout=(10, 60),
        )

        def generate():
            for chunk in resp.iter_content(chunk_size=8192):
                if chunk:
                    yield chunk

        headers = {}
        for key in ["content-type", "content-disposition", "content-length", "accept-ranges", "cache-control"]:
            v = resp.headers.get(key)
            if v:
                headers[key] = v
        headers["Access-Control-Allow-Origin"] = "*"

        return Response(generate(), status=resp.status_code, headers=headers)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/delete", methods=["POST", "OPTIONS"])
def delete():
    if request.method == "OPTIONS":
        return jsonify({}), 200

    repo = request.form.get("repo")
    path = request.form.get("path")
    token = request.form.get("token")

    if not repo:
        return jsonify({"error": "missing repo"}), 400
    if not path:
        return jsonify({"error": "missing path"}), 400
    if not token:
        return jsonify({"error": "missing token"}), 400

    try:
        result = delete_from_hf(repo=repo, path=path, token=token)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    # HF Spaces 内部服务必须监听 7860 端口
    app.run(host="0.0.0.0", port=7860, debug=False)
