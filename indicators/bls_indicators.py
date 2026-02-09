"""
BLS 경제 지표 정의
=================

미국 노동통계국(Bureau of Labor Statistics)에서 수집할 경제 지표들의 정의입니다.
각 지표는 Series ID와 한국어 설명으로 구성됩니다.

📌 BLS Series ID 구조:
- 접두사: 데이터 유형 (예: CU=CPI, CE=고용, PR=생산성, LN=실업)
- 지역코드: 0000=전국
- 항목코드: 세부 항목 식별자

📌 계절조정 표기:
- (SA): Seasonally Adjusted - 계절조정치
- (NSA): Not Seasonally Adjusted - 계절미조정치
"""

# 💰 물가/CPI 관련 지표 (Consumer Price Index)
# CUUR = CPI-U, Not Seasonally Adjusted
# CUSR = CPI-U, Seasonally Adjusted
PRICE_INDICATORS = {
    "CUUR0000SA0": "CPI 전체 항목 (NSA) (CPI All Items) - 월별",
    "CUUR0000SA0L1E": "근원 CPI (NSA) (Core CPI, 식품/에너지 제외) - 월별",
    "CUUR0000SAF1": "CPI 식품 (NSA) (CPI Food) - 월별",
    "CUUR0000SETA01": "CPI 신차 (NSA) (CPI New Vehicles) - 월별",
    "CUUR0000SETA02": "CPI 중고차 (NSA) (CPI Used Vehicles) - 월별",
    "CUUR0000SAH1": "CPI 주거비 (NSA) (CPI Shelter) - 월별",
    "CUUR0000SEHA": "CPI 임대료 (NSA) (CPI Rent) - 월별",
    "CUUR0000SAM1": "CPI 의료비 (NSA) (CPI Medical Care) - 월별",
    "CUUR0000SETB01": "CPI 휘발유 (NSA) (CPI Gasoline) - 월별",
    "CUUR0000SEHF01": "CPI 전기료 (NSA) (CPI Electricity) - 월별",
}

# 📈 고용 관련 지표 (Employment)
# CES = Current Employment Statistics, Seasonally Adjusted
EMPLOYMENT_INDICATORS = {
    "CES0000000001": "비농업 고용자수 총계 (SA) (Total Nonfarm Employment) - 월별",
    "CES0500000001": "민간 비농업 고용자수 (SA) (Private Nonfarm Employment) - 월별",
    "CES1000000001": "광업 고용자수 (SA) (Mining Employment) - 월별",
    "CES2000000001": "건설업 고용자수 (SA) (Construction Employment) - 월별",
    "CES3000000001": "제조업 고용자수 (SA) (Manufacturing Employment) - 월별",
    "CES4000000001": "운송/창고 고용자수 (SA) (Transportation Employment) - 월별",
    "CES5000000001": "정보산업 고용자수 (SA) (Information Employment) - 월별",
    "CES6000000001": "금융 고용자수 (SA) (Financial Employment) - 월별",
    "CES7000000001": "전문서비스 고용자수 (SA) (Professional Services) - 월별",
    "CES8000000001": "교육/헬스케어 고용자수 (SA) (Education & Healthcare) - 월별",
    "CES6500000001": "레저/접객 고용자수 (SA) (Leisure & Hospitality) - 월별",
}

# 📊 실업 관련 지표 (Unemployment)
# LNS = Labor Force Statistics
UNEMPLOYMENT_INDICATORS = {
    "LNS14000000": "실업률 (SA) (Unemployment Rate) - 월별",
    "LNS13000000": "실업자 수 (SA) (Number of Unemployed) - 월별",
    "LNS11000000": "경제활동인구 (SA) (Civilian Labor Force) - 월별",
    "LNS12000000": "취업자 수 (SA) (Employed Persons) - 월별",
    "LNS11300000": "경제활동참가율 (SA) (Labor Force Participation Rate) - 월별",
    "LNS12300000": "고용률 (SA) (Employment-Population Ratio) - 월별",
    "LNS14100000": "실업률 16-19세 (SA) (Unemployment Rate 16-19) - 월별",
    "LNS13008636": "장기 실업자 수 27주+ (SA) (Long-term Unemployed 27+ weeks) - 월별",
    "LNS14023621": "U-6 광의 실업률 (SA) (U-6 Unemployment Rate) - 월별",
}

