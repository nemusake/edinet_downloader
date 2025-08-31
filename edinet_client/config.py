"""
EDINET API設定ファイル
"""
import os
from dotenv import load_dotenv

# .envファイルを読み込み
load_dotenv()

# EDINET API設定
EDINET_BASE_URL = "https://api.edinet-fsa.go.jp/api/v2"
EDINET_DOCUMENTS_URL = f"{EDINET_BASE_URL}/documents.json"
EDINET_DOCUMENT_URL = f"{EDINET_BASE_URL}/documents"

# APIキー（.envファイルまたは環境変数から取得）
API_KEY = os.getenv("EDINET_API_KEY", "your_subscription_key")

# 文書種別
DOCUMENT_TYPES = {
    "有価証券報告書": 2,
    "四半期報告書": 4,
    "半期報告書": 3
}

# ファイル形式
FILE_TYPES = {
    "ZIP": 1,
    "PDF": 2,
    "CSV": 5
}

# フィルタリング条件
FILTER_CONDITIONS = {
    "有価証券報告書": {
        "ordinance_code": "010",
        "form_code": "030000"
    }
}

# 出力設定
DEFAULT_DOWNLOAD_DIR = "./downloads"
DEFAULT_OUTPUT_DIR = "./output"