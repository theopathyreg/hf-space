#!/usr/bin/env python3
"""Hugging Face 大文件上传核心逻辑

供本地 HTTPS 服务器和 Vercel serverless 函数复用。
"""

import io
from typing import Optional

from huggingface_hub import HfApi


def upload_to_hf(
    file_bytes: bytes,
    filename: str,
    repo: str,
    path: str,
    token: str,
    commit_message: Optional[str] = None,
) -> dict:
    """上传文件到 Hugging Face 数据集仓库

    使用 huggingface_hub 的 upload_file，底层自动走 XET 协议，
    支持大文件（>1MB，如 5MB+ 的 MP3）。

    Args:
        file_bytes: 文件二进制内容
        filename: 原始文件名
        repo: HF 仓库 ID，如 "username/dataset"
        path: 文件在仓库中的路径，如 "attachments/xxx.mp3"
        token: HF 访问令牌
        commit_message: Git 提交信息，可选

    Returns:
        包含 success/oid/commit_url 的字典

    Raises:
        Exception: 上传失败时抛出
    """
    api = HfApi()
    file_obj = io.BytesIO(file_bytes)
    result = api.upload_file(
        path_or_fileobj=file_obj,
        path_in_repo=path,
        repo_id=repo,
        repo_type="dataset",
        token=token,
        commit_message=commit_message or f"upload {filename}",
    )
    return {
        "success": True,
        "oid": result.oid,
        "commit_url": result.commit_url,
    }


def delete_from_hf(repo: str, path: str, token: str, commit_message: Optional[str] = None) -> dict:
    """从 Hugging Face 数据集仓库删除文件

    使用 huggingface_hub 的 delete_file，底层自动走 commit API。

    Args:
        repo: HF 仓库 ID，如 "username/dataset"
        path: 文件在仓库中的路径，如 "attachments/xxx.mp3"
        token: HF 访问令牌
        commit_message: Git 提交信息，可选

    Returns:
        包含 success/oid/commit_url 的字典

    Raises:
        Exception: 删除失败时抛出
    """
    api = HfApi()
    result = api.delete_file(
        path_in_repo=path,
        repo_id=repo,
        repo_type="dataset",
        token=token,
        commit_message=commit_message or f"delete {path}",
    )
    return {
        "success": True,
        "oid": result.oid,
        "commit_url": result.commit_url,
    }
