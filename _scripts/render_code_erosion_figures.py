"""Render the new post's figures from its Markdown tables (standard library only)."""

from html import escape
from pathlib import Path
import argparse
import re


ROOT = Path(__file__).resolve().parents[1]
POST = ROOT / "_posts/2026-11-15-coding-agent-code-erosion-counterfactuals-and-governance.md"


def cells(line):
    return [re.sub(r"<[^>]+>|[*`]", "", cell).strip() for cell in line.strip().strip("|").split("|")]


def values(rows, label):
    row = next(row for row in rows if label in row[0])
    return [float(re.search(r"\d+(?:\.\d+)?", cell)[0]) for cell in row[1:]]


def panel(title, labels, numbers, maximum, offset, currency=False):
    out = [f'<text x="0" y="{offset + 20}" font-weight="600">{escape(title)}</text>']
    for tick in (0, maximum / 2, maximum):
        x = 140 + 410 * tick / maximum
        out.append(f'<path d="M{x:g},{offset + 40}V{offset + 60 + 42 * len(labels)}" stroke="var(--ar-rule, #d9d9d9)"/>')
        out.append(f'<text x="{x:g}" y="{offset + 36}" text-anchor="middle" font-size="12">{tick:g}</text>')
    colors = {"A": "#df693c", "B′": "#327bce", "B": "#258e70", "G": "#327bce",
              "C": "#258e70", "D": "#9165bf", "D+": "#327bce"}
    for i, (label, value) in enumerate(zip(labels, numbers, strict=True)):
        y = offset + 64 + i * 42
        width = 410 * value / maximum
        estimate = currency and label.startswith("D+")
        border = ' fill-opacity="0.45" stroke="currentColor" stroke-dasharray="4 3"' if estimate else ""
        text = f"{'≈' if estimate else ''}{'$' if currency else ''}{value:.2f}" if currency else f"{value:.1f}"
        out.extend([
            f'<text x="128" y="{y + 5}" text-anchor="end">{escape(label)}</text>',
            f'<rect x="140" y="{y - 11}" width="{width:.2f}" height="22" fill="{colors[label.split(" · ")[0]]}"{border}/>',
            f'<text x="{148 + width:.2f}" y="{y + 5}">{text}</text>',
        ])
    return "\n".join(out), 90 + len(labels) * 42


