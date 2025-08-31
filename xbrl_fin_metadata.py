"""
XBRLから取得可能な財務データ項目のリスト化
"""
import csv
from datetime import datetime

def generate_xbrl_financial_items():
    """XBRLから取得可能な財務項目を定義してCSV出力"""
    
    # 財務データ項目の定義
    financial_items = []
    
    # 損益計算書（P/L）項目
    pl_items = [
        {
            "category": "損益計算書",
            "subcategory": "売上",
            "item_name_jp": "売上高",
            "item_name_en": "NetSales",
            "xbrl_element": "jppfs_cor:NetSales",
            "description": "企業の主たる営業活動から得た収益の総額",
            "unit": "円",
            "importance": "最重要",
            "calculation": "直接取得"
        },
        {
            "category": "損益計算書",
            "subcategory": "売上",
            "item_name_jp": "売上原価",
            "item_name_en": "CostOfSales",
            "xbrl_element": "jppfs_cor:CostOfSales",
            "description": "売上高に対応する商品・サービスの原価",
            "unit": "円",
            "importance": "重要",
            "calculation": "直接取得"
        },
        {
            "category": "損益計算書",
            "subcategory": "売上",
            "item_name_jp": "売上総利益",
            "item_name_en": "GrossProfit",
            "xbrl_element": "jppfs_cor:GrossProfit",
            "description": "売上高から売上原価を差し引いた利益",
            "unit": "円",
            "importance": "重要",
            "calculation": "売上高 - 売上原価"
        },
        {
            "category": "損益計算書",
            "subcategory": "営業損益",
            "item_name_jp": "販売費及び一般管理費",
            "item_name_en": "SellingGeneralAndAdministrativeExpenses",
            "xbrl_element": "jppfs_cor:SellingGeneralAndAdministrativeExpenses",
            "description": "営業活動に必要な販売費と管理費の合計",
            "unit": "円",
            "importance": "重要",
            "calculation": "直接取得"
        },
        {
            "category": "損益計算書",
            "subcategory": "営業損益",
            "item_name_jp": "営業利益",
            "item_name_en": "OperatingIncome",
            "xbrl_element": "jppfs_cor:OperatingIncome",
            "description": "本業から得られた利益。売上総利益から販管費を差し引いた額",
            "unit": "円",
            "importance": "最重要",
            "calculation": "売上総利益 - 販管費"
        },
        {
            "category": "損益計算書",
            "subcategory": "経常損益",
            "item_name_jp": "営業外収益",
            "item_name_en": "NonOperatingIncome",
            "xbrl_element": "jppfs_cor:NonOperatingIncome",
            "description": "本業以外から得られる収益（受取利息、配当金等）",
            "unit": "円",
            "importance": "通常",
            "calculation": "直接取得"
        },
        {
            "category": "損益計算書",
            "subcategory": "経常損益",
            "item_name_jp": "営業外費用",
            "item_name_en": "NonOperatingExpenses",
            "xbrl_element": "jppfs_cor:NonOperatingExpenses",
            "description": "本業以外で発生する費用（支払利息等）",
            "unit": "円",
            "importance": "通常",
            "calculation": "直接取得"
        },
        {
            "category": "損益計算書",
            "subcategory": "経常損益",
            "item_name_jp": "経常利益",
            "item_name_en": "OrdinaryIncome",
            "xbrl_element": "jppfs_cor:OrdinaryIncome",
            "description": "経常的な事業活動から得られる利益",
            "unit": "円",
            "importance": "最重要",
            "calculation": "営業利益 + 営業外収益 - 営業外費用"
        },
        {
            "category": "損益計算書",
            "subcategory": "特別損益",
            "item_name_jp": "特別利益",
            "item_name_en": "ExtraordinaryIncome",
            "xbrl_element": "jppfs_cor:ExtraordinaryIncome",
            "description": "臨時的・偶発的に発生した利益",
            "unit": "円",
            "importance": "通常",
            "calculation": "直接取得"
        },
        {
            "category": "損益計算書",
            "subcategory": "特別損益",
            "item_name_jp": "特別損失",
            "item_name_en": "ExtraordinaryLosses",
            "xbrl_element": "jppfs_cor:ExtraordinaryLosses",
            "description": "臨時的・偶発的に発生した損失",
            "unit": "円",
            "importance": "通常",
            "calculation": "直接取得"
        },
        {
            "category": "損益計算書",
            "subcategory": "税引前後損益",
            "item_name_jp": "税金等調整前当期純利益",
            "item_name_en": "IncomeBeforeIncomeTaxes",
            "xbrl_element": "jppfs_cor:IncomeBeforeIncomeTaxes",
            "description": "法人税等を控除する前の利益",
            "unit": "円",
            "importance": "重要",
            "calculation": "経常利益 + 特別利益 - 特別損失"
        },
        {
            "category": "損益計算書",
            "subcategory": "税引前後損益",
            "item_name_jp": "法人税等",
            "item_name_en": "IncomeTaxes",
            "xbrl_element": "jppfs_cor:IncomeTaxes",
            "description": "法人税、住民税及び事業税の合計",
            "unit": "円",
            "importance": "通常",
            "calculation": "直接取得"
        },
        {
            "category": "損益計算書",
            "subcategory": "税引前後損益",
            "item_name_jp": "当期純利益",
            "item_name_en": "NetIncome",
            "xbrl_element": "jppfs_cor:NetIncome",
            "description": "最終的な利益。全ての収益から全ての費用を差し引いた額",
            "unit": "円",
            "importance": "最重要",
            "calculation": "税金等調整前当期純利益 - 法人税等"
        },
        {
            "category": "損益計算書",
            "subcategory": "税引前後損益",
            "item_name_jp": "親会社株主に帰属する当期純利益",
            "item_name_en": "ProfitAttributableToOwnersOfParent",
            "xbrl_element": "jppfs_cor:ProfitAttributableToOwnersOfParent",
            "description": "連結決算における親会社の株主に帰属する利益",
            "unit": "円",
            "importance": "最重要",
            "calculation": "当期純利益から非支配株主持分を除いた額"
        }
    ]
    
    # 貸借対照表（B/S）項目
    bs_items = [
        # 流動資産
        {
            "category": "貸借対照表",
            "subcategory": "流動資産",
            "item_name_jp": "流動資産",
            "item_name_en": "CurrentAssets",
            "xbrl_element": "jppfs_cor:CurrentAssets",
            "description": "1年以内に現金化される資産の合計",
            "unit": "円",
            "importance": "重要",
            "calculation": "直接取得"
        },
        {
            "category": "貸借対照表",
            "subcategory": "流動資産",
            "item_name_jp": "現金及び預金",
            "item_name_en": "CashAndDeposits",
            "xbrl_element": "jppfs_cor:CashAndDeposits",
            "description": "現金と銀行預金の合計",
            "unit": "円",
            "importance": "最重要",
            "calculation": "直接取得"
        },
        {
            "category": "貸借対照表",
            "subcategory": "流動資産",
            "item_name_jp": "受取手形及び売掛金",
            "item_name_en": "NotesAndAccountsReceivableTrade",
            "xbrl_element": "jppfs_cor:NotesAndAccountsReceivableTrade",
            "description": "商品やサービスの販売による未回収金",
            "unit": "円",
            "importance": "重要",
            "calculation": "直接取得"
        },
        {
            "category": "貸借対照表",
            "subcategory": "流動資産",
            "item_name_jp": "棚卸資産",
            "item_name_en": "Inventories",
            "xbrl_element": "jppfs_cor:Inventories",
            "description": "商品、製品、原材料、仕掛品等の在庫",
            "unit": "円",
            "importance": "重要",
            "calculation": "直接取得"
        },
        {
            "category": "貸借対照表",
            "subcategory": "流動資産",
            "item_name_jp": "有価証券",
            "item_name_en": "ShortTermInvestmentSecurities",
            "xbrl_element": "jppfs_cor:ShortTermInvestmentSecurities",
            "description": "短期保有目的の有価証券",
            "unit": "円",
            "importance": "通常",
            "calculation": "直接取得"
        },
        # 固定資産
        {
            "category": "貸借対照表",
            "subcategory": "固定資産",
            "item_name_jp": "固定資産",
            "item_name_en": "NonCurrentAssets",
            "xbrl_element": "jppfs_cor:NonCurrentAssets",
            "description": "1年を超えて保有する資産の合計",
            "unit": "円",
            "importance": "重要",
            "calculation": "直接取得"
        },
        {
            "category": "貸借対照表",
            "subcategory": "固定資産",
            "item_name_jp": "有形固定資産",
            "item_name_en": "PropertyPlantAndEquipment",
            "xbrl_element": "jppfs_cor:PropertyPlantAndEquipment",
            "description": "土地、建物、機械装置等の物理的な資産",
            "unit": "円",
            "importance": "重要",
            "calculation": "直接取得"
        },
        {
            "category": "貸借対照表",
            "subcategory": "固定資産",
            "item_name_jp": "無形固定資産",
            "item_name_en": "IntangibleAssets",
            "xbrl_element": "jppfs_cor:IntangibleAssets",
            "description": "特許権、商標権、ソフトウェア等の無形の資産",
            "unit": "円",
            "importance": "通常",
            "calculation": "直接取得"
        },
        {
            "category": "貸借対照表",
            "subcategory": "固定資産",
            "item_name_jp": "投資その他の資産",
            "item_name_en": "InvestmentsAndOtherAssets",
            "xbrl_element": "jppfs_cor:InvestmentsAndOtherAssets",
            "description": "長期保有の投資有価証券、長期貸付金等",
            "unit": "円",
            "importance": "通常",
            "calculation": "直接取得"
        },
        # 資産合計
        {
            "category": "貸借対照表",
            "subcategory": "資産合計",
            "item_name_jp": "資産合計",
            "item_name_en": "TotalAssets",
            "xbrl_element": "jppfs_cor:TotalAssets",
            "description": "全ての資産の合計額",
            "unit": "円",
            "importance": "最重要",
            "calculation": "流動資産 + 固定資産"
        },
        # 流動負債
        {
            "category": "貸借対照表",
            "subcategory": "流動負債",
            "item_name_jp": "流動負債",
            "item_name_en": "CurrentLiabilities",
            "xbrl_element": "jppfs_cor:CurrentLiabilities",
            "description": "1年以内に支払期限が到来する負債",
            "unit": "円",
            "importance": "重要",
            "calculation": "直接取得"
        },
        {
            "category": "貸借対照表",
            "subcategory": "流動負債",
            "item_name_jp": "支払手形及び買掛金",
            "item_name_en": "NotesAndAccountsPayableTrade",
            "xbrl_element": "jppfs_cor:NotesAndAccountsPayableTrade",
            "description": "商品や原材料の購入による未払金",
            "unit": "円",
            "importance": "重要",
            "calculation": "直接取得"
        },
        {
            "category": "貸借対照表",
            "subcategory": "流動負債",
            "item_name_jp": "短期借入金",
            "item_name_en": "ShortTermBorrowings",
            "xbrl_element": "jppfs_cor:ShortTermBorrowings",
            "description": "1年以内に返済予定の借入金",
            "unit": "円",
            "importance": "重要",
            "calculation": "直接取得"
        },
        # 固定負債
        {
            "category": "貸借対照表",
            "subcategory": "固定負債",
            "item_name_jp": "固定負債",
            "item_name_en": "NonCurrentLiabilities",
            "xbrl_element": "jppfs_cor:NonCurrentLiabilities",
            "description": "1年を超えて支払期限が到来する負債",
            "unit": "円",
            "importance": "重要",
            "calculation": "直接取得"
        },
        {
            "category": "貸借対照表",
            "subcategory": "固定負債",
            "item_name_jp": "長期借入金",
            "item_name_en": "LongTermBorrowings",
            "xbrl_element": "jppfs_cor:LongTermBorrowings",
            "description": "1年を超えて返済予定の借入金",
            "unit": "円",
            "importance": "重要",
            "calculation": "直接取得"
        },
        {
            "category": "貸借対照表",
            "subcategory": "固定負債",
            "item_name_jp": "社債",
            "item_name_en": "BondsPayable",
            "xbrl_element": "jppfs_cor:BondsPayable",
            "description": "企業が発行した社債の残高",
            "unit": "円",
            "importance": "通常",
            "calculation": "直接取得"
        },
        # 負債合計
        {
            "category": "貸借対照表",
            "subcategory": "負債合計",
            "item_name_jp": "負債合計",
            "item_name_en": "TotalLiabilities",
            "xbrl_element": "jppfs_cor:TotalLiabilities",
            "description": "全ての負債の合計額",
            "unit": "円",
            "importance": "最重要",
            "calculation": "流動負債 + 固定負債"
        },
        # 純資産
        {
            "category": "貸借対照表",
            "subcategory": "純資産",
            "item_name_jp": "純資産合計",
            "item_name_en": "TotalNetAssets",
            "xbrl_element": "jppfs_cor:TotalNetAssets",
            "description": "資産から負債を差し引いた企業の正味価値",
            "unit": "円",
            "importance": "最重要",
            "calculation": "資産合計 - 負債合計"
        },
        {
            "category": "貸借対照表",
            "subcategory": "純資産",
            "item_name_jp": "資本金",
            "item_name_en": "CapitalStock",
            "xbrl_element": "jppfs_cor:CapitalStock",
            "description": "株主が払い込んだ資本の額",
            "unit": "円",
            "importance": "重要",
            "calculation": "直接取得"
        },
        {
            "category": "貸借対照表",
            "subcategory": "純資産",
            "item_name_jp": "資本剰余金",
            "item_name_en": "CapitalSurplus",
            "xbrl_element": "jppfs_cor:CapitalSurplus",
            "description": "資本金以外の株主からの払込金",
            "unit": "円",
            "importance": "通常",
            "calculation": "直接取得"
        },
        {
            "category": "貸借対照表",
            "subcategory": "純資産",
            "item_name_jp": "利益剰余金",
            "item_name_en": "RetainedEarnings",
            "xbrl_element": "jppfs_cor:RetainedEarnings",
            "description": "過去の利益の累積額",
            "unit": "円",
            "importance": "重要",
            "calculation": "直接取得"
        },
        {
            "category": "貸借対照表",
            "subcategory": "純資産",
            "item_name_jp": "自己株式",
            "item_name_en": "TreasuryShares",
            "xbrl_element": "jppfs_cor:TreasuryShares",
            "description": "企業が自社の株式を取得した額（マイナス表示）",
            "unit": "円",
            "importance": "通常",
            "calculation": "直接取得"
        }
    ]
    
    # キャッシュフロー計算書項目
    cf_items = [
        {
            "category": "キャッシュフロー計算書",
            "subcategory": "営業活動",
            "item_name_jp": "営業活動によるキャッシュフロー",
            "item_name_en": "CashFlowsFromOperatingActivities",
            "xbrl_element": "jppfs_cor:NetCashProvidedByUsedInOperatingActivities",
            "description": "本業の営業活動から生じた現金の増減",
            "unit": "円",
            "importance": "最重要",
            "calculation": "直接取得"
        },
        {
            "category": "キャッシュフロー計算書",
            "subcategory": "投資活動",
            "item_name_jp": "投資活動によるキャッシュフロー",
            "item_name_en": "CashFlowsFromInvestingActivities",
            "xbrl_element": "jppfs_cor:NetCashProvidedByUsedInInvestingActivities",
            "description": "設備投資や有価証券投資による現金の増減",
            "unit": "円",
            "importance": "最重要",
            "calculation": "直接取得"
        },
        {
            "category": "キャッシュフロー計算書",
            "subcategory": "財務活動",
            "item_name_jp": "財務活動によるキャッシュフロー",
            "item_name_en": "CashFlowsFromFinancingActivities",
            "xbrl_element": "jppfs_cor:NetCashProvidedByUsedInFinancingActivities",
            "description": "借入、返済、配当支払等による現金の増減",
            "unit": "円",
            "importance": "最重要",
            "calculation": "直接取得"
        },
        {
            "category": "キャッシュフロー計算書",
            "subcategory": "現金残高",
            "item_name_jp": "現金及び現金同等物の期末残高",
            "item_name_en": "CashAndCashEquivalentsAtEndOfPeriod",
            "xbrl_element": "jppfs_cor:CashAndCashEquivalentsAtEndOfPeriod",
            "description": "期末時点の現金及び現金同等物の残高",
            "unit": "円",
            "importance": "重要",
            "calculation": "直接取得"
        },
        {
            "category": "キャッシュフロー計算書",
            "subcategory": "現金残高",
            "item_name_jp": "フリーキャッシュフロー",
            "item_name_en": "FreeCashFlow",
            "xbrl_element": "計算項目",
            "description": "企業が自由に使える現金。営業CF＋投資CF",
            "unit": "円",
            "importance": "最重要",
            "calculation": "営業CF + 投資CF"
        }
    ]
    
    # その他の重要指標
    other_items = [
        {
            "category": "その他指標",
            "subcategory": "従業員情報",
            "item_name_jp": "従業員数",
            "item_name_en": "NumberOfEmployees",
            "xbrl_element": "jppfs_cor:NumberOfEmployees",
            "description": "期末時点の従業員数",
            "unit": "人",
            "importance": "重要",
            "calculation": "直接取得"
        },
        {
            "category": "その他指標",
            "subcategory": "従業員情報",
            "item_name_jp": "平均年間給与",
            "item_name_en": "AverageAnnualSalary",
            "xbrl_element": "jppfs_cor:AverageAnnualSalary",
            "description": "従業員の平均年間給与額",
            "unit": "円",
            "importance": "重要",
            "calculation": "直接取得"
        },
        {
            "category": "その他指標",
            "subcategory": "従業員情報",
            "item_name_jp": "平均勤続年数",
            "item_name_en": "AverageYearsOfService",
            "xbrl_element": "jppfs_cor:AverageLengthOfServiceYears",
            "description": "従業員の平均勤続年数",
            "unit": "年",
            "importance": "通常",
            "calculation": "直接取得"
        },
        {
            "category": "その他指標",
            "subcategory": "従業員情報",
            "item_name_jp": "平均年齢",
            "item_name_en": "AverageAge",
            "xbrl_element": "jppfs_cor:AverageAgeYears",
            "description": "従業員の平均年齢",
            "unit": "歳",
            "importance": "通常",
            "calculation": "直接取得"
        },
        {
            "category": "その他指標",
            "subcategory": "研究開発",
            "item_name_jp": "研究開発費",
            "item_name_en": "ResearchAndDevelopmentExpenses",
            "xbrl_element": "jppfs_cor:ResearchAndDevelopmentExpenses",
            "description": "研究開発活動に使用した費用",
            "unit": "円",
            "importance": "重要",
            "calculation": "直接取得"
        },
        {
            "category": "その他指標",
            "subcategory": "設備投資",
            "item_name_jp": "設備投資額",
            "item_name_en": "CapitalExpenditures",
            "xbrl_element": "jppfs_cor:CapitalExpenditures",
            "description": "有形固定資産の取得に使用した金額",
            "unit": "円",
            "importance": "重要",
            "calculation": "直接取得"
        },
        {
            "category": "その他指標",
            "subcategory": "設備投資",
            "item_name_jp": "減価償却費",
            "item_name_en": "DepreciationAndAmortization",
            "xbrl_element": "jppfs_cor:DepreciationAndAmortization",
            "description": "固定資産の価値減少分",
            "unit": "円",
            "importance": "重要",
            "calculation": "直接取得"
        },
        {
            "category": "その他指標",
            "subcategory": "配当",
            "item_name_jp": "一株当たり配当金",
            "item_name_en": "DividendPerShare",
            "xbrl_element": "jppfs_cor:DividendPaidPerShare",
            "description": "一株当たりの配当金額",
            "unit": "円/株",
            "importance": "重要",
            "calculation": "直接取得"
        },
        {
            "category": "その他指標",
            "subcategory": "一株指標",
            "item_name_jp": "一株当たり純利益（EPS）",
            "item_name_en": "EarningsPerShare",
            "xbrl_element": "jppfs_cor:BasicEarningsPerShare",
            "description": "一株当たりの純利益",
            "unit": "円/株",
            "importance": "最重要",
            "calculation": "当期純利益 ÷ 発行済株式数"
        },
        {
            "category": "その他指標",
            "subcategory": "一株指標",
            "item_name_jp": "一株当たり純資産（BPS）",
            "item_name_en": "BookValuePerShare",
            "xbrl_element": "jppfs_cor:NetAssetsPerShare",
            "description": "一株当たりの純資産額",
            "unit": "円/株",
            "importance": "重要",
            "calculation": "純資産 ÷ 発行済株式数"
        }
    ]
    
    # 財務比率（計算項目）
    ratio_items = [
        {
            "category": "財務比率",
            "subcategory": "収益性",
            "item_name_jp": "売上高総利益率",
            "item_name_en": "GrossProfitMargin",
            "xbrl_element": "計算項目",
            "description": "売上高に対する売上総利益の割合",
            "unit": "%",
            "importance": "重要",
            "calculation": "(売上総利益 ÷ 売上高) × 100"
        },
        {
            "category": "財務比率",
            "subcategory": "収益性",
            "item_name_jp": "売上高営業利益率",
            "item_name_en": "OperatingProfitMargin",
            "xbrl_element": "計算項目",
            "description": "売上高に対する営業利益の割合",
            "unit": "%",
            "importance": "最重要",
            "calculation": "(営業利益 ÷ 売上高) × 100"
        },
        {
            "category": "財務比率",
            "subcategory": "収益性",
            "item_name_jp": "売上高経常利益率",
            "item_name_en": "OrdinaryProfitMargin",
            "xbrl_element": "計算項目",
            "description": "売上高に対する経常利益の割合",
            "unit": "%",
            "importance": "重要",
            "calculation": "(経常利益 ÷ 売上高) × 100"
        },
        {
            "category": "財務比率",
            "subcategory": "収益性",
            "item_name_jp": "売上高純利益率",
            "item_name_en": "NetProfitMargin",
            "xbrl_element": "計算項目",
            "description": "売上高に対する純利益の割合",
            "unit": "%",
            "importance": "重要",
            "calculation": "(当期純利益 ÷ 売上高) × 100"
        },
        {
            "category": "財務比率",
            "subcategory": "収益性",
            "item_name_jp": "ROE（自己資本利益率）",
            "item_name_en": "ReturnOnEquity",
            "xbrl_element": "計算項目",
            "description": "自己資本に対する純利益の割合。株主資本の効率性",
            "unit": "%",
            "importance": "最重要",
            "calculation": "(当期純利益 ÷ 純資産) × 100"
        },
        {
            "category": "財務比率",
            "subcategory": "収益性",
            "item_name_jp": "ROA（総資産利益率）",
            "item_name_en": "ReturnOnAssets",
            "xbrl_element": "計算項目",
            "description": "総資産に対する純利益の割合。資産の効率性",
            "unit": "%",
            "importance": "最重要",
            "calculation": "(当期純利益 ÷ 総資産) × 100"
        },
        {
            "category": "財務比率",
            "subcategory": "効率性",
            "item_name_jp": "総資産回転率",
            "item_name_en": "AssetTurnover",
            "xbrl_element": "計算項目",
            "description": "総資産がどれだけ効率的に売上を生み出しているか",
            "unit": "回",
            "importance": "重要",
            "calculation": "売上高 ÷ 総資産"
        },
        {
            "category": "財務比率",
            "subcategory": "効率性",
            "item_name_jp": "棚卸資産回転率",
            "item_name_en": "InventoryTurnover",
            "xbrl_element": "計算項目",
            "description": "在庫の回転効率",
            "unit": "回",
            "importance": "通常",
            "calculation": "売上原価 ÷ 棚卸資産"
        },
        {
            "category": "財務比率",
            "subcategory": "安全性",
            "item_name_jp": "自己資本比率",
            "item_name_en": "EquityRatio",
            "xbrl_element": "計算項目",
            "description": "総資産に占める自己資本の割合。財務の健全性",
            "unit": "%",
            "importance": "最重要",
            "calculation": "(純資産 ÷ 総資産) × 100"
        },
        {
            "category": "財務比率",
            "subcategory": "安全性",
            "item_name_jp": "流動比率",
            "item_name_en": "CurrentRatio",
            "xbrl_element": "計算項目",
            "description": "流動負債に対する流動資産の割合。短期的な支払能力",
            "unit": "%",
            "importance": "重要",
            "calculation": "(流動資産 ÷ 流動負債) × 100"
        },
        {
            "category": "財務比率",
            "subcategory": "安全性",
            "item_name_jp": "当座比率",
            "item_name_en": "QuickRatio",
            "xbrl_element": "計算項目",
            "description": "即座に現金化可能な資産による支払能力",
            "unit": "%",
            "importance": "通常",
            "calculation": "((流動資産 - 棚卸資産) ÷ 流動負債) × 100"
        },
        {
            "category": "財務比率",
            "subcategory": "安全性",
            "item_name_jp": "負債比率",
            "item_name_en": "DebtRatio",
            "xbrl_element": "計算項目",
            "description": "自己資本に対する負債の割合",
            "unit": "%",
            "importance": "重要",
            "calculation": "(負債合計 ÷ 純資産) × 100"
        },
        {
            "category": "財務比率",
            "subcategory": "成長性",
            "item_name_jp": "売上高成長率",
            "item_name_en": "SalesGrowthRate",
            "xbrl_element": "計算項目",
            "description": "前期比での売上高の成長率",
            "unit": "%",
            "importance": "最重要",
            "calculation": "((当期売上高 - 前期売上高) ÷ 前期売上高) × 100"
        },
        {
            "category": "財務比率",
            "subcategory": "成長性",
            "item_name_jp": "営業利益成長率",
            "item_name_en": "OperatingIncomeGrowthRate",
            "xbrl_element": "計算項目",
            "description": "前期比での営業利益の成長率",
            "unit": "%",
            "importance": "重要",
            "calculation": "((当期営業利益 - 前期営業利益) ÷ 前期営業利益) × 100"
        },
        {
            "category": "財務比率",
            "subcategory": "成長性",
            "item_name_jp": "純利益成長率",
            "item_name_en": "NetIncomeGrowthRate",
            "xbrl_element": "計算項目",
            "description": "前期比での純利益の成長率",
            "unit": "%",
            "importance": "重要",
            "calculation": "((当期純利益 - 前期純利益) ÷ 前期純利益) × 100"
        },
        {
            "category": "財務比率",
            "subcategory": "株価指標",
            "item_name_jp": "PER（株価収益率）",
            "item_name_en": "PriceEarningsRatio",
            "xbrl_element": "計算項目",
            "description": "株価が一株当たり純利益の何倍かを示す",
            "unit": "倍",
            "importance": "最重要",
            "calculation": "株価 ÷ EPS（要：株価データ）"
        },
        {
            "category": "財務比率",
            "subcategory": "株価指標",
            "item_name_jp": "PBR（株価純資産倍率）",
            "item_name_en": "PriceBookRatio",
            "xbrl_element": "計算項目",
            "description": "株価が一株当たり純資産の何倍かを示す",
            "unit": "倍",
            "importance": "重要",
            "calculation": "株価 ÷ BPS（要：株価データ）"
        },
        {
            "category": "財務比率",
            "subcategory": "株価指標",
            "item_name_jp": "配当利回り",
            "item_name_en": "DividendYield",
            "xbrl_element": "計算項目",
            "description": "株価に対する配当金の割合",
            "unit": "%",
            "importance": "重要",
            "calculation": "(配当金 ÷ 株価) × 100（要：株価データ）"
        }
    ]
    
    # 全項目を結合
    financial_items.extend(pl_items)
    financial_items.extend(bs_items)
    financial_items.extend(cf_items)
    financial_items.extend(other_items)
    financial_items.extend(ratio_items)
    
    # CSV出力
    output_file = f"xbrl_fin_metadata_{datetime.now().strftime('%Y%m%d')}.csv"
    
    with open(output_file, 'w', encoding='utf-8-sig', newline='') as f:
        if financial_items:
            writer = csv.DictWriter(f, fieldnames=financial_items[0].keys())
            writer.writeheader()
            writer.writerows(financial_items)
    
    # サマリー表示
    print("=" * 80)
    print("📊 XBRLから取得可能な財務データ項目の分析")
    print("=" * 80)
    
    # カテゴリ別集計
    categories = {}
    importance_count = {"最重要": 0, "重要": 0, "通常": 0}
    
    for item in financial_items:
        cat = item["category"]
        categories[cat] = categories.get(cat, 0) + 1
        importance_count[item["importance"]] = importance_count.get(item["importance"], 0) + 1
    
    print(f"\n✅ 合計項目数: {len(financial_items)}項目")
    print(f"💾 保存先: {output_file}")
    
    print("\n📂 カテゴリ別項目数:")
    for cat, count in categories.items():
        print(f"  {cat}: {count}項目")
    
    print("\n⭐ 重要度別項目数:")
    for imp, count in importance_count.items():
        print(f"  {imp}: {count}項目")
    
    print("\n" + "=" * 80)
    print("💡 データ取得方法")
    print("=" * 80)
    print("1. 直接取得項目（XBRLから直接読み取り）")
    print("   - 損益計算書、貸借対照表、CF計算書の各項目")
    print("   - 従業員情報、研究開発費等")
    print()
    print("2. 計算項目（取得した値から計算）")
    print("   - 各種財務比率（ROE、ROA、自己資本比率等）")
    print("   - 成長率（売上高成長率、利益成長率等）")
    print("   - フリーキャッシュフロー")
    
    print("\n" + "=" * 80)
    print("📝 注意事項")
    print("=" * 80)
    print("• XBRL要素名は日本会計基準（JGAAP）のものを記載")
    print("• IFRS適用企業の場合は要素名が異なる場合があります")
    print("• 企業によっては一部項目が存在しない場合があります")
    print("• 連結/単体の区別に注意が必要です")
    print("• 株価関連指標は別途株価データの取得が必要です")
    
    return financial_items

if __name__ == "__main__":
    items = generate_xbrl_financial_items()