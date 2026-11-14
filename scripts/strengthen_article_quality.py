#!/usr/bin/env python3
"""Safe site-wide editorial and technical enhancement for the Yorisuguri sites.

Does not change titles/content claims automatically, insert unverified products or
affiliates, invent reviews, pretend expert review, or remove existing copy.

Usage: python3 scripts/strengthen_article_quality.py --apply
       python3 scripts/strengthen_article_quality.py --audit
"""
from __future__ import annotations
import argparse
import html
import json
import posixpath
import re
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

ROOT = Path(__file__).resolve().parent.parent
DOMAIN = "https://yorisuguri-note.com/"
BEAUTY = "https://beauty.yorisuguri-note.com/"
OLD_GITHUB = "https://a66173800-stack.github.io/ai-tools-lab/"
GITHUB_ROOT = "https://a66173800-stack.github.io/ai-tools-lab"
REPORT = ROOT / "reports" / "article-quality-audit.json"
STANDALONE_BEAUTY = (ROOT / "CNAME").exists() and (ROOT / "CNAME").read_text(encoding="utf-8").strip() == "beauty.yorisuguri-note.com"

NON_ARTICLES = {
    "index.html", "about.html", "privacy.html", "contact.html",
    "disclosure.html", "categories.html", "choosing.html",
    "google2b664ac5bafbff25.html", "404.html",
    "coconala-home.html", "coconala.html", "rede-hairdry-guide.html",
}
INFORMATIONAL = {
    "yorisuguri/cooking/index.html", "yorisuguri/work/index.html",
    "yorisuguri/index.html", "yorisuguri/beauty/index.html",
    "yorisuguri/beauty/nail-salon/index.html", "index.html",
    "nail-salon/index.html",
}
# Each entry gives a distinct, relevant decision step; links use repository-root
# relative paths. The note is editorial guidance, not fabricated experience.
NEXT = {
    "yorisuguri/business-card-cost.html": (
       "最安値を比べる前に", "「100枚の本体価格」だけで比較しないこと。送料・税込総額・紙・加工・校正・納期まで同じ条件に揃えると、予想外の追加費用を避けられます。",
       [("印刷方法の違いを比較する", "yorisuguri/business-card-online-vs-shop.html"), ("初めての名刺注文の準備", "yorisuguri/business-card-first.html")]),
    "yorisuguri/business-card-design.html": (
       "注文前の最終チェック", "パソコン画面で読めても、紙にすると文字は小さく見えます。必ず実寸で印刷して、電話番号・QRコード・余白を確認しましょう。",
       [("QRコードの試し刷りを確認", "yorisuguri/business-card-qr-proof.html"), ("初回注文のチェック項目", "yorisuguri/business-card-first.html")]),
    "yorisuguri/business-card-first.html": (
       "初回注文はここまで確認", "肩書き・店舗名・連絡先を確定し、名刺を渡す相手に必要な情報だけ載せます。修正できない大量印刷より、まず少量の試し刷りを。",
       [("名刺のデザインで失敗しない", "yorisuguri/business-card-design.html"), ("100枚の総額比較の考え方", "yorisuguri/business-card-cost.html")]),
    "yorisuguri/business-card-online-vs-shop.html": (
       "迷ったときの判断", "自分で入稿データを用意でき、納期に余裕があるならネット印刷。紙や色を実物で確かめ、相談しながら決めたいなら店舗印刷も候補です。",
       [("100枚の費用を比べる", "yorisuguri/business-card-cost.html"), ("注文前の文字・QRチェック", "yorisuguri/business-card-qr-proof.html")]),
    "yorisuguri/business-card-opening.html": (
       "開業時に名刺は必須？", "名刺はすべてのお店に必要なわけではありません。予約時の連絡先やSNSへの導線が整っているかを先に考え、実際に配る場面があるなら作りましょう。",
       [("開業向け名刺の基本", "yorisuguri/business-card-first.html"), ("サロン開業の準備全体", "yorisuguri/work/nail-salon-opening.html")]),
    "yorisuguri/business-card-qr-proof.html": (
       "QRコードは公開後も点検", "印刷前だけでなく、リンク先を変更した日にもチェック。スマートフォンで読み取り、予約フォームが最後まで進められるかまで確認しましょう。",
       [("名刺デザインの確認項目", "yorisuguri/business-card-design.html"), ("サロン予約枠を整える", "yorisuguri/salon-reservation-buffer.html")]),
    "yorisuguri/compare-web-estimates.html": (
       "比較したいのは「総額」と「できること」", "同じページ数で見積もっても、文章作成・画像準備・公開作業・スマホ対応・運用費が含まれるかで差が出ます。比較表の条件欄を揃えましょう。",
       [("ホームページ制作のよくある失敗", "coconala-website-mistakes.html"), ("サロン向けWebサービスの選び方", "yorisuguri/goope-small-shop-website.html")]),
    "yorisuguri/goope-small-shop-website.html": (
       "申し込む前に確認", "料金だけでなく、ドメインの扱い・予約導線・自分で更新できる範囲・解約時のデータ移行方法を、公式の最新プランで確認してください。",
       [("制作見積もりを比較", "yorisuguri/compare-web-estimates.html"), ("Web制作の失敗を防ぐ", "coconala-website-mistakes.html")]),
    "yorisuguri/holiday-hours-check.html": (
       "変更したら、お客さま目線で確認", "営業時間を変更したら、Googleマップ・サイト・予約ページの表示をスマートフォンで順番に見て、予約可能な最終時刻まで確認しましょう。",
       [("予約の余裕時間を決める", "yorisuguri/salon-reservation-buffer.html"), ("お店のWebページを整える", "yorisuguri/goope-small-shop-website.html")]),
    "yorisuguri/logo-delivery-formats.html": (
       "見た目だけでなく使える形式を", "Web用のPNGと、印刷・看板用の拡大に耐えるベクターデータは用途が違います。発注先の入稿条件を確認してから納品ファイルを指定しましょう。",
       [("ロゴ制作の見積もり比較", "logo-quote-comparison.html"), ("ココナラでロゴを依頼する準備", "coconala-logo-guide.html")]),
    "yorisuguri/moneyforward-tax-return.html": (
       "ソフト選びの前に、必要な記録を決める", "売上・経費・領収書の記録を日々つける仕組みが先。プラン料金と必要機能は変わるため、申込前に最新の公式情報を必ず確認してください。",
       [("サロン開業の資金計画", "yorisuguri/work/nail-salon-opening.html"), ("利益を残す経営の考え方", "yorisuguri/work/nail-salon-growth.html")]),
    "yorisuguri/sakupeji-checklist.html": (
       "安さだけでなく運用まで比較", "契約前に、初期費用・年額・修正料金・ドメイン所有権・解約後のサイトの扱いを表にして、複数のサービスで同じ条件を確認しましょう。",
       [("小さなお店のWebサービス比較", "yorisuguri/goope-small-shop-website.html"), ("制作見積もりの揃え方", "yorisuguri/compare-web-estimates.html")]),
    "yorisuguri/salon-reservation-buffer.html": (
       "予約の枠を実際に計算", "施術60分に、片付け10分と会計・入替5分が必要なら、次の予約まで75分必要になります。数字は一例なので自店の実測に置き換えてください。",
       [("開業したばかりの集客", "yorisuguri/work/nail-salon-new-owner.html"), ("利益と予約枠を見直す", "yorisuguri/work/nail-salon-growth.html")]),
    "yorisuguri/work/nail-salon-opening.html": (
       "開業前に3つだけ書き出す", "①開業時に必要な初期費用、②毎月必ず出る固定費、③1施術あたりの粗利益。売上だけでなく、予約が少ない月でも継続できるか確認することが大切です。",
       [("予約枠の作り方", "yorisuguri/salon-reservation-buffer.html"), ("ロゴ・看板に使うデータの確認", "yorisuguri/logo-delivery-formats.html")]),
    "yorisuguri/work/nail-salon-new-owner.html": (
       "今週の改善は一つずつ", "予約が少ないときは投稿回数を増やす前に、料金・施術内容・所要時間・予約方法が初めての人にも分かるかをチェック。改善前後で問い合わせ件数を比較しましょう。",
       [("予約の余裕時間を設定する", "yorisuguri/salon-reservation-buffer.html"), ("お店のサイトの選び方", "yorisuguri/goope-small-shop-website.html")]),
    "yorisuguri/work/nail-salon-growth.html": (
       "客数より先に、残る利益を見る", "たとえば売上30万円でも、材料費・家賃・決済手数料などで残る金額は変わります。各メニューの施術時間と利益を同じ表にして、無理な値下げを避けましょう。",
       [("サロン予約枠の組み方", "yorisuguri/salon-reservation-buffer.html"), ("帳簿づけとソフトの選び方", "yorisuguri/moneyforward-tax-return.html")]),
    "yorisuguri/cooking/knife-guide.html": (
       "包丁選びの最後の確認", "手の大きさ、握りやすさ、重さ、まな板のサイズを一緒に考えます。高い包丁なら必ず使いやすいというわけではありません。",
       [("包丁を長く使う手入れ方法", "yorisuguri/cooking/knife-care.html"), ("まな板の素材と衛生管理", "yorisuguri/cooking/cutting-board-guide.html")]),
    "yorisuguri/cooking/frying-pan-guide.html": (
       "選んだ後の手入れまで考える", "使う火力、油の量、洗える道具、収納場所を比較。初心者は「今の料理で何が困るか」を決めてから候補を絞ると失敗しにくくなります。",
       [("玉ねぎを炒める科学", "yorisuguri/cooking/onion-sweetness-science.html"), ("鍋の素材も比較する", "yorisuguri/cooking/pot-guide.html")]),
    "yorisuguri/cooking/onion-sweetness-science.html": (
       "炒め方を変えて違いを確かめる", "同じ量・同じ切り方の玉ねぎを、透明になるまでと薄いきつね色になるまで炒めて比べると、甘みと香りの違いが分かりやすくなります。",
       [("フライパンを選ぶポイント", "yorisuguri/cooking/frying-pan-guide.html"), ("食材の目利きと保存", "yorisuguri/cooking/vegetable-guide.html")]),
    "yorisuguri/cooking/mushrooms-wash-guide.html": (
       "「洗う？」は種類と商品表示で判断", "同じ「きのこ」でも、なめこ・しいたけ・ぶなしめじでは扱い方が異なります。洗う必要がある場合は水気を取り、調理中に味が薄くならないようにします。",
       [("食材の選び方と保存", "yorisuguri/cooking/vegetable-guide.html"), ("食品衛生の基本", "yorisuguri/cooking/food-safety-guide.html")]),
    "yorisuguri/cooking/egg-expiration-safety.html": (
       "期限だけで安全は決められない", "保存温度、殻のひび、調理方法が大切。期限を過ぎた卵を「〇日までは必ず安全」と判断しないでください。",
       [("家庭の食中毒対策", "yorisuguri/cooking/food-safety-guide.html"), ("鶏肉を洗わない理由", "yorisuguri/cooking/dont-wash-raw-chicken.html")]),
    "yorisuguri/cooking/kitchen-sponge-replacement.html": (
       "スポンジ以外の衛生も確認", "スポンジを交換するだけでなく、ふきん・まな板・シンクに汚れや水分を残さないことも重要です。",
       [("生肉トレーを片付けるとき", "yorisuguri/cooking/meat-tray-disposal-safety.html"), ("まな板の衛生管理", "yorisuguri/cooking/cutting-board-guide.html")]),
    "yorisuguri/cooking/dont-wash-raw-chicken.html": (
       "鶏肉は洗わず、道具を分ける", "調理の順番を工夫して、生肉の汁を加熱しない野菜へ移さない。中心まで十分に加熱してから食べましょう。",
       [("生肉トレーの後片付け", "yorisuguri/cooking/meat-tray-disposal-safety.html"), ("家庭の食品衛生", "yorisuguri/cooking/food-safety-guide.html")]),
    "yorisuguri/cooking/meat-tray-disposal-safety.html": (
       "片付け方は自治体の回収ルールと両立", "生肉を洗わないことと、回収用トレーの洗浄は別。飛び散りを防ぎながら地域の分別ルールに従いましょう。",
       [("鶏肉を洗わない理由", "yorisuguri/cooking/dont-wash-raw-chicken.html"), ("台所のスポンジと衛生", "yorisuguri/cooking/kitchen-sponge-replacement.html")]),
    "yorisuguri/cooking/cutting-board-guide.html": (
       "まな板は素材だけで決めない", "大事なのは生肉と加熱しない食材の使い分け、洗いやすさ、十分な乾燥。包丁との相性も確認しましょう。",
       [("包丁の選び方", "yorisuguri/cooking/knife-guide.html"), ("衛生管理の基本", "yorisuguri/cooking/food-safety-guide.html")]),
    "yorisuguri/cooking/pot-guide.html": (
       "毎日のメニューで決める", "味噌汁中心か煮込み中心かで、必要な容量や深さは違います。家族人数だけでなくコンロとの相性や片付けやすさも見て選びましょう。",
       [("フライパンとの使い分け", "yorisuguri/cooking/frying-pan-guide.html"), ("家庭の衛生管理", "yorisuguri/cooking/food-safety-guide.html")]),
    "yorisuguri/cooking/food-safety-guide.html": (
       "今日から始める3つの習慣", "生肉は最後に扱う・手と器具を洗う・中心まで加熱する。調理前から食後の片付けまで、一連の作業で考えると安全管理が続けやすくなります。",
       [("鶏肉を洗わない理由", "yorisuguri/cooking/dont-wash-raw-chicken.html"), ("スポンジの洗浄と交換", "yorisuguri/cooking/kitchen-sponge-replacement.html")]),
    "yorisuguri/cooking/vegetable-guide.html": (
       "保存は食材の種類別に", "同じ野菜でも低温が苦手なものや乾燥に弱いものがあります。買ってきたらひとまとめにせず、食材ごとに保存方法を確認しましょう。",
       [("きのこの下処理", "yorisuguri/cooking/mushrooms-wash-guide.html"), ("栄養と調理の科学", "yorisuguri/cooking/onion-sweetness-science.html")]),
    "yorisuguri/cooking/knife-care.html": (
       "包丁を長く使うなら", "使ったら汚れを落として水分を拭き取り、材質に合った方法で保管。切れ味が落ちたら必要に応じて研ぎ方も確認します。",
       [("包丁選びを見直す", "yorisuguri/cooking/knife-guide.html"), ("まな板の素材と衛生", "yorisuguri/cooking/cutting-board-guide.html")]),
}
# Additional contextual links for the Coconala article group, without fabricating a
# user experience or altering existing sponsored destinations.
ROOT_NEXT = {
    "coconala-logo-guide.html": ("ロゴを発注する前に", "用途・修正回数・商用利用の条件を揃えて比較。看板とSNSの両方で使うなら納品形式も先に確認しましょう。", [("ロゴの見積もり比較表","logo-quote-comparison.html"),("看板にも使える納品形式","yorisuguri/logo-delivery-formats.html")]),
    "coconala-web-guide.html": ("制作後の管理まで確認", "完成してから困りやすいのは、ドメイン・サーバー・更新作業の担当です。公開と運用の範囲を契約前に整理しておきましょう。", [("制作依頼の失敗例を見る","coconala-website-mistakes.html"),("制作見積もりの比較方法","yorisuguri/compare-web-estimates.html")]),
    "coconala-website-mistakes.html": ("公開前に本当に必要なチェック", "制作費だけでなく運用費・修正範囲・管理権限が残るかを確認。後から変更できない契約条件は、文章で記録することが大切です。", [("同じ条件で見積もりを取る","yorisuguri/compare-web-estimates.html"),("店舗サイトの選び方","yorisuguri/goope-small-shop-website.html")]),
    "coconala-brief-writing.html": ("相談文を書けたら", "1件だけに依頼する前に、同じ条件で複数の候補の作例・納期・総額を比較しておくと、予算超過を避けやすくなります。", [("見積もりを比較する","coconala-compare-quotes.html"),("初回依頼の流れ","coconala-first-order.html")]),
    "coconala-commercial-rights.html": ("商用利用が必要なら", "看板・SNS・印刷物・グッズ販売など、想定している使い方を具体的に伝えて、利用許諾の範囲を確認してください。", [("ロゴ依頼の準備","coconala-logo-guide.html"),("印刷に必要なデータ形式","yorisuguri/logo-delivery-formats.html")]),
    "coconala-cost-check.html": ("実際に比較するときは", "基本料金、提案数、修正回数、納品形式と追加費用を同じ条件に揃えます。表示された最低価格だけでは総額を判断できません。", [("見積もり比較表の作り方","coconala-compare-quotes.html"),("依頼文を準備する","coconala-brief-writing.html")]),
}
NEXT.update(ROOT_NEXT)

