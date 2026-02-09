"""
BLS 데이터 수집기
================

미국 노동통계국(Bureau of Labor Statistics) API를 사용하여
미국 노동/물가 관련 경제 지표를 자동으로 수집합니다.

📌 BLS API 문서: https://www.bls.gov/developers/

📌 사용 방법:
    python -m collectors.bls_collector
    또는
    from collectors.bls_collector import BLSCollector
    collector = BLSCollector()
    collector.run()
"""

import json
from datetime import datetime
from typing import Optional, List

import pandas as pd
import requests

from .base_collector import BaseCollector
from indicators.bls_indicators import (
    INDICATOR_CATEGORIES,
    ALL_INDICATORS,
)


class BLSCollector(BaseCollector):
    """
    BLS API 데이터 수집기
    
    📌 수집 가능한 지표 카테고리:
    - 물가: CPI 전체/근원/세부항목
    - 고용: 산업별 비농업 고용자수
    - 임금: 평균 시간당 임금, 주당 근무시간
    - 생산성: 노동생산성, 단위노동비용
    - 생산자물가: PPI 최종수요/상품
    
    📌 API 버전:
    - v2.0 사용 (등록 필요, 일일 500회 요청, 20년 데이터)
    """
    
    SOURCE_NAME = "BLS"
    API_KEY_ENV_VAR = "BLS_API_KEY"
    DATA_FILENAME = "bls_data.xlsx"
    
    # BLS API v2.0 URL
    BASE_URL = "https://api.bls.gov/publicAPI/v2/timeseries/data/"
    
    def __init__(self):
        super().__init__()
        self.indicators = ALL_INDICATORS
        self.indicator_categories = INDICATOR_CATEGORIES
    
    def connect(self) -> None:
        """BLS API 연결 확인 (별도 연결 객체 없음)"""
        # BLS는 REST API이므로 별도 연결 객체가 필요 없음
        pass
    
    def _fetch_series_batch(
        self, series_ids: List[str], start_year: int, end_year: int
    ) -> dict:
        """
        BLS API에서 여러 시리즈를 한 번에 가져옵니다.
        
        BLS API는 한 번에 최대 50개 시리즈, 20년 데이터를 요청할 수 있습니다.
        """
        headers = {"Content-type": "application/json"}
        payload = {
            "seriesid": series_ids,
            "startyear": str(start_year),
            "endyear": str(end_year),
            "registrationkey": self.api_key,
            "catalog": True,  # 메타데이터 포함
            "calculations": True,  # 계산값 포함
            "annualaverage": False,
        }
        
        response = requests.post(
            self.BASE_URL,
            data=json.dumps(payload),
            headers=headers,
            timeout=60
        )
        response.raise_for_status()
        
        return response.json()
    
    def fetch_indicator_data(
        self, series_id: str, description: str, start_date: Optional[datetime] = None
    ) -> pd.DataFrame:
        """
        BLS API에서 특정 경제 지표의 데이터를 가져옵니다.
        
        Args:
            series_id: 지표 코드 (예: "CUUR0000SA0")
            description: 지표 설명
            start_date: 이 날짜 이후의 데이터만 가져옴 (선택사항)
        
        Returns:
            DataFrame with columns: date, indicator, value, description, unit
        """
        try:
            print(f"   📥 {series_id}: {description}")
            
            # 연도 범위 설정 (BLS API는 최대 20년)
            current_year = datetime.now().year
            if start_date:
                start_year = start_date.year
            else:
                start_year = 2005  # 기본 시작년도
            
            # 최대 20년 제한
            if current_year - start_year > 20:
                start_year = current_year - 20
            
            # API 요청
            result = self._fetch_series_batch([series_id], start_year, current_year)
            
            # 응답 확인
            if result.get("status") != "REQUEST_SUCCEEDED":
                error_msg = result.get("message", ["알 수 없는 오류"])
                print(f"      ⚠️ API 오류: {error_msg}")
                return pd.DataFrame()
            
            series_data = result.get("Results", {}).get("series", [])
            
            if not series_data:
                print(f"      ⚠️ 데이터 없음")
                return pd.DataFrame()
            
            series = series_data[0]
            data_list = series.get("data", [])
            
            if not data_list:
                print(f"      ⚠️ 데이터 없음")
                return pd.DataFrame()
            
            # 메타데이터에서 단위 추출
            catalog = series.get("catalog", {})
            unit = catalog.get("series_title", "N/A")
            if len(unit) > 50:
                unit = unit[:50] + "..."
            
            # 데이터 변환
            records = []
            for item in data_list:
                year = int(item.get("year", 0))
                period = item.get("period", "")
                value = item.get("value", "")
                
                # 월별 데이터만 처리 (M01-M12)
                if not period.startswith("M") or period == "M13":
                    continue
                
                try:
                    month = int(period[1:])
                    date = datetime(year, month, 1)
                except:
                    continue
                
                # 시작일 필터링
                if start_date and date <= start_date:
                    continue
                
                try:
                    value = float(value) if value else None
                except:
                    value = None
                
                if value is not None:
                    records.append({
                        "date": date,
                        "indicator": series_id,
                        "value": value,
                        "description": description,
                        "unit": unit
                    })
            
            if not records:
                print(f"      ⚠️ 유효한 데이터 없음")
                return pd.DataFrame()
            
            df = pd.DataFrame(records)
            df = df.sort_values("date")
            print(f"      ✅ {len(df)}개 데이터 포인트 수집")
            return df
            
        except requests.exceptions.RequestException as e:
            print(f"      ❌ 네트워크 오류: {e}")
            return pd.DataFrame()
        except Exception as e:
            print(f"      ❌ 오류 발생: {e}")
            return pd.DataFrame()


def main():
    """BLS 데이터 수집 실행"""
    collector = BLSCollector()
    collector.run()


if __name__ == "__main__":
    main()
