"""
FRED 경제 지표 정의
==================

FRED(Federal Reserve Economic Data)에서 수집할 경제 지표들의 정의입니다.
각 지표는 Series ID와 한국어 설명으로 구성됩니다.

📌 계절조정 표기:
- (SA): Seasonally Adjusted - 계절조정치
- (NSA): Not Seasonally Adjusted - 계절미조정치
"""

# 📈 고용 관련 지표 (Employment)
EMPLOYMENT_INDICATORS = {
    "UNRATE": "실업률 (SA) (Unemployment Rate) - 월별",
    "PAYEMS": "비농업 고용자수 (SA) (Nonfarm Payrolls) - 월별",
    "ICSA": "신규 실업수당 청구건수 (SA) (Initial Jobless Claims) - 주별",
    "CCSA": "계속 실업수당 청구건수 (SA) (Continued Claims) - 주별",
    "CIVPART": "경제활동참가율 (SA) (Labor Force Participation Rate) - 월별",
    "EMRATIO": "고용률 (SA) (Employment-Population Ratio) - 월별",
    "U6RATE": "광의 실업률 U-6 (SA) (U-6 Unemployment Rate) - 월별",
    "AWHAETP": "민간 평균 주당 근무시간 (SA) (Avg Weekly Hours) - 월별",
    "CES0500000003": "민간 평균 시간당 임금 (SA) (Avg Hourly Earnings) - 월별",
    "JTSJOL": "구인건수 JOLTS (SA) (Job Openings) - 월별",
}

# 💰 물가 관련 지표 (Prices/Inflation)
PRICE_INDICATORS = {
    "CPIAUCSL": "소비자물가지수 CPI (SA) (Consumer Price Index) - 월별",
    "CPILFESL": "근원 CPI (SA) (Core CPI, 식품/에너지 제외) - 월별",
    "PCEPI": "PCE 물가지수 (SA) (Personal Consumption Expenditures) - 월별",
    "PCEPILFE": "근원 PCE (SA) (Core PCE) - 월별",
    "PPIFIS": "생산자물가지수 PPI (SA) (Producer Price Index) - 월별",
    "T5YIE": "5년 기대 인플레이션 (5-Year Breakeven Inflation) - 일별",
    "T10YIE": "10년 기대 인플레이션 (10-Year Breakeven Inflation) - 일별",
    "MICH": "미시간대 기대 인플레이션 (NSA) (U of Michigan Inflation Expectation) - 월별",
    "GASREGW": "휘발유 가격 (NSA) (Regular Gas Price) - 주별",
    "DCOILWTICO": "WTI 원유 가격 (Crude Oil Price WTI) - 일별",
}

# 📊 경기 관련 지표 (Business Cycle/Economic Activity)
BUSINESS_CYCLE_INDICATORS = {
    "GDP": "명목 GDP (SA) (Gross Domestic Product) - 분기별",
    "GDPC1": "실질 GDP (SA) (Real GDP) - 분기별",
    "INDPRO": "산업생산지수 (SA) (Industrial Production Index) - 월별",
    "TCU": "설비가동률 (SA) (Capacity Utilization) - 월별",
    "RSXFS": "소매판매 (SA) (Retail Sales ex. Food Services) - 월별",
    "HOUST": "주택착공건수 (SA) (Housing Starts) - 월별",
    "PERMIT": "건축허가건수 (SA) (Building Permits) - 월별",
    "DGORDER": "내구재 주문 (SA) (Durable Goods Orders) - 월별",
    "CFNAI": "시카고연준 경기지수 (SA) (Chicago Fed National Activity Index) - 월별",
}

# 🧠 심리/센티먼트 지표 (Sentiment/Confidence)
SENTIMENT_INDICATORS = {
    "UMCSENT": "미시간대 소비자심리지수 (NSA) (U of Michigan Consumer Sentiment) - 월별",
    "CSCICP03USM665S": "컨퍼런스보드 소비자신뢰지수 (SA) (Consumer Confidence) - 월별",
    "STLFSI4": "세인트루이스 금융스트레스지수 (Financial Stress Index) - 주별",
    "NFCI": "시카고연준 금융여건지수 (National Financial Conditions Index) - 주별",
}

# 💵 금리 관련 지표 (Interest Rates)
INTEREST_RATE_INDICATORS = {
    "FEDFUNDS": "연방기금금리 (Federal Funds Rate) - 월별",
    "DFEDTARU": "연준 목표금리 상한 (Fed Target Rate Upper) - 일별",
    "DFEDTARL": "연준 목표금리 하한 (Fed Target Rate Lower) - 일별",
    "DGS2": "2년 국채 수익률 (2-Year Treasury Rate) - 일별",
    "DGS5": "5년 국채 수익률 (5-Year Treasury Rate) - 일별",
    "DGS10": "10년 국채 수익률 (10-Year Treasury Rate) - 일별",
    "DGS30": "30년 국채 수익률 (30-Year Treasury Rate) - 일별",
    "T10Y2Y": "장단기 금리차 10Y-2Y (10Y-2Y Treasury Spread) - 일별",
    "T10Y3M": "장단기 금리차 10Y-3M (10Y-3M Treasury Spread) - 일별",
    "BAMLH0A0HYM2": "하이일드 스프레드 (High Yield Spread) - 일별",
}

# 💰 통화/유동성 지표 (Money Supply/Liquidity)
MONEY_SUPPLY_INDICATORS = {
    "M1SL": "M1 통화량 (SA) (M1 Money Stock) - 월별",
    "M2SL": "M2 통화량 (SA) (M2 Money Stock) - 월별",
    "BOGMBASE": "본원통화 (SA) (Monetary Base) - 월별",
    "WALCL": "연준 총자산 (Fed Total Assets) - 주별",
    "WTREGEN": "재무부 일반계정 TGA (Treasury General Account) - 주별",
    "RRPONTSYD": "역레포 잔액 (Reverse Repo) - 일별",
    "TOTRESNS": "은행 지급준비금 (NSA) (Bank Reserves) - 월별",
}

# 모든 카테고리를 하나의 딕셔너리로 통합
INDICATOR_CATEGORIES = {
    "고용": EMPLOYMENT_INDICATORS,
    "물가": PRICE_INDICATORS,
    "경기": BUSINESS_CYCLE_INDICATORS,
    "심리": SENTIMENT_INDICATORS,
    "금리": INTEREST_RATE_INDICATORS,
    "통화": MONEY_SUPPLY_INDICATORS,
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
    # "실업률 (SA) (Unemployment Rate) - 월별" -> "실업률 (SA)"
    if " (" in desc:
        parts = desc.split(" (")
        if len(parts) >= 2 and parts[1].startswith("SA)") or parts[1].startswith("NSA)"):
            return parts[0] + " (" + parts[1].split(")")[0] + ")"
        return parts[0]
    return desc