def clean_text(raw: str) -> str:
    x = re.sub(r"<script\b[^>]*>.*?</script>", " ", raw, flags=re.I|re.S)
    x = re.sub(r"<style\b[^>]*>.*?</style>", " ", x, flags=re.I|re.S)
    x = re.sub(r"<[^>]+>", " ", x)
    return html.unescape(re.sub(r"\s+", " ", x)).strip()

def article(path: str) -> bool:
    if STANDALONE_BEAUTY:
        return path.startswith("articles/") and path.endswith(".html") or path == "nail-salon-style.html"
    if path in NON_ARTICLES or path in INFORMATIONAL:
        return False
    if not path.endswith(".html") or path.startswith("scripts/"):
        return False
    if path.startswith("yorisuguri/"):
        return True
    return "/" not in path

def canonical_url(p: str) -> str:
    if STANDALONE_BEAUTY:
        return BEAUTY + p
    if p.startswith("yorisuguri/beauty/"):
        rest = p[len("yorisuguri/beauty/"):]
        return BEAUTY + (rest[:-len("index.html")] if rest.endswith("index.html") else rest)
    if p.endswith("/index.html"):
        return DOMAIN + p[:-len("index.html")]
    return DOMAIN + p

def update_href(old: str, current_path: str) -> str:
    u = old.replace(OLD_GITHUB, DOMAIN).replace(GITHUB_ROOT, DOMAIN.rstrip("/"))
    u = u.replace("https://yorisuguri-beauty.yuushi20040721.chatgpt.site/", BEAUTY)
    if u.startswith(DOMAIN + "yorisuguri/beauty/"):
        return BEAUTY + u[len(DOMAIN + "yorisuguri/beauty/"):]
    if u.startswith("#") or u.startswith("//") or u.startswith("mailto:") or u.startswith("tel:"):
        return u
    if urlsplit(u).scheme:
        return u
    if STANDALONE_BEAUTY:  # all local links already live under beauty.example
        return u
    stem, sep, tail = u.partition("#")
    stem, qsep, query = stem.partition("?")
    if not stem: return u
    target = posixpath.normpath(posixpath.join(posixpath.dirname(current_path),stem))
    if target == "yorisuguri/beauty":
        return BEAUTY + (qsep + query if qsep else "") + (sep + tail if sep else "")
    if target.startswith("yorisuguri/beauty/"):
        dest = target[len("yorisuguri/beauty/"):]
        if stem.endswith("/") and not dest.endswith("/"): dest += "/"
        return BEAUTY + dest + (qsep + query if qsep else "") + (sep + tail if sep else "")
    return u

