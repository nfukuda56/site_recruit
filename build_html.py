#!/usr/bin/env python3
"""
slides_content_sample.md → index.html 変換スクリプト

【通常実行】
    python build_html.py
    → スクリプトと同じフォルダの slides_content_sample.md を読み込む

【ドラッグ&ドロップ / 引数指定】
    python build_html.py path/to/slides_content_sample.md
    → 指定した MD ファイルを読み込む

出力先: スクリプト（または .exe）と同じフォルダの index.html
slides_content_sample.md は変更しません。

■ MDフォーマット
  スライド区切り : --- (行全体がハイフン3つ以上)
  スライド種別   : 各ブロック先頭行に [type] を記述
                   title / lr / rl / full / qa
  フィールド     : key: value 形式（コロン以降すべてが値）
  テキスト装飾   : *テキスト* → <em>テキスト</em>（緑色強調）
  改行           : <br> をそのまま記述
  コメント行     : # で始まる行は無視

■ スライド種別ごとの使用フィールド
  [title]  company / h1 / tagline
  [lr/rl/full]  label / photo / h2 / caption
                photo にファイルパス(.jpg 等)を指定→<img>タグ
                photo にテキストを指定→プレースホルダー表示
  [qa]     qa_label / h2 / qa_sub
"""

import re
import sys
from pathlib import Path

# -- パス設定 ----------------------------------------------------
# .exe として実行されているか判定
if getattr(sys, 'frozen', False):
    # PyInstaller exe の場合：exeファイルのあるフォルダを基準にする
    EXE_DIR = Path(sys.executable).parent
else:
    # Pythonスクリプトの場合：スクリプトのあるフォルダを基準にする
    EXE_DIR = Path(__file__).parent

# ドラッグ&ドロップまたはコマンドライン引数でMDパスを受け取る
if len(sys.argv) >= 2:
    MD_FILE = Path(sys.argv[1])
else:
    MD_FILE = EXE_DIR / "slides_content_sample.md"

OUT = EXE_DIR / "index.html"

# -- SVGプレースホルダー ----------------------------------------─
_SVG = (
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.2">'
    '<rect x="3" y="3" width="18" height="18" rx="2"/>'
    '<circle cx="8.5" cy="8.5" r="1.5"/>'
    '<path d="M21 15l-5-5L5 21"/>'
    '</svg>'
)

# -- ユーティリティ ----------------------------------------------
def inline(text: str) -> str:
    """*text* を <em>text</em> に変換する"""
    return re.sub(r'\*(.+?)\*', r'<em>\1</em>', text, flags=re.DOTALL)

def photo_html(value: str) -> str:
    """photoフィールドの値に応じて <img> またはプレースホルダーを返す"""
    v = value.strip()
    if re.search(r'\.(jpe?g|png|webp|gif|svg)$', v, re.IGNORECASE):
        return f'<img src="{v}" alt="">'
    return (
        '<div class="s-placeholder">\n'
        f'          {_SVG}\n'
        f'          <span>{v}</span>\n'
        '        </div>'
    )

# -- スライド描画 ------------------------------------------------
def render_slide(f: dict) -> str:
    t = f.get("type", "lr")

    # ① タイトルスライド
    if t == "title":
        return (
            '    <section>\n'
            '      <div class="slide-inner title-slide">\n'
            f'        <p class="t-company">{f.get("company", "")}</p>\n'
            f'        <h1>{inline(f.get("h1", ""))}</h1>\n'
            f'        <p class="t-tagline">{f.get("tagline", "")}</p>\n'
            '      </div>\n'
            '    </section>'
        )

    # ② Q&Aスライド
    if t == "qa":
        return (
            '    <section>\n'
            '      <div class="slide-inner qa-slide">\n'
            f'        <p class="qa-label">{f.get("qa_label", "Q &amp; A")}</p>\n'
            f'        <h2>{inline(f.get("h2", ""))}</h2>\n'
            f'        <p class="qa-sub">{f.get("qa_sub", "")}</p>\n'
            '      </div>\n'
            '    </section>'
        )

    # ③ lr / rl / full
    label   = f.get("label", "")
    caption = f.get("caption", "")
    h2      = inline(f.get("h2", ""))
    photo   = photo_html(f.get("photo", ""))

    label_part   = f'        <p class="s-label">{label}</p>\n' if label else ""
    caption_part = f'        <p class="s-caption">{caption}</p>\n' if caption else ""

    return (
        '    <section>\n'
        f'      <div class="slide-inner {t}">\n'
        '        <div class="s-photo">\n'
        f'          {photo}\n'
        '        </div>\n'
        '        <div class="s-body">\n'
        f'{label_part}'
        f'          <h2>{h2}</h2>\n'
        f'{caption_part}'
        '        </div>\n'
        '      </div>\n'
        '    </section>'
    )

