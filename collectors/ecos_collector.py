"""
ECOS 데이터 수집기
=================

한국은행 경제통계시스템(ECOS) API를 사용하여
한국 경제 지표를 자동으로 수집합니다.

📌 ECOS API 문서: https://ecos.bok.or.kr/api/

📌 사용 방법:
    python -m collectors.ecos_collector
    또는
    from collectors.ecos_collector import ECOSCollector
    collector = ECOSCollector()
    collector.run()
"""

from datetime import datetime
from typing import Optional

import pandas as pd
import requests

from .base_collector import BaseCollector
from indicators.ecos_indicators import (
    INDICATOR_CATEGORIES,
    ALL_INDICATORS,
    parse_ecos_code,
)


class ECOSCollector(BaseCollector):
    """
    ECOS API 데이터 수집기
    
    📌 수집 가능한 지표 카테고리:
    - 금리: 기준금리, 콜금리, 국고채 수익률 등
    - 환율: 원/달러, 원/엔, 원/유로 등
    - 물가: 소비자물가, 생산자물가, 수출입물가 등
    - 경기: 경기동행지수, 산업생산지수 등
    - 통화: M1, M2, 가계신용 등
    - 무역: 경상수지, 무역수지, 수출입 등
    """
    
    SOURCE_NAME = "ECOS"
    API_KEY_ENV_VAR = "ECOS_API_KEY"
    DATA_FILENAME = "ecos_data.xlsx"
    
    # ECOS API 기본 URL
    BASE_URL = "https://ecos.bok.or.kr/api/StatisticSearch"
    
    def __init__(self):
        super().__init__()
        self.indicators = ALL_INDICATORS
        self.indicator_categories = INDICATOR_CATEGORIES
    
    def connect(self) -> None:
        """ECOS API 연결 확인 (별도 연결 객체 없음)"""
        # ECOS는 REST API이므로 별도 연결 객체가 필요 없음
        # API 키 유효성만 확인
        pass
    
    def _determine_cycle(self, stat_code: str) -> str:
        """
        통계표 코드로 데이터 주기를 결정합니다.
        
        Returns:
            D(일별), M(월별), Q(분기별), A(연별)
        """
        # 일별 데이터: 환율, 금리 관련
        daily_codes = ["731Y", "722Y", "817Y"]
        for code in daily_codes:
            if stat_code.startswith(code):
                return "D"
        
        # 분기별 데이터
        quarterly_codes = ["104Y"]
        for code in quarterly_codes:
            if stat_code.startswith(code):
                return "Q"
        
        # 기본값: 월별
        return "M"
    
    def _get_start_end_dates(
        self, cycle: str, start_date: Optional[datetime] = None
    ) -> tuple:
        """
        주기에 따른 시작/종료 날짜 문자열을 반환합니다.
        """
        if start_date:
            if cycle == "D":
                start_str = start_date.strftime("%Y%m%d")
            elif cycle == "M":
                start_str = start_date.strftime("%Y%m")
            elif cycle == "Q":
                quarter = (start_date.month - 1) // 3 + 1
                start_str = f"{start_date.year}Q{quarter}"
            else:  # A
                start_str = start_date.strftime("%Y")
        else:
            # 기본 시작일: 2000년
            if cycle == "D":
                start_str = "20000101"
            elif cycle == "M":
                start_str = "200001"
            elif cycle == "Q":
                start_str = "2000Q1"
            else:
                start_str = "2000"
        
        # 종료일: 현재
        now = datetime.now()
        if cycle == "D":
            end_str = now.strftime("%Y%m%d")
        elif cycle == "M":
            end_str = now.strftime("%Y%m")
        elif cycle == "Q":
            quarter = (now.month - 1) // 3 + 1
            end_str = f"{now.year}Q{quarter}"
        else:
            end_str = now.strftime("%Y")
        
        return start_str, end_str
    
    def fetch_indicator_data(
        self, series_id: str, description: str, start_date: Optional[datetime] = None
    ) -> pd.DataFrame:
        """
        ECOS API에서 특정 경제 지표의 데이터를 가져옵니다.
        
        Args:
            series_id: 지표 코드 (예: "722Y001/0101000")
            description: 지표 설명
            start_date: 이 날짜 이후의 데이터만 가져옴 (선택사항)
        
        Returns:
            DataFrame with columns: date, indicator, value, description, unit
        """
        try:
            print(f"   📥 {series_id}: {description}")
            
            # 통계표코드와 항목코드 분리
            stat_code, item_code = parse_ecos_code(series_id)
            
            # 주기 결정
            cycle = self._determine_cycle(stat_code)
            
            # 날짜 범위 설정
            start_str, end_str = self._get_start_end_dates(cycle, start_date)
            
            # API URL 구성
            # 형식: /api/StatisticSearch/{인증키}/{요청유형}/{언어}/{시작}/{끝}/{통계표코드}/{주기}/{시작일자}/{종료일자}/{항목코드1}
            url = (
                f"{self.BASE_URL}/{self.api_key}/json/kr/1/10000/"
                f"{stat_code}/{cycle}/{start_str}/{end_str}/{item_code}"
            )
            
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # 응답 확인
            if "StatisticSearch" not in data:
                if "RESULT" in data:
                    error_msg = data["RESULT"].get("MESSAGE", "알 수 없는 오류")
                    print(f"      ⚠️ API 오류: {error_msg}")
                else:
                    print(f"      ⚠️ 데이터 없음")
                return pd.DataFrame()
            
            rows = data["StatisticSearch"]["row"]
            
            if not rows:
                print(f"      ⚠️ 데이터 없음")
                return pd.DataFrame()
            
            # 데이터 변환
            records = []
            unit = rows[0].get("UNIT_NAME", "N/A") if rows else "N/A"
            
            for row in rows:
                time_str = row.get("TIME", "")
                value = row.get("DATA_VALUE", "")
                
                # 날짜 파싱
                try:
                    if cycle == "D":
                        date = datetime.strptime(time_str, "%Y%m%d")
                    elif cycle == "M":
                        date = datetime.strptime(time_str, "%Y%m")
                    elif cycle == "Q":
                        year = int(time_str[:4])
                        quarter = int(time_str[-1])
                        month = (quarter - 1) * 3 + 1
                        date = datetime(year, month, 1)
                    else:  # A
                        date = datetime.strptime(time_str, "%Y")
                except:
                    continue
                
                # 값 파싱
                try:
                    value = float(value) if value and value != "-" else None
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
            print(f"      ✅ {len(df)}개 데이터 포인트 수집 (단위: {unit})")
            return df
            
        except requests.exceptions.RequestException as e:
            print(f"      ❌ 네트워크 오류: {e}")
            return pd.DataFrame()
        except Exception as e:
            print(f"      ❌ 오류 발생: {e}")
            return pd.DataFrame()


def main():
    """ECOS 데이터 수집 실행"""
    collector = ECOSCollector()
    collector.run()


if __name__ == "__main__":
    main()
