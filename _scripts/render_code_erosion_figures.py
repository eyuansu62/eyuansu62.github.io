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
    """Render the plain-language overview from the article's starting/result rows."""
    anchor = "code-erosion-splice-design" + ("-en" if english else "")
    title = ("Fixing existing bugs did not reduce test failures for new requirements" if english
             else "只修复已有 Bug，未减少新增需求的测试失败")
    failures = values(table, "Failed Tests from C5–C8" if english else "来自第 5–8 关的失败测试数")
    tests = [re.search(r"(\d+(?:\.\d+)?)\s*/\s*(\d+)", cell).groups() for cell in table[0][1:]]
    if len(failures) != 3 or len(tests) != 3:
        raise ValueError("Splicing overview requires three starting/result conditions")
    names = (["Original code", "Bugs fixed", "Modular code"] if english
             else ["原始代码", "仅修复 Bug", "模块化代码"])
    statuses = [("All pass" if english else "全部通过") if float(passed) == float(total)
                else ("Some fail" if english else "部分失败") for passed, total in tests]
    colors = ("#df693c", "#327bce", "#258e70")
    ink = "var(--ar-ink-3, #555)"
    rule = "var(--ar-rule, #d9d9d9)"
    note = ("forge · Claude Opus 5.5 · 3 runs per starting version. Values are mean failed tests for Checkpoints 5–8, evaluated after Checkpoint 8. Bug fixes preserve the original structure; the modular version uses the official reference implementation. Differences in specification semantics remain a potential confounder."
            if english else "forge · Claude Opus 5.5 · 每种起点运行 3 次。数值为完成第 8 关后、第 5–8 关测试的平均失败数。修复 Bug 后保留原结构；模块化代码采用官方参考实现，规格理解差异仍是潜在混淆变量。")
    description = "; ".join(f"{name}: {status}, {failed:.1f}" for name, status, failed
                            in zip(names, statuses, failures, strict=True))
    parts = [f'''<defs>
  <marker id="{anchor}-arrow" viewBox="0 0 8 8" refX="7" refY="4" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
    <path d="M1,1 L7,4 L1,7" fill="none" stroke="context-stroke" stroke-width="1.3"/>
  </marker>
</defs>''']

    def text(x, y, label, size=14, weight=400, align="start", color=None):
        style = f' style="fill: {color}"' if color else ""
        parts.append(f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" text-anchor="{align}"{style}>{escape(label)}</text>')

    def line(path, color=ink, arrow=False):
        marker = f' marker-end="url(#{anchor}-arrow)"' if arrow else ""
        parts.append(f'<path d="{path}" fill="none" stroke="{color}" stroke-width="1.4"{marker}/>')

    def code_picture(x, color, modular):
        structure = "modular" if modular else "single-file"
        parts.append(f'<g transform="translate({x},54)" data-code-structure="{structure}">')
        if modular:
            line("M66,34 V54 M17,70 V54 H115 V70 M66,54 V70")
            files = [(42, 0, 48, 34), (0, 70, 34, 34), (49, 70, 34, 34), (98, 70, 34, 34)]
            for px, py, width, height in files:
                line(f"M{px},{py} H{px + width - 9} L{px + width},{py + 9} V{py + height} H{px} Z M{px + width - 9},{py} V{py + 9} H{px + width}")
                line(f"M{px + 7},{py + 16} H{px + width - 7} M{px + 7},{py + 23} H{px + width - 12}", color)
        else:
            line("M0,0 H112 L132,20 V112 H0 Z M112,0 V20 H132")
            line("M46,29 C110,46 30,62 95,89 M79,29 C12,49 117,61 46,89 M29,39 C3,66 105,105 94,70 C76,43 0,68 28,89 M63,58 C111,53 121,93 72,105")
            for px, py in [(12, 18), (79, 18), (46, 48), (12, 80), (79, 80)]:
                parts.append(f'<rect x="{px}" y="{py}" width="34" height="20" rx="2" fill="var(--ar-paper, var(--global-bg-color, #fff))" stroke="{ink}" stroke-width="1.2"/>')
                line(f"M{px + 6},{py + 6} H{px + 25} M{px + 6},{py + 11} H{px + 20} M{px + 6},{py + 16} H{px + 23}", color)
        parts.append("</g>")

    for i, (name, color) in enumerate(zip(names, colors, strict=True)):
        center = 100 + 220 * i
        text(center, 22, name, size=16, weight=600, align="middle")
        line(f"M{center - 79},35 H{center + 79}", color)
        code_picture(center - 66, color, i == 2)
    line("M181,112 H232", arrow=True)
    line("M48,180 V186 H372 V180")
    text(210, 207, "Same structure" if english else "保留相同结构", size=13, align="middle")
    text(0, 236, "Same test suite" if english else "同一套测试", size=13, weight=600)
    for i, ((passed, total), status) in enumerate(zip(tests, statuses, strict=True)):
        center = 100 + 220 * i
        passing = float(passed) == float(total)
        color = "#258e70" if passing else "#c43f38"
        if passing:
            line(f"M{center - 50},253 l4,4 l8,-10", color)
        else:
            line(f"M{center - 50},248 l10,10 M{center - 50},258 l10,-10", color)
        text(center + 8, 259, status, weight=600, align="middle")
        line(f"M{center},274 V292", arrow=True)
    text(320, 318, "Ask the AI to add more features" if english else "让 AI 继续实现相同的新功能", align="middle")
    line("M0,334 H640", rule)
    text(0, 357, "Failed tests for new requirements (average)" if english else "新增需求的失败测试数（平均）", size=14, weight=600)
    for i, (number, color) in enumerate(zip(failures, colors, strict=True)):
        text(100 + 220 * i, 399, f"{number:.1f}", size=30, weight=600, align="middle", color=color)
    return f'''<!-- Generated from the starting conditions and result rows in the post's splicing table. -->
<figure class="ar-chart" aria-labelledby="{anchor}-caption">
  <figcaption id="{anchor}-caption">{escape(title)}</figcaption>
  <div style="overflow-x: auto; margin-top: 16px;" tabindex="0" role="region" aria-label="{escape(title)}{'; scroll horizontally on narrow screens' if english else '；窄屏可横向滚动'}">
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 414" role="img" aria-labelledby="{anchor}-title {anchor}-desc" style="min-width: 600px; width: 100%; height: auto;">
      <title id="{anchor}-title">{escape(title)}</title>
      <desc id="{anchor}-desc">{escape(description + '. ' + note)}</desc>
      <g fill="{ink}" font-size="14" font-family="sans-serif">
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