# -- MDパース ----------------------------------------------------
def parse_md(text: str) -> list:
    slides = []
    # --- でブロック分割
    blocks = re.split(r'\n[ \t]*---+[ \t]*\n', '\n' + text + '\n')
    for block in blocks:
        # コメント行(#)とHTMLコメントを除去
        block = re.sub(r'<!--.*?-->', '', block, flags=re.DOTALL)
        lines = [l for l in block.splitlines()
                 if l.strip() and not l.strip().startswith('#')]
        if not lines:
            continue
        # 先頭行から [type] を取得
        m = re.match(r'^\[(\w+)\]', lines[0].strip())
        if not m:
            continue
        fields: dict = {"type": m.group(1)}
        for line in lines[1:]:
            if ':' not in line:
                continue
            key, _, val = line.partition(':')
            k = key.strip()
            v = val.strip()
            if k:
                fields[k] = v
        slides.append(fields)
    return slides

# -- CSS (index.html 共通スタイル) ------------------------------
CSS = """\
  :root {
    --blue:    #059669;   /* Accent：ミントグリーン */
    --blue-lt: #D1FAE5;   /* Accent Lt：薄いミント */
    --amber:   #34D399;   /* Accent 2：明るいグリーン */
    --gray:    #6B7280;   /* テキストグレー */
    --light:   #F0FDF8;   /* 背景：クリーム寄りの薄緑 */
    --dark:    #064E3B;   /* 見出し：深いグリーン */

    /* -- フォントサイズ変数 -- */
    --fs-title-h1:   4.25rem;
    --fs-company:    1.17rem;
    --fs-tagline:    1.10rem;
    --fs-h2:         2.40rem;
    --fs-h2-qa:      2.75rem;
    --fs-caption:    1.17rem;
    --fs-label:      1.02rem;
    --fs-qa-label:   1.02rem;
    --fs-qa-sub:     1.02rem;
  }

  .reveal {
    font-family: 'Hiragino Kaku Gothic ProN', 'Noto Sans JP', 'Yu Gothic', sans-serif;
  }

  /* -- section リセット -- */
  .reveal .slides section {
    padding: 0 !important;
    text-align: left !important;
    top: 0 !important;
    height: 100% !important;
  }

  /* ════════════════
     共通インナーラッパー
  ════════════════ */
  .reveal .slide-inner {
    position: absolute;
    inset: 0;
    width: 100%;
    height: 100%;
    display: flex;
  }

  /* -- 左写真・右テキスト -- */
  .reveal .slide-inner.lr { flex-direction: row; }
  .reveal .slide-inner.rl { flex-direction: row-reverse; }

  .reveal .slide-inner.lr .s-photo,
  .reveal .slide-inner.rl .s-photo {
    width: 52%;
    flex-shrink: 0;
    overflow: hidden;
    background: var(--light);
    display: flex;
    align-items: center;
    justify-content: center;
  }
  .reveal .slide-inner.lr .s-photo img,
  .reveal .slide-inner.rl .s-photo img {
    width: 100%; height: 100%;
    object-fit: cover;
    display: block;
  }
  .reveal .slide-inner.lr .s-body,
  .reveal .slide-inner.rl .s-body {
    width: 48%;
    padding: 60px 52px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    background: #fff;
    overflow: hidden;
  }

  /* -- フル写真 -- */
  .reveal .slide-inner.full {
    position: absolute;
    inset: 0;
  }
  .reveal .slide-inner.full .s-photo {
    position: absolute;
    inset: 0;
    overflow: hidden;
    background: var(--light);
    display: flex;
    align-items: center;
    justify-content: center;
  }
  .reveal .slide-inner.full .s-photo img {
    width: 100%; height: 100%;
    object-fit: cover;
  }
  .reveal .slide-inner.full .s-body {
    position: absolute;
    bottom: 0; left: 0; right: 0;
    padding: 32px 64px 52px;
    background: linear-gradient(to top, rgba(240,253,248,0.97) 60%, transparent);
    z-index: 2;
    display: flex;
    flex-direction: column;
  }

  /* -- タイトル -- */
  .reveal .slide-inner.title-slide {
    flex-direction: column;
    align-items: center;
    justify-content: center;
    background: var(--light);
    text-align: center;
  }
  .reveal .slide-inner.title-slide::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 5px;
    background: linear-gradient(90deg, var(--blue), var(--amber));
  }

  /* -- Q&A -- */
  .reveal .slide-inner.qa-slide {
    flex-direction: column;
    align-items: center;
    justify-content: center;
    background: var(--blue);
    text-align: center;
  }

  /* ════════════════
     テキスト要素
  ════════════════ */

  /* タイトルスライド */
  .reveal .slide-inner.title-slide .t-company {
    font-size: var(--fs-company);
    letter-spacing: 0.25em;
    color: var(--gray);
    margin-bottom: 32px;
  }
  .reveal .slide-inner.title-slide h1 {
    font-size: var(--fs-title-h1) !important;
    font-weight: 900 !important;
    line-height: 1.35 !important;
    color: var(--dark) !important;
    margin-bottom: 24px !important;
    text-shadow: none !important;
    letter-spacing: -0.01em;
  }
  .reveal .slide-inner.title-slide h1 em {
    font-style: normal;
    color: var(--blue);
  }
  .reveal .slide-inner.title-slide .t-tagline {
    font-size: var(--fs-tagline);
    color: var(--gray);
    letter-spacing: 0.06em;
  }

  /* セクションラベル */
  .reveal .s-label {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    font-size: var(--fs-label) !important;
    font-weight: 700 !important;
    letter-spacing: 0.2em !important;
    text-transform: uppercase !important;
    color: var(--blue) !important;
    margin-bottom: 16px !important;
    text-shadow: none !important;
  }
  .reveal .s-label::before {
    content: '';
    display: block;
    width: 20px; height: 2px;
    background: var(--blue);
    border-radius: 1px;
    flex-shrink: 0;
  }

  /* 見出し h2 */
  .reveal .slides section h2 {
    font-size: var(--fs-h2) !important;
    font-weight: 800 !important;
    line-height: 1.5 !important;
    color: var(--dark) !important;
    margin: 0 0 20px !important;
    letter-spacing: -0.01em !important;
    text-shadow: none !important;
    text-transform: none !important;
  }
  .reveal .slides section h2 em {
    font-style: normal !important;
    color: var(--blue) !important;
  }

  /* キャプション */
  .reveal .s-caption {
    font-size: var(--fs-caption) !important;
    line-height: 1.95 !important;
    color: var(--gray) !important;
    border-left: 3px solid var(--blue-lt) !important;
    padding-left: 16px !important;
    margin: 0 !important;
    text-shadow: none !important;
  }

  /* Q&A テキスト */
  .reveal .slide-inner.qa-slide .qa-label {
    font-size: var(--fs-qa-label);
    letter-spacing: 0.3em;
    color: rgba(255,255,255,0.6);
    margin-bottom: 24px;
  }
  .reveal .slide-inner.qa-slide h2 {
    font-size: var(--fs-h2-qa) !important;
    font-weight: 900 !important;
    color: #fff !important;
    line-height: 1.55 !important;
    margin: 0 0 20px !important;
    text-shadow: none !important;
  }
  .reveal .slide-inner.qa-slide .qa-sub {
    font-size: var(--fs-qa-sub);
    color: rgba(255,255,255,0.65);
    letter-spacing: 0.08em;
  }

  /* ════════════════
     プレースホルダー
  ════════════════ */
  .reveal .s-placeholder {
    width: 100%; height: 100%;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 14px;
    background: var(--light);
  }
  .reveal .s-placeholder svg {
    width: 48px; height: 48px;
    color: #6EE7B7;
  }
  .reveal .s-placeholder span {
    font-size: 0.68rem;
    letter-spacing: 0.08em;
    color: #34D399;
  }

  /* ════════════════
     Reveal UI
  ════════════════ */
  .reveal .progress { color: var(--blue); height: 3px; }
  .reveal .slide-number {
    font-size: 0.62rem;
    color: var(--gray);
    background: transparent;
    right: 16px; bottom: 16px;
  }"""

