"""지표 필터링 유틸리티 함수

중복되는 지표 필터링 로직을 중앙화합니다.
"""
import pandas as pd
from typing import Dict


def filter_hidden_indicators(
    indicators: Dict[str, str],
    source: str,
    settings: dict
) -> Dict[str, str]:
    """
    숨김 처리된 지표를 필터링합니다.
    
    Args:
        indicators: 지표 ID와 이름의 매핑
        source: 데이터 소스 ("FRED", "ECOS", "BLS")
        settings: 설정 딕셔너리 (hidden_indicators 포함)
    
    Returns:
        숨김 처리되지 않은 지표만 포함하는 딕셔너리
    """
    hidden = settings.get("hidden_indicators", [])
    return {
        k: v for k, v in indicators.items()
        if f"{source}:{k}" not in hidden
    }


def filter_available_in_data(
    indicators: Dict[str, str],
    df: pd.DataFrame
) -> Dict[str, str]:
    """
    데이터프레임에 실제로 존재하는 지표만 필터링합니다.
    
    Args:
        indicators: 지표 ID와 이름의 매핑
        df: 데이터프레임
    
    Returns:
        데이터프레임의 컬럼에 존재하는 지표만 포함하는 딕셔너리
    """
    if df is None:
        return {}
    
    return {
        k: v for k, v in indicators.items()
        if k in df.columns
    }


def get_category_indicators(
    all_indicators: Dict[str, str],
    category_dict: Dict[str, dict],
    category_name: str,
    df: pd.DataFrame
) -> Dict[str, str]:
    """
    특정 카테고리의 지표들을 가져옵니다.
    
    Args:
        all_indicators: 전체 지표 ID와 이름의 매핑
        category_dict: 카테고리별 지표 딕셔너리
        category_name: 카테고리 이름
        df: 데이터프레임
    
    Returns:
        해당 카테고리의 지표만 포함하는 딕셔너리
    """
    if category_name == "전체":
        return all_indicators
    
    category_indicators = category_dict.get(category_name, {})
    return {
        k: all_indicators.get(k, v)
        for k, v in category_indicators.items()
        if k in df.columns
    }
