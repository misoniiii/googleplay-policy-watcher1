import os
import sys
import hashlib
import requests
from bs4 import BeautifulSoup

# ── 설정 ──────────────────────────────────────────────
POLICY_URL = "https://support.google.com/googleplay/android-developer/table/12921780?hl=ko"
HASH_FILE = "last_hash.txt"
WEBHOOK_URL = os.environ.get("CHAT_WEBHOOK_URL")  # GitHub Secrets에서 주입

if not WEBHOOK_URL:
    print("❌ CHAT_WEBHOOK_URL 환경변수가 설정되지 않았습니다.")
    sys.exit(1)


def fetch_table_text() -> str:
    """정책 페이지에서 테이블 텍스트만 추출"""
    res = requests.get(POLICY_URL, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
    res.raise_for_status()
    soup = BeautifulSoup(res.text, "html.parser")

    table = soup.find("table")
    if table is None:
        # 테이블을 못 찾으면 본문 전체로 fallback
        return soup.get_text(separator="\n", strip=True)
    return table.get_text(separator="\n", strip=True)


def get_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_previous_hash() -> str | None:
    if os.path.exists(HASH_FILE):
        with open(HASH_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    return None


def save_hash(new_hash: str) -> None:
    with open(HASH_FILE, "w", encoding="utf-8") as f:
        f.write(new_hash)


def send_chat_notification(message: str) -> None:
    payload = {"text": message}
    res = requests.post(WEBHOOK_URL, json=payload, timeout=15)
    res.raise_for_status()


def main():
    current_text = fetch_table_text()
    current_hash = get_hash(current_text)
    previous_hash = load_previous_hash()

    if previous_hash is None:
        # 최초 실행: 기준 해시만 저장하고 알림은 생략(원치 않으면 아래 알림 코드 주석 해제)
        save_hash(current_hash)
        print("✅ 최초 실행 - 기준 해시 저장 완료")
        return

    if current_hash != previous_hash:
        message = (
            "🔔 Google Play 정책 페이지가 변경되었습니다.\n"
            f"확인: {POLICY_URL}"
        )
        send_chat_notification(message)
        save_hash(current_hash)
        print("✅ 변경 감지 - 알림 전송 완료")
    else:
        print("ℹ️ 변경 사항 없음")


if __name__ == "__main__":
    main()
