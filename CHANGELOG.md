# Changelog

Edit Subdivision の変更履歴です。

書式は [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) に倣い、バージョン番号は [Semantic Versioning](https://semver.org/) に従います。

## [Unreleased]

## [0.2.0] - 2026-06-22

### Added

- 処理対象から特定のオブジェクトを除外する **Exclude フィルタ**。`*_face_*` のようなワイルドカード（glob）でオブジェクト名を指定し、いずれかのパターンに一致したオブジェクトを処理から除外（OR 合成）
- Exclude パターンはスクロール可能なリスト（UIList）＋右側ボタン列で管理し、`+` / `-` で追加・削除（1 行 = 1 条件）
- Exclude パターンのテキスト形式 **Export / Import**（右下の specials メニュー）。1 行 1 パターン・`#` コメント対応。Import は既存リストを置換
- Exclude セクション全体の ON/OFF チェックボックスと折り畳み表示
- 一致判定は大文字小文字を区別（全 OS 共通の `fnmatchcase`）

## [0.1.0] - 2026-06-18

Blender 4.2 Extension 形式での初回リリース。

### Added

- N-Panel（既定タブ `EditSubdiv`）から Subdivision Surface（SUBSURF）モディファイア設定を一括変更
- 対象切替: Selection（選択オブジェクト）/ Scene（シーン全体）
- 一括トグル: On Cage / Edit Mode / Realtime / Render（Modifier ヘッダと同じ並び・アイコン）
- Levels Viewport / Render（0〜6）、Optimal Display
- プロパティ変更時に対象の全 SUBSURF へ即適用するライブ更新
- 現在のパネル設定を対象へ一括再適用する **Apply to All** ボタン
- AddonPreferences の General に N-Panel カテゴリ設定（`Category (N-Panel)`、リセットボタン付き）

### Changed

- プロパティ登録を `register()` / `unregister()` に集約し、Scene プロパティを `Scene.edit_subdivision`（PropertyGroup）へ名前空間化
