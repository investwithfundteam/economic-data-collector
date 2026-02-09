"""
Base Collector 추상 클래스
========================

모든 데이터 수집기가 구현해야 하는 공통 인터페이스를 정의합니다.
FRED, BLS, ECOS 등 각 데이터 소스별 collector는 이 클래스를 상속받습니다.
"""

import os
import sys
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

import pandas as pd
from dotenv import load_dotenv


class BaseCollector(ABC):
    """
    경제 데이터 수집기의 기본 추상 클래스
    
    📌 주요 메서드:
    - load_api_key(): API 키 로드
    - load_existing_data(): 기존 데이터 로드
    - fetch_indicator_data(): 단일 지표 데이터 수집 (구현 필요)
    - collect_all_data(): 모든 지표 수집
    - save_data(): Excel로 저장
    """
    
    # 서브클래스에서 정의해야 하는 상수들
    SOURCE_NAME: str = "BASE"  # 데이터 소스 이름 (예: "FRED", "BLS", "ECOS")
    API_KEY_ENV_VAR: str = ""  # 환경 변수 이름 (예: "FRED_API_KEY")
    DATA_FILENAME: str = "data.xlsx"  # 저장할 파일명
    
    def __init__(self):
        """공통 초기화"""
        # Windows 콘솔 UTF-8 인코딩 설정
        if sys.platform == 'win32':
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        
        self.script_dir = Path(__file__).parent.parent
        self.data_dir = self.script_dir / "data"
        self.data_dir.mkdir(exist_ok=True)
        
        self.api_key: Optional[str] = None
        self.indicators: Dict[str, str] = {}
        self.indicator_categories: Dict[str, Dict[str, str]] = {}
    
    def load_api_key(self) -> str:
        """
        .env 파일에서 API 키를 불러옵니다.
        """
        env_path = self.script_dir / ".env"
        load_dotenv(env_path)
        
        api_key = os.getenv(self.API_KEY_ENV_VAR)
        
        if not api_key:
            print(f"❌ 오류: {self.API_KEY_ENV_VAR}를 찾을 수 없습니다!")
            print(f"   .env 파일에 {self.API_KEY_ENV_VAR}=your_key 형식으로 API 키를 입력해주세요.")
            sys.exit(1)
        
        self.api_key = api_key
        return api_key
    
    def get_excel_path(self) -> Path:
        """Excel 파일 경로를 반환합니다."""
        return self.data_dir / self.DATA_FILENAME
    
    def get_indicator_category(self, series_id: str) -> str:
        """지표 코드로 해당 카테고리를 찾습니다."""
        for category_name, indicators in self.indicator_categories.items():
            if series_id in indicators:
                return category_name
        return "기타"
    
    def get_korean_name(self, indicator_code: str) -> str:
        """지표 코드에서 한국어 이름만 추출합니다."""
        desc = self.indicators.get(indicator_code, indicator_code)
        # "실업률 (Unemployment Rate) - 월별" -> "실업률"
        if " (" in desc:
            return desc.split(" (")[0]
        return desc
    
    def load_existing_data(self) -> pd.DataFrame:
        """
        기존 Excel 파일이 있으면 데이터를 불러옵니다.
        
        📌 Excel 파일 구조:
        1행=한국어 이름, 2행=단위, 3행=지표코드(헤더), 4행~=데이터
        """
        excel_path = self.get_excel_path()
        
        if excel_path.exists():
            print(f"📂 기존 데이터 파일을 불러옵니다: {excel_path}")
            
            try:
                all_sheets = pd.read_excel(
                    excel_path, sheet_name=None, engine='openpyxl',
                    skiprows=2, header=0
                )
                
                all_data = []
                for sheet_name, df in all_sheets.items():
                    if df.empty or 'date' not in df.columns:
                        continue
                    
                    df['date'] = pd.to_datetime(df['date'], errors='coerce')
                    df = df.dropna(subset=['date'])
                    indicator_cols = [col for col in df.columns if col != 'date']
                    
                    for indicator in indicator_cols:
                        indicator_df = df[['date', indicator]].dropna()
                        if not indicator_df.empty:
                            indicator_df = indicator_df.rename(columns={indicator: 'value'})
                            indicator_df['indicator'] = indicator
                            indicator_df['description'] = self.indicators.get(indicator, indicator)
                            all_data.append(indicator_df)
                
                if all_data:
                    combined = pd.concat(all_data, ignore_index=True)
                    print(f"   → 기존 데이터: {len(combined)}개 행")
                    return combined
                else:
                    print("   → 기존 파일에 유효한 데이터가 없습니다.")
                    return pd.DataFrame()
            except Exception as e:
                print(f"   ⚠️ 기존 데이터 로드 중 오류: {e}")
                return pd.DataFrame()
        else:
            print("📄 기존 데이터 파일이 없습니다. 새로 생성합니다.")
            return pd.DataFrame()
    
    @abstractmethod
    def connect(self) -> None:
        """
        API에 연결합니다.
        각 서브클래스에서 구현해야 합니다.
        """
        pass
    
    @abstractmethod
    def fetch_indicator_data(
        self, series_id: str, description: str, start_date: Optional[datetime] = None
    ) -> pd.DataFrame:
        """
        특정 지표의 데이터를 수집합니다.
        각 서브클래스에서 구현해야 합니다.
        
        Returns:
            DataFrame with columns: date, indicator, value, description, unit
        """
        pass
    
    def collect_all_data(self, existing_data: pd.DataFrame) -> pd.DataFrame:
        """
        모든 지표 데이터를 수집합니다.
        """
        from datetime import timedelta
        
        all_new_data = []
        
        print(f"\n📊 {self.SOURCE_NAME} 경제 지표 데이터 수집 시작...")
        print("=" * 50)
        
        for series_id, description in self.indicators.items():
            start_date = None
            if not existing_data.empty:
                indicator_data = existing_data[existing_data["indicator"] == series_id]
                if not indicator_data.empty:
                    last_date = indicator_data["date"].max()
                    start_date = last_date + timedelta(days=1)
            
            new_data = self.fetch_indicator_data(series_id, description, start_date)
            if not new_data.empty:
                all_new_data.append(new_data)
        
        print("=" * 50)
        
        if all_new_data:
            combined_new_data = pd.concat(all_new_data, ignore_index=True)
            print(f"\n✅ 총 {len(combined_new_data)}개의 새로운 데이터 포인트 수집 완료")
            return combined_new_data
        else:
            print("\n📭 새로운 데이터가 없습니다.")
            return pd.DataFrame()
    
    def save_data(self, existing_data: pd.DataFrame, new_data: pd.DataFrame) -> None:
        """
        수집된 데이터를 Excel 파일로 저장합니다.
        카테고리별로 별도의 시트에 저장됩니다.
        """
        excel_path = self.get_excel_path()
        
        if new_data.empty and existing_data.empty:
            print("💾 저장할 데이터가 없습니다.")
            return
        
        # 기존 데이터와 새 데이터 합치기
        if existing_data.empty:
            final_data = new_data
        elif new_data.empty:
            final_data = existing_data
        else:
            final_data = pd.concat([existing_data, new_data], ignore_index=True)
        
        # 중복 제거
        final_data = final_data.drop_duplicates(subset=["date", "indicator"], keep="last")
        final_data = final_data.sort_values(["date", "indicator"])
        
        # 카테고리 추가
        final_data["category"] = final_data["indicator"].apply(self.get_indicator_category)
        
        # 단위 정보 추출 함수
        def get_unit(indicator_code):
            indicator_rows = final_data[final_data['indicator'] == indicator_code]
            if not indicator_rows.empty and 'unit' in indicator_rows.columns:
                unit = indicator_rows['unit'].iloc[0]
                return unit if pd.notna(unit) else 'N/A'
            return 'N/A'
        
        print(f"\n💾 Excel 파일로 저장 중: {excel_path}")
        
        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            # 카테고리별 시트 저장
            for category_name in self.indicator_categories.keys():
                category_data = final_data[final_data["category"] == category_name]
                
                if category_data.empty:
                    print(f"   📋 {category_name}: 데이터 없음")
                    continue
                
                # Wide format으로 변환
                wide_data = category_data.pivot(
                    index="date", columns="indicator", values="value"
                )
                wide_data = wide_data.reset_index()
                wide_data = wide_data.sort_values("date", ascending=False)
                
                cols = ["date"] + sorted([c for c in wide_data.columns if c != "date"])
                wide_data = wide_data[cols]
                
                # 한국어 이름 행 + 단위 행 생성
                korean_names = ["날짜"] + [self.get_korean_name(c) for c in cols[1:]]
                korean_row = pd.DataFrame([korean_names], columns=cols)
                
                units = ["단위"] + [get_unit(c) for c in cols[1:]]
                unit_row = pd.DataFrame([units], columns=cols)
                
                output_data = pd.concat([korean_row, unit_row, wide_data], ignore_index=True)
                output_data.to_excel(writer, sheet_name=category_name, index=False)
                
                print(f"   📋 {category_name}: {len(wide_data)}행 × {len(cols)}열")
            
            # '전체' 시트
            all_wide = final_data.pivot(index="date", columns="indicator", values="value")
            all_wide = all_wide.reset_index()
            all_wide = all_wide.sort_values("date", ascending=False)
            all_cols = ["date"] + sorted([c for c in all_wide.columns if c != "date"])
            all_wide = all_wide[all_cols]
            
            all_korean_names = ["날짜"] + [self.get_korean_name(c) for c in all_cols[1:]]
            all_korean_row = pd.DataFrame([all_korean_names], columns=all_cols)
            
            all_units = ["단위"] + [get_unit(c) for c in all_cols[1:]]
            all_unit_row = pd.DataFrame([all_units], columns=all_cols)
            
            all_output = pd.concat([all_korean_row, all_unit_row, all_wide], ignore_index=True)
            all_output.to_excel(writer, sheet_name="전체", index=False)
            print(f"   📋 전체: {len(all_wide)}행 × {len(all_cols)}열")
        
        print(f"\n✅ 저장 완료: {excel_path}")
    
    def run(self) -> None:
        """
        전체 수집 프로세스를 실행합니다.
        """
        print("=" * 60)
        print(f"🏛️  {self.SOURCE_NAME} 경제 지표 자동 수집기")
        print(f"📅 실행 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        # 1. API 키 로드
        self.load_api_key()
        print("🔑 API 키 로드 완료")
        
        # 2. API 연결
        self.connect()
        print(f"🌐 {self.SOURCE_NAME} API 연결 완료")
        
        # 3. 기존 데이터 로드
        existing_data = self.load_existing_data()
        
        # 4. 새 데이터 수집
        new_data = self.collect_all_data(existing_data)
        
        # 5. 저장
        self.save_data(existing_data, new_data)
        
        print(f"\n✨ {self.SOURCE_NAME} 데이터 수집이 완료되었습니다!")
        print("=" * 60)
