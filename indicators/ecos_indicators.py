"""
ECOS 경제 지표 정의
==================

한국은행 경제통계시스템(ECOS)에서 수집할 경제 지표들의 정의입니다.
각 지표는 통계코드와 한국어 설명으로 구성됩니다.

📌 ECOS API 구조:
- 통계표코드 (STAT_CODE): 통계표 식별자
- 항목코드 (ITEM_CODE): 통계표 내 세부 항목
- 주기 (CYCLE): D(일), M(월), Q(분기), A(연)

📌 주요 통계표 코드:
- 722Y001: 기준금리 및 정책금리 (D)
- 817Y002: 시장금리 (D) 
- 731Y001: 환율 (D)
- 021Y126: 소비자물가지수 (M)
- 013Y126: 생산자물가지수 (M)
- 512Y040: 경기종합지수 (M)
- 101Y018: 통화 및 유동성 (M)
- 301Y013: 국제수지 (M)
- 403Y001: 수출입 (M)
"""

# 💵 금리 관련 지표 (일별)
INTEREST_RATE_INDICATORS = {
    "722Y001/010101000": "한국은행 기준금리 (Base Rate) - 일별",
    "817Y002/010200000": "콜금리 (Call Rate, 1일물) - 일별",
    "817Y002/010101000": "CD금리 91일 (CD 91-day Rate) - 일별",
    "817Y002/010502000": "국고채 3년 (Treasury Bond 3Y) - 일별",
    "817Y002/010503000": "국고채 5년 (Treasury Bond 5Y) - 일별",
    "817Y002/010504000": "국고채 10년 (Treasury Bond 10Y) - 일별",
    "817Y002/010500000": "국고채 1년 (Treasury Bond 1Y) - 일별",
}

# 💱 환율 관련 지표 (일별)
EXCHANGE_RATE_INDICATORS = {
    "731Y001/0000001": "원/달러 환율 (KRW/USD) - 일별",
    "731Y001/0000002": "원/엔(100엔) 환율 (KRW/JPY 100) - 일별",
    "731Y001/0000003": "원/유로 환율 (KRW/EUR) - 일별",
    "731Y001/0000053": "원/위안 환율 (KRW/CNY) - 일별",
}

# 💰 물가 관련 지표 (월별)
PRICE_INDICATORS = {
    "021Y126/0": "소비자물가지수 총지수 (CPI) - 월별",
    "021Y126/AAC": "근원 소비자물가지수 (Core CPI, 농산물및석유류제외) - 월별",
    "021Y126/AB": "생활물가지수 (Living CPI) - 월별",
    "013Y126/0000": "생산자물가지수 총지수 (PPI) - 월별",
}

# 📊 경기/생산 관련 지표 (월별)
BUSINESS_CYCLE_INDICATORS = {
    "512Y040/I16A": "경기동행지수 (Coincident Index) - 월별",
    "512Y040/I16B": "경기선행지수 (Leading Index) - 월별",
    "512Y040/I16C": "경기후행지수 (Lagging Index) - 월별",
    "512Y040/I16AA": "경기동행지수 순환변동치 (CI Cycle) - 월별",
    "512Y040/I16BB": "경기선행지수 순환변동치 (LI Cycle) - 월별",
}

# 💵 통화/금융 관련 지표 (월별)
MONEY_SUPPLY_INDICATORS = {
    "101Y018/BBHA": "M1 (협의통화) - 월별",
    "101Y018/BBHB": "M2 (광의통화) - 월별",
    "101Y018/BBHD": "Lf (금융기관 유동성) - 월별",
}

# 📈 국제수지/무역 관련 지표 (월별)
TRADE_INDICATORS = {
    "301Y013/SA000": "경상수지 (Current Account) - 월별",
    "301Y013/SB000": "상품수지 (Goods Balance) - 월별",
    "403Y001/AA": "수출금액 (Exports) - 월별",
    "403Y001/AB": "수입금액 (Imports) - 월별",
}

# 모든 카테고리를 하나의 딕셔너리로 통합
INDICATOR_CATEGORIES = {
    "금리": INTEREST_RATE_INDICATORS,
    "환율": EXCHANGE_RATE_INDICATORS,
    "물가": PRICE_INDICATORS,
    "경기": BUSINESS_CYCLE_INDICATORS,
    "통화": MONEY_SUPPLY_INDICATORS,
    "무역": TRADE_INDICATORS,
}

# 전체 지표 딕셔너리 (편의용)
ALL_INDICATORS = {}
for category_indicators in INDICATOR_CATEGORIES.values():
    ALL_INDICATORS.update(category_indicators)


def get_indicator_category(series_id: str) -> str:
    """지표 코드로 해당 카테고리를 찾습니다."""
    for category_name, indicators in INDICATOR_CATEGORIES.items():
        if series_id in indicators:
            return category_name
    return "기타"


def get_korean_name(indicator_code: str) -> str:
    """지표 코드에서 한국어 이름만 추출합니다."""
    desc = ALL_INDICATORS.get(indicator_code, indicator_code)
    if " (" in desc:
        return desc.split(" (")[0]
    return desc


def parse_ecos_code(indicator_code: str) -> tuple:
    """
    ECOS 지표 코드를 통계표코드와 항목코드로 분리합니다.
    
    예: "722Y001/0101000" -> ("722Y001", "0101000")
    """
    parts = indicator_code.split("/")
    if len(parts) == 2:
        return parts[0], parts[1]
    return indicator_code, ""
