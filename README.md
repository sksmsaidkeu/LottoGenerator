# 로또 6/45 번호 생성기

과거 당첨 데이터를 참고해 로또 번호를 생성해보는 개인용 프로젝트입니다.
파이썬 CLI 스크립트 하나와, 브라우저에서 바로 열어볼 수 있는 정적 HTML 페이지로 구성되어 있습니다.

> ⚠ 로또는 매 회차 완전히 독립적인 무작위 추첨입니다. 과거 당첨 번호는 미래 결과에 어떠한 영향도 주지 않습니다.
> 이 프로젝트의 "통계 기반 생성"은 과거 출현 빈도를 참고한 재미 요소일 뿐, 당첨을 예측하거나 보장하지 않습니다.

## 폴더 구성

| 파일 | 설명 |
|---|---|
| `lotto_generator.py` | 핵심 로직이 담긴 파이썬 CLI. 번호 생성, 원격 데이터 동기화, HTML 파일 생성을 모두 처리 |
| `lotto_cache.csv` | 과거 당첨 번호 로컬 캐시 (`--sync`로 생성/갱신). 회차, 번호1~6, 보너스 컬럼 |
| `lotto_generator.html` | `--export-html`로 생성된 독립 실행형 웹페이지. 더블클릭으로 열면 인터넷 없이도 번호 생성 가능 |

## 번호 생성 방식

- **완전 무작위 생성**: 1~45 중 6개를 순수 무작위로 추출
- **통계 기반 생성 (참고용)**: 과거 당첨 데이터에서 번호별 출현 빈도를 구하고, 이를 가중치로 삼아 룰렛휠 방식(가중치 비례 비복원추출)으로 6개를 추출. 파이썬(`generate_weighted_numbers`)과 HTML의 JS(`weightedSample`)가 동일한 알고리즘을 사용

## 파이썬 CLI 사용법

```bash
# 완전 무작위 5게임 생성 (기본)
python lotto_generator.py

# 게임 수 지정
python lotto_generator.py -n 3

# 과거 데이터 기반 통계 생성 포함 (최초 실행 시 캐시 없으면 --sync 필요)
python lotto_generator.py --history lotto_cache.csv --sync

# 무작위 생성 없이 통계 기반 결과만 보기
python lotto_generator.py --history lotto_cache.csv --stats-only

# 캐시를 최신 회차로 갱신 + HTML 페이지도 함께 재생성
python lotto_generator.py --history lotto_cache.csv --sync --export-html lotto_generator.html --stats-only
```

### 옵션 정리

| 옵션 | 설명 |
|---|---|
| `-n, --count` | 생성할 게임 수 (기본값 5) |
| `--history <경로>` | 과거 당첨 번호 캐시 CSV 경로. 통계 기반 생성을 사용하려면 필수 |
| `--sync` | `--history` 캐시를 원격 데이터([lotto.ety.kr](https://lotto.ety.kr/))와 동기화. 캐시가 없으면 전체를, 있으면 새 회차만 추가 |
| `--stats-only` | 완전 무작위 생성 없이 통계 기반 생성만 수행 |
| `--export-html <경로>` | 현재 캐시 데이터를 내장한 독립 실행형 HTML 파일 생성 |

## 데이터 출처 및 갱신

과거 당첨 번호는 [lotto.ety.kr](https://lotto.ety.kr/)의 공개 JSON(`lotto.json`)에서 가져옵니다.
`lotto_cache.csv`는 스냅샷이므로, 새 회차 추첨 이후에는 아래 명령으로 캐시와 HTML을 함께 갱신하세요.

```bash
python lotto_generator.py --history lotto_cache.csv --sync --export-html lotto_generator.html --stats-only
```

`--sync`는 캐시에 이미 있는 회차는 건너뛰고 새로 추가된 회차만 이어붙이므로, 매번 전체 데이터를 다시 받지 않습니다.

## HTML 페이지 (`lotto_generator.html`)

- 인터넷 연결 없이 더블클릭만으로 브라우저에서 실행되는 정적 페이지입니다 (외부 CDN/네트워크 요청 없음).
- 생성 시점의 캐시 데이터가 파일 안에 그대로 내장되어 있어, 별도 서버나 fetch 없이 동작합니다.
- "완전 무작위 생성" / "통계 기반 생성(참고용)" 버튼으로 원하는 게임 수만큼 번호를 뽑을 수 있고, 역대 출현 빈도 TOP 10 표도 함께 확인할 수 있습니다.
- 결과 기록은 최신 2개까지만 화면에 남고 이전 기록은 자동으로 정리됩니다.
- 최신 회차를 반영하려면 위 갱신 명령으로 캐시와 HTML을 다시 생성해야 합니다 (페이지 자체는 실시간으로 데이터를 갱신하지 않습니다).