def head_meta(s: str, url: str) -> str:
    head_match = re.search(r"</head>",s,re.I)
    if not head_match: return s
    head=s[:head_match.start()]
    title=clean_text(re.search(r"<title[^>]*>(.*?)</title>",head,re.I|re.S).group(1)) if re.search(r"<title[^>]*>(.*?)</title>",head,re.I|re.S) else ""
    descm=re.search(r'<meta\s+name=["\']description["\']\s+content=["\']([^"\']*)["\']',head,re.I)
    description=html.unescape(descm.group(1)) if descm else ""
    if not description:
        first=re.search(r"<p\b[^>]*>(.*?)</p>",s[head_match.end():],re.I|re.S)
        description=(clean_text(first.group(1))[:125] if first else title[:125])
        if description:
            head += '<meta name="description" content="'+html.escape(description,quote=True)+'">'
    can=re.search(r'<link\b[^>]*rel=["\']canonical["\'][^>]*>',head,re.I)
    if can:
        head=head[:can.start()]+re.sub(r'href=["\'][^"\']*["\']', 'href="'+html.escape(url,quote=True)+'"',can.group(0),count=1)+head[can.end():]
    else:
        head+='<link rel="canonical" href="'+html.escape(url,quote=True)+'">'
    ogdata=[
        ("og:type","article"),("og:title",title),("og:description",description),
        ("og:url",url),("og:site_name","ヨリスグリノート")
    ]
    for name,value in ogdata:
        if value and not re.search(r'<meta\b[^>]*property=["\']'+re.escape(name)+r'["\']',head,re.I):
            head+='<meta property="'+name+'" content="'+html.escape(value,quote=True)+'">'
    if not re.search(r'<meta\b[^>]*name=["\']twitter:card["\']',head,re.I):
        head+='<meta name="twitter:card" content="summary_large_image">'
    # BreadcrumbList states only actual navigation hierarchy. Avoid fake author/review data.
    if '"BreadcrumbList"' not in head:
        if STANDALONE_BEAUTY or url.startswith(BEAUTY):
            trail=[("美容",BEAUTY)]
        elif current := ("yorisuguri/cooking/" in url):
            trail=[("ヨリスグリノート",DOMAIN+"yorisuguri/"),("料理",DOMAIN+"yorisuguri/cooking/")]
        elif "yorisuguri/work/" in url or "/yorisuguri/business" in url or "/yorisuguri/salon-" in url:
            trail=[("ヨリスグリノート",DOMAIN+"yorisuguri/"),("仕事",DOMAIN+"yorisuguri/work/")]
        else:
            trail=[("ヨリスグリノート",DOMAIN+"yorisuguri/")]
        crumb={"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[{"@type":"ListItem","position":i+1,"name":n,"item":u} for i,(n,u) in enumerate(trail+[(title or "記事",url)])]}
        head+='<script type="application/ld+json" data-yorisuguri-quality="breadcrumb">'+json.dumps(crumb,ensure_ascii=False,separators=(",",":"))+'</script>'
    return head+s[head_match.start():]

def practical_step(s: str, p: str, existing: set[str]) -> str:
    if STANDALONE_BEAUTY or p not in NEXT: return s
    if 'data-yorisuguri-quality="next"' in s: return s
    title,explanation,links=NEXT[p]
    li=[]
    for label,target in links:
        if target not in existing: continue
        relative=posixpath.relpath(target,posixpath.dirname(p) or ".")
        # Prefer links not already on the page when possible.
        li.append('<a href="'+html.escape(relative,quote=True)+'">'+html.escape(label)+' ↗</a>')
    if not li: return s
    block=('<section data-yorisuguri-quality="next" aria-label="読んだ後にできること" '
           'style="margin:36px auto;padding:23px 25px;max-width:830px;'
           'background:#f8f6ed;border:1px solid #e6e2d4;border-radius:14px;'
           'font-family:inherit;color:#3d4138;line-height:1.85">'
           '<div style="font-size:11px;font-weight:700;letter-spacing:.12em;color:#718262">NEXT STEP / 次の一歩</div>'
           '<h2 style="font-size:21px;margin:8px 0 8px;line-height:1.5;border:0;padding:0">'+html.escape(title)+'</h2>'
           '<p style="font-size:14px;margin:5px 0 14px">'+html.escape(explanation)+'</p>'
           '<div style="display:flex;gap:8px 18px;flex-wrap:wrap;font-size:13px;font-weight:700">'
           + "　".join(li) + '</div></section>')
    # Only add to actual article content at end, before footer / after main.
    m=list(re.finditer(r"</main>",s,re.I))
    if m:
        k=m[-1].start()
        return s[:k]+block+s[k:]
    m=re.search(r"<footer\b",s,re.I)
    if m: return s[:m.start()]+block+s[m.start():]
    return s

def report_entry(path: str, content: str, files: set[str]) -> dict:
    title_m=re.search(r"<title[^>]*>(.*?)</title>",content,re.I|re.S)
    title=clean_text(title_m.group(1)) if title_m else ""
    h1=re.findall(r"<h1\b",content,re.I)
    desc=re.search(r'<meta\s+name=["\']description["\']',content,re.I)
    images=re.findall(r"<img\b[^>]*>",content,re.I|re.S)
    missing_alt=[x for x in images if not re.search(r"\balt\s*=",x,re.I)]
    affiliate=bool(re.search(r"https?://px\.a8\.net|a8mat=",content,re.I))
    disclosed=bool(re.search(r"PR[：·]|アフィリエイト広告|広告[｜：]",clean_text(content[:max(2400,len(content)//2)]),re.I))
    urls=[]
    for u in re.findall(r'href=["\']([^"\']+)["\']',content,re.I):
        if u.startswith("#") or urlsplit(u).scheme or u.startswith("//") or u.startswith("mailto:"): continue
        clean=u.split("?")[0].split("#")[0]
        if not clean: continue
        if clean.startswith("/"):
            resolved=posixpath.normpath(clean.lstrip("/") + ("index.html" if clean.endswith("/") else ""))
        elif clean.endswith("/"):
            resolved=posixpath.normpath(posixpath.join(posixpath.dirname(path),clean,"index.html"))
        else:
            resolved=posixpath.normpath(posixpath.join(posixpath.dirname(path),clean))
        if resolved not in files:urls.append(u)
    return {"path":path,"title":title,"hasDescription":bool(desc),"h1Count":len(h1),
            "images":len(images),"imagesMissingAlt":len(missing_alt),
            "affiliate":affiliate,"earlyPrDisclosure":disclosed,
            "possibleBrokenRelativeLinks":urls,"contentLength":len(clean_text(content)),
            "canonical":(re.search(r'<link\b[^>]*rel=["\']canonical["\'][^>]*href=["\']([^"\']+)',content,re.I) or [None,None])[1]}

def main()->None:
    cli=argparse.ArgumentParser()
    cli.add_argument("--apply",action="store_true")
    cli.add_argument("--audit",action="store_true")
    args=cli.parse_args()
    paths=sorted(p for p in ROOT.rglob("*.html") if ".git" not in p.parts and "dist" not in p.parts)
    names={p.relative_to(ROOT).as_posix() for p in ROOT.rglob("*") if p.is_file() and ".git" not in p.parts and "dist" not in p.parts}
    rows=[]
    revised=[]
    for f in paths:
        name=f.relative_to(ROOT).as_posix()
        old=f.read_text(encoding="utf-8")
        s=old
        if article(name):
            # Update outdated GitHub Pages and legacy beauty URLs. Preserve text and
            # external affiliate URLs without changing their tracking parameters.
            s=s.replace(OLD_GITHUB,DOMAIN)
            s=s.replace("https://yorisuguri-beauty.yuushi20040721.chatgpt.site/",BEAUTY)
            if name.startswith("yorisuguri/beauty/"):
                s=s.replace(DOMAIN+"yorisuguri/beauty/",BEAUTY)
            def href_change(m:re.Match[str])->str:
                return m.group(1)+update_href(m.group(2),name)+m.group(3)
            s=re.sub(r'(href=["\'])([^"\']+)(["\'])',href_change,s)
            s=head_meta(s,canonical_url(name))
            if re.search(r"https?://px\.a8\.net|a8mat=",s,re.I):
                # Label sponsored links, leaving original tracking URLs untouched.
                def sponsored(m:re.Match[str])->str:
                    tag=m.group(0)
                    if not re.search(r"https?://px\.a8\.net|a8mat=",tag,re.I):return tag
                    match=re.search(r'\brel=["\']([^"\']*)["\']',tag,re.I)
                    if match:
                        values=match.group(1).split()
                        for val in ("sponsored","nofollow"):
                            if val not in values:values.append(val)
                        return tag[:match.start()]+('rel="'+ " ".join(values) +'"')+tag[match.end():]
                    return tag[:-1]+' rel="sponsored nofollow">'
                s=re.sub(r'<a\b[^>]*>',sponsored,s,flags=re.I)
                excerpt=clean_text(s[s.find("<body"):][:2400]) if "<body" in s else ""
                if not re.search(r'PR[：·]|アフィリエイト広告|広告[｜：]',excerpt) and 'data-yorisuguri-quality="ad-disclosure"' not in s:
                    disclosure=('<p data-yorisuguri-quality="ad-disclosure" style="max-width:830px;margin:16px auto 8px;padding:0 18px;color:#726e68;font-size:12px">広告：この記事にはアフィリエイト広告が含まれます。掲載内容は読者の判断に役立つ情報を優先しています。</p>')
                    s=re.sub(r'(<main\b[^>]*>)',lambda m:m.group(1)+disclosure,s,count=1,flags=re.I)
            s=practical_step(s,name,names)
            if STANDALONE_BEAUTY:
                # Only after an actual content edit, update article dateModified (datePublished unchanged)
                pass
        else:
            # Update genuine cross-site navigation on hub pages; do not change old root
            # noindex redirect or legal/utility content.
            if name in INFORMATIONAL:
                if name == "yorisuguri/beauty/index.html":
                    s = re.sub(r'(<link\b[^>]*rel=["\']canonical["\'][^>]*href=["\'])[^"\']+',r'\g<1>'+BEAUTY,s,flags=re.I)
                    s = s.replace(DOMAIN+"yorisuguri/beauty/",BEAUTY)
                def href_change(m:re.Match[str])->str:
                    return m.group(1)+update_href(m.group(2),name)+m.group(3)
                s=re.sub(r'(href=["\'])([^"\']+)(["\'])',href_change,s)
                s=s.replace(OLD_GITHUB,DOMAIN)
        if args.apply and old!=s:
            f.write_text(s,encoding="utf-8")
            revised.append(name)
        rows.append(report_entry(name,s,names))
    REPORT.parent.mkdir(parents=True,exist_ok=True)
    report={"site":("beauty" if STANDALONE_BEAUTY else "main"),"totalHtml":len(rows),
            "articleCount":sum(article(x["path"]) for x in rows),
            "changed":revised,"missingDescription":[x["path"] for x in rows if not x["hasDescription"]],
            "affiliatePagesWithoutEarlyDisclosure":[x["path"] for x in rows if x["affiliate"] and not x["earlyPrDisclosure"]],
            "missingAlt":[x["path"] for x in rows if x["imagesMissingAlt"]],
            "possibleBrokenRelativeLinks":[{"path":x["path"],"links":x["possibleBrokenRelativeLinks"]} for x in rows if x["possibleBrokenRelativeLinks"]],
            "pages":rows}
    REPORT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("Site:", report["site"])
    print("HTML pages:",len(rows),"articles:",report["articleCount"],"changed:",len(revised))
    print("Missing descriptions:",len(report["missingDescription"]),
          "affiliate disclosure concerns:",len(report["affiliatePagesWithoutEarlyDisclosure"]),
          "missing image alt:",len(report["missingAlt"]),
          "possible broken relative paths:",len(report["possibleBrokenRelativeLinks"]))
    print("Report:",REPORT.relative_to(ROOT))
    for f in revised:print("UPDATED",f)

if __name__=="__main__":
    main()
