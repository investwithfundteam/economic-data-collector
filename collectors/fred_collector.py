"""
FRED 데이터 수집기
=================

미국 연방준비은행(Federal Reserve)의 FRED API를 사용하여
주요 경제 지표를 자동으로 수집합니다.

📌 사용 방법:
    python -m collectors.fred_collector
    또는
    from collectors.fred_collector import FREDCollector
    collector = FREDCollector()
    collector.run()
"""

from datetime import datetime
from typing import Optional

import pandas as pd
from fredapi import Fred

from .base_collector import BaseCollector
from indicators.fred_indicators import (
    INDICATOR_CATEGORIES,
    ALL_INDICATORS,
)


class FREDCollector(BaseCollector):
    """
    FRED API 데이터 수집기
    
    📌 수집 가능한 지표 카테고리:
    - 고용: 실업률, 비농업 고용자수, 실업수당 청구건수 등
    - 물가: CPI, PCE, PPI, 기대 인플레이션 등
    - 경기: GDP, 산업생산, 소매판매 등
    - 심리: 소비자심리지수, 금융스트레스지수 등
    - 금리: 연방기금금리, 국채 수익률, 스프레드 등
    - 통화: M1, M2, 연준 자산, 역레포 등
    """
    
    SOURCE_NAME = "FRED"
    API_KEY_ENV_VAR = "FRED_API_KEY"
    DATA_FILENAME = "fred_data.xlsx"
    
    def __init__(self):
        super().__init__()
        self.indicators = ALL_INDICATORS
        self.indicator_categories = INDICATOR_CATEGORIES
        self.fred: Optional[Fred] = None
    
    def connect(self) -> None:
        """FRED API에 연결합니다."""
        self.fred = Fred(api_key=self.api_key)
    
    def fetch_indicator_data(
        self, series_id: str, description: str, start_date: Optional[datetime] = None
    ) -> pd.DataFrame:
        """
        FRED API에서 특정 경제 지표의 데이터를 가져옵니다.
        
        Args:
            series_id: 지표 코드 (예: "GDP", "UNRATE")
            description: 지표 설명
            start_date: 이 날짜 이후의 데이터만 가져옴 (선택사항)
        
        Returns:
            DataFrame with columns: date, indicator, value, description, unit
        """
        try:
            print(f"   📥 {series_id}: {description}")
            
            # 지표 메타데이터에서 단위 정보 가져오기
            try:
                series_info = self.fred.get_series_info(series_id)
                unit = series_info.get('units', 'N/A') if series_info is not None else 'N/A'
            except:
                unit = 'N/A'
            
            # FRED API에서 데이터 가져오기
            if start_date:
                data = self.fred.get_series(series_id, observation_start=start_date)
            else:
                default_start = datetime(2000, 1, 1)
                data = self.fred.get_series(series_id, observation_start=default_start)
            
            if data is None or len(data) == 0:
                print(f"      ⚠️ 데이터 없음")
                return pd.DataFrame()
            
            df = pd.DataFrame({
                "date": data.index,
                "indicator": series_id,
                "value": data.values,
                "description": description,
                "unit": unit
            })
            
            print(f"      ✅ {len(df)}개 데이터 포인트 수집 (단위: {unit})")
            return df
            
        except Exception as e:
            print(f"      ❌ 오류 발생: {e}")
            return pd.DataFrame()


def main():
    """FRED 데이터 수집 실행"""
    collector = FREDCollector()
    collector.run()


if __name__ == "__main__":
    main()
