"""
EDINETから取得可能な項目を分析してCSV出力（詳細説明付き）

旧ファイル名: analyze_available_fields_v2.py → edinet_metadata.py (2025-08-14変更)
取得済みのfinancial_data.jsonから29項目のメタデータを詳細分析
"""
import json
import csv
from datetime import datetime

def analyze_edinet_fields_with_details():
    """取得済みデータから利用可能な項目を分析（詳細説明付き）"""
    
    # JSONファイルを読み込み
    with open('financial_data.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if not data:
        print("データがありません")
        return
    
    # 最初のレコードからフィールドを取得
    sample_record = data[0]
    
    # フィールド情報を整理（詳細説明付き）
    field_info = []
    
    # フィールド定義（日本語名と詳細説明）
    field_definitions = {
        "seqNumber": {
            "name": "シーケンス番号",
            "description": "APIレスポンス内での順序番号。1日の中での取得順を示す",
            "data_category": "メタデータ"
        },
        "docID": {
            "name": "書類ID",
            "description": "書類を一意に識別するID。XBRLやPDFダウンロード時にこのIDを使用する",
            "data_category": "メタデータ"
        },
        "edinetCode": {
            "name": "EDINETコード",
            "description": "金融庁が企業に付与する一意のコード。企業を特定する際の主キー",
            "data_category": "企業識別"
        },
        "secCode": {
            "name": "証券コード",
            "description": "上場企業の4桁または5桁の証券コード。東証等で使用される",
            "data_category": "企業識別"
        },
        "JCN": {
            "name": "法人番号",
            "description": "国税庁が付与する13桁の法人番号。日本の全法人に付与",
            "data_category": "企業識別"
        },
        "filerName": {
            "name": "提出者名",
            "description": "書類を提出した企業の正式名称",
            "data_category": "企業識別"
        },
        "fundCode": {
            "name": "ファンドコード",
            "description": "投資信託等のファンドを識別するコード。企業の場合はnull",
            "data_category": "企業識別"
        },
        "ordinanceCode": {
            "name": "府令コード",
            "description": "010=企業内容等開示、020=特定有価証券開示など、法的根拠を示す",
            "data_category": "書類分類"
        },
        "formCode": {
            "name": "様式コード",
            "description": "030000=有価証券報告書、043000=四半期報告書など、書類の様式",
            "data_category": "書類分類"
        },
        "docTypeCode": {
            "name": "書類種別コード",
            "description": "120=有価証券報告書、140=四半期報告書など、書類の種類",
            "data_category": "書類分類"
        },
        "periodStart": {
            "name": "期間開始日",
            "description": "会計期間の開始日（YYYY-MM-DD形式）。決算期間の始まり",
            "data_category": "期間情報"
        },
        "periodEnd": {
            "name": "期間終了日",
            "description": "会計期間の終了日（YYYY-MM-DD形式）。決算日を示す",
            "data_category": "期間情報"
        },
        "submitDateTime": {
            "name": "提出日時",
            "description": "EDINETに書類が提出された日時。法定開示のタイミング",
            "data_category": "期間情報"
        },
        "docDescription": {
            "name": "書類の説明",
            "description": "書類の内容を説明する文字列。期や期間を含む詳細情報",
            "data_category": "書類情報"
        },
        "issuerEdinetCode": {
            "name": "発行者EDINETコード",
            "description": "有価証券の発行者のEDINETコード。大量保有報告書等で使用",
            "data_category": "関連企業"
        },
        "subjectEdinetCode": {
            "name": "対象EDINETコード",
            "description": "公開買付等の対象企業のEDINETコード",
            "data_category": "関連企業"
        },
        "subsidiaryEdinetCode": {
            "name": "子会社EDINETコード",
            "description": "子会社のEDINETコード。連結対象を識別",
            "data_category": "関連企業"
        },
        "currentReportReason": {
            "name": "臨時報告書提出事由",
            "description": "臨時報告書の場合の提出理由コード",
            "data_category": "書類情報"
        },
        "parentDocID": {
            "name": "親書類ID",
            "description": "訂正報告書の場合の元書類ID。書類の関連性を示す",
            "data_category": "書類情報"
        },
        "opeDateTime": {
            "name": "操作日時",
            "description": "EDINETでの最終操作日時",
            "data_category": "期間情報"
        },
        "withdrawalStatus": {
            "name": "取下区分",
            "description": "0=通常、1=取下済み。取下げられた書類を識別",
            "data_category": "ステータス"
        },
        "docInfoEditStatus": {
            "name": "書類情報修正区分",
            "description": "0=通常、1=修正済み、2=削除。書類の修正状態",
            "data_category": "ステータス"
        },
        "disclosureStatus": {
            "name": "開示不開示区分",
            "description": "0=開示、1=不開示。一般公開の可否",
            "data_category": "ステータス"
        },
        "xbrlFlag": {
            "name": "XBRLファイル有無",
            "description": "1=あり、0=なし。財務データの構造化ファイルの有無。財務分析には必須",
            "data_category": "ファイル情報"
        },
        "pdfFlag": {
            "name": "PDFファイル有無",
            "description": "1=あり、0=なし。人間が読むための書類PDFの有無",
            "data_category": "ファイル情報"
        },
        "attachDocFlag": {
            "name": "代替書面・添付文書有無",
            "description": "1=あり、0=なし。監査報告書等の添付書類の有無",
            "data_category": "ファイル情報"
        },
        "englishDocFlag": {
            "name": "英文ファイル有無",
            "description": "1=あり、0=なし。英語版書類の有無",
            "data_category": "ファイル情報"
        },
        "csvFlag": {
            "name": "CSVファイル有無",
            "description": "1=あり、0=なし。財務データのCSV形式ファイルの有無",
            "data_category": "ファイル情報"
        },
        "legalStatus": {
            "name": "縦覧区分",
            "description": "1=縦覧中、0=縦覧終了。法定の縦覧期間内かどうか",
            "data_category": "ステータス"
        }
    }
    
    # 各フィールドの情報を収集
    for field_name, value in sample_record.items():
        field_type = type(value).__name__
        if value is None:
            field_type = "null"
            sample_value = "null"
        else:
            sample_value = str(value)[:50]
        
        field_def = field_definitions.get(field_name, {
            "name": "不明",
            "description": "定義なし",
            "data_category": "その他"
        })
        
        # データベース用の推奨型を決定
        if field_type == "str":
            if "date" in field_name.lower() or "period" in field_name.lower():
                if len(sample_value) == 10:
                    db_type = "DATE"
                else:
                    db_type = "DATETIME"
            elif "code" in field_name.lower() or "Code" in field_name:
                db_type = "VARCHAR(20)"
            elif "flag" in field_name.lower() or "Flag" in field_name:
                db_type = "CHAR(1)"
            elif "status" in field_name.lower() or "Status" in field_name:
                db_type = "CHAR(1)"
            else:
                db_type = "VARCHAR(255)"
        elif field_type == "int":
            db_type = "INTEGER"
        elif field_type == "null":
            db_type = "VARCHAR(255)"
        else:
            db_type = "TEXT"
        
        # 主キーやインデックスの推奨
        is_key = ""
        if field_name == "docID":
            is_key = "PRIMARY KEY"
        elif field_name in ["edinetCode", "secCode", "submitDateTime", "periodEnd"]:
            is_key = "INDEX推奨"
        
        # 財務データかどうか
        has_financial_data = "いいえ（メタデータのみ）"
        
        field_info.append({
            "フィールド名": field_name,
            "日本語名": field_def["name"],
            "データカテゴリ": field_def["data_category"],
            "説明": field_def["description"],
            "データ型": field_type,
            "推奨DB型": db_type,
            "キー/インデックス": is_key,
            "財務データ": has_financial_data,
            "サンプル値": sample_value,
            "必須": "Yes" if value is not None else "No"
        })
    
    # CSV出力
    output_file = f"edinet_metadata_{datetime.now().strftime('%Y%m%d')}.csv"
    
    with open(output_file, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=field_info[0].keys())
        writer.writeheader()
        writer.writerows(field_info)
    
    print("=" * 70)
    print("📊 現在取得しているデータの分析結果")
    print("=" * 70)
    print(f"✅ フィールド分析完了: {len(field_info)}個のフィールド")
    print(f"💾 保存先: {output_file}")
    
    # カテゴリ別集計
    categories = {}
    for field in field_info:
        cat = field["データカテゴリ"]
        categories[cat] = categories.get(cat, 0) + 1
    
    print("\n📂 データカテゴリ別の項目数:")
    for cat, count in sorted(categories.items()):
        print(f"  - {cat}: {count}項目")
    
    print("\n" + "=" * 70)
    print("⚠️  重要な注意事項")
    print("=" * 70)
    print("現在取得しているのは「書類のメタデータ」のみです。")
    print("実際の財務数値（売上高、利益等）は含まれていません。")
    
    print("\n" + "=" * 70)
    print("💰 実際の財務データを取得するには")
    print("=" * 70)
    print("XBRLファイルをダウンロードして解析する必要があります：")
    print()
    print("1️⃣  docIDを使用してXBRLファイルをダウンロード")
    print("   例: https://api.edinet-fsa.go.jp/api/v2/documents/{docID}?type=1")
    print()
    print("2️⃣  XBRLファイル内から財務データを抽出")
    print("   取得可能な主な財務データ：")
    print("   【損益計算書】")
    print("     - 売上高 (NetSales)")
    print("     - 売上原価 (CostOfSales)")
    print("     - 営業利益 (OperatingIncome)")
    print("     - 経常利益 (OrdinaryIncome)")
    print("     - 当期純利益 (NetIncome)")
    print()
    print("   【貸借対照表】")
    print("     - 総資産 (TotalAssets)")
    print("     - 流動資産 (CurrentAssets)")
    print("     - 固定資産 (NonCurrentAssets)")
    print("     - 負債合計 (TotalLiabilities)")
    print("     - 純資産 (TotalEquity)")
    print()
    print("   【キャッシュフロー計算書】")
    print("     - 営業CF (CashFlowsFromOperatingActivities)")
    print("     - 投資CF (CashFlowsFromInvestingActivities)")
    print("     - 財務CF (CashFlowsFromFinancingActivities)")
    print()
    print("   【その他の重要指標】")
    print("     - 従業員数 (NumberOfEmployees)")
    print("     - 平均年間給与 (AverageAnnualSalary)")
    print("     - 研究開発費 (ResearchAndDevelopmentExpenses)")
    print("     - 設備投資額 (CapitalExpenditures)")
    
    print("\n" + "=" * 70)
    print("📌 次のステップの提案")
    print("=" * 70)
    print("1. XBRLファイルのダウンロード機能を実装")
    print("2. XBRLパーサーを実装して財務データを抽出")
    print("3. メタデータと財務データを統合してデータベースに保存")
    
    return field_info

if __name__ == "__main__":
    print("=== EDINET取得可能項目の詳細分析 ===\n")
    analyze_edinet_fields_with_details()