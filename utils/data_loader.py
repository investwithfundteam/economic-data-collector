"""데이터 로딩 및 구조 관리

데이터 소스별로 로드된 데이터를 명확한 구조로 관리합니다.
"""
from dataclasses import dataclass
from typing import Optional
import pandas as pd


@dataclass
class SourceData:
    """
    데이터 소스 정보를 담는 구조체
    
    Attributes:
        df: 데이터프레임 (date 컬럼과 지표 컬럼들 포함)
        id_to_name: 지표 ID와 한국어 이름의 매핑
        categories: 사용 가능한 카테고리 리스트
    """
    df: Optional[pd.DataFrame]
    id_to_name: dict[str, str]
    categories: list[str]
    
    @property
    def has_data(self) -> bool:
        """데이터가 있는지 확인"""
        return self.df is not None and not self.df.empty
    
    def get_available_indicators(self) -> dict[str, str]:
        """
        데이터프레임에 실제로 존재하는 지표만 반환
        
        Returns:
            지표 ID와 이름의 딕셔너리 (데이터프레임에 있는 것만)
        """
        if not self.has_data:
            return {}
        
        return {
            k: v for k, v in self.id_to_name.items()
            if k in self.df.columns and k != 'date'
        }
    
    def get_date_range(self) -> tuple[Optional[pd.Timestamp], Optional[pd.Timestamp]]:
        """
        데이터의 날짜 범위 반환
        
        Returns:
            (최소 날짜, 최대 날짜) 튜플
        """
        if not self.has_data or 'date' not in self.df.columns:
            return None, None
        
        valid_dates = self.df['date'].dropna()
        if len(valid_dates) == 0:
            return None, None
        
        return valid_dates.min(), valid_dates.max()