def splicing_diagram(table, english):
    """Show snapshot construction and independent continuation, using C3 table data."""
    anchor = "code-erosion-splice-design" + ("-en" if english else "")
    title = ("Three-way snapshot splicing: three starts, one continuation protocol" if english
             else "三向快照嫁接：三种起点，共用续跑协议")
    peaks = values(table, "C3 Start: Peak Function Complexity" if english else "第 3 关起点：最高函数复杂度")
    tests = [re.search(r"(\d+(?:\.\d+)?)\s*/\s*(\d+)", cell).groups() for cell in table[0][1:]]
    names = (["A · Default start", "B′ · Patched control", "B · Reference start"] if english
             else ["A · 自然起点", "B′ · 原位修补", "B · 参考答案"])
    structures = (["Single file · high complexity", "Original single-file layout", "Modular reference solution"] if english
                  else ["单文件 · 高复杂度", "保留原有单文件与函数结构", "模块化参考实现"])
    colors = ("#df693c", "#327bce", "#258e70")
    if len(peaks) != 3 or len(tests) != 3:
        raise ValueError("Splicing diagram requires three C3 starting conditions")
    note = ("forge · Claude Opus 5.5 · 3 runs per group; C3 values are means. The dashed arrow shows how B′ is patched from A; solid arrows show independent continuation. B′ matches B's tested correctness while retaining A's structure. Reference-solution semantics remain a potential confounder."
            if english else "forge · Claude Opus 5.5 · 每组 3 次运行，C3 数值为均值。虚线表示由 A 原位修补得到 B′，实线表示各组独立续跑。B′ 将测试通过数对齐 B，同时保留 A 的结构；参考答案的规格理解差异仍是潜在混淆变量。")
    description = "; ".join(f"{name}: {structure}, {passed}/{total}, {peak:.1f}"
                            for name, structure, (passed, total), peak in zip(names, structures, tests, peaks, strict=True))
    parts = [f'''<defs>
  <marker id="{anchor}-arrow" viewBox="0 0 8 8" refX="7" refY="4" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
    <path d="M1,1 L7,4 L1,7" fill="none" stroke="context-stroke" stroke-width="1.3"/>
  </marker>
</defs>''']

    def text(x, y, label, size=14, weight=400, align="start"):
        parts.append(f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" text-anchor="{align}">{escape(label)}</text>')

    def arrow(path, color, dashed=False):
        dash = ' stroke-dasharray="5 4"' if dashed else ""
        parts.append(f'<path d="{path}" fill="none" stroke="{color}" stroke-width="1.6"{dash} marker-end="url(#{anchor}-arrow)"/>')

    text(0, 22, "C3 · Starting workspace snapshots" if english else "第 3 关结束 · 三种工作区快照", weight=600)
    text(210, 53, "Patch tests; preserve structure" if english else "仅修测试，保留结构", size=12, align="middle")
    arrow("M100,89 V66 H320 V89", colors[1], dashed=True)
    for i, (name, structure, (passed, total), peak, color) in enumerate(zip(names, structures, tests, peaks, colors, strict=True)):
        x = i * 220
        parts.append(f'<rect x="{x + 1}" y="92" width="198" height="152" rx="2" fill="none" stroke="var(--ar-rule, #d9d9d9)"/>')
        parts.append(f'<path d="M{x + 2},93 H{x + 198}" stroke="{color}" stroke-width="3"/>')
        text(x + 14, 121, name, weight=600)
        text(x + 14, 151, structure, size=13)
        text(x + 14, 185, ("Tests passed: " if english else "测试通过：") + passed + " / " + total, size=13)
        text(x + 14, 216, ("Peak complexity: " if english else "最高复杂度：") + f"{peak:.1f}", size=13)
        arrow(f"M{x + 100},245 V287", color)

    parts.append('<rect x="1" y="291" width="638" height="100" rx="2" fill="none" stroke="var(--ar-rule, #d9d9d9)"/>')
    text(320, 319, "C4 → C8 · Identical continuation protocol" if english else "第 4 → 8 关 · 相同的续跑协议", weight=600, align="middle")
    text(320, 346, "Claude Opus 5.5 · just-solve", align="middle")
    text(320, 372, "Separate workspaces · 3 runs per group" if english else "各组工作区独立续跑 · 每组 3 次", size=13, align="middle")
    for i, color in enumerate(colors):
        arrow(f"M{100 + 220 * i},392 V429", color)
    text(320, 456, "C8 · Evaluate each group separately" if english else "第 8 关 · 分别评估各组结果", weight=600, align="middle")
    text(320, 482, "Peak complexity · Large functions · New test failures" if english else "最高复杂度 · 高复杂度函数数 · 后续关卡失败测试数", size=13, align="middle")
    return f'''<!-- Generated from the C3 starting conditions in the post's splicing table. -->
<figure class="ar-chart" aria-labelledby="{anchor}-caption">
  <figcaption id="{anchor}-caption">{escape(title)}</figcaption>
  <div style="overflow-x: auto; margin-top: 16px;" tabindex="0" role="region" aria-label="{escape(title)}{'; scroll horizontally on narrow screens' if english else '；窄屏可横向滚动'}">
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 498" role="img" aria-labelledby="{anchor}-title {anchor}-desc" style="min-width: 600px; width: 100%; height: auto;">
      <title id="{anchor}-title">{escape(title)}</title>
      <desc id="{anchor}-desc">{escape(description + '. ' + note)}</desc>
      <g fill="var(--ar-ink-3, #555)" font-size="14" font-family="sans-serif">
        {chr(10).join(parts)}
      </g>
    </svg>
  </div>
  <p class="ar-chart-note">{escape(note)}</p>
</figure>
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lang", choices=("zh", "en"), default="zh")
    english = parser.parse_args().lang == "en"
    post = POST.with_name(POST.stem + "-en.md") if english else POST
    source = post.read_text()
    figures = {
        "splice": {
            "title": "三向嫁接：终局复杂度与新增失败分别比较",
            "labels": ["A · 默认起点", "B′ · 修满测试", "B · 参考答案"],
            "metrics": [("第 8 关最高函数复杂度", "第 8 关：最高函数复杂度", 50, False),
                        ("第 8 关中来自第 5–8 关的失败测试数（个）", "来自第 5–8 关的失败测试数", 25, False)],
            "note": "forge · Claude Opus 5.5 · 各组 3 次运行均值。两幅图使用独立量纲，条形均从零起；完整数据与起点条件见上表。",
        },
        "forge": {
            "title": "forge：会话内门禁的复杂度与费用",
            "labels": ["A · 默认", "G · AST 门禁", "C · anti_slop"],
            "metrics": [("第 8 关最高函数复杂度", "最高函数复杂度", 50, False),
                        ("完整 8 关总费用（USD）", "费用", 5, True)],
            "note": "Claude Opus 5.5 · 各组 3 次运行均值。通过率分别为 91.1%、91.5%、92.1%；复杂度与费用各自使用独立刻度。",
        },
        "circuit": {
            "title": "circuit_eval：重构契约与全程约束的对照",
            "labels": ["A · 默认", "D · 单次重构", "D+ · 加契约", "C · anti_slop"],
            "metrics": [("第 8 关最高函数复杂度", "最高函数复杂度", 80, False),
                        ("完整 8 关总费用（USD）", "费用", 25, True)],
            "note": "Claude Opus 5.5 · 各组 3 次运行均值。D+ 费用约 $16.40，含超时关估算，以浅色虚线标记；通过率见上表。",
        },
    }
    if english:
        figures = {
            "splice": {
                "title": "Three-way splicing: final complexity and new test failures",
                "labels": ["A · Default", "B′ · Patched", "B · Reference"],
                "metrics": [("Checkpoint 8 peak function complexity", "C8 Final: Peak Function Complexity", 50, False),
                            ("Failed C5–C8 tests at Checkpoint 8 (count)", "Failed Tests from C5–C8", 25, False)],
                "note": "forge · Claude Opus 5.5 · Means of 3 runs per group. Panels use separate units; bars start at zero. Starting conditions and full data appear in the preceding table.",
            },
            "forge": {
                "title": "forge: in-session gating, complexity, and cost",
                "labels": ["A · Default", "G · AST gate", "C · anti_slop"],
                "metrics": [("Checkpoint 8 peak function complexity", "Peak Function Complexity", 50, False),
                            ("Total cost for all 8 checkpoints (USD)", "Cost", 5, True)],
                "note": "Claude Opus 5.5 · Means of 3 runs per group. Test pass rates: 91.1%, 91.5%, and 92.1%, respectively. Complexity and cost use separate scales.",
            },
            "circuit": {
                "title": "circuit_eval: persistent contracts and continuous constraints",
                "labels": ["A · Default", "D · Refactor", "D+ · Contract", "C · anti_slop"],
                "metrics": [("Checkpoint 8 peak function complexity", "Peak Function Complexity", 80, False),
                            ("Total cost for all 8 checkpoints (USD)", "Cost", 25, True)],
                "note": "Claude Opus 5.5 · Means of 3 runs per group. D+ costs approximately $16.40, including one timed-out checkpoint estimate; its bar is pale and dashed. Pass rates appear above.",
            },
        }
    for key, spec in figures.items():
        anchor = f"code-erosion-{key}" + ("-en" if english else "")
        marker = f"<!-- erosion-chart: {key} -->"
        include = "{% include " + anchor + ".svg %}"
        position = source.index(marker if marker in source else include)
        preceding = source[:position].rstrip().splitlines()
        table = []
        for line in reversed(preceding):
            if not line.startswith("|"):
                break
            table.insert(0, cells(line))
        if not table:
            raise ValueError(f"Missing source table before {key}")
        if key == "splice":
            design = "code-erosion-splice-design" + ("-en" if english else "")
            (ROOT / "_includes" / (design + ".svg")).write_text(splicing_diagram(table, english))
            print(f"Rendered {design}.svg from the C3 starting conditions")
        plots, height = [], 0
        for title, label, maximum, currency in spec["metrics"]:
            numbers = values(table, label)
            if len(numbers) != len(spec["labels"]) or any(v < 0 or v > maximum for v in numbers):
                raise ValueError(f"Invalid chart values: {key}/{label}: {numbers}")
            plot, panel_height = panel(title, spec["labels"], numbers, maximum, height, currency)
            plots.append(plot)
            height += panel_height
        result = f'''<!-- Generated from the preceding post table by _scripts/render_code_erosion_figures.py. -->
<figure class="ar-chart" aria-labelledby="{anchor}-caption">
  <figcaption id="{anchor}-caption">{spec['title']}</figcaption>
  <div style="overflow-x: auto; margin-top: 16px;" tabindex="0" role="region" aria-label="{spec['title']}{'; scroll horizontally on narrow screens' if english else '；窄屏可横向滚动'}">
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 {height}" role="img" aria-labelledby="{anchor}-title {anchor}-desc" style="min-width: 600px; width: 100%; height: auto;">
      <title id="{anchor}-title">{spec['title']}</title>
      <desc id="{anchor}-desc">{escape(spec['note'])} {'Values are labeled and retained in the adjacent table.' if english else '数据以文字标注，并保留在相邻表格中。'}</desc>
      <g fill="var(--ar-ink-3, #555)" font-size="14" font-family="sans-serif">
        {chr(10).join(plots)}
      </g>
    </svg>
  </div>
  <p class="ar-chart-note">{escape(spec['note'])}</p>
</figure>
'''
        (ROOT / "_includes" / (anchor + ".svg")).write_text(result)
        source = source.replace(marker, include)
        print(f"Rendered {anchor}.svg from the post table")
    post.write_text(source)


if __name__ == "__main__":
    main()
