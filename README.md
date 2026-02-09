# Economic Data Collector

멀티 소스 경제 데이터 수집 및 시각화 도구입니다. 
FRED(미국 연준), ECOS(한국은행), BLS(미국 노동통계국)에서 경제 지표를 자동으로 수집하고 대시보드로 시각화합니다.

## 🚀 빠른 시작

### 1. 의존성 설치

```bash
pip install -r requirements.txt
```

### 2. API 키 설정

`.env` 파일을 생성하고 API 키를 입력합니다:

```env
FRED_API_KEY=your_fred_api_key
BLS_API_KEY=your_bls_api_key
ECOS_API_KEY=your_ecos_api_key
```

**API 키 발급처:**
- FRED: https://fred.stlouisfed.org/docs/api/api_key.html
- BLS: https://data.bls.gov/registrationEngine/
- ECOS: https://ecos.bok.or.kr/api/

### 3. 데이터 수집

```bash
# 모든 소스에서 수집
python collect_all.py

# 특정 소스만 수집
python collect_all.py --source fred
python collect_all.py --source ecos
python collect_all.py --source bls
```

### 4. 대시보드 실행

```bash
streamlit run dashboard.py
```

## 📁 프로젝트 구조

```
economic-data-collector/
├── collectors/                 # 데이터 수집 모듈
│   ├── base_collector.py      # 공통 추상 클래스
│   ├── fred_collector.py      # FRED API 수집기
│   ├── ecos_collector.py      # ECOS API 수집기
│   └── bls_collector.py       # BLS API 수집기
├── indicators/                 # 지표 정의
│   ├── fred_indicators.py     # FRED 지표 목록
│   ├── ecos_indicators.py     # ECOS 지표 목록
│   └── bls_indicators.py      # BLS 지표 목록
├── data/                       # 수집된 데이터 저장
│   ├── fred_data.xlsx
│   ├── ecos_data.xlsx
│   └── bls_data.xlsx
├── collect_all.py             # 일괄 수집 스크립트
├── dashboard.py               # 통합 대시보드
├── requirements.txt
└── .env                       # API 키 (버전 관리에 포함하지 않음)
```

## 📊 수집 가능한 지표

### 🇺🇸 FRED (미국 연준)
| 카테고리 | 지표 예시 |
|----------|----------|
| 고용 | 실업률, 비농업 고용자수, 실업수당 청구건수 |
| 물가 | CPI, PCE, PPI, 기대 인플레이션 |
| 경기 | GDP, 산업생산, 소매판매, 주택착공 |
| 심리 | 소비자심리지수, 금융스트레스지수 |
| 금리 | 연방기금금리, 국채 수익률, 스프레드 |
| 통화 | M1, M2, 연준 자산, 역레포 |

### 🇰🇷 ECOS (한국은행)
| 카테고리 | 지표 예시 |
|----------|----------|
| 금리 | 기준금리, 콜금리, 국고채 수익률 |
| 환율 | 원/달러, 원/엔, 원/유로 |
| 물가 | 소비자물가, 생산자물가 |
| 경기 | 경기동행지수, 산업생산지수 |
| 통화 | M1, M2, 가계신용 |
| 무역 | 경상수지, 무역수지, 수출입 |

### 📊 BLS (미국 노동통계국)
| 카테고리 | 지표 예시 |
|----------|----------|
| 물가 | CPI 전체/근원/세부항목 |
| 고용 | 산업별 비농업 고용자수 |
| 임금 | 평균 시간당 임금, 주당 근무시간 |
| 생산성 | 노동생산성, 단위노동비용 |
| 생산자물가 | PPI 최종수요/상품 |

## 🔧 개별 수집기 사용

각 수집기를 개별적으로 사용할 수도 있습니다:

```python
from collectors.fred_collector import FREDCollector
from collectors.ecos_collector import ECOSCollector
from collectors.bls_collector import BLSCollector

# FRED 수집
collector = FREDCollector()
collector.run()

# ECOS 수집
collector = ECOSCollector()
collector.run()

# BLS 수집
collector = BLSCollector()
collector.run()
```

## 📈 대시보드 기능

- **소스별 탭**: FRED, ECOS, BLS 데이터를 탭으로 구분
- **카테고리 필터**: 고용, 물가, 경기 등 카테고리별 필터링
- **다중 지표 선택**: 여러 지표를 동시에 비교
- **기간 조절**: 슬라이더로 분석 기간 설정
- **데이터 변환**: 원 데이터, 지수화, YoY, QoQ, MoM
- **차트 스타일**: 라인, 마커, 영역 차트
- **데이터 테이블**: 원본 데이터 확인

## 📝 새 지표 추가하기

`indicators/` 폴더의 해당 파일에 지표를 추가합니다:

```python
# indicators/fred_indicators.py
EMPLOYMENT_INDICATORS = {
    "UNRATE": "실업률 (Unemployment Rate) - 월별",
    "NEW_SERIES": "새 지표 (New Indicator) - 주기",  # 추가
}
```

## 📜 라이선스

MIT License
