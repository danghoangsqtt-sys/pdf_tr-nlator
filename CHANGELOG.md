# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Fixed

- Preserve glyphs contained in PDF `LTFigure` / Form XObject regions instead of sending them to the prose translator when a layout detector misses the surrounding figure.
- Detect high-confidence image and large vector-drawing figure regions before conversion, then preserve their glyphs even when the layout model does not label the surrounding figure.
- Classify formula-font, Unicode-math and scan-image regions before conversion; ambiguous equation syntax now fails closed by preserving the source glyphs.
