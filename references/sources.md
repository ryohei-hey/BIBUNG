# 参照元と設計上の選択

参照日：2026-09-13。以下は設計時に本文を確認した固定コミットである。各リポジトリの更新は自動では取り込まない。

## 編集原則の参照

| 参照元・固定コミット | 参考にした箇所 | BIBUNGでの扱い |
|---|---|---|
| [matsuikentaro1/humanizer_academic](https://github.com/matsuikentaro1/humanizer_academic/blob/dcaef2198b236f7d9ac91a5596fedd83ed77e133/SKILL.md) | 用語の一貫性、接続表現、段落の結束性、言い換えの重複、空疎な評価文、改稿後の点検 | 学術文章の主要な参照先。日本語用の判断と架空例を独自作成 |
| [blader/humanizer](https://github.com/blader/humanizer/blob/9862685f575c65a8247f90369951df1b3416e3d6/SKILL.md) | 誇張、見せかけの対比、定型的な締め、書式の装飾、再点検 | 文脈を伴う編集パターンとして整理 |
| [tqkqt0/humanizer-jp](https://github.com/tqkqt0/humanizer-jp/blob/a8628b765b3de91cc7ea66ac78b5faab0777236f/SKILL.md) | 日本語への適応、情報を保った再構成、文体見本 | 日本語の科学文章に限定して独自に設計 |
| [matsutouya/humanizer-ja](https://github.com/matsutouya/humanizer-ja/blob/b4edf87d98ab81f8a2f5068e9641a50ea4a141d6/SKILL.md) | 主体・文型・用途による判断 | 学術文章へ感情や人格を加える処理は採用しない |
| [K-Dense-AI/scientific-agent-skills](https://github.com/K-Dense-AI/scientific-agent-skills/blob/0b2afe68a5f9379097ad815e028af664f1e222b7/skills/scientific-writing/references/writing_principles.md) | 科学的忠実性、不確実性、観察と解釈の区別 | 原文との意味の照合に絞る。文献調査・投稿管理は含めない |
| [ilyautov/humanizer-ru](https://github.com/ilyautov/humanizer-ru/blob/7fed91f99700a937b82e0c32094872ba8a5843da/eval/README.md) | 意味保持の評価、既に良い文章を使った過剰修正の評価 | 検出器の点数を使わず、原文と改稿文の対応を評価 |

## そのまま採用しなかった規則

humanizer_academicには、文長の変化をAI検出器の点数と結び付ける規則がある。BIBUNGは読者の理解と科学的忠実性を評価し、文長のばらつきや検出器の点数を目標にしない。英語の特定語、ダッシュ、接続語の出現回数に関する規則も日本語に機械的に移さない。

同スキルの一部の修正例では入力にない数値が補われている。BIBUNGの例は入力との情報対応を確認できる架空例とし、原文にない事実・数値・引用を補わない。「may」などの留保を足すだけで因果的主張を適切と判断しない。

参照先にある「AIらしさ」の説明は、編集上の経験則として検討する。日本語の科学文章について検証済みの普遍的法則として扱わず、特定の表現から執筆者がAIだと判定しない。

## 「AI臭い文章」の特徴づけの参照

参照日：2026-10-01。Kiminori Yokoi（@nasuvit_z）「[AI臭い文章とは何なのか](https://speakerdeck.com/nasuvitz/ai-kusai-bunshou-toha-nanina-no-ka)」（Speaker Deck）。

| 参考にした考え方 | BIBUNGでの扱い |
|---|---|
| 構造（不要な対比・否定・留保から入り、主文を直接書かない）、語彙（抽象語・比喩的な動詞）、表現（短文・対句・不自然な読点・名詞化）の三分類 | 既存の型で扱えない部分を、型3・13の拡張と、型5（対句・反復）・型16（強調のための読点）・型20（比喩的な動詞）の追加で補った |
| 話者の補足なしに、文章だけから「誰が・何を・どうした」を読み取れるか | 全ての型に共通する判断基準として、SKILL.mdの手順3と編集基準の冒頭に置いた |
| 「どういう意味か」を問い、答えをそのまま書く | 原文の他の記述から答えが決まる場合だけ書き直し、決まらない場合は要確認で著者に問う手順に当てはめた |
| 「AI臭い」という指摘自体も抽象的なので、具体的に指摘する | 修正理由と査読のみの指摘で評価語を使わず、読者が補わなければならない情報を書くようにした |
| 同じ癖の反復が、書き手の判断を見えなくする | 改稿で別の画一的な癖を持ち込んでいないかを、手順4の読み直しで確かめるようにした |

スライドの修正例には、原文にない対象・主体・条件（「運用者は」「原則として」など）を補って意味を確定したものがある。BIBUNGは原文にない事実を補わないため、この補い方は採用しない。スライド後半のAIが作るスライドのデザインの話は、文章の推敲が対象のBIBUNGの範囲外として扱わない。

## 著作物の扱い

BIBUNGの指示文・例文・評価文・コードは独自作成し、上記スキルとスライドの本文・例文・図を転載していない。考え方を参照した箇所はこのファイルで示す。humanizer_academicはKentaro Matsuiによるスキルで、blader/humanizerを基にしたMIT表示がある（[参照コミットのLICENSE](https://github.com/matsuikentaro1/humanizer_academic/blob/dcaef2198b236f7d9ac91a5596fedd83ed77e133/LICENSE)）。

将来、外部の文章・コードを転載または翻案する場合は、出典・該当ファイル・変更内容を記録し、元の著作権表示とライセンス条文を同梱する。参照先に含まれる論文由来の図表や例文を、スキルのライセンスだけで利用可能と判断しない。

## 導入仕様の参照

- [Agent Skills仕様](https://agentskills.io/specification)：`name` は64字以内・小文字英数字とハイフン・親フォルダ名と一致、`description` は1024字以内。任意項目は `license`・`compatibility`・`metadata`・`allowed-tools`。本文は500行以内、参照ファイルはSKILL.mdから一段のみ。
- [OpenAI公式：Build skills](https://learn.chatgpt.com/docs/build-skills)：`.agents/skills`（作業フォルダからリポジトリルートまで）と `~/.agents/skills`、`$bibung` による呼び出し、`agents/openai.yaml` は任意。スキル一覧は文脈の2%または8,000字までで、超えると説明が短縮される。
- [Claude Code公式：Extend Claude with skills](https://code.claude.com/docs/en/skills)：`~/.claude/skills` と `.claude/skills`、`/bibung` による呼び出し。本文に `$ARGUMENTS` がなければ、`/bibung` の後の文章は本文末尾に `ARGUMENTS:` として付加される。未知のfrontmatter項目は無視される。
- [Claude Platform公式：Agent Skills](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)・[claude.aiヘルプ](https://support.claude.com/en/articles/12512198-how-to-create-custom-skills)：claude.aiとSkills APIへのアップロードは、上記仕様の項目以外のfrontmatterをエラーにする。zipは `bibung/` をルートにする。環境間で自動同期はない。

導入仕様の記述は2026-09-13時点。BIBUNGは仕様共通の `name`・`description`・`license`・`metadata` だけを使い、`argument-hint`・`paths`・`disable-model-invocation` などClaude Code専用項目や `$ARGUMENTS` は、他環境でエラーや文字どおりの表示になるため使わない。特定環境のツールを必須にしない。
