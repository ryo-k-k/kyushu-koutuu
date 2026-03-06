#!/usr/bin/env python3
"""
九州交通事業者ニュース自動送信ボット（GitHub Actions版）
スケジューラー不要・実行されたらニュースを収集してDiscordに送信するだけ
"""

import os
import time
import requests
from datetime import datetime
import anthropic

# 環境変数から取得（GitHub Secretsで設定）
DISCORD_WEBHOOK_URL = os.environ["DISCORD_WEBHOOK_URL"]
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]

KYUSHU_OPERATORS = [
    "JR九州", "西日本鉄道（西鉄）", "福岡市地下鉄", "北九州モノレール",
    "熊本電気鉄道", "長崎電気軌道", "鹿児島市電", "大分交通",
    "宮崎交通", "沖縄都市モノレール（ゆいレール）",
    "西鉄バス", "大分バス", "亀の井バス", "九州産交バス",
    "長崎バス", "鹿児島交通", "宮崎交通バス",
    "九州郵船", "名門大洋フェリー", "フェリーさんふらわあ",
    "松浦鉄道", "平成筑豊鉄道", "甘木鉄道", "南阿蘇鉄道",
    "くま川鉄道", "肥薩おれんじ鉄道", "島原鉄道"
]


def collect_and_summarize_news() -> str:
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    today = datetime.now().strftime("%Y年%m月%d日")
    operators_list = "、".join(KYUSHU_OPERATORS)

    prompt = f"""
今日（{today}）の九州の交通事業者に関する最新ニュースを収集・整理してください。

対象事業者：{operators_list}

以下の形式でまとめてください：

## 📰 九州交通事業者 ニュースまとめ（{today}）

### 🚃 鉄道・地下鉄
（JR九州、西鉄、各私鉄・第三セクターのニュース）

### 🚌 バス
（九州各県のバス事業者のニュース）

### ⛴️ フェリー・船舶
（九州発着のフェリー・航路のニュース）

### 📌 その他注目トピック
（ダイヤ改正、新サービス、補助金・政策など）

各カテゴリで重要なトピックを3〜5件ピックアップし、簡潔に説明してください。
ニュースが見つからない場合は「本日は特に新しい情報はありませんでした」と記載してください。
"""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        tools=[{"type": "web_search_20250305", "name": "web_search"}],
        messages=[{"role": "user", "content": prompt}]
    )

    result_text = ""
    for block in response.content:
        if block.type == "text":
            result_text += block.text

    return result_text if result_text else "ニュースの取得に失敗しました。"


def send_to_discord(message: str):
    max_length = 1900
    chunks = []

    if len(message) <= max_length:
        chunks = [message]
    else:
        lines = message.split('\n')
        current_chunk = ""
        for line in lines:
            if len(current_chunk) + len(line) + 1 > max_length:
                chunks.append(current_chunk)
                current_chunk = line + "\n"
            else:
                current_chunk += line + "\n"
        if current_chunk:
            chunks.append(current_chunk)

    for i, chunk in enumerate(chunks):
        response = requests.post(DISCORD_WEBHOOK_URL, json={"content": chunk})
        if response.status_code == 204:
            print(f"✅ Discord送信成功 ({i+1}/{len(chunks)})")
        else:
            print(f"❌ Discord送信失敗: {response.status_code} - {response.text}")
            raise Exception(f"Discord送信失敗: {response.status_code}")
        time.sleep(0.5)


def main():
    print(f"🚀 ニュース収集開始: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("📡 Claude AIでニュースを収集中...")
    news_summary = collect_and_summarize_news()
    print("📤 Discordに送信中...")
    send_to_discord(news_summary)
    print(f"✅ 完了: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()
