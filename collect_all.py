"""
경제 데이터 일괄 수집 스크립트
============================

모든 데이터 소스(FRED, ECOS, BLS)에서 경제 지표를 일괄 수집합니다.

📌 사용 방법:
    python collect_all.py [--source SOURCE]

📌 옵션:
    --source: 특정 소스만 수집 (fred, ecos, bls)
              생략 시 모든 소스 수집
"""

import argparse
import sys
from datetime import datetime

# Windows 콘솔 UTF-8 인코딩 설정
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# 필요한 패키지 경로 추가
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from collectors.fred_collector import FREDCollector
from collectors.ecos_collector import ECOSCollector
from collectors.bls_collector import BLSCollector


def collect_all(sources: list = None):
    """
    지정된 소스에서 데이터를 수집합니다.
    
    Args:
        sources: 수집할 소스 목록 ['fred', 'ecos', 'bls']
                 None이면 모든 소스 수집
    """
    if sources is None:
        sources = ['fred', 'ecos', 'bls']
    
    print("=" * 70)
    print("🌐 경제 데이터 일괄 수집기 (Economic Data Collector)")
    print(f"📅 실행 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📊 수집 대상: {', '.join(s.upper() for s in sources)}")
    print("=" * 70)
    
    collectors = {
        'fred': FREDCollector,
        'ecos': ECOSCollector,
        'bls': BLSCollector,
    }
    
    results = {}
    
    for source in sources:
        source = source.lower()
        if source not in collectors:
            print(f"\n⚠️ 알 수 없는 소스: {source}")
            continue
        
        print(f"\n{'='*70}")
        print(f"📊 {source.upper()} 데이터 수집 시작...")
        print("=" * 70)
        
        try:
            collector = collectors[source]()
            collector.run()
            results[source] = "✅ 성공"
        except Exception as e:
            print(f"\n❌ {source.upper()} 수집 중 오류 발생: {e}")
            results[source] = f"❌ 실패: {e}"
    
    # 결과 요약
    print("\n" + "=" * 70)
    print("📋 수집 결과 요약")
    print("=" * 70)
    for source, status in results.items():
        print(f"   {source.upper()}: {status}")
    print("=" * 70)
    print("\n✨ 모든 데이터 수집이 완료되었습니다!")


def main():
    parser = argparse.ArgumentParser(
        description="경제 데이터 일괄 수집기",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  python collect_all.py              # 모든 소스 수집
  python collect_all.py --source fred    # FRED만 수집
  python collect_all.py --source ecos bls  # ECOS와 BLS 수집
        """
    )
    parser.add_argument(
        "--source", "-s",
        nargs="+",
        choices=["fred", "ecos", "bls"],
        help="수집할 데이터 소스 (기본값: 전체)"
    )
    
    args = parser.parse_args()
    collect_all(args.source)


if __name__ == "__main__":
    main()