# -- HTMLテンプレート --------------------------------------------
HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>採用説明会</title>

<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/dist/reveal.css" crossorigin="anonymous">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/dist/theme/white.css" crossorigin="anonymous">

<style>
{css}
</style>
</head>
<body>
<div class="reveal">
  <div class="slides">

{slides}

  </div>
</div>

<script src="https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/dist/reveal.js" crossorigin="anonymous"></script>
<script>
  Reveal.initialize({{
    hash: false,
    slideNumber: 'c/t',
    progress: true,
    controls: true,
    touch: true,
    transition: 'fade',
    transitionSpeed: 'default',
    width: 1280,
    height: 720,
    margin: 0,
    minScale: 0.2,
    maxScale: 2.0,
    plugins: []
  }});
</script>
</body>
</html>"""

# -- メイン処理 --------------------------------------------------
def main():
    print(f"読み込み: {MD_FILE}")

    if not MD_FILE.exists():
        print(f"\n[エラー] ファイルが見つかりません:\n  {MD_FILE}")
        print("MDファイルをこのexeにドラッグ&ドロップして実行してください。")
        input("\nEnterキーで閉じる...")
        sys.exit(1)

    try:
        md_text = MD_FILE.read_text(encoding="utf-8")
    except Exception as e:
        print(f"\n[エラー] ファイルを読み込めませんでした: {e}")
        input("\nEnterキーで閉じる...")
        sys.exit(1)

    slides = parse_md(md_text)

    if not slides:
        print("\n[エラー] スライドが1枚も解析できませんでした。")
        print("MDファイルのフォーマットを確認してください。")
        input("\nEnterキーで閉じる...")
        sys.exit(1)

    slides_html = "\n\n".join(render_slide(s) for s in slides)
    html = HTML_TEMPLATE.format(css=CSS, slides=slides_html)

    try:
        OUT.write_text(html, encoding="utf-8")
    except Exception as e:
        print(f"\n[エラー] index.html を書き出せませんでした: {e}")
        input("\nEnterキーで閉じる...")
        sys.exit(1)

    print(f"出力先:   {OUT}")
    print(f"\n[完了] {len(slides)} 枚のスライドを生成しました。")
    input("\nEnterキーで閉じる...")

if __name__ == "__main__":
    main()
