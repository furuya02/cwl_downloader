"""
CloudWatch Logs downloader implementation
"""

import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from datetime import datetime, timedelta
from typing import List, Tuple, Optional, Callable
import time
import os
from pathlib import Path

from .utils import get_error_message, sanitize_filename, format_datetime_for_filename


class CloudWatchLogsDownloader:
    """
    CloudWatch Logs downloader class
    """

    def __init__(self, region: str = "ap-northeast-1"):
        """
        Initialize CloudWatch Logs downloader

        Args:
            region: AWS region name

        Raises:
            NoCredentialsError: If AWS credentials are not configured
        """
        try:
            self.client = boto3.client("logs", region_name=region)
            self.region = region
            # Test credentials by making a simple API call
            self.client.describe_log_groups(limit=1)
        except NoCredentialsError:
            raise NoCredentialsError(get_error_message("no_aws_credentials"))

    def log_group_exists(self, log_group_name: str) -> bool:
        """
        Check if log group exists

        Args:
            log_group_name: Name of the log group

        Returns:
            True if log group exists, False otherwise
        """
        try:
            response = self.client.describe_log_groups(
                logGroupNamePrefix=log_group_name, limit=1
            )
            for log_group in response.get("logGroups", []):
                if log_group["logGroupName"] == log_group_name:
                    return True
            return False
        except ClientError:
            return False

    def _split_time_range(
        self, start_time: datetime, end_time: datetime, interval_minutes: int = 10
    ) -> List[Tuple[datetime, datetime]]:
        """
        Split time range into intervals

        Args:
            start_time: Start datetime
            end_time: End datetime
            interval_minutes: Interval in minutes (default: 10)

        Returns:
            List of (start, end) datetime tuples
        """
        intervals = []
        current = start_time

        while current < end_time:
            next_time = min(current + timedelta(minutes=interval_minutes), end_time)
            intervals.append((current, next_time))
            current = next_time

        return intervals

    def _download_logs_for_interval(
        self, log_group_name: str, start_time: datetime, end_time: datetime
    ) -> List[str]:
        """
        Download logs for a specific time interval with retry logic

        Args:
            log_group_name: Name of the log group
            start_time: Start datetime
            end_time: End datetime

        Returns:
            List of log entries
        """
        logs = []
        start_ms = int(start_time.timestamp() * 1000)
        end_ms = int(end_time.timestamp() * 1000)

        max_retries = 3
        retry_delay = 1  # seconds

        for attempt in range(max_retries):
            try:
                next_token = None

                while True:
                    if next_token:
                        response = self.client.filter_log_events(
                            logGroupName=log_group_name,
                            startTime=start_ms,
                            endTime=end_ms,
                            nextToken=next_token,
                        )
                    else:
                        response = self.client.filter_log_events(
                            logGroupName=log_group_name,
                            startTime=start_ms,
                            endTime=end_ms,
                        )

                    # Process events
                    for event in response.get("events", []):
                        timestamp = datetime.fromtimestamp(
                            event["timestamp"] / 1000
                        ).strftime("%Y-%m-%d %H:%M:%S")
                        log_stream = event.get("logStreamName", "unknown")
                        message = event.get("message", "")
                        logs.append(f"[{timestamp}] [{log_stream}] {message}")

                    # Check for more pages
                    next_token = response.get("nextToken")
                    if not next_token:
                        break

                # Success - break retry loop
                break

            except ClientError as e:
                if attempt < max_retries - 1:
                    # Exponential backoff
                    time.sleep(retry_delay * (2**attempt))
                    continue
                else:
                    # Final attempt failed
                    error_msg = get_error_message("api_error", error=str(e))
                    raise RuntimeError(error_msg) from e

        return logs

    def download_logs(
        self,
        log_group_name: str,
        start_time: datetime,
        end_time: datetime,
        output_file: Optional[str] = None,
        progress_callback: Optional[Callable[[int, int, datetime, datetime], None]] = None,
    ) -> str:
        """
        Download logs from CloudWatch Logs

        Args:
            log_group_name: Name of the log group
            start_time: Start datetime
            end_time: End datetime
            output_file: Output file path (optional, auto-generated if not provided)
            progress_callback: Callback function for progress updates
                              (current_index, total_count, interval_start, interval_end)

        Returns:
            Path to the output file

        Raises:
            RuntimeError: If log group doesn't exist or download fails
        """
        # Check if log group exists
        if not self.log_group_exists(log_group_name):
            raise RuntimeError(
                get_error_message("log_group_not_found", log_group=log_group_name)
            )

        # Generate output filename if not provided
        if output_file is None:
            sanitized_log_group = sanitize_filename(log_group_name)
            start_str = format_datetime_for_filename(start_time)
            end_str = format_datetime_for_filename(end_time)
            output_file = f"{sanitized_log_group}_{start_str}_{end_str}.log"

        # Split time range into intervals
        intervals = self._split_time_range(start_time, end_time)
        total_intervals = len(intervals)

        # Temporary files list
        temp_files = []

        try:
            # Download each interval
            for index, (interval_start, interval_end) in enumerate(intervals, start=1):
                # Download logs for this interval
                logs = self._download_logs_for_interval(
                    log_group_name, interval_start, interval_end
                )

                # Save to temporary file
                temp_file = f"temp_{index:04d}.log"
                temp_files.append(temp_file)

                with open(temp_file, "w", encoding="utf-8") as f:
                    for log_entry in logs:
                        f.write(log_entry + "\n")

                # Call progress callback if provided
                if progress_callback:
                    progress_callback(index, total_intervals, interval_start, interval_end)

            # Merge all temporary files into final output
            with open(output_file, "w", encoding="utf-8") as outfile:
                for temp_file in temp_files:
                    if os.path.exists(temp_file):
                        with open(temp_file, "r", encoding="utf-8") as infile:
                            outfile.write(infile.read())

        except Exception as e:
            raise RuntimeError(get_error_message("io_error", error=str(e))) from e

        finally:
            # Clean up temporary files
            for temp_file in temp_files:
                try:
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                except OSError:
                    pass  # Ignore cleanup errors

        return output_file
