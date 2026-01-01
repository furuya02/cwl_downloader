# cwl_downloader

AWS CloudWatch Logsを日付指定でダウンロードするコマンドラインツール

[English README is here](README.md)

## 特徴

- 日付範囲を指定してCloudWatch Logsをダウンロード
- 10分単位に分割することで大容量ログに効率的に対応
- 対話型のCLIインターフェース（確認プロンプト付き）
- ダウンロード中の進捗表示
- ダウンロードしたログを自動的に1つのファイルに結合

## 要件

- Python 3.10以上
- 環境変数で設定されたAWS認証情報

## インストール

### 開発用

```bash
git clone https://github.com/furuya02/cwl_downloader.git
cd cwl_downloader
pip install -e .
```

### 本番用（将来的にPyPIに公開予定）

```bash
pip install cwl-downloader
```

## AWS認証

AWS認証情報は、環境変数または `.env` ファイルで設定できます。

### オプション1: 環境変数

```bash
export AWS_ACCESS_KEY_ID=your_access_key_id
export AWS_SECRET_ACCESS_KEY=your_secret_access_key
export AWS_DEFAULT_REGION=ap-northeast-1  # オプション
export AWS_SESSION_TOKEN=your_session_token  # オプション（一時的な認証情報の場合）
```

### オプション2: .envファイル（推奨）

プロジェクトディレクトリに `.env` ファイルを作成：

```env
AWS_ACCESS_KEY_ID=your_access_key_id
AWS_SECRET_ACCESS_KEY=your_secret_access_key
AWS_DEFAULT_REGION=ap-northeast-1
AWS_SESSION_TOKEN=your_session_token  # オプション
```

**重要**: `.env` ファイルは `.gitignore` に追加して、認証情報をコミットしないようにしてください。

## 使い方

対話モードでツールを実行します：

```bash
$ cwl_downloader
リージョンを指定してください (default: ap-northeast-1)
>
ロググループを指定してください
> /aws/lambda/my-function
開始日時を指定してください（例 2026-01-01 10:00）
> 2026-01-01 10:00
終了日時を指定してください（例 2026-01-01 12:00）
> 2026-01-01 12:00

ダウンロードする対象は、以下で宜しいでしょうか？

region: ap-northeast-1
log_group: /aws/lambda/my-function
start: 2026-01-01 10:00
end: 2026-01-01 12:00

(y/n)> y

ダウンロード中...
[1/12] 2026-01-01 10:00 - 10:10 完了
[2/12] 2026-01-01 10:10 - 10:20 完了
...
[12/12] 2026-01-01 11:50 - 12:00 完了

ダウンロード完了: _aws_lambda_my-function_2026-01-01_10-00_2026-01-01_12-00.log
```

### 使用例

#### 例1: Lambda関数のログをダウンロード

```bash
$ cwl_downloader
リージョンを指定してください (default: ap-northeast-1)
> ap-northeast-1
ロググループを指定してください
> /aws/lambda/my-function
開始日時を指定してください（例 2026-01-01 10:00）
> 2026-01-02 00:00
終了日時を指定してください（例 2026-01-01 12:00）
> 2026-01-02 08:00
```

#### 例2: ECSコンテナのログをダウンロード

```bash
$ cwl_downloader
リージョンを指定してください (default: ap-northeast-1)
>
ロググループを指定してください
> /ecs/my-service-production
開始日時を指定してください（例 2026-01-01 10:00）
> 2026-01-01 15:00
終了日時を指定してください（例 2026-01-01 12:00）
> 2026-01-01 18:00
```

#### 例3: 長時間のログダウンロード

8時間分のログは自動的に48区間に分割されます：

```bash
ダウンロード中...
[1/48] 2026-01-02 00:00 - 00:10 完了
[2/48] 2026-01-02 00:10 - 00:20 完了
...
[48/48] 2026-01-02 07:50 - 08:00 完了

ダウンロード完了: _ecs_my-service_2026-01-02_00-00_2026-01-02_08-00.log
ファイルサイズ: 3,752,376 bytes
```

## 出力

- **ファイル名形式**: `{log_group_name}_{start}_{end}.log`
  - ロググループ名のスラッシュ（/）はアンダースコア（_）に置換されます
  - タイムスタンプのコロン（:）はハイフン（-）に置換されます
