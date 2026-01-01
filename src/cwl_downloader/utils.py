"""
Utility functions for cwl_downloader
"""

from datetime import datetime
from typing import Optional
import re


def parse_datetime(datetime_str: str) -> Optional[datetime]:
    """
    Parse datetime string in the format 'YYYY-MM-DD HH:MM'

    Args:
        datetime_str: Datetime string to parse

    Returns:
        datetime object if parsing succeeds, None otherwise
    """
    try:
        return datetime.strptime(datetime_str.strip(), "%Y-%m-%d %H:%M")
    except ValueError:
        return None


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename by replacing invalid characters

    Args:
        filename: Original filename

    Returns:
        Sanitized filename safe for file system
    """
    # Replace slashes with underscores
    filename = filename.replace("/", "_")
    # Replace colons with hyphens
    filename = filename.replace(":", "-")
    # Remove other potentially problematic characters
    filename = re.sub(r'[<>:"|?*]', "_", filename)
    return filename


def format_datetime_for_filename(dt: datetime) -> str:
    """
    Format datetime for use in filename

    Args:
        dt: datetime object

    Returns:
        Formatted datetime string (YYYY-MM-DD_HH-MM)
    """
    return dt.strftime("%Y-%m-%d_%H-%M")


# Error messages
ERROR_MESSAGES = {
    "no_aws_credentials": "AWS認証情報が設定されていません。環境変数を確認してください。",
    "log_group_not_found": "ロググループ '{log_group}' が見つかりません。",
    "invalid_datetime_format": "日時のフォーマットが正しくありません。YYYY-MM-DD HH:MM の形式で入力してください。",
    "start_after_end": "開始日時は終了日時より前である必要があります。",
    "api_error": "AWS API呼び出しでエラーが発生しました: {error}",
    "io_error": "ファイル操作でエラーが発生しました: {error}",
}


def get_error_message(error_key: str, **kwargs: str) -> str:
    """
    Get error message by key with optional formatting

    Args:
        error_key: Key to look up error message
        **kwargs: Format parameters for the error message

    Returns:
        Formatted error message
    """
    message = ERROR_MESSAGES.get(error_key, "不明なエラーが発生しました。")
    if kwargs:
        message = message.format(**kwargs)
    return message
