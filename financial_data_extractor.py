"""
統合財務データ取得システム
企業選択から70項目の財務データ抽出まで一元化
"""
import pandas as pd
import json
import logging
import os
import zipfile
import tempfile
import shutil
import re
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import sys
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET

from edinet_client.api.client import EdinetAPIClient

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class FinancialDataExtractor:
    """統合財務データ取得システム"""
    
    def __init__(self):
        self.client = EdinetAPIClient()
        self.edinet_list_df = None
        self.fund_list_df = None
        self.financial_mapping = {}
        self.load_company_lists()
        self.load_financial_mapping()
    
    def load_company_lists(self):
        """企業・ファンドリストを読み込み"""
        try:
            # EDINETコードリスト読み込み
            edinet_files = list(Path('.').glob('list_edinetcode_*.csv'))
            if edinet_files:
                latest_edinet = max(edinet_files, key=lambda x: x.name)
                self.edinet_list_df = pd.read_csv(latest_edinet, encoding='utf-8-sig')
                logger.info(f"EDINETリスト読み込み: {latest_edinet.name} ({len(self.edinet_list_df)}件)")
            
            # ファンドコードリスト読み込み
            fund_files = list(Path('.').glob('list_fundcode_*.csv'))
            if fund_files:
                latest_fund = max(fund_files, key=lambda x: x.name)
                self.fund_list_df = pd.read_csv(latest_fund, encoding='utf-8-sig')
                logger.info(f"ファンドリスト読み込み: {latest_fund.name} ({len(self.fund_list_df)}件)")
                
        except Exception as e:
            logger.error(f"企業リスト読み込みエラー: {e}")
            raise
    
    def load_financial_mapping(self):
        """70項目の財務指標マッピングを読み込み"""
        try:
            mapping_files = list(Path('.').glob('xbrl_fin_metadata_*.csv'))
            if not mapping_files:
                logger.error("財務指標マッピングファイルが見つかりません")
                return
            
            latest_mapping = max(mapping_files, key=lambda x: x.name)
            df = pd.read_csv(latest_mapping, encoding='utf-8-sig')
            
            # XBRLエレメント名と項目のマッピングを作成
            for _, row in df.iterrows():
                if pd.notna(row['xbrl_element']) and row['xbrl_element'] != '計算項目':
                    element_patterns = self._generate_element_patterns(row['xbrl_element'])
                    self.financial_mapping[row['item_name_en']] = {
                        'japanese_name': row['item_name_jp'],
                        'xbrl_patterns': element_patterns,
                        'unit': row['unit'],
                        'importance': row['importance'],
                        'category': row['category']
                    }
            
            logger.info(f"財務指標マッピング読み込み: {len(self.financial_mapping)}項目")
            
        except Exception as e:
            logger.error(f"財務指標マッピング読み込みエラー: {e}")
    
    def _generate_element_patterns(self, base_element: str) -> List[str]:
        """XBRLエレメント名のパターンを生成"""
        patterns = [base_element]
        
        element_name = base_element.split(':')[-1]
        
        common_prefixes = [
            'jppfs_cor', 'jpcrp_cor', 'jpdei_cor', 'jpigp_cor',
            'us-gaap', 'ifrs', 'jpfr', 'jpcre', 'jpcrp'
        ]
        
        for prefix in common_prefixes:
            patterns.append(f"{prefix}:{element_name}")
        
        patterns.append(element_name)
        return patterns
    
    def display_company_selection_menu(self, 
                                      filter_by_sec_code: bool = True,
                                      limit: int = 20) -> Optional[Dict]:
        """企業選択メニューを表示"""
        if self.edinet_list_df is None:
            logger.error("EDINETリストが読み込まれていません")
            return None
        
        df = self.edinet_list_df.copy()
        
        if filter_by_sec_code:
            df = df[df['証券コード'].notna() & (df['証券コード'] != '')]
            logger.info(f"証券コード保有企業: {len(df)}件")
        
        if len(df) > limit:
            df_display = df.head(limit)
            logger.info(f"表示制限により最初の{limit}件を表示")
        else:
            df_display = df
        
        print("\n=== 企業選択メニュー ===")
        print("番号 | EDINETコード | 証券コード | 企業名")
        print("-" * 80)
        
        for i, (_, row) in enumerate(df_display.iterrows(), 1):
            edinet_code = row['EDINETコード']
            sec_code = row['証券コード'] if pd.notna(row['証券コード']) else 'なし'
            company_name = row['提出者名'][:30]
            
            print(f"{i:3d}  | {edinet_code:10s} | {str(sec_code):8s} | {company_name}")
        
        print(f"\n検索オプション:")
        print(f"{len(df_display) + 1}: 企業名で検索")
        print(f"{len(df_display) + 2}: EDINETコードで検索")
        print(f"{len(df_display) + 3}: 証券コードで検索")
        print(f"\n特別オプション:")
        print(f"{len(df_display) + 4}: 🚀 全銘柄一括処理（期間指定）")
        print("0: 終了")
        
        while True:
            try:
                choice = input(f"\n選択してください (1-{len(df_display) + 4}, 0): ").strip()
                
                if choice == '0':
                    return None
                
                choice_num = int(choice)
                
                if 1 <= choice_num <= len(df_display):
                    selected_row = df_display.iloc[choice_num - 1]
                    return selected_row.to_dict()
                elif choice_num == len(df_display) + 1:
                    return self._search_by_name(df)
                elif choice_num == len(df_display) + 2:
                    return self._search_by_edinet_code(df)
                elif choice_num == len(df_display) + 3:
                    return self._search_by_sec_code(df)
                elif choice_num == len(df_display) + 4:
                    # 全銘柄一括処理を示す特別な値を返す
                    return {"全銘柄一括処理": True}
                else:
                    print("無効な選択です。再度入力してください。")
                    
            except ValueError:
                print("数字を入力してください。")
            except KeyboardInterrupt:
                print("\n処理を中断しました。")
                return None
    
    def _search_by_name(self, df: pd.DataFrame) -> Optional[Dict]:
        """企業名で検索"""
        search_term = input("企業名の一部を入力してください: ").strip()
        if not search_term:
            return None
        
        results = df[df['提出者名'].str.contains(search_term, na=False, case=False)]
        return self._select_from_search_results(results, f"'{search_term}'を含む企業")
    
    def _search_by_edinet_code(self, df: pd.DataFrame) -> Optional[Dict]:
        """EDINETコードで検索"""
        edinet_code = input("EDINETコードを入力してください: ").strip().upper()
        if not edinet_code:
            return None
        
        results = df[df['EDINETコード'] == edinet_code]
        return self._select_from_search_results(results, f"EDINETコード '{edinet_code}'")
    
    def _search_by_sec_code(self, df: pd.DataFrame) -> Optional[Dict]:
        """証券コードで検索"""
        sec_code = input("証券コードを入力してください: ").strip()
        if not sec_code:
            return None
        
        results = df[df['証券コード'].astype(str) == sec_code]
        return self._select_from_search_results(results, f"証券コード '{sec_code}'")
    
    def _select_from_search_results(self, results: pd.DataFrame, search_desc: str) -> Optional[Dict]:
        """検索結果から選択"""
        if len(results) == 0:
            print(f"{search_desc}に該当する企業が見つかりませんでした。")
            return None
        
        if len(results) == 1:
            selected = results.iloc[0].to_dict()
            print(f"企業が見つかりました: {selected['提出者名']}")
            return selected
        
        print(f"\n{search_desc}の検索結果 ({len(results)}件):")
        print("番号 | EDINETコード | 証券コード | 企業名")
        print("-" * 80)
        
        for i, (_, row) in enumerate(results.iterrows(), 1):
            edinet_code = row['EDINETコード']
            sec_code = row['証券コード'] if pd.notna(row['証券コード']) else 'なし'
            company_name = row['提出者名'][:30]
            
            print(f"{i:3d}  | {edinet_code:10s} | {str(sec_code):8s} | {company_name}")
        
        while True:
            try:
                choice = input(f"\n選択してください (1-{len(results)}, 0=戻る): ").strip()
                
                if choice == '0':
                    return None
                
                choice_num = int(choice)
                if 1 <= choice_num <= len(results):
                    return results.iloc[choice_num - 1].to_dict()
                else:
                    print("無効な選択です。")
                    
            except ValueError:
                print("数字を入力してください。")
    
    def estimate_filing_period(self, company_info: Dict) -> List[date]:
        """決算期から有価証券報告書の提出時期を推定"""
        fiscal_year_end = company_info.get('決算日', '')
        if not fiscal_year_end:
            logger.warning("決算日情報がありません。デフォルト期間を使用します")
            return self._get_default_search_dates()
        
        try:
            current_year = datetime.now().year
            
            if '月' in fiscal_year_end and '日' in fiscal_year_end:
                month_str = fiscal_year_end.split('月')[0]
                day_str = fiscal_year_end.split('月')[1].replace('日', '')
                
                fiscal_month = int(month_str)
                fiscal_day = int(day_str)
                
                potential_dates = []
                
                for year in [current_year, current_year - 1]:
                    try:
                        fiscal_date = date(year, fiscal_month, fiscal_day)
                        
                        filing_start = fiscal_date + timedelta(days=60)
                        filing_end = fiscal_date + timedelta(days=90)
                        
                        current_date = filing_start
                        while current_date <= filing_end and current_date <= date.today():
                            potential_dates.append(current_date)
                            current_date += timedelta(days=1)
                            
                    except ValueError:
                        continue
                
                return sorted(potential_dates, reverse=True)
                
        except Exception as e:
            logger.warning(f"決算期解析エラー: {e}")
        
        return self._get_default_search_dates()
    
    def _get_default_search_dates(self) -> List[date]:
        """デフォルトの検索期間（過去60日）"""
        dates = []
        for i in range(60):
            dates.append(date.today() - timedelta(days=i))
        return dates
    
    def find_company_documents(self, company_info: Dict, max_search_days: int = 60) -> List[Dict]:
        """企業の有価証券報告書を効率的に検索"""
        target_edinet_code = company_info['EDINETコード']
        company_name = company_info['提出者名']
        
        logger.info(f"=== {company_name} の文書検索開始 ===")
        
        search_dates = self.estimate_filing_period(company_info)
        search_dates = search_dates[:max_search_days]
        
        logger.info(f"検索期間: {len(search_dates)}日間")
        
        found_documents = []
        
        for search_date in search_dates:
            try:
                logger.info(f"検索中: {search_date}")
                
                documents = self.client.get_documents_list(search_date)
                securities_reports = self.client.filter_securities_reports(documents)
                
                for doc in securities_reports:
                    if doc.get("edinetCode") == target_edinet_code:
                        found_documents.append(doc)
                        logger.info(f"発見: {doc.get('docDescription')} (提出: {doc.get('submitDateTime')})")
                        
                        if len(found_documents) >= 1:
                            logger.info("最新の有価証券報告書を発見したため検索を終了")
                            return found_documents
                
            except Exception as e:
                logger.warning(f"{search_date} の検索でエラー: {e}")
                continue
        
        return found_documents
    
    def download_and_extract_xbrl(self, doc_id: str, output_dir: str = "temp_xbrl") -> str:
        """XBRLファイルをダウンロードして解凍"""
        logger.info(f"文書 {doc_id} をダウンロード中...")
        
        zip_data = self.client.download_document(doc_id)
        
        output_path = Path(output_dir) / doc_id
        output_path.mkdir(parents=True, exist_ok=True)
        
        with tempfile.NamedTemporaryFile(suffix='.zip') as temp_zip:
            temp_zip.write(zip_data)
            temp_zip.flush()
            
            with zipfile.ZipFile(temp_zip.name, 'r') as zip_ref:
                zip_ref.extractall(output_path)
        
        logger.info(f"ファイルを {output_path} に解凍しました")
        return str(output_path)
    
    def find_xbrl_files(self, extract_path: str) -> List[Dict[str, str]]:
        """XBRLファイルを検索して詳細情報を取得"""
        xbrl_files = []
        
        for xbrl_file in Path(extract_path).glob("**/*.xbrl"):
            file_info = {
                'path': str(xbrl_file),
                'name': xbrl_file.name,
                'size': xbrl_file.stat().st_size,
                'type': self._classify_xbrl_file(xbrl_file.name)
            }
            
            # インスタンス文書を優先
            if 'instance' in xbrl_file.name.lower() or 'jpcrp' in xbrl_file.name:
                xbrl_files.insert(0, file_info)
            else:
                xbrl_files.append(file_info)
        
        logger.info(f"XBRLファイルが {len(xbrl_files)} 個見つかりました")
        for i, file_info in enumerate(xbrl_files):
            logger.info(f"  {i+1}. {file_info['name']} ({file_info['type']}, {file_info['size']:,} bytes)")
        
        return xbrl_files
    
    def _classify_xbrl_file(self, filename: str) -> str:
        """XBRLファイルの種類を分類"""
        filename_lower = filename.lower()
        
        if 'jpcrp' in filename_lower and 'instance' in filename_lower:
            return "有価証券報告書インスタンス文書"
        elif 'jpcrp' in filename_lower:
            return "有価証券報告書関連"
        elif 'jpdei' in filename_lower:
            return "基本情報タクソノミ"
        elif 'jpigp' in filename_lower:
            return "業種別タクソノミ"
        elif 'jppfs' in filename_lower:
            return "財務諸表タクソノミ"
        elif 'instance' in filename_lower:
            return "インスタンス文書"
        elif 'taxonomy' in filename_lower or 'tax' in filename_lower:
            return "タクソノミファイル"
        else:
            return "その他XBRL文書"
    
    def extract_financial_data(self, xbrl_file_info: Dict[str, str]) -> Dict[str, Any]:
        """XBRLファイルから財務データを抽出"""
        xbrl_path = xbrl_file_info['path']
        file_name = xbrl_file_info['name']
        file_type = xbrl_file_info['type']
        
        logger.info(f"XBRLファイル解析中: {file_name} ({file_type})")
        
        try:
            with open(xbrl_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            soup = BeautifulSoup(content, 'xml')
            
            extracted_data = {}
            found_count = 0
            
            for item_key, mapping_info in self.financial_mapping.items():
                value = self._find_element_value(soup, mapping_info['xbrl_patterns'])
                
                if value is not None:
                    extracted_data[item_key] = {
                        'value': value,
                        'japanese_name': mapping_info['japanese_name'],
                        'unit': mapping_info['unit'],
                        'importance': mapping_info['importance'],
                        'category': mapping_info['category']
                    }
                    found_count += 1
                else:
                    extracted_data[item_key] = {
                        'value': None,
                        'japanese_name': mapping_info['japanese_name'],
                        'unit': mapping_info['unit'],
                        'importance': mapping_info['importance'],
                        'category': mapping_info['category']
                    }
            
            logger.info(f"財務データ抽出完了: {found_count}/{len(self.financial_mapping)}項目")
            
            period_info = self._extract_period_info(soup)
            
            return {
                'financial_data': extracted_data,
                'period_info': period_info,
                'source_file_info': {
                    'filename': file_name,
                    'file_type': file_type,
                    'file_size': xbrl_file_info['size'],
                    'extraction_datetime': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                },
                'extraction_summary': {
                    'total_items': len(self.financial_mapping),
                    'found_items': found_count,
                    'success_rate': round(found_count / len(self.financial_mapping) * 100, 1)
                }
            }
            
        except Exception as e:
            logger.error(f"XBRL解析エラー: {e}")
            return {}
    
    def _find_element_value(self, soup: BeautifulSoup, patterns: List[str]) -> Optional[str]:
        """XBRLエレメントの値を検索"""
        for pattern in patterns:
            elements = soup.find_all(pattern)
            if elements:
                return self._extract_numeric_value(elements[0])
            
            if ':' in pattern:
                local_name = pattern.split(':')[-1]
                elements = soup.find_all(lambda tag: tag.name and tag.name.endswith(local_name))
                if elements:
                    return self._extract_numeric_value(elements[0])
            
            elements = soup.find_all(lambda tag: tag.name and tag.name.lower() == pattern.lower())
            if elements:
                return self._extract_numeric_value(elements[0])
        
        return None
    
    def _extract_numeric_value(self, element) -> Optional[str]:
        """エレメントから数値を抽出"""
        if element is None:
            return None
        
        text = element.get_text(strip=True)
        
        if not text:
            return None
        
        numeric_text = re.sub(r'[^\d.-]', '', text)
        
        if numeric_text:
            try:
                float(numeric_text)
                return numeric_text
            except ValueError:
                pass
        
        return text
    
    def _extract_period_info(self, soup: BeautifulSoup) -> Dict[str, str]:
        """期間情報を抽出"""
        period_info = {}
        
        period_patterns = [
            ('period_start', ['periodStart', 'PeriodStart', 'startDate']),
            ('period_end', ['periodEnd', 'PeriodEnd', 'endDate']),
            ('instant', ['instant', 'Instant'])
        ]
        
        for key, patterns in period_patterns:
            for pattern in patterns:
                elements = soup.find_all(lambda tag: tag.name and pattern.lower() in tag.name.lower())
                if elements:
                    period_info[key] = elements[0].get_text(strip=True)
                    break
        
        return period_info
    
    def _extract_document_date_and_name(self, doc_info: Dict) -> tuple:
        """文書の公開日付と書類名称を抽出"""
        # 公開日付の抽出（提出日時から日付部分を取得）
        submit_datetime = doc_info.get('submitDateTime', '')
        if submit_datetime:
            try:
                # "2025-06-26 13:21" -> "2025-06-26"
                date_part = submit_datetime.split(' ')[0]
                return date_part, self._classify_document_type(doc_info)
            except:
                pass
        
        # フォールバック：期末日を使用
        period_end = doc_info.get('periodEnd', '')
        if period_end:
            return period_end, self._classify_document_type(doc_info)
        
        return 'unknown', self._classify_document_type(doc_info)
    
    def _classify_document_type(self, doc_info: Dict) -> str:
        """文書種別を分類"""
        doc_description = doc_info.get('docDescription', '').lower()
        form_code = doc_info.get('formCode', '')
        
        # 有価証券報告書
        if '有価証券報告書' in doc_description or form_code == '030000':
            return '有価証券報告書'
        # 四半期報告書
        elif '四半期報告書' in doc_description or form_code in ['043000', '044000']:
            return '四半期報告書'
        # 半期報告書  
        elif '半期報告書' in doc_description or form_code == '050000':
            return '半期報告書'
        # 臨時報告書
        elif '臨時報告書' in doc_description or form_code == '070000':
            return '臨時報告書'
        # 有価証券届出書
        elif '有価証券届出書' in doc_description:
            return '有価証券届出書'
        # 変更報告書
        elif '変更報告書' in doc_description:
            return '変更報告書'
        # 訂正報告書
        elif '訂正' in doc_description:
            if '有価証券報告書' in doc_description:
                return '有価証券報告書（訂正）'
            elif '四半期報告書' in doc_description:
                return '四半期報告書（訂正）'
            elif '半期報告書' in doc_description:
                return '半期報告書（訂正）'
            else:
                return '訂正報告書'
        else:
            # form_codeから推定
            form_code_mapping = {
                '010000': '届出書',
                '020000': '目論見書',
                '030000': '有価証券報告書',
                '040000': '四半期報告書',
                '050000': '半期報告書',
                '060000': '臨時報告書',
                '070000': '臨時報告書',
                '080000': '親会社等状況報告書',
                '090000': '自己株券買付状況報告書',
                '100000': '変更報告書',
                '110000': '訂正届出書',
                '120000': '有価証券報告書',
                '130000': '有価証券報告書（訂正）'
            }
            return form_code_mapping.get(form_code, 'その他書類')

    def save_extracted_data(self, extracted_data: Dict, company_info: Dict, doc_info: Dict) -> str:
        """抽出データを保存"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        company_safe_name = company_info.get('提出者名', 'unknown').replace('株式会社', '').replace(' ', '_')[:10]
        
        # 文書の日付と名称を取得
        doc_date, doc_name = self._extract_document_date_and_name(doc_info)
        
        output_data = {
            'extraction_timestamp': timestamp,
            'company_info': company_info,
            'document_info': doc_info,
            'extracted_data': extracted_data
        }
        
        json_file = f"{company_safe_name}_financial_data_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        csv_data = []
        if 'financial_data' in extracted_data:
            for item_key, item_data in extracted_data['financial_data'].items():
                csv_data.append({
                    'date': doc_date,
                    'doc_name': doc_name,
                    'item_key': item_key,
                    'japanese_name': item_data['japanese_name'],
                    'value': item_data['value'],
                    'unit': item_data['unit'],
                    'importance': item_data['importance'],
                    'category': item_data['category']
                })
        
        if csv_data:
            csv_file = f"{company_safe_name}_financial_data_{timestamp}.csv"
            df = pd.DataFrame(csv_data)
            # カラム順序を明示的に指定
            column_order = ['date', 'doc_name', 'item_key', 'japanese_name', 'value', 'unit', 'importance', 'category']
            df = df[column_order]
            df.to_csv(csv_file, index=False, encoding='utf-8-sig')
            
            logger.info(f"CSV保存完了: {len(csv_data)}行のデータ")
        
        logger.info(f"抽出データを保存: {json_file}")
        return json_file
    
    def _ensure_output_directories(self) -> tuple[Path, Path]:
        """output/csvとoutput/jsonフォルダの存在確認と自動作成"""
        output_dir = Path('output')
        csv_dir = output_dir / 'csv'
        json_dir = output_dir / 'json'
        
        # 各フォルダの作成
        for dir_path in [output_dir, csv_dir, json_dir]:
            if not dir_path.exists():
                dir_path.mkdir(parents=True, exist_ok=True)
                logger.info(f"フォルダを作成しました: {dir_path.absolute()}")
        
        return csv_dir, json_dir
    
    def save_document_individual(self, extracted_data: Dict, company_info: Dict, doc_info: Dict) -> str:
        """単一文書を個別ファイルとして保存（CSV/JSON別フォルダ）"""
        # output/csvとoutput/jsonフォルダの確保
        csv_dir, json_dir = self._ensure_output_directories()
        
        # 企業情報から安全なファイル名要素を生成
        company_name = company_info.get('提出者名', 'unknown').replace('株式会社', '').replace(' ', '').replace('　', '')[:10]
        securities_code = company_info.get('証券コード', 'nocode')
        edinet_code = company_info.get('EDINETコード', 'noedinet')
        
        # 文書情報から日付と書類種別を取得
        doc_date, doc_name = self._extract_document_date_and_name(doc_info)
        
        # 日付をyyyymmdd形式に変換
        try:
            if doc_date and '-' in doc_date:
                date_str = doc_date.replace('-', '')
            else:
                date_str = datetime.now().strftime('%Y%m%d')
        except:
            date_str = datetime.now().strftime('%Y%m%d')
        
        # 書類種別をファイル名用に調整
        doc_name_safe = doc_name.replace('（', '').replace('）', '').replace('・', '').replace(' ', '')
        
        # ファイル名生成: 企業名_証券コード_EDINETコード_書類種別_yyyymmdd
        base_filename = f"{company_name}_{securities_code}_{edinet_code}_{doc_name_safe}_{date_str}"
        
        # JSON保存（output/jsonフォルダ内）
        output_data = {
            'extraction_date': date_str,
            'company_info': company_info,
            'document_info': doc_info,
            'extracted_data': extracted_data
        }
        
        json_file_path = json_dir / f"{base_filename}.json"
        with open(json_file_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        # CSV保存（output/csvフォルダ内）
        csv_data = []
        if 'financial_data' in extracted_data:
            for item_key, item_data in extracted_data['financial_data'].items():
                csv_data.append({
                    'date': doc_date,
                    'doc_name': doc_name,
                    'item_key': item_key,
                    'japanese_name': item_data['japanese_name'],
                    'value': item_data['value'],
                    'unit': item_data['unit'],
                    'importance': item_data['importance'],
                    'category': item_data['category']
                })
        
        if csv_data:
            csv_file_path = csv_dir / f"{base_filename}.csv"
            df = pd.DataFrame(csv_data)
            # カラム順序を明示的に指定
            column_order = ['date', 'doc_name', 'item_key', 'japanese_name', 'value', 'unit', 'importance', 'category']
            df = df[column_order]
            df.to_csv(csv_file_path, index=False, encoding='utf-8-sig')
            
            logger.info(f"個別CSV保存完了: {csv_file_path} ({len(csv_data)}行)")
        
        logger.info(f"個別ファイル保存完了: output/csv/{base_filename}.csv と output/json/{base_filename}.json")
        return str(json_file_path)
    
    def process_company_document(self, company_info: Dict, doc_info: Dict) -> Optional[str]:
        """企業文書の処理（完全パイプライン）"""
        doc_id = doc_info['docID']
        company_name = company_info.get('提出者名', 'unknown')
        
        logger.info(f"=== {company_name} の財務データ抽出開始 ===")
        logger.info(f"文書ID: {doc_id}")
        logger.info(f"提出日時: {doc_info.get('submitDateTime', '不明')}")
        logger.info(f"対象期間: {doc_info.get('periodStart', '不明')} ～ {doc_info.get('periodEnd', '不明')}")
        
        try:
            extract_path = self.download_and_extract_xbrl(doc_id)
            xbrl_files = self.find_xbrl_files(extract_path)
            
            if not xbrl_files:
                logger.error("XBRLファイルが見つかりませんでした")
                return None
            
            print(f"\n=== 利用可能なXBRLファイル ===")
            for i, file_info in enumerate(xbrl_files):
                print(f"{i+1}. {file_info['name']}")
                print(f"   種類: {file_info['type']}")
                print(f"   サイズ: {file_info['size']:,} bytes")
            
            # メインファイル（最初のファイル）を使用
            main_xbrl = xbrl_files[0]
            print(f"\n--- メインファイルを使用: {main_xbrl['name']} ---")
            
            extracted_data = self.extract_financial_data(main_xbrl)
            
            if not extracted_data:
                logger.error("財務データの抽出に失敗しました")
                return None
            
            # XBRLファイル一覧も保存データに追加
            extracted_data['available_xbrl_files'] = xbrl_files
            
            output_file = self.save_extracted_data(extracted_data, company_info, doc_info)
            
            shutil.rmtree(extract_path, ignore_errors=True)
            
            return output_file
            
        except Exception as e:
            logger.error(f"文書処理エラー: {e}")
            return None
    
    def display_extraction_summary(self, result_file: str):
        """抽出結果のサマリーを表示"""
        try:
            with open(result_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            extracted_data = data['extracted_data']
            summary = extracted_data.get('extraction_summary', {})
            financial_data = extracted_data.get('financial_data', {})
            source_info = extracted_data.get('source_file_info', {})
            
            print(f"\n=== 財務データ抽出サマリー ===")
            print(f"対象項目数: {summary.get('total_items', 0)}")
            print(f"抽出成功: {summary.get('found_items', 0)}")
            print(f"成功率: {summary.get('success_rate', 0)}%")
            
            # 文書情報
            doc_info = data.get('document_info', {})
            if doc_info:
                doc_date, doc_name = self._extract_document_date_and_name(doc_info)
                print(f"\n=== 対象文書情報 ===")
                print(f"書類名: {doc_name}")
                print(f"公開日: {doc_date}")
                print(f"文書: {doc_info.get('docDescription', '不明')}")
                print(f"対象期間: {doc_info.get('periodStart', '不明')} ～ {doc_info.get('periodEnd', '不明')}")
            
            # データソース情報
            if source_info:
                print(f"\n=== データソース情報 ===")
                print(f"使用ファイル: {source_info.get('filename', '不明')}")
                print(f"ファイル種類: {source_info.get('file_type', '不明')}")
                print(f"ファイルサイズ: {source_info.get('file_size', 0):,} bytes")
                print(f"抽出日時: {source_info.get('extraction_datetime', '不明')}")
            
            # 重要度別統計
            importance_stats = {}
            category_stats = {}
            successful_items = []
            
            for item_key, item_data in financial_data.items():
                importance = item_data.get('importance', 'unknown')
                if importance not in importance_stats:
                    importance_stats[importance] = {'total': 0, 'found': 0}
                importance_stats[importance]['total'] += 1
                
                category = item_data.get('category', 'unknown')
                if category not in category_stats:
                    category_stats[category] = {'total': 0, 'found': 0}
                category_stats[category]['total'] += 1
                
                if item_data.get('value') is not None:
                    importance_stats[importance]['found'] += 1
                    category_stats[category]['found'] += 1
                    successful_items.append(item_data)
            
            print(f"\n--- 重要度別抽出状況 ---")
            for importance, stats in importance_stats.items():
                rate = round(stats['found'] / stats['total'] * 100, 1) if stats['total'] > 0 else 0
                print(f"{importance}: {stats['found']}/{stats['total']} ({rate}%)")
            
            print(f"\n--- カテゴリ別抽出状況 ---")
            for category, stats in category_stats.items():
                rate = round(stats['found'] / stats['total'] * 100, 1) if stats['total'] > 0 else 0
                print(f"{category}: {stats['found']}/{stats['total']} ({rate}%)")
            
            if successful_items:
                print(f"\n--- 抽出成功例（最初の10項目） ---")
                for i, item in enumerate(successful_items[:10]):
                    value = item['value']
                    unit = item.get('unit', '')
                    name = item['japanese_name']
                    print(f"{i+1:2d}. {name}: {value} {unit}")
            
        except Exception as e:
            print(f"サマリー表示エラー: {e}")
    
    def process_date_range(self, company_info: Dict, start_date: str, end_date: str) -> List[str]:
        """日付範囲指定での複数文書処理"""
        company_name = company_info.get('提出者名', 'unknown')
        edinet_code = company_info.get('EDINETコード', 'unknown')
        
        print(f"\n=== {company_name} の日付範囲処理 ===")
        print(f"期間: {start_date} ～ {end_date}")
        print(f"EDINETコード: {edinet_code}")
        
        try:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_dt = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError as e:
            print(f"❌ 日付形式エラー: {e}")
            return []
        
        # 日付範囲での文書検索
        all_documents = []
        current_date = start_dt
        
        while current_date <= end_dt:
            try:
                print(f"検索中: {current_date}")
                documents = self.client.get_documents_list(current_date)
                securities_reports = self.client.filter_securities_reports(documents)
                
                # 対象企業の文書のみ抽出
                for doc in securities_reports:
                    if doc.get("edinetCode") == edinet_code:
                        doc['search_date'] = str(current_date)  # 検索日を記録
                        doc_name = self._classify_document_type(doc)
                        all_documents.append(doc)
                        print(f"  発見: {doc_name} - {doc.get('docDescription')} (提出: {doc.get('submitDateTime')})")
                
            except Exception as e:
                print(f"  エラー: {e}")
            
            current_date += timedelta(days=1)
        
        print(f"\n合計 {len(all_documents)} 件の文書が見つかりました")
        
        if not all_documents:
            print("対象期間に有価証券報告書が見つかりませんでした")
            return []
        
        # 各文書を処理
        result_files = []
        for i, doc in enumerate(all_documents, 1):
            print(f"\n--- 文書 {i}/{len(all_documents)} の処理 ---")
            print(f"文書: {doc.get('docDescription')}")
            print(f"検索日: {doc.get('search_date')}")
            
            result_file = self.process_company_document(company_info, doc)
            if result_file:
                result_files.append(result_file)
                print(f"✅ 処理完了: {result_file}")
            else:
                print(f"❌ 処理失敗")
        
        return result_files
    
    def process_date_range_individual(self, company_info: Dict, start_date: str, end_date: str) -> List[str]:
        """日付範囲内の文書を個別ファイルで処理"""
        edinet_code = company_info.get('EDINETコード')
        company_name = company_info.get('提出者名')
        
        logger.info(f"=== {company_name} の期間内文書個別処理開始 ===")
        logger.info(f"期間: {start_date} ～ {end_date}")
        
        # 日付範囲を設定
        current_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        all_documents = []
        
        print(f"\n--- 期間内文書検索: {start_date} ～ {end_date} ---")
        
        while current_date <= end_date_obj:
            print(f"検索中: {current_date}")
            
            try:
                documents = self.client.get_documents_list(current_date)
                securities_reports = self.client.filter_securities_reports(documents)
                
                # 対象企業の文書のみ抽出
                for doc in securities_reports:
                    if doc.get("edinetCode") == edinet_code:
                        doc['search_date'] = str(current_date)  # 検索日を記録
                        doc_name = self._classify_document_type(doc)
                        all_documents.append(doc)
                        print(f"  発見: {doc_name} - {doc.get('docDescription')} (提出: {doc.get('submitDateTime')})")
                
            except Exception as e:
                print(f"  エラー: {e}")
            
            current_date += timedelta(days=1)
        
        print(f"\n合計 {len(all_documents)} 件の文書が見つかりました")
        
        if not all_documents:
            print("対象期間に有価証券報告書が見つかりませんでした")
            return []
        
        # 各文書を個別ファイルで処理
        result_files = []
        for i, doc in enumerate(all_documents, 1):
            print(f"\n--- 文書 {i}/{len(all_documents)} の個別処理 ---")
            print(f"文書: {doc.get('docDescription')}")
            print(f"検索日: {doc.get('search_date')}")
            
            try:
                # XBRLダウンロードと解析
                doc_id = doc['docID']
                extract_path = self.download_and_extract_xbrl(doc_id)
                xbrl_files = self.find_xbrl_files(extract_path)
                
                if not xbrl_files:
                    print("❌ XBRLファイルが見つかりませんでした")
                    continue
                
                # メインファイルを使用してデータ抽出
                main_xbrl = xbrl_files[0]
                extracted_data = self.extract_financial_data(main_xbrl)
                
                if not extracted_data:
                    print("❌ 財務データ抽出に失敗しました")
                    continue
                
                # 個別ファイルで保存
                result_file = self.save_document_individual(extracted_data, company_info, doc)
                result_files.append(result_file)
                print(f"✅ 個別ファイル処理完了: {result_file}")
                
            except Exception as e:
                print(f"❌ 処理失敗: {e}")
                logger.error(f"文書処理エラー: {e}")
        
        return result_files
    
    def process_all_companies_in_period(self, start_date: str, end_date: str) -> List[str]:
        """全銘柄の期間内文書を一括処理"""
        logger.info(f"=== 全銘柄一括処理開始 ===")
        logger.info(f"期間: {start_date} ～ {end_date}")
        
        # 日付範囲を設定
        current_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        all_result_files = []
        processed_count = 0
        error_count = 0
        
        print(f"\n--- 全銘柄期間内文書一括処理: {start_date} ～ {end_date} ---")
        print("※ この処理は非常に時間がかかります（数時間〜数日）")
        print("※ 11,075社 × 期間内文書数の処理が実行されます")
        
        while current_date <= end_date_obj:
            print(f"\n🔍 日付: {current_date} の文書検索中...")
            
            try:
                # その日の全文書を取得
                documents = self.client.get_documents_list(current_date)
                securities_reports = self.client.filter_securities_reports(documents)
                
                print(f"  発見された文書数: {len(securities_reports)}件")
                
                # 各文書を処理
                for i, doc in enumerate(securities_reports, 1):
                    edinet_code = doc.get("edinetCode")
                    doc_description = doc.get("docDescription", "")
                    
                    print(f"  処理中 ({i}/{len(securities_reports)}): {doc_description[:50]}...")
                    
                    try:
                        # EDINETコードから企業情報を取得
                        company_info = self._get_company_info_by_edinet_code(edinet_code)
                        if not company_info:
                            print(f"    ❌ 企業情報が見つかりません: {edinet_code}")
                            error_count += 1
                            continue
                        
                        # XBRLダウンロードと解析
                        doc_id = doc['docID']
                        extract_path = self.download_and_extract_xbrl(doc_id)
                        xbrl_files = self.find_xbrl_files(extract_path)
                        
                        if not xbrl_files:
                            print(f"    ❌ XBRLファイルが見つかりません")
                            error_count += 1
                            continue
                        
                        # メインファイルを使用してデータ抽出
                        main_xbrl = xbrl_files[0]
                        extracted_data = self.extract_financial_data(main_xbrl)
                        
                        if not extracted_data:
                            print(f"    ❌ 財務データ抽出に失敗")
                            error_count += 1
                            continue
                        
                        # 個別ファイルで保存
                        result_file = self.save_document_individual(extracted_data, company_info, doc)
                        all_result_files.append(result_file)
                        processed_count += 1
                        
                        print(f"    ✅ 処理完了: {company_info.get('提出者名', 'unknown')}")
                        
                    except Exception as e:
                        print(f"    ❌ 処理エラー: {e}")
                        logger.error(f"文書処理エラー: {e}")
                        error_count += 1
                        
                    # APIレート制限対応
                    import time
                    time.sleep(1)
                
            except Exception as e:
                print(f"  日付処理エラー: {e}")
                logger.error(f"日付処理エラー: {e}")
            
            current_date += timedelta(days=1)
        
        print(f"\n=== 全銘柄一括処理完了 ===")
        print(f"処理成功: {processed_count}件")
        print(f"処理失敗: {error_count}件")
        print(f"出力ファイル数: {len(all_result_files) * 2}件（CSV/JSON各{len(all_result_files)}件）")
        print(f"CSV出力フォルダ: ./output/csv/")
        print(f"JSON出力フォルダ: ./output/json/")
        
        return all_result_files
    
    def _get_company_info_by_edinet_code(self, edinet_code: str) -> Optional[Dict]:
        """EDINETコードから企業情報を取得"""
        if self.edinet_list_df is None:
            return None
        
        results = self.edinet_list_df[self.edinet_list_df['EDINETコード'] == edinet_code]
        if len(results) == 0:
            return None
        
        return results.iloc[0].to_dict()
    
    def run_interactive_mode(self):
        """対話型メイン処理"""
        print("=== 統合財務データ取得システム ===")
        print("企業を選択して70項目の財務データを自動取得します")
        
        while True:
            try:
                # 1. 企業選択
                print("\n" + "="*50)
                company_info = self.display_company_selection_menu()
                
                if company_info is None:
                    print("システムを終了します。")
                    break
                
                # 全銘柄一括処理の判定
                if company_info.get('全銘柄一括処理'):
                    print(f"\n=== 🚀 全銘柄一括処理モード ===")
                    print("期間内の全企業（11,075社）の財務データを一括取得します")
                    print("※ この処理は非常に時間がかかります（数時間〜数日）")
                    print("※ CSV出力先: ./output/csv/ フォルダ")
                    print("※ JSON出力先: ./output/json/ フォルダ")
                    print("※ ファイル名: 企業名_証券コード_EDINETコード_書類種別_yyyymmdd")
                    
                    # 期間指定
                    print(f"\n日付形式: YYYY-MM-DD（例: 2024-01-01）")
                    start_date = input("開始日を入力してください: ").strip()
                    end_date = input("終了日を入力してください: ").strip()
                    
                    if not start_date or not end_date:
                        print("日付が入力されませんでした。")
                        continue
                    
                    print(f"\n⚠️  警告: {start_date} ～ {end_date} の期間で全銘柄処理を実行します")
                    print("この処理は非常に時間がかかり、大量のファイルが生成されます")
                    confirm = input("本当に実行しますか？ (yes/no): ").strip().lower()
                    
                    if confirm != 'yes':
                        print("処理をキャンセルしました。")
                        continue
                    
                    # 全銘柄一括処理実行
                    result_files = self.process_all_companies_in_period(start_date, end_date)
                    
                    if result_files:
                        print(f"\n🎉 全銘柄一括処理完了!")
                        print(f"処理済みファイル数: {len(result_files) * 2}件（CSV: {len(result_files)}件, JSON: {len(result_files)}件）")
                        print("CSVファイル: ./output/csv/ フォルダに保存")
                        print("JSONファイル: ./output/json/ フォルダに保存")
                    else:
                        print("❌ 処理できた文書がありませんでした。")
                    
                    # 次の処理確認
                    continue_choice = input("\n別の処理を実行しますか？ (y/n): ").strip().lower()
                    if continue_choice not in ['y', 'yes', 'はい']:
                        break
                    continue
                
                # 2. 企業詳細表示（通常モード）
                print(f"\n=== 選択された企業 ===")
                print(f"企業名: {company_info['提出者名']}")
                print(f"EDINETコード: {company_info['EDINETコード']}")
                print(f"証券コード: {company_info.get('証券コード', 'なし')}")
                print(f"決算日: {company_info.get('決算日', '不明')}")
                print(f"業種: {company_info.get('提出者業種', '不明')}")
                
                # 3. 処理モード選択
                print(f"\n=== 処理モード選択 ===")
                print("1: 最新の有価証券報告書のみ取得")
                print("2: 日付範囲を指定して複数文書を統合CSV出力")
                print("3: 日付範囲を指定して各文書を個別ファイル出力")
                print("0: 企業選択に戻る")
                
                mode_choice = input("\nモードを選択してください (1/2/3/0): ").strip()
                
                if mode_choice == '0':
                    continue
                elif mode_choice == '1':
                    # 最新文書のみ処理
                    print("\n--- 有価証券報告書を検索中 ---")
                    documents = self.find_company_documents(company_info)
                    
                    if not documents:
                        print("有価証券報告書が見つかりませんでした。")
                        continue
                    
                    latest_doc = documents[0]
                    print(f"\n=== 発見された文書 ===")
                    print(f"文書: {latest_doc.get('docDescription')}")
                    print(f"文書ID: {latest_doc.get('docID')}")
                    print(f"提出日時: {latest_doc.get('submitDateTime')}")
                    print(f"対象期間: {latest_doc.get('periodStart')} ～ {latest_doc.get('periodEnd')}")
                    
                    analyze = input("\nXBRLファイルを解析して財務データを抽出しますか？ (y/n): ").strip().lower()
                    
                    if analyze not in ['y', 'yes', 'はい']:
                        continue
                    
                    print("\n--- XBRLファイル解析中 ---")
                    print("※ この処理には数分かかる場合があります")
                    
                    result_file = self.process_company_document(company_info, latest_doc)
                    
                    if result_file:
                        print(f"\n✅ 財務データ抽出完了!")
                        print(f"結果ファイル: {result_file}")
                        self.display_extraction_summary(result_file)
                    else:
                        print("❌ 財務データ抽出に失敗しました。")
                
                elif mode_choice == '2':
                    # 日付範囲指定処理
                    print(f"\n=== 日付範囲指定 ===")
                    print("日付形式: YYYY-MM-DD（例: 2024-01-01）")
                    
                    start_date = input("開始日を入力してください: ").strip()
                    end_date = input("終了日を入力してください: ").strip()
                    
                    if not start_date or not end_date:
                        print("日付が入力されませんでした。")
                        continue
                    
                    confirm = input(f"\n期間 {start_date} ～ {end_date} で処理しますか？ (y/n): ").strip().lower()
                    
                    if confirm not in ['y', 'yes', 'はい']:
                        continue
                    
                    print("\n--- 日付範囲での文書処理開始 ---")
                    print("※ 期間が長い場合は処理に時間がかかります")
                    
                    result_files = self.process_date_range(company_info, start_date, end_date)
                    
                    if result_files:
                        print(f"\n✅ 日付範囲処理完了!")
                        print(f"処理されたファイル数: {len(result_files)}")
                        for result_file in result_files:
                            print(f"  - {result_file}")
                    else:
                        print("❌ 処理できた文書がありませんでした。")
                
                elif mode_choice == '3':
                    # 日付範囲指定個別ファイル処理
                    print(f"\n=== 日付範囲指定（個別ファイル出力） ===")
                    print("日付形式: YYYY-MM-DD（例: 2024-01-01）")
                    print("※ 各文書が個別のファイルで保存されます")
                    print("※ CSV出力先: ./output/csv/ フォルダ")
                    print("※ JSON出力先: ./output/json/ フォルダ")
                    print("※ ファイル名: 企業名_証券コード_EDINETコード_書類種別_yyyymmdd")
                    
                    start_date = input("開始日を入力してください: ").strip()
                    end_date = input("終了日を入力してください: ").strip()
                    
                    if not start_date or not end_date:
                        print("日付が入力されませんでした。")
                        continue
                    
                    confirm = input(f"\n期間 {start_date} ～ {end_date} で各文書を個別ファイル出力しますか？ (y/n): ").strip().lower()
                    
                    if confirm not in ['y', 'yes', 'はい']:
                        continue
                    
                    print("\n--- 日付範囲での個別ファイル処理開始 ---")
                    print("※ 期間が長い場合は処理に時間がかかります")
                    print("※ 有価証券報告書と四半期報告書を取得します")
                    
                    result_files = self.process_date_range_individual(company_info, start_date, end_date)
                    
                    if result_files:
                        print(f"\n✅ 個別ファイル処理完了!")
                        print(f"生成されたファイル数: {len(result_files) * 2}件（CSV: {len(result_files)}件, JSON: {len(result_files)}件）")
                        print("CSV出力フォルダ: ./output/csv/")
                        print("JSON出力フォルダ: ./output/json/")
                        print("生成されたファイル:")
                        for result_file in result_files:
                            # ファイル名のみ表示
                            json_filename = Path(result_file).name
                            csv_filename = json_filename.replace('.json', '.csv')
                            print(f"  - csv/{csv_filename}")
                            print(f"  - json/{json_filename}")
                    else:
                        print("❌ 処理できた文書がありませんでした。")
                
                else:
                    print("無効な選択です。")
                    continue
                
                # 継続確認
                continue_choice = input("\n別の企業を処理しますか？ (y/n): ").strip().lower()
                if continue_choice not in ['y', 'yes', 'はい']:
                    break
                    
            except KeyboardInterrupt:
                print("\n\n処理が中断されました。")
                break
            except Exception as e:
                logger.error(f"システムエラー: {e}")
                print(f"エラーが発生しました: {e}")
                continue_choice = input("\n別の企業を処理しますか？ (y/n): ").strip().lower()
                if continue_choice not in ['y', 'yes', 'はい']:
                    break


def main():
    """メイン処理"""
    try:
        extractor = FinancialDataExtractor()
        extractor.run_interactive_mode()
        
    except KeyboardInterrupt:
        print("\n\n処理を中断しました。")
    except Exception as e:
        logger.error(f"システム初期化エラー: {e}")
        print(f"システムエラー: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()