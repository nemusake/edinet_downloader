"""
EDINET文書メタデータ取得スクリプト
有価証券報告書の基本情報（メタデータ）を取得し、JSONファイルに保存
※実際の財務数値（売上高、利益等）は含まれません
"""
import os
import json
from datetime import date, timedelta
from edinet_client.api.client import EdinetAPIClient

def get_financial_data():
    """文書メタデータを取得（財務数値は含まない）"""
    
    # APIキーの確認
    api_key = os.getenv("EDINET_API_KEY")
    if not api_key or api_key == "your_subscription_key":
        print("❌ 環境変数 EDINET_API_KEY を設定してください")
        return
    
    # クライアント初期化
    client = EdinetAPIClient(api_key)
    
    # 取得期間（過去1週間）
    end_date = date.today()
    start_date = end_date - timedelta(days=7)
    
    print(f"📅 期間: {start_date} から {end_date}")
    print("📡 文書メタデータを取得中...\n")
    
    all_documents = []
    current_date = start_date
    
    # 日付ごとに取得
    while current_date <= end_date:
        try:
            documents = client.get_documents_list(current_date)
            
            if documents:
                # 有価証券報告書のみフィルタリング
                securities = client.filter_securities_reports(documents)
                if securities:
                    all_documents.extend(securities)
                    print(f"✅ {current_date}: {len(securities)}件の有価証券報告書")
            
        except Exception as e:
            print(f"❌ {current_date}: エラー - {e}")
        
        current_date += timedelta(days=1)
    
    # 結果を保存
    if all_documents:
        output_file = "financial_data.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_documents, f, ensure_ascii=False, indent=2)
        
        print(f"\n📊 合計: {len(all_documents)}件の有価証券報告書を取得")
        print(f"💾 保存先: {output_file}")
        
        # サンプル表示
        print("\n📋 取得した企業（最初の5件）:")
        for i, doc in enumerate(all_documents[:5], 1):
            print(f"  {i}. {doc.get('filerName')} - {doc.get('docDescription')}")
    else:
        print("\n⚠️  指定期間に有価証券報告書が見つかりませんでした")

if __name__ == "__main__":
    print("=== EDINET文書メタデータ取得 ===\n")
    get_financial_data()