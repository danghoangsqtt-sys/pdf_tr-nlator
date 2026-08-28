# Academic ML PDF regression fixture

`academic-ml-source.pdf` is a two-page, self-authored fixture released under [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/). It does not reproduce text, figures, formulas or layout from third-party research papers.

It covers terminology-sensitive prose, two monospace formulas, and a boxed vector graphic with English labels. The vector graphic is intentionally direct page content: it provides a future regression target for region inventory beyond the `LTFigure` hardening already implemented.

Regenerate it with:

```powershell
& .venv\Scripts\python.exe tests\fixtures\academic-v1\build_fixture.py
```

Then verify the SHA-256 and page count against `manifest.json`, and render both pages before changing expected behaviour.
