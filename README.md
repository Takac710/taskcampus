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
- **Google OAuth（Supabase Auth）（M1, F-01)**：フロントは`@supabase/supabase-js`でGoogle OAuthを実行し、取得したアクセストークンをAPIリクエストの`Authorization: Bearer`ヘッダーに付与。バックエンドは`backend/app/deps.py`でSupabaseのJWT（HS256, legacy JWT secret）を検証し、`sub`クレームでユーザーを解決・自動作成する。Supabaseプロジェクトを作成して環境変数を設定するまでは、どのAPIリクエストも401になる（ダミーログインへのフォールバックはない）
- **リマインド通知（M6, F-05)**：Web Push。バックエンドは`backend/app/notifications.py`が締切24時間前／当日朝8時（JST）の2種類をチェックし、`pywebpush`で送信する。FastAPIプロセス内の`apscheduler`が既定15分間隔で巡回（本番でRenderのスリープに引っかかる場合はSupabase pg_cron + Edge Functionsへの移行が必要、未実装）。フロントは`public/sw.js`（Service Worker）がpush/notificationclickを処理し、ホーム画面の「通知を有効にする」ボタンから`pushManager.subscribe()`で購読してバックエンドに登録する

## まだ実装していない範囲（要件どおり後回し）

- **Supabaseプロジェクトの作成自体**：コードは実装済みだが、実際のSupabaseプロジェクト作成・Google OAuthクライアントの設定・環境変数への値の投入はこのリポジトリの外で行う必要がある（下記セットアップ参照）
- **本番DB（Supabase Postgres）への切り替え**：`DATABASE_URL`をSupabaseの接続文字列に差し替えれば動く想定（`psycopg2-binary`導入済みだが実DBでの動作は未検証）。ローカル開発は引き続きSQLiteがデフォルト
- **通知スケジューラのSupabase pg_cron化**：デプロイ時にRenderの無料枠がスリープする問題への対応（要件§6で言及されている対策）。現状はFastAPIプロセス内のapschedulerで代替
- **デプロイ（Vercel / Render）**：未着手

## セットアップ

### Supabaseプロジェクトの準備（Google OAuthに必須）

ログインが実際に動くには、Supabaseプロジェクトを1つ作成し、以下を取得する必要がある：

1. [supabase.com](https://supabase.com) でプロジェクトを作成
2. Authentication → Sign In / Providers → Google を有効化
   - Google Cloud Console で OAuth クライアントID を作成し、承認済みリダイレクトURIに `https://<project-ref>.supabase.co/auth/v1/callback` を設定
   - 発行されたクライアントID／シークレットをSupabaseのGoogleプロバイダ設定に貼る
3. Authentication → URL Configuration → Redirect URLs に `http://localhost:3000` を追加（本番公開時は本番URLも追加）
4. Project Settings → API から `Project URL` と `anon public` キーを取得 → フロントの環境変数（`NEXT_PUBLIC_SUPABASE_URL` / `NEXT_PUBLIC_SUPABASE_ANON_KEY`）へ。同じ `Project URL` をバックエンドの `SUPABASE_URL` にも設定する
5. バックエンドのJWT検証は `backend/app/deps.py` がトークンの`alg`ヘッダーを見て自動的に分岐する：
   - 新しいプロジェクト（既定）はES256などの非対称鍵で署名される → `SUPABASE_URL`から`/auth/v1/.well-known/jwks.json`を取得して検証する。`SUPABASE_JWT_SECRET`は空でよい
   - 古いプロジェクト（Legacy JWT Secretのまま運用しているもの）はHS256の共有シークレットで署名される → Project Settings → API → JWT Settings の `Legacy JWT Secret` を `SUPABASE_JWT_SECRET` に設定する
   - どちらか迷う場合は、まず`SUPABASE_URL`だけ設定して試す（＝ES256側が既定で動く）。401が出続ける場合だけLegacy側を疑うとよい（**JWT SettingsのKey ID(kid)をJWT Secretと誤って貼ってしまうミスが起きやすいので注意**）
6. （DBもSupabaseに載せる場合）Project Settings → Database → Connection string から接続文字列を取得 → バックエンドの `DATABASE_URL` へ

### 通知用VAPIDキーの準備（Web Pushに必須、外部アカウント不要）

Supabaseとは異なり、こちらはローカルで鍵ペアを生成するだけで外部サービスへの登録は不要：

```bash
cd backend && source .venv/bin/activate
python scripts/generate_vapid_keys.py
```

出力された `VAPID_PUBLIC_KEY` / `VAPID_PRIVATE_KEY` を `.env` に貼る。`VAPID_SUBJECT` には連絡用の `mailto:` アドレスを設定する。

### バックエンド

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# .env を編集し、SUPABASE_JWT_SECRET と VAPID_PUBLIC_KEY / VAPID_PRIVATE_KEY を設定する
# （DATABASE_URL は未設定ならSQLiteのまま。Postgresに載せるなら上記6の接続文字列に差し替え）
uvicorn app.main:app --reload --port 8000
```

初回起動時にテーブルが自動作成される。テストは `pytest`（貼り付け登録の抽出精度テスト `tests/test_extraction.py`、JWT検証のテスト `tests/test_auth.py`、リマインド送信ロジックのテスト `tests/test_notifications.py` を含む、30件パス確認済み）。テストはSupabase/VAPIDなしでも通る（`get_current_user` をテスト用ユーザーにオーバーライドし、`pywebpush.webpush` 自体はモックしている）。

### フロントエンド

```bash
cd frontend
npm install
cp .env.local.example .env.local
# .env.local を編集し、NEXT_PUBLIC_SUPABASE_URL / NEXT_PUBLIC_SUPABASE_ANON_KEY を設定する
npm run dev
```

`http://localhost:3000` を開き、「Googleでログイン」ボタンでログイン後、科目を1つ登録してから「貼り付け登録」を試すのがおすすめ（科目が登録されていないと科目の自動マッチは働かない）。Supabaseの環境変数が未設定のままだと、ログインボタンを押しても失敗する（コンソールに警告が出る）。

## 貼り付け登録の抽出ロジックについて

`backend/app/extraction/` にロジックを分離している：

- `time_parser.py` — ja-timexが出すTIMEX3タグ（DURATION/DATE/TIME）を実際の絶対日時に解決する自作の合成ロジック。ja-timex自体は「来週」「月曜」を別々のタグとして返すだけで日時までは解決しないため、ここが本質的な自作部分
- `course_matcher.py` — RapidFuzzの部分一致スコアで登録済み科目とマッチング
- `type_classifier.py` — キーワード辞書によるレポート／小テスト／発表の分類
- `title_extractor.py` — 上記で特定した日時・科目名の文字列を取り除き、定型の提出指示文言を削るヒューリスティック

`tests/test_extraction.py` に30件のテストケースと精度テストがある（要件の「30件で80%」を満たす）。このうち数件は「正しく動いている」ことよりも「正しく諦めてマニュアル入力にフォールバックしている」ことを確認するケース（略称が曖昧一致の信頼度閾値未満、「3日以内」「次回の授業まで」のような相対表現が未対応）。加えて、テストセット拡充時に2つの既知の改善余地を見つけてコメントで記録した：「今週中に」が週の終わりでなく今日に解決される、過去時制（「〜でした」）の日付が1年先に繰り上げられてしまう。どちらも確認画面で気づいて手修正できるため実害は限定的だが、ルール改善の候補として残してある。
