# 美文技 BIBUNG（ビブンギ）

**「美しき我が日本語を汚す悪文は、何文たりとも許さない。」**

論文、研究費申請書、学術解説の日本語を、科学的な意味を保ちながら磨くスキルです。論旨と段落構成から見直し、冗長な表現、説明に寄与しない比喩、誇張、不自然な語彙を整えます。

[Agent Skills共通仕様](https://agentskills.io/specification)に沿った `SKILL.md` 形式で、Codex、Claude Code、claude.ai、Claude APIで同じフォルダを使えます。スキルの利用自体にPythonや専用APIの設定は必要ありません。実機で確認した範囲は[検証状況](#検証状況)にあります。

## どのように直すか

科学的忠実性、論理の明晰さ、日本語の自然さ、簡潔さの順に優先します。修正範囲の指定がなければ、段落の順序や構成から直します。パラグラフ・ライティングを基本とし、原文の箇条書き・表は保ち、用途と書式が許す場合に使います。

「重要」「示唆」「関連」などの一律禁止はしません。専門用語、必要な留保、意味のある対比を残し、良い文章には変更を強制しません。AI検出器の点数を下げることや、AIが書いたかどうかの判定は目的に含めません。

### 改稿例

独自作成した架空例です。実在の研究結果ではありません。

**原文**

> 本研究においては、握力の測定を実施した。測定には握力計を使用した。測定は利き手で2回実施し、大きい方の値の採用を行った。

**改稿文**

> 利き手の握力を握力計で2回測定し、大きい方の値を採用した。

測定部位、器具、回数、採用規則を保ち、冗長な述語を整理しています。構成から直す例は[研究費申請書](examples/grant.md)、ほかに[論文](examples/paper.md)と[学術解説](examples/explanation.md)の例があります。これらの説明用の例と[評価実行の結果](evals/RESULTS.md)は区別しています。

### 段落から直す例

語句が正確でも読みにくい文章の多くは、動作を名詞にしたことが原因です。名詞にすると、日本語では誰が・何を・何に対してを書かなくても文が成立します。落ちた役割を読者が前の段落へ戻って補うことになり、読み返しても誤りは見つからないのに、読みにくさだけが残ります。次は独自作成した架空例です。

**原文**

> 退院支援の質は、退院前カンファレンスの構成で左右される。医師と看護師だけで固めると、計画は医学的な課題に偏りやすい。一方、A病院は、薬剤師と理学療法士を加えた運用を導入している。そこで作られる計画は、生活面の課題も含む。多職種化は再入院を減らす仕組みであり、当院の取り組みも後者に当たる。

**改稿文**

> 退院支援の質は、退院前カンファレンスの職種構成に左右される。医師と看護師だけでカンファレンスを構成すると、計画は医学的な課題に偏りやすい。これに対し、薬剤師と理学療法士を加えた職種構成では、生活面の課題も計画に入る。A病院と当院は、後者の職種構成を採っており、再入院を減らすことを期待している。

直したのは次の6点です。

- **落ちた目的語を戻した。** 「固めると」が何を固めるのかを書いていません。前の文にある「カンファレンス」で確定できます。
- **名詞が求める「何の」を補った。** 「構成」だけでは何の構成か決まりません。段落が職種の顔ぶれを述べているので「職種構成」としました。
- **比べるものをそろえた。** 「一方」の前は構成、後ろはA病院という組織でした。構成どうしの比較にしています。
- **「後者」の片側を本文に出した。** 二つのうち一方しか名前がないまま「後者」で受けていました。両方を示せば「後者」はそのまま使えます。
- **断定を期待の記述にした。** 再入院を減らすかどうかの根拠は本文にありません。原文にない証拠を作らず、期待を述べる形にしています。
- **つなぐ相手を変えた。** 原文は「再入院を減らす仕組みである」という効果の断定と、自院の位置付けを「であり」で結んでいました。主語の違う二つです。改稿文では主語をA病院と当院にそろえ、採っている職種構成とその期待を一文にしています。文を短く割るのではなく、つながる内容どうしを一文にします。

どれも原文にある語を使い直しただけで、新しい事実は足していません。落ちていた役割は、すべて同じ段落の中にありました。型の一覧と、それぞれの「直さない場合」は[日本語の編集基準](references/japanese-editing.md)にあります。

## 導入

このリポジトリをダウンロードまたはcloneし、**フォルダ名を `bibung` にして、フォルダ全体を配置**してください。配置に必要なのは `SKILL.md`、`LICENSE`、`references/`、`agents/` の四つで、`README.md`・`examples/`・`evals/` は不要です。`SKILL.md` だけでは補助資料が不足します。

| 利用環境 | 自分の全プロジェクトで使う配置先 | 一つのプロジェクトで使う配置先 |
|---|---|---|
| Codex | `~/.agents/skills/bibung/` | `.agents/skills/bibung/` |
| Claude Code | `~/.claude/skills/bibung/` | `.claude/skills/bibung/` |
| claude.ai／Claude Desktop | `bibung/` をルートにしたzipを、設定のSkillsから追加（利用者ごと） | 同左 |
| Claude API／Agent SDK | API：同じzipを `POST /v1/skills` に送る。SDK：`.claude/skills/bibung/` を置き、`settingSources` に `project` か `user` を含める | 同左 |

`~` はユーザーのホームフォルダです。配置後、各フォルダの直下に `SKILL.md` と `references/` があることを確認し、新しいセッションで呼び出してください。既存の `bibung` フォルダがある場合は、変更を確認してから更新します。各環境の導入は共有されず、claude.aiに追加したものはCodexやClaude Codeへ自動では入りません。

CodexとClaude Codeは互いのフォルダを読みません（Codexは `.agents/skills`、Claude CodeとAgent SDKは `.claude/skills` だけを探します）。両方で使う場合は、実体を一つにしてもう片方をリンクにするか、両方に同じ内容を置いて更新時に両方を入れ替えてください。リンク経由の読み込みは公式資料に明記がないため、初回に `$bibung` と `/bibung` の両方で呼び出せることを確認してください。

配置先は[Agent Skills仕様](https://agentskills.io/specification)、[OpenAI公式資料](https://learn.chatgpt.com/docs/build-skills)、[Claude Code公式資料](https://code.claude.com/docs/en/skills)、[Claude Platform公式資料](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)に基づきます。確認日：2026-09-13。

### ダウンロード後の配置例

以下は、ダウンロードしたリポジトリのフォルダ内で実行する初回導入用コマンドです。配置先に既存フォルダがある場合は停止します。Claude Codeでは配置先を `.claude/skills/bibung` に読み替えてください。

**PowerShell：Codex（Claude Codeは1行目の `.agents` を `.claude` に）**

```powershell
$bibungDest = Join-Path $HOME '.agents/skills/bibung'
$bibungSource = (Get-Location).Path
if (Test-Path -LiteralPath $bibungDest) { throw '既存のBIBUNGがあります。更新内容を確認してください。' }
if (-not (Test-Path -LiteralPath (Join-Path $bibungSource 'SKILL.md'))) { throw 'SKILL.mdのあるフォルダ内で実行してください。' }
New-Item -ItemType Directory -Path $bibungDest -Force | Out-Null
foreach ($entry in @('SKILL.md', 'LICENSE', 'references', 'agents')) {
    Copy-Item -LiteralPath (Join-Path $bibungSource $entry) -Destination $bibungDest -Recurse
}
```

**macOS／Linux：Codex（Claude Codeは1行目の `.agents` を `.claude` に）**

```sh
bibung_dest="$HOME/.agents/skills/bibung"
if [ -e "$bibung_dest" ]; then
  echo '既存のBIBUNGがあります。更新内容を確認してください。'
elif [ ! -f SKILL.md ]; then
  echo 'SKILL.mdのあるフォルダ内で実行してください。'
else
  mkdir -p "$bibung_dest"
  cp SKILL.md LICENSE "$bibung_dest/"
  cp -R references agents "$bibung_dest/"
fi
```

配置したコピーは `python evals/validate.py --installed --root <配置先>` で構成を確認できます（開発者向け。利用には不要）。

### claude.ai・Claude API用のzip

GitHubのDownload ZIPは `BIBUNG-main/` がルートになるため、`bibung/` をルートにしたzipを作ります。

```sh
mkdir -p dist/bibung && cp -R SKILL.md LICENSE references agents dist/bibung/ && (cd dist && zip -r bibung.zip bibung)
```

PowerShellでは `Compress-Archive -Path dist/bibung -DestinationPath dist/bibung.zip` を使います。claude.aiでは設定のSkillsからこのzipを追加します。Claude APIでは同じzipを `POST /v1/skills` に送ります。frontmatterはAgent Skills仕様の項目だけを使っているため、アップロード時の項目エラーは起きません。

## 使い方

Codexでは次のように呼び出します。

```text
$bibung この研究費申請書を、論旨と段落構成から見直してください。
科学的な意味を保ち、改稿文と主要な修正理由を示してください。

（ここに本文）
```

Claude Codeでは `/bibung` に続けて同じ依頼を書きます。続けて書いた文章はスキル本文の末尾に `ARGUMENTS:` として渡されます。claude.aiとAgent SDKでは、依頼文に「BIBUNGで」と書くか、日本語の科学文章の推敲を頼めば説明文に基づいて選ばれます。どの環境でも、特定の原稿を確実にBIBUNGで処理したい場合は名前を指定してください。

- 最小限の変更にしたいとき：「語句と文だけを直し、段落構成は維持してください」
- 本文だけ欲しいとき：「改稿文だけを返してください」
- 原文を編集しないとき：「本文は直さず、問題と修正案だけを示してください」
- 文体を合わせたいとき：著者の見本と、編集する本文を区別して渡してください。
- 字数制限があるとき：上限と数え方を書いてください。改稿前後の文字数を修正理由に示します。

応答は「改稿文」「修正理由」「要確認」の順です。要確認がなければ省きます。原文に矛盾や根拠不明の実質的な主張がある場合は、推測で書き換えず、該当箇所を引用して「要確認」に示します。確認事項がある改稿文は、内容の確認が済んだ完成稿ではありません。

## 入力形式と保持するもの

貼り付け文章、Markdown、Quarto本文を対象にします。貼り付けた本文は応答で返し、ファイルは作りません。ファイルを指定した場合は、同じフォルダに `原名.bibung.拡張子`（例：`intro.qmd` → `intro.bibung.qmd`）を作り、同名の出力があれば `原名.bibung.2.拡張子` から番号を付けます。長い原稿では修正理由と要確認を `原名.bibung.notes.md` にも書きます。原本の変更を明示的に依頼した場合は、その範囲で編集します。

数値、単位、対象集団、比較対象、評価時点、主体、否定、条件、不確実性、引用・図表参照の対応を保ちます。YAML、数式、コード、引用キー、リンク先、図表ID、相互参照、直接引用の内容は編集しません。英文抄録や文献情報など英語の部分も編集しません。

Wordの変更履歴付き編集、PDFの直接編集、英文校正、文献調査や研究結果の新規作成は対象外です。BIBUNGの推敲は原文の事実を独立に検証するものではありません。

## 検証状況

検証済みの項目と未検証の項目は、[評価結果](evals/RESULTS.md)の冒頭の一覧表に日付付きでまとめています。v0.1.0ではCodex CLIでの発見・呼び出し・補助資料の読み込みを、v0.2.0ではClaude Code CLIでの同じ項目と、独自作成した架空例による改稿の比較を確認しました。2026-09-14に公開し、GitHub ActionsのCIがWindows・macOS・Ubuntu × Python 3.10／3.13 の6環境で成功しました。

小規模な架空例による開発時の評価であり、全モデル・全原稿での品質や、スキルなしに対する優越性を保証しません。

## 開発・検証

スキルを使うだけなら以下の操作は不要です。配布物を変更したときに実行します。Python 3.10以上とPyYAMLが必要です。

```sh
python -m pip install -r evals/requirements.txt
python evals/validate.py
python -m unittest discover -s evals -p "test_*.py"
```

CIはfrontmatterの互換性（共通仕様の項目だけを使っているか）、内部リンク、必須ファイル、未完成の記述、評価例の構成などを確認します。科学的意味や文章品質は[評価手順](evals/README.md)に沿って別途確認します。Claude Codeがあれば `python evals/run_claude_code.py evals/runs/trial-01` で、スキルなし・スキルありの両条件を非対話で実行し、出力の形式を検証できます。

## 参照元・ライセンス

[humanizer_academic](https://github.com/matsuikentaro1/humanizer_academic)をはじめ、Humanizer系スキルと科学文章の編集原則を参考に、日本語用の指示と例文を独自作成しました。[参照コミットと採用箇所](references/sources.md)を記録しています。

BIBUNG本体は[MIT License](LICENSE)です。著者：Ryohei Kobayashi-Yamamoto。改善提案は[貢献方法](CONTRIBUTING.md)、版ごとの変更は[変更履歴](CHANGELOG.md)をご覧ください。

名称は「美文技」、表記は **BIBUNG（ビブンギ）**。`BIBUN（美文）＋ G（技）` に由来します。VIVANTにあやかった命名ですが、作品の画像・ロゴは使用していません。
