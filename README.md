# TaskCampus

要件定義書 v0.2 に基づく雛形実装。「貼るだけ登録」（自由テキストを貼り付けると科目・締切・種類を自動抽出する）が核となる差別化機能で、外部LLMを使わず ja-timex + RapidFuzz + 辞書ルールの自作パイプラインで実現している。

## 構成

```
backend/   FastAPI（タスク・科目CRUD、貼り付け登録の抽出エンジン）
frontend/  Next.js App Router + Tailwind（5画面のPWA）
```

## 今回実装した範囲

- タスクCRUD／科目CRUD（M2, M3）
- 締切ビュー：期限切れ／今日／今週／それ以降（M4, F-04）
- 貼り付け登録＋確認画面（M5, F-03）：ja-timexで日時表現を解決し、RapidFuzzで科目を曖昧マッチ、キーワード辞書で種類分類
- 5画面：ログイン／ホーム／貼り付け登録・確認／タスク編集／科目管理

## まだ実装していない範囲（要件どおり後回し）

- **Google OAuth（Supabase Auth）**：`backend/app/deps.py` は常に固定の開発用ユーザーを返すダミー実装。`frontend/src/lib/auth.tsx` も localStorage フラグだけの疑似ログイン。Supabaseプロジェクトを作成し、両方を差し替える必要がある
- **本番DB（Supabase Postgres）**：現状はSQLite（`backend/taskcampus.db`）。`DATABASE_URL` を差し替えれば動くはず（未検証）
- **リマインド通知（M6, F-05）**：Web Push / pg_cron 部分は未着手
- **デプロイ（Vercel / Render）**：未着手

## セットアップ

### バックエンド

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

初回起動時にSQLiteのテーブルが自動作成される。テストは `pytest`（貼り付け登録の抽出精度テスト `tests/test_extraction.py` を含む、20件パス確認済み）。

### フロントエンド

```bash
cd frontend
npm install
cp .env.local.example .env.local
npm run dev
```

`http://localhost:3000` を開き、ダミーのGoogleログインボタンでログイン後、科目を1つ登録してから「貼り付け登録」を試すのがおすすめ（科目が登録されていないと科目の自動マッチは働かない）。

## 貼り付け登録の抽出ロジックについて

`backend/app/extraction/` にロジックを分離している：

- `time_parser.py` — ja-timexが出すTIMEX3タグ（DURATION/DATE/TIME）を実際の絶対日時に解決する自作の合成ロジック。ja-timex自体は「来週」「月曜」を別々のタグとして返すだけで日時までは解決しないため、ここが本質的な自作部分
- `course_matcher.py` — RapidFuzzの部分一致スコアで登録済み科目とマッチング
- `type_classifier.py` — キーワード辞書によるレポート／小テスト／発表の分類
- `title_extractor.py` — 上記で特定した日時・科目名の文字列を取り除き、定型の提出指示文言を削るヒューリスティック

`tests/test_extraction.py` に16件のテストケースと精度テストがある（要件の「30件で80%」の出発点。実際に使ってみたテキストを追加していくと良い）。
