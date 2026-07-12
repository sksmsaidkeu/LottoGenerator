"""
로또 6/45 번호 생성기

- 완전 무작위 생성 (기본 모드)
- 과거 당첨 번호 통계를 반영한 가중치 기반 생성 (통계 모드)
- 원격 JSON(https://lotto.ety.kr/lotto.json)에서 과거 당첨 번호를 받아와
  로컬 CSV 캐시로 저장하고, 이후에는 새로 추가된 회차만 이어서 갱신 (--sync)

주의:
    로또는 매 회차 완전히 독립적인 무작위 추첨입니다.
    과거 당첨 번호는 미래 당첨 번호에 어떠한 영향도 주지 않으므로,
    통계 모드는 "진짜 예측"이 아니라 과거 출현 빈도를 참고해 번호를
    고르는 재미 요소일 뿐입니다. 당첨을 보장하지 않습니다.
"""

import argparse
import csv
import json
import random
import urllib.error
import urllib.request
from collections import Counter
from pathlib import Path

NUM_MIN = 1
NUM_MAX = 45
PICK_COUNT = 6

REMOTE_JSON_URL = "https://lotto.ety.kr/lotto.json"
CSV_FIELDNAMES = ["회차", "번호1", "번호2", "번호3", "번호4", "번호5", "번호6", "보너스"]


def generate_random_numbers(count=1):
    """완전 무작위로 로또 번호 세트를 생성한다."""
    results = []
    for _ in range(count):
        numbers = sorted(random.sample(range(NUM_MIN, NUM_MAX + 1), PICK_COUNT))
        results.append(numbers)
    return results