- **出力先**: カレントディレクトリ
- **ファイル形式**: プレーンテキスト形式（`[タイムスタンプ] [ログストリーム名] ログメッセージ`）

## 動作の流れ

1. **ユーザー入力**: リージョン、ロググループ、開始/終了日時を収集
2. **検証**: 日時フォーマットの確認、開始 < 終了のチェック、ロググループの存在確認
3. **確認**: 設定内容を表示してユーザーに確認を求める
4. **ダウンロード**:
   - 指定期間を10分単位に分割
   - 各区間ごとに全ログストリームからログを取得
   - 各区間を一時ファイルに保存
   - 進捗を表示
5. **結合**: 全一時ファイルを時系列順に結合
6. **クリーンアップ**: 一時ファイルを削除
7. **完了**: 出力ファイルのパスを表示

## エラーハンドリング

- **AWS認証エラー**: 環境変数が設定されていない場合はエラーメッセージを表示
- **ロググループ不存在エラー**: 指定されたロググループが存在しない場合はエラーを表示
- **APIエラー**: 指数バックオフで最大3回まで自動リトライ
- **日時フォーマットエラー**: 日時フォーマットが正しくない場合は再入力を促す

## トラブルシューティング

### 認証エラー

**問題**: `NoCredentialsError` または「AWS認証情報が設定されていません」

**解決方法**:
1. `.env` ファイルが存在し、有効な認証情報が含まれているか確認
2. 環境変数が正しく設定されているか確認: `echo $AWS_ACCESS_KEY_ID`
3. 認証情報の有効期限が切れていないか確認（特に一時的なセッショントークンの場合）
4. 一時的な認証情報を使用する場合は、`AWS_SESSION_TOKEN` も含める

### ロググループが見つからない

**問題**: 「ロググループ '{log_group}' が見つかりません」

**解決方法**:
1. ロググループ名が正しいか確認（大文字小文字を区別します）
2. 正しいAWSリージョンを使用しているか確認
3. AWS認証情報にCloudWatch Logsへのアクセス権限があるか確認
4. 利用可能なロググループを一覧表示: `aws logs describe-log-groups --region ap-northeast-1`

### ログがダウンロードされない

**問題**: ダウンロードは完了するが、ファイルが空またはサイズが非常に小さい

**解決方法**:
1. 指定した時間範囲に実際のログデータが存在するか確認
2. 日時フォーマットが正しいか確認: `YYYY-MM-DD HH:MM`
3. 開始日時が終了日時より前であることを確認
4. 注意: 時刻はローカルタイムゾーンであり、UTCではありません

### パフォーマンスの問題

**問題**: ダウンロードが非常に遅い

**解決方法**:
1. 大きなロググループの場合は時間範囲を減らす
2. ツールは10分単位でダウンロードするため、長い期間ほど時間がかかります
3. AWSへのネットワーク接続を確認
4. オフピーク時にダウンロードを実行することを検討

### 権限エラー

**問題**: アクセス拒否エラー

**必要なIAM権限**:
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

## プロジェクト構造

```
cwl_downloader/
├── src/
│   └── cwl_downloader/
│       ├── __init__.py
│       ├── __main__.py          # エントリーポイント
│       ├── cli.py               # CLIインターフェース
│       ├── downloader.py        # ダウンロードロジック
│       └── utils.py             # ユーティリティ関数
├── tests/                       # テストコード
│   ├── __init__.py
│   └── test_downloader.py
├── .gitignore
├── README.md                    # 英語ドキュメント
├── README.ja.md                 # 日本語ドキュメント
├── pyproject.toml               # プロジェクト設定
└── LICENSE                      # MITライセンス
```

## 開発

### 開発用依存関係のインストール

```bash
pip install -e ".[dev]"
```

### テストの実行

```bash
pytest
```

### コードフォーマット

```bash
black src tests
```

### 型チェック

```bash
mypy src
```

## ライセンス

MIT License - 詳細は[LICENSE](LICENSE)ファイルを参照してください

## コントリビューション

コントリビューションを歓迎します！Pull Requestをお気軽に送ってください。

## 作者

furuya02

## 関連プロジェクト

- [gi_cleaner](https://github.com/furuya02/gi_cleaner) - プロジェクト構造の参考
