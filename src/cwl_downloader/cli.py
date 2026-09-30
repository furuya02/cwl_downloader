"""
CLI interface for cwl_downloader
"""

from datetime import datetime
from typing import Tuple, Optional

from .utils import parse_datetime, get_error_message
from .downloader import CloudWatchLogsDownloader


def get_user_input(prompt: str, default: Optional[str] = None) -> str:
    """
    Get user input with optional default value

    Args:
        prompt: Prompt message
        default: Default value if user presses Enter without input

    Returns:
        User input string
    """
    if default:
        full_prompt = f"{prompt} (default: {default})\n> "
    else:
        full_prompt = f"{prompt}\n> "

    user_input = input(full_prompt).strip()

    if not user_input and default:
        return default

    return user_input


def get_datetime_input(prompt: str) -> datetime:
    """
    Get datetime input from user with validation

    Args:
        prompt: Prompt message

    Returns:
        Validated datetime object
    """
    while True:
        datetime_str = get_user_input(prompt)
        dt = parse_datetime(datetime_str)

        if dt is None:
            print(get_error_message("invalid_datetime_format"))
            continue

        return dt


def confirm_settings(
    region: str, log_group: str, start_time: datetime, end_time: datetime
) -> bool:
    """
    Display settings and ask for confirmation

    Args:
        region: AWS region
        log_group: Log group name
        start_time: Start datetime
        end_time: End datetime

    Returns:
        True if user confirms, False otherwise
    """
    print("\nダウンロードする対象は、以下で宜しいでしょうか？\n")
    print(f"region: {region}")
    print(f"log_group: {log_group}")
    print(f"start: {start_time.strftime('%Y-%m-%d %H:%M')}")
    print(f"end: {end_time.strftime('%Y-%m-%d %H:%M')}")
    print("unmask: ON")
    print()

    while True:
        response = input("(y/n)> ").strip().lower()
        if response in ["y", "yes"]:
            return True
        elif response in ["n", "no"]:
            return False
        else:
            print("'y' または 'n' で回答してください。")


def display_progress(
    current: int, total: int, interval_start: datetime, interval_end: datetime
) -> None:
    """
    Display download progress

    Args:
        current: Current interval index
        total: Total number of intervals
        interval_start: Start time of current interval
        interval_end: End time of current interval
    """
    start_str = interval_start.strftime("%Y-%m-%d %H:%M")
    end_str = interval_end.strftime("%H:%M")
    print(f"[{current}/{total}] {start_str} - {end_str} 完了")


def collect_input() -> Tuple[str, str, datetime, datetime]:
    """
    Collect all required input from user

    Returns:
        Tuple of (region, log_group, start_time, end_time)
    """
    # Get region
    region = get_user_input("リージョンを指定してください", default="ap-northeast-1")

    # Get log group
    log_group = get_user_input("ロググループを指定してください")

    # Get start datetime
    start_time = get_datetime_input("開始日時を指定してください（例 2026-01-01 10:00）")

    # Get end datetime
    while True:
        end_time = get_datetime_input("終了日時を指定してください（例 2026-01-01 12:00）")

        # Validate that start < end
        if start_time >= end_time:
            print(get_error_message("start_after_end"))
            continue

        break

    return region, log_group, start_time, end_time


def run_interactive_mode() -> None:
    """
    Run the CLI in interactive mode
    """
    try:
        # Collect input
        region, log_group, start_time, end_time = collect_input()

        # Confirm settings
        if not confirm_settings(region, log_group, start_time, end_time):
            print("キャンセルされました。")
            return

        # Initialize downloader
        print("\nダウンロード中...")
        downloader = CloudWatchLogsDownloader(region=region)

        # Download logs with progress callback
        output_file = downloader.download_logs(
            log_group_name=log_group,
            start_time=start_time,
            end_time=end_time,
            progress_callback=display_progress,
        )

        # Display completion message
        print(f"\nダウンロード完了: {output_file}")

    except KeyboardInterrupt:
        print("\n\n中断されました。")
    except Exception as e:
        print(f"\nエラーが発生しました: {e}")
