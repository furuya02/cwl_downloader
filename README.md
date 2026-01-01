# cwl_downloader

A command-line tool to download AWS CloudWatch Logs for a specified time period.

[日本語版 README はこちら](README.ja.md)

## Features

- Download CloudWatch Logs by specifying a date range
- Efficient handling of large log volumes by splitting downloads into 10-minute intervals
- Interactive CLI interface with confirmation prompts
- Progress display during download
- Automatic merging of downloaded logs into a single file

## Requirements

- Python 3.10 or higher
- AWS credentials configured via environment variables

## Installation

### For Development

```bash
git clone https://github.com/furuya02/cwl_downloader.git
cd cwl_downloader
pip install -e .
```

### For Production (Future PyPI Release)

```bash
pip install cwl-downloader
```

## AWS Authentication

You can set your AWS credentials using either environment variables or a `.env` file.

### Option 1: Environment Variables

```bash
export AWS_ACCESS_KEY_ID=your_access_key_id
export AWS_SECRET_ACCESS_KEY=your_secret_access_key
export AWS_DEFAULT_REGION=ap-northeast-1  # Optional
export AWS_SESSION_TOKEN=your_session_token  # Optional, for temporary credentials
```

### Option 2: .env File (Recommended)

Create a `.env` file in your project directory:

```env
AWS_ACCESS_KEY_ID=your_access_key_id
AWS_SECRET_ACCESS_KEY=your_secret_access_key
AWS_DEFAULT_REGION=ap-northeast-1
AWS_SESSION_TOKEN=your_session_token  # Optional
```

**Important**: Add `.env` to your `.gitignore` to prevent committing sensitive credentials.

## Usage

Run the tool in interactive mode:

```bash
$ cwl_downloader
Please specify the region (default: ap-northeast-1)
>
Please specify the log group
> /aws/lambda/my-function
Please specify the start datetime (e.g., 2026-01-01 10:00)
> 2026-01-01 10:00
Please specify the end datetime (e.g., 2026-01-01 12:00)
> 2026-01-01 12:00

Are the following settings correct?

region: ap-northeast-1
log_group: /aws/lambda/my-function
start: 2026-01-01 10:00
end: 2026-01-01 12:00

(y/n)> y

Downloading...
[1/12] 2026-01-01 10:00 - 10:10 completed
[2/12] 2026-01-01 10:10 - 10:20 completed
...
[12/12] 2026-01-01 11:50 - 12:00 completed

Download complete: _aws_lambda_my-function_2026-01-01_10-00_2026-01-01_12-00.log
```

### Usage Examples

#### Example 1: Download Lambda Function Logs

```bash
$ cwl_downloader
Please specify the region (default: ap-northeast-1)
> ap-northeast-1
Please specify the log group
> /aws/lambda/my-function
Please specify the start datetime (e.g., 2026-01-01 10:00)
> 2026-01-02 00:00
Please specify the end datetime (e.g., 2026-01-01 12:00)
> 2026-01-02 08:00
```

#### Example 2: Download ECS Container Logs

```bash
$ cwl_downloader
Please specify the region (default: ap-northeast-1)
>
Please specify the log group
> /ecs/my-service-production
Please specify the start datetime (e.g., 2026-01-01 10:00)
> 2026-01-01 15:00
Please specify the end datetime (e.g., 2026-01-01 12:00)
> 2026-01-01 18:00
```

#### Example 3: Large Time Range Download

For an 8-hour period, the tool automatically splits into 48 intervals:

```bash
Downloading...
[1/48] 2026-01-02 00:00 - 00:10 completed
[2/48] 2026-01-02 00:10 - 00:20 completed
...
[48/48] 2026-01-02 07:50 - 08:00 completed

Download complete: _ecs_my-service_2026-01-02_00-00_2026-01-02_08-00.log
File size: 3,752,376 bytes
```

## Output

- **File name format**: `{log_group_name}_{start}_{end}.log`
  - Slashes in the log group name are replaced with underscores
  - Colons in timestamps are replaced with hyphens
- **Output directory**: Current working directory
- **File format**: Plain text with the format `[timestamp] [log_stream_name] log_message`

## How It Works

1. **User Input**: Collect region, log group, start/end datetime
2. **Validation**: Verify datetime format, check if start < end, confirm log group exists
3. **Confirmation**: Display settings and request user confirmation
4. **Download**:
   - Split the time period into 10-minute intervals
   - Download logs for each interval from all log streams
   - Save each interval to a temporary file
   - Display progress
5. **Merge**: Combine all temporary files in chronological order
6. **Cleanup**: Delete temporary files
7. **Complete**: Display the output file path

## Error Handling

- **AWS authentication errors**: Displays error message if environment variables are not set
- **Log group not found**: Displays error if the specified log group doesn't exist
- **API errors**: Automatically retries up to 3 times with exponential backoff
- **Invalid datetime format**: Prompts for re-entry if datetime format is incorrect

## Troubleshooting

### Authentication Errors

**Problem**: `NoCredentialsError` or "AWS認証情報が設定されていません"

**Solutions**:
1. Verify your `.env` file exists and contains valid credentials
2. Check that environment variables are properly set: `echo $AWS_ACCESS_KEY_ID`
3. Ensure your credentials have not expired (especially for temporary session tokens)
4. For temporary credentials, make sure `AWS_SESSION_TOKEN` is included

### Log Group Not Found

**Problem**: "ロググループ '{log_group}' が見つかりません"

**Solutions**:
1. Verify the log group name is correct (case-sensitive)
2. Check that you're using the correct AWS region
3. Ensure your AWS credentials have permission to access CloudWatch Logs
4. List available log groups: `aws logs describe-log-groups --region ap-northeast-1`

### No Logs Downloaded

**Problem**: Download completes but file is empty or very small

**Solutions**:
1. Verify the time range contains actual log data
2. Check that the datetime format is correct: `YYYY-MM-DD HH:MM`
3. Ensure the start time is before the end time
4. Note: Times are in the local timezone, not UTC

### Performance Issues

**Problem**: Download is very slow

**Solutions**:
1. Reduce the time range for large log groups
2. The tool splits downloads into 10-minute intervals, so longer periods take more time
3. Check your network connection to AWS
4. Consider downloading during off-peak hours

### Permission Errors

**Problem**: Access denied errors

**Required IAM Permissions**:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "logs:DescribeLogGroups",
        "logs:FilterLogEvents"
      ],
      "Resource": "*"
    }
  ]
}
```

## Project Structure

```
cwl_downloader/
├── src/
│   └── cwl_downloader/
│       ├── __init__.py
│       ├── __main__.py          # Entry point
│       ├── cli.py               # CLI interface
│       ├── downloader.py        # Download logic
│       └── utils.py             # Utility functions
├── tests/                       # Test code
│   ├── __init__.py
│   └── test_downloader.py
├── .gitignore
├── README.md                    # English documentation
├── README.ja.md                 # Japanese documentation
├── pyproject.toml               # Project configuration
└── LICENSE                      # MIT License
```

## Development

### Install Development Dependencies

```bash
pip install -e ".[dev]"
```

### Run Tests

```bash
pytest
```

### Code Formatting

```bash
black src tests
```

### Type Checking

```bash
mypy src
```

## License

MIT License - see [LICENSE](LICENSE) file for details

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Author

furuya02

## Related Projects

- [gi_cleaner](https://github.com/furuya02/gi_cleaner) - Reference project for structure