# 🔄 JOLTS 관련 지표 (Job Openings and Labor Turnover Survey)
# JTS = JOLTS
JOLTS_INDICATORS = {
    "JTS000000000000000JOL": "구인 건수 (SA) (Job Openings) - 월별",
    "JTS000000000000000HIR": "채용 건수 (SA) (Hires) - 월별",
    "JTS000000000000000TSL": "이직 총계 (SA) (Total Separations) - 월별",
    "JTS000000000000000QUL": "자발적 퇴사 건수 (SA) (Quits) - 월별",
    "JTS000000000000000LDL": "해고 건수 (SA) (Layoffs & Discharges) - 월별",
    "JTS000000000000000JOR": "구인율 (SA) (Job Openings Rate) - 월별",
    "JTS000000000000000HIR": "채용율 (SA) (Hires Rate) - 월별",
    "JTS000000000000000QUR": "퇴사율 (SA) (Quits Rate) - 월별",
}

# 💵 임금 관련 지표 (Wages & Earnings)
WAGE_INDICATORS = {
    "CES0500000003": "민간 평균 시간당 임금 (SA) (Avg Hourly Earnings, Private) - 월별",
    "CES0500000011": "민간 평균 주당 근무시간 (SA) (Avg Weekly Hours, Private) - 월별",
    "CES3000000003": "제조업 평균 시간당 임금 (SA) (Avg Hourly Earnings, Manufacturing) - 월별",
    "CES3000000011": "제조업 평균 주당 근무시간 (SA) (Avg Weekly Hours, Manufacturing) - 월별",
    "CES0500000030": "민간 주당 임금 (SA) (Avg Weekly Earnings, Private) - 월별",
    "CES0500000008": "민간 시간당 임금 (생산직) (SA) (Avg Hourly Earnings, Production) - 월별",
}

# 📊 생산성 관련 지표 (Productivity)
PRODUCTIVITY_INDICATORS = {
    "PRS85006092": "비농업 노동생산성 (SA) (Nonfarm Business Productivity) - 분기별",
    "PRS85006112": "비농업 단위노동비용 (SA) (Nonfarm Unit Labor Costs) - 분기별",
    "PRS85006152": "비농업 시간당 보상 (SA) (Nonfarm Hourly Compensation) - 분기별",
    "PRS30006092": "제조업 노동생산성 (SA) (Manufacturing Productivity) - 분기별",
    "PRS30006112": "제조업 단위노동비용 (SA) (Manufacturing Unit Labor Costs) - 분기별",
}

# 🏭 생산자물가 관련 지표 (Producer Price Index)
# WPU = PPI, Not Seasonally Adjusted
PPI_INDICATORS = {
    "WPUFD4": "PPI 최종수요 (NSA) (PPI Final Demand) - 월별",
    "WPUFD49104": "PPI 최종수요 식품 제외 (NSA) (PPI Final Demand less Foods) - 월별",
    "WPUFD49116": "PPI 최종수요 식품/에너지 제외 (NSA) (PPI Core) - 월별",
    "WPU00000000": "PPI 전체 상품 (NSA) (PPI All Commodities) - 월별",
}

# 📈 실업수당 청구 지표 (Unemployment Insurance)
# 참고: BLS가 아닌 DOL(노동부) 데이터지만 FRED에서 제공
UI_INDICATORS = {
    # BLS에서는 실업수당 데이터가 제한적이므로 
    # 주요 실업 관련 지표는 위의 UNEMPLOYMENT_INDICATORS에 포함
}

# 모든 카테고리를 하나의 딕셔너리로 통합
INDICATOR_CATEGORIES = {
    "물가": PRICE_INDICATORS,
    "고용": EMPLOYMENT_INDICATORS,
    "실업": UNEMPLOYMENT_INDICATORS,
    "JOLTS": JOLTS_INDICATORS,
    "임금": WAGE_INDICATORS,
    "생산성": PRODUCTIVITY_INDICATORS,
    "생산자물가": PPI_INDICATORS,
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
    # "CPI 전체 항목 (NSA) (CPI All Items) - 월별" -> "CPI 전체 항목 (NSA)"
    if " (" in desc:
        parts = desc.split(" (")
        if len(parts) >= 2 and (parts[1].startswith("SA)") or parts[1].startswith("NSA)")):
            return parts[0] + " (" + parts[1].split(")")[0] + ")"
        return parts[0]
    return desc