def fetch_remote_draws(url=REMOTE_JSON_URL, timeout=10):
    """원격 JSON에서 전체 회차 데이터를 받아와 정규화된 딕셔너리 리스트로 반환한다."""
    request = urllib.request.Request(
        url, headers={"User-Agent": "lotto-generator/1.0 (personal project)"}
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        raw = json.load(response)

    records = []
    for item in raw:
        try:
            round_no = int(item["회차"])
            numbers = sorted(int(item[f"번호{i}"]) for i in range(1, 7))
            bonus = int(item["보너스"]) if item.get("보너스") is not None else None
        except (KeyError, TypeError, ValueError):
            continue  # 형식이 다른 항목은 건너뜀
        records.append({"회차": round_no, "numbers": numbers, "보너스": bonus})

    return records


def read_cache(csv_path):
    """로컬 캐시 CSV를 읽어 회차 오름차순 딕셔너리 리스트로 반환한다. 없으면 빈 리스트."""
    path = Path(csv_path)
    if not path.exists():
        return []

    records = []
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                round_no = int(row["회차"])
                numbers = sorted(int(row[f"번호{i}"]) for i in range(1, 7))
                bonus_raw = row.get("보너스")
                bonus = int(bonus_raw) if bonus_raw not in (None, "") else None
            except (KeyError, TypeError, ValueError):
                continue
            records.append({"회차": round_no, "numbers": numbers, "보너스": bonus})

    records.sort(key=lambda r: r["회차"])
    return records


def write_cache(csv_path, records):
    """딕셔너리 리스트를 회차 오름차순으로 정렬해 캐시 CSV에 저장한다."""
    records = sorted(records, key=lambda r: r["회차"])
    path = Path(csv_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDNAMES)
        writer.writeheader()
        for r in records:
            row = {"회차": r["회차"], "보너스": r["보너스"] if r["보너스"] is not None else ""}
            for i, n in enumerate(r["numbers"], start=1):
                row[f"번호{i}"] = n
            writer.writerow(row)


def sync_cache(csv_path, url=REMOTE_JSON_URL):
    """
    원격 데이터를 받아와 로컬 캐시를 갱신한다.
    이미 저장된 회차는 건너뛰고, 그보다 최신 회차만 추가한다.

    반환값: (새로 추가된 회차 수, 전체 회차 수)
    """
    existing = read_cache(csv_path)
    last_round = max((r["회차"] for r in existing), default=0)

    remote = fetch_remote_draws(url)
    new_records = [r for r in remote if r["회차"] > last_round]

    if new_records:
        merged = existing + new_records
        write_cache(csv_path, merged)
        total = len(merged)
    else:
        total = len(existing)

    return len(new_records), total


HTML_TEMPLATE = """<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>로또 6/45 번호 생성기</title>
<link rel="manifest" href="manifest.json">
<link rel="apple-touch-icon" href="icons/apple-touch-icon.png">
<link rel="icon" href="icons/icon-192.png">
<meta name="theme-color" content="#1a2942">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="로또 생성기">
<style>
  :root {
    color-scheme: light dark;
    --bg: #faf9f7;
    --surface: #ffffff;
    --text: #1c1c1e;
    --text-muted: #6b6b70;
    --border: #e8e6e1;
    --accent: #1a2942;
    --accent-soft: #33455f;
    --gold: #a9812f;
    --gold-soft: #f4ecd8;
    --shadow: 0 1px 2px rgba(20, 20, 20, 0.04), 0 8px 24px rgba(20, 20, 20, 0.06);
  }
  * { box-sizing: border-box; }
  body {
    font-family: "Pretendard", -apple-system, "Segoe UI", "Malgun Gothic", sans-serif;
    background: var(--bg);
    color: var(--text);
    max-width: 720px;
    margin: 0 auto;
    padding: 56px 20px 40px;
    line-height: 1.6;
    letter-spacing: -0.01em;
  }
  .brand { display: flex; align-items: baseline; gap: 10px; margin-bottom: 4px; }
  .brand .mark { width: 10px; height: 10px; border-radius: 50%; background: var(--gold); display: inline-block; }
  h1 { font-size: 1.55rem; font-weight: 700; margin: 0; letter-spacing: -0.02em; }
  .meta { color: var(--text-muted); font-size: 0.85rem; margin: 6px 0 28px; }

  .notice {
    background: var(--surface);
    border: 1px solid var(--border);
    border-left: 3px solid var(--gold);
    border-radius: 10px;
    padding: 16px 18px;
    font-size: 0.87rem;
    color: var(--text-muted);
    margin-bottom: 32px;
    box-shadow: var(--shadow);
  }

  .panel {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 22px 24px;
    margin-bottom: 28px;
    box-shadow: var(--shadow);
  }

  .controls { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }
  .controls label { font-size: 0.88rem; color: var(--text-muted); }
  .controls input[type=number] {
    width: 64px; padding: 8px 10px; border: 1px solid var(--border); border-radius: 8px;
    font-size: 0.9rem; background: var(--bg); color: var(--text);
  }
  .controls input[type=number]:focus { outline: none; border-color: var(--accent-soft); }

  button {
    padding: 10px 18px; border: 1px solid var(--accent); border-radius: 999px;
    background: var(--accent); color: #fff; cursor: pointer; font-size: 0.88rem;
    font-weight: 600; letter-spacing: -0.01em; transition: transform 0.12s ease, opacity 0.12s ease;
  }
  button.secondary { background: transparent; color: var(--accent); border-color: var(--border); }
  button:hover { opacity: 0.85; }
  button:active { transform: scale(0.97); }

  .result-block { margin-top: 22px; padding-top: 20px; border-top: 1px dashed var(--border); }
  .result-block:first-child { margin-top: 0; padding-top: 0; border-top: none; }
  .result-block h2 { font-size: 0.95rem; font-weight: 700; margin: 0 0 14px; color: var(--accent); }
  .game-row { display: flex; align-items: center; gap: 14px; margin-bottom: 10px; }
  .game-row:last-child { margin-bottom: 0; }
  .game-label { width: 46px; flex-shrink: 0; font-size: 0.78rem; color: var(--text-muted); }
  .balls { display: flex; gap: 8px; flex-wrap: wrap; }
  .ball {
    width: 34px; height: 34px; border-radius: 50%;
    background: linear-gradient(160deg, var(--accent-soft), var(--accent));
    color: #fff; display: flex; align-items: center; justify-content: center;
    font-weight: 700; font-size: 0.82rem; box-shadow: 0 2px 5px rgba(26, 41, 66, 0.25);
  }

  table { border-collapse: collapse; width: 100%; margin-top: 4px; }
  th, td { padding: 10px 12px; text-align: center; font-size: 0.87rem; }
  th { color: var(--text-muted); font-weight: 600; font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.04em; border-bottom: 1px solid var(--border); }
  td { border-bottom: 1px solid var(--border); }
  tbody tr:last-child td { border-bottom: none; }
  tbody tr:hover { background: var(--gold-soft); }

  footer { margin-top: 8px; font-size: 0.78rem; color: var(--text-muted); text-align: center; }
  footer code { background: var(--surface); border: 1px solid var(--border); padding: 2px 6px; border-radius: 5px; font-size: 0.75rem; }

  @media (prefers-color-scheme: dark) {
    :root {
      --bg: #121214;
      --surface: #1c1c1f;
      --text: #ededee;
      --text-muted: #9a9a9e;
      --border: #2e2e32;
      --accent: #e8e6e1;
      --accent-soft: #c9c6bf;
      --gold: #d4af6a;
      --gold-soft: #2a2620;
      --shadow: 0 1px 2px rgba(0, 0, 0, 0.3), 0 8px 24px rgba(0, 0, 0, 0.35);
    }
    .ball { background: linear-gradient(160deg, var(--accent-soft), var(--accent)); color: #16161a; box-shadow: 0 2px 5px rgba(0,0,0,0.4); }
    button { color: #16161a; }
    button.secondary { color: var(--accent); }
  }
</style>
</head>
<body>
  <div class="brand"><span class="mark"></span><h1>로또 6/45 번호 생성기</h1></div>
  <div class="meta" id="meta"></div>

  <div class="notice">
    로또는 매 회차 완전히 독립적인 무작위 추첨입니다. 과거 당첨 번호는 미래 결과에 어떠한 영향도 주지 않습니다.
    아래 "통계 기반 생성"은 과거 출현 빈도를 참고한 재미 요소일 뿐, 당첨을 예측하거나 보장하지 않습니다.
  </div>

  <div class="panel">
    <div class="controls">
      <label for="count">게임 수</label>
      <input type="number" id="count" value="5" min="1" max="20">
      <button id="btnRandom">완전 무작위 생성</button>
      <button id="btnWeighted" class="secondary">통계 기반 생성 (참고용)</button>
    </div>
    <div id="results"></div>
  </div>

  <div class="panel">
    <div class="result-block">
      <h2>역대 출현 빈도 TOP 10</h2>
      <table>
        <thead><tr><th>순위</th><th>번호</th><th>출현 횟수</th></tr></thead>
        <tbody id="freqBody"></tbody>
      </table>
    </div>
  </div>

  <footer>
    이 데이터는 회차 __LATEST_ROUND__ 까지 반영된 정적 스냅샷입니다 (총 __TOTAL_ROUNDS__ 회차).<br>
    최신 회차를 반영하려면 파이썬 스크립트로 캐시를 갱신한 뒤 이 파일을 다시 생성하세요:<br>
    <code>python lotto_generator.py --history lotto_cache.csv --sync --export-html lotto_generator.html</code>
  </footer>

<script>
const LOTTO_DATA = __LOTTO_DATA_JSON__;

function computeFrequency(data) {
  const freq = new Array(46).fill(0);
  data.forEach(rec => rec.n.forEach(num => { freq[num] += 1; }));
  return freq;
}

function randomSample(k) {
  const arr = Array.from({length: 45}, (_, i) => i + 1);
  for (let i = arr.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [arr[i], arr[j]] = [arr[j], arr[i]];
  }
  return arr.slice(0, k).sort((a, b) => a - b);
}

function weightedSample(weights, k) {
  const pool = weights.map((w, idx) => ({ num: idx + 1, w }));
  const chosen = [];
  for (let i = 0; i < k; i++) {
    const total = pool.reduce((s, p) => s + p.w, 0);
    let r = Math.random() * total;
    for (let j = 0; j < pool.length; j++) {
      r -= pool[j].w;
      if (r <= 0) {
        chosen.push(pool[j].num);
        pool.splice(j, 1);
        break;
      }
    }
  }
  return chosen.sort((a, b) => a - b);
}

function renderBalls(numbers) {
  return numbers.map(n => `<div class="ball">${n}</div>`).join('');
}

function renderSets(label, sets) {
  const container = document.getElementById('results');
  const block = document.createElement('div');
  block.className = 'result-block';
  const title = document.createElement('h2');
  title.textContent = label;
  block.appendChild(title);
  sets.forEach((numbers, i) => {
    const row = document.createElement('div');
    row.className = 'game-row';
    row.innerHTML = `<div class="game-label">${i + 1}게임</div><div class="balls">${renderBalls(numbers)}</div>`;
    block.appendChild(row);
  });
  container.prepend(block);

  const blocks = container.querySelectorAll('.result-block');
  const MAX_HISTORY = 2;
  blocks.forEach((el, i) => { if (i >= MAX_HISTORY) el.remove(); });
}

function renderFrequencyTable(freq) {
  const entries = [];
  for (let n = 1; n <= 45; n++) entries.push([n, freq[n]]);
  entries.sort((a, b) => b[1] - a[1]);
  const top10 = entries.slice(0, 10);
  const body = document.getElementById('freqBody');
  body.innerHTML = top10.map((e, i) => `<tr><td>${i + 1}</td><td>${e[0]}번</td><td>${e[1]}회</td></tr>`).join('');
}

function init() {
  const rounds = LOTTO_DATA.map(r => r.r);
  const latest = Math.max(...rounds);
  document.getElementById('meta').textContent = `내장 데이터: 총 ${LOTTO_DATA.length}회차 (최신 ${latest}회차 기준)`;

  const freq = computeFrequency(LOTTO_DATA);
  renderFrequencyTable(freq);

  document.getElementById('btnRandom').addEventListener('click', () => {
    const count = Math.max(1, Math.min(20, parseInt(document.getElementById('count').value, 10) || 1));
    const sets = Array.from({length: count}, () => randomSample(6));
    renderSets('완전 무작위 생성', sets);
  });

  document.getElementById('btnWeighted').addEventListener('click', () => {
    const count = Math.max(1, Math.min(20, parseInt(document.getElementById('count').value, 10) || 1));
    const weights = [];
    for (let n = 1; n <= 45; n++) weights.push(freq[n] + 1);
    const sets = Array.from({length: count}, () => weightedSample(weights, 6));
    renderSets('통계 기반 생성 (참고용)', sets);
  });
}

init();

if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('sw.js').catch(() => {});
  });
}
</script>
</body>
</html>
"""


def write_html_export(html_path, records):
    """캐시 레코드를 내장한 정적 HTML 파일을 생성한다 (오프라인에서 브라우저로 실행 가능)."""
    if not records:
        raise ValueError("내보낼 데이터가 없습니다.")

    latest_round = max(r["회차"] for r in records)
    data_for_js = [{"r": r["회차"], "n": r["numbers"], "b": r["보너스"]} for r in records]
    data_json = json.dumps(data_for_js, ensure_ascii=False)

    html = (
        HTML_TEMPLATE.replace("__LOTTO_DATA_JSON__", data_json)
        .replace("__LATEST_ROUND__", str(latest_round))
        .replace("__TOTAL_ROUNDS__", str(len(records)))
    )

    path = Path(html_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html, encoding="utf-8")


def build_weights(history):
    """과거 출현 빈도를 기반으로 1~45 각 번호의 가중치를 계산한다."""
    counter = Counter()
    for draw in history:
        counter.update(draw)

    # 한 번도 나오지 않은 번호도 0이 아닌 최소 가중치를 부여해
    # 뽑힐 기회를 완전히 배제하지 않는다.
    weights = []
    for n in range(NUM_MIN, NUM_MAX + 1):
        weights.append(counter.get(n, 0) + 1)
    return weights


def weighted_sample_without_replacement(numbers, weights, k):
    """가중치 비례 룰렛휠 방식으로 중복 없이 k개를 뽑는다."""
    pool = list(zip(numbers, weights))
    chosen = []

    for _ in range(k):
        total = sum(w for _, w in pool)
        r = random.uniform(0, total)
        for i, (num, w) in enumerate(pool):
            r -= w
            if r <= 0:
                chosen.append(num)
                pool.pop(i)
                break

    return chosen


def generate_weighted_numbers(weights, count=1):
    """과거 빈도 가중치를 반영해 중복 없는 6개 번호 세트를 생성한다 (룰렛휠 방식)."""
    population = list(range(NUM_MIN, NUM_MAX + 1))
    results = []

    for _ in range(count):
        chosen = weighted_sample_without_replacement(population, weights, PICK_COUNT)
        results.append(sorted(chosen))
    return results


def print_numbers(label, sets_of_numbers):
    print(f"\n[{label}]")
    for i, numbers in enumerate(sets_of_numbers, start=1):
        formatted = " ".join(f"{n:2d}" for n in numbers)
        print(f"  {i}게임: {formatted}")


def show_top_frequency(history, top_n=10):
    counter = Counter()
    for draw in history:
        counter.update(draw)

    print(f"\n[역대 출현 빈도 TOP {top_n}]")
    for number, count in counter.most_common(top_n):
        print(f"  {number:2d}번: {count}회")


def main():
    parser = argparse.ArgumentParser(description="로또 6/45 번호 생성기")
    parser.add_argument(
        "-n", "--count", type=int, default=5, help="생성할 게임 수 (기본값: 5)"
    )
    parser.add_argument(
        "--history",
        type=str,
        default=None,
        help="과거 당첨 번호 캐시 CSV 파일 경로. 지정 시 통계 기반 생성 모드가 함께 실행됩니다.",
    )
    parser.add_argument(
        "--sync",
        action="store_true",
        help="--history 경로의 캐시를 원격 데이터(lotto.ety.kr)와 동기화합니다. "
        "파일이 없으면 전체를 새로 받고, 있으면 새로 추가된 회차만 이어붙입니다.",
    )
    parser.add_argument(
        "--stats-only",
        action="store_true",
        help="완전 무작위 생성 없이 통계 기반 생성만 수행합니다 (--history 필요).",
    )
    parser.add_argument(
        "--export-html",
        type=str,
        default=None,
        help="현재 캐시 데이터를 내장한 독립 실행형 HTML 파일을 생성합니다 (--history 필요). "
        "생성된 파일은 브라우저에서 더블클릭으로 열어 오프라인으로 사용할 수 있습니다.",
    )
    args = parser.parse_args()

    if args.stats_only and not args.history:
        parser.error("--stats-only 옵션은 --history와 함께 사용해야 합니다.")
    if args.sync and not args.history:
        parser.error("--sync 옵션은 --history와 함께 사용해야 합니다.")
    if args.export_html and not args.history:
        parser.error("--export-html 옵션은 --history와 함께 사용해야 합니다.")

    if not args.stats_only:
        random_sets = generate_random_numbers(args.count)
        print_numbers("완전 무작위 생성", random_sets)

    if args.history:
        if args.sync:
            try:
                added, total = sync_cache(args.history)
            except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
                print(f"\n경고: 원격 데이터 동기화에 실패했습니다 ({e}). 기존 캐시로 계속 진행합니다.")
            else:
                if added:
                    print(f"\n캐시 동기화 완료: 새 회차 {added}개 추가 (전체 {total}회차).")
                else:
                    print(f"\n캐시 동기화 완료: 새로 추가된 회차 없음 (전체 {total}회차).")

        cache_records = read_cache(args.history)
        if not cache_records:
            print(f"\n오류: 히스토리 파일을 찾을 수 없거나 유효한 데이터가 없습니다: {args.history}")
            print("먼저 --sync 옵션으로 데이터를 받아오세요.")
            return

        history = [r["numbers"] for r in cache_records]

        print(f"\n총 {len(history)}회차의 과거 데이터를 사용합니다.")
        show_top_frequency(history)

        weights = build_weights(history)
        weighted_sets = generate_weighted_numbers(weights, args.count)
        print_numbers("과거 통계 기반 생성 (참고용)", weighted_sets)

        print(
            "\n※ 로또는 매 회차 독립적인 무작위 추첨이며, 과거 데이터는 "
            "미래 당첨 결과에 영향을 주지 않습니다. 통계 기반 결과는 재미로만 참고하세요."
        )

        if args.export_html:
            write_html_export(args.export_html, cache_records)
            print(f"\nHTML 파일 생성 완료: {args.export_html} (브라우저에서 더블클릭으로 열어보세요)")


if __name__ == "__main__":
    main()
