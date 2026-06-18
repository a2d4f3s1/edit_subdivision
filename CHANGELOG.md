# Changelog

Edit Subdivision の変更履歴です。

書式は [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) に倣い、バージョン番号は [Semantic Versioning](https://semver.org/) に従います。

## [Unreleased]

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
