"""
EDINET API接続クライアント
"""
import requests
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, date
import logging

from ..config import (
    EDINET_DOCUMENTS_URL, 
    EDINET_DOCUMENT_URL, 
    API_KEY,
    DOCUMENT_TYPES,
    FILE_TYPES
)

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EdinetAPIClient:
    """EDINET API クライアント"""
    
    def __init__(self, api_key: str = None):
        """
        初期化
        
        Args:
            api_key: APIキー（未指定の場合は環境変数から取得）
        """
        self.api_key = api_key or API_KEY
        self.session = requests.Session()
        self.rate_limit_delay = 1  # レート制限対策（秒）
        
    def _make_request(self, url: str, params: Dict[str, Any]) -> requests.Response:
        """
        APIリクエストを実行
        
        Args:
            url: リクエストURL
            params: リクエストパラメータ
            
        Returns:
            レスポンス
        """
        # APIキーを追加
        params["Subscription-Key"] = self.api_key
        
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            # レート制限対策
            time.sleep(self.rate_limit_delay)
            
            return response
            
        except requests.exceptions.RequestException as e:
            logger.error(f"APIリクエストエラー: {e}")
            raise
            
    def get_documents_list(self, 
                          target_date: date, 
                          doc_type: int = DOCUMENT_TYPES["有価証券報告書"]) -> List[Dict[str, Any]]:
        """
        指定日の文書リストを取得
        
        Args:
            target_date: 対象日付
            doc_type: 文書種別
            
        Returns:
            文書リスト
        """
        params = {
            "date": target_date.strftime("%Y-%m-%d"),
            "type": doc_type
        }
        
        response = self._make_request(EDINET_DOCUMENTS_URL, params)
        data = response.json()
        
        if "results" in data:
            logger.info(f"{target_date}: {len(data['results'])}件の文書を取得")
            return data["results"]
        else:
            logger.warning(f"{target_date}: 文書が見つかりませんでした")
            return []
            
    def download_document(self, 
                         doc_id: str, 
                         file_type: int = FILE_TYPES["ZIP"]) -> bytes:
        """
        文書をダウンロード
        
        Args:
            doc_id: 文書ID
            file_type: ファイル形式
            
        Returns:
            文書データ（バイナリ）
        """
        url = f"{EDINET_DOCUMENT_URL}/{doc_id}"
        params = {"type": file_type}
        
        response = self._make_request(url, params)
        
        if response.status_code == 200:
            logger.info(f"文書 {doc_id} をダウンロードしました")
            return response.content
        else:
            logger.error(f"文書 {doc_id} のダウンロードに失敗しました")
            raise Exception(f"ダウンロード失敗: {response.status_code}")
            
    def filter_securities_reports(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        有価証券報告書、四半期報告書、半期報告書をフィルタリング
        
        Args:
            documents: 文書リスト
            
        Returns:
            フィルタリング後の文書リスト
        """
        # 取得対象の様式コード
        SECURITIES_REPORT_FORMS = [
            '030000',  # 有価証券報告書（年次）
            '043000',  # 四半期報告書（第1四半期）※2024年4月以降廃止
            '044000',  # 四半期報告書（第2四半期）※2024年4月以降廃止  
            '045000',  # 四半期報告書（第3四半期）※2024年4月以降廃止
            '050000',  # 半期報告書
        ]
        
        filtered = []
        
        for doc in documents:
            ordinance_code = doc.get("ordinanceCode")
            form_code = doc.get("formCode")
            edit_status = doc.get("docInfoEditStatus")
            doc_description = doc.get("docDescription", "")
            
            # 有価証券報告書、四半期報告書、半期報告書のフィルタリング条件
            if (ordinance_code == "010" and 
                form_code in SECURITIES_REPORT_FORMS and 
                edit_status != 2):  # 編集状態が2（削除）でない
                
                # 書類種別を判定
                if form_code == '030000':
                    doc_type = "有価証券報告書"
                elif form_code in ['043000', '044000', '045000']:
                    doc_type = "四半期報告書"
                elif form_code == '050000':
                    doc_type = "半期報告書"
                else:
                    doc_type = "その他報告書"
                
                filtered.append(doc)
                logger.info(f"{doc_type}: {doc.get('filerName')} - {doc.get('docID')}")
                
        return filtered