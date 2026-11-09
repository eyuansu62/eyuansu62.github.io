// Progressive enhancement of the SlopCodeBench source tables. Read the
// rendered cells so charts and accessible tables cannot drift independently.
(function () {
  "use strict";

  const NS = "http://www.w3.org/2000/svg";
  const svgNode = (tag, attrs = {}, text) => {
    const node = document.createElementNS(NS, tag);
    Object.entries(attrs).forEach(([key, value]) => node.setAttribute(key, value));
    if (text !== undefined) node.textContent = text;
    return node;
  };
  const number = (text) => Number(text.match(/\d+(?:\.\d+)?/)?.[0]);
  // Literal class names also keep these tokens discoverable by PurgeCSS.
  const SERIES = { blue: "ar-chart-series-blue", orange: "ar-chart-series-orange", green: "ar-chart-series-green" };
  const marker = (shape, x, y, category) => {
    const attrs = { class: "ar-chart-marker " + SERIES[category] };
    if (shape === 0) return svgNode("circle", { ...attrs, cx: x, cy: y, r: 4 });
    if (shape === 1) return svgNode("rect", { ...attrs, x: x - 4, y: y - 4, width: 8, height: 8 });
    return svgNode("path", { ...attrs, d: `M${x},${y - 5}l5,5l-5,5l-5,-5Z` });
  };
  const textNode = (svg, x, y, text, attrs = {}) => {
    svg.appendChild(svgNode("text", { x, y, ...attrs }, text));
  };

  document.querySelectorAll(".ar-chart").forEach((figure) => {
    const source = document.getElementById(figure.dataset.source);
    const table = source?.querySelector("table");
    if (!table) return;
    const rows = Array.from(table.tBodies[0]?.rows || [], (row) => Array.from(row.cells, (cell) => cell.textContent.trim()));
    const zh = figure.dataset.lang === "zh";
    const plot = figure.querySelector(".ar-chart-plot");
    const tooltip = document.createElement("div");
    tooltip.className = "ar-chart-tooltip";
    tooltip.id = figure.dataset.source + "-tooltip";
    tooltip.setAttribute("role", "tooltip");
    tooltip.hidden = true;
    figure.appendChild(tooltip);
    const hide = () => (tooltip.hidden = true);
    const show = (title, items, clientX, clientY) => {
      tooltip.replaceChildren();
      const heading = document.createElement("strong");
      heading.textContent = title;
      tooltip.appendChild(heading);
      items.forEach((item) => {
        const line = document.createElement("div");
        line.textContent = item;
        tooltip.appendChild(line);
      });
      tooltip.hidden = false;
      const box = figure.getBoundingClientRect();
      const left = Math.max(0, Math.min(clientX - box.left + 14, box.width - tooltip.offsetWidth));
      const top = Math.max(0, Math.min(clientY - box.top + 14, box.height - tooltip.offsetHeight));
      tooltip.style.left = left + "px";
      tooltip.style.top = top + "px";
    };
    figure.addEventListener("keydown", (event) => {
      if (event.key === "Escape") {
        hide();
        figure.querySelector(".ar-chart-crosshair")?.setAttribute("visibility", "hidden");
      }
    });

    const makeSVG = (width, height, label) => {
      const svg = svgNode("svg", { viewBox: `0 0 ${width} ${height}`, role: "group", "aria-label": label });
      svg.appendChild(svgNode("title", {}, label));
      return svg;
    };

    const trajectory = () => {
      if (rows.length !== 6 || rows.some((row) => row.length !== 10)) return false;
      const periodicTable = document.getElementById(figure.dataset.extraSource)?.querySelector("table");
      const periodicRow = periodicTable?.tBodies[0]?.rows[0];
      if (!periodicRow || periodicRow.cells.length !== 9) return false;
      const periodic = Array.from(periodicRow.cells)
        .slice(1)
        .map((cell) => number(cell.textContent));
      const aggregate = (prompt, label, short, category, shape) => {
        const runs = rows.filter((row) => row[0].includes(prompt)).map((row) => row.slice(1, 9).map(number));
        if (runs.length !== 3 || runs.some((run) => run.some((v) => !Number.isFinite(v)))) return null;
        const columns = runs[0].map((_, i) => runs.map((run) => run[i]));
        return {
          label,
          short,
          category,
          shape,
          n: runs.length,
          values: columns.map((values) => values.reduce((sum, v) => sum + v, 0) / values.length),
          min: columns.map((values) => Math.min(...values)),
          max: columns.map((values) => Math.max(...values)),
        };
      };
      const series = [
        aggregate("just-solve", zh ? "默认提示词" : "Default prompt", zh ? "默认提示词" : "Default", "orange", 0),
        {
          label: zh ? "每 2 关重构" : "Periodic refactor",
          short: zh ? "定期重构" : "Periodic refactor",
          category: "green",
          shape: 1,
          n: 1,
          values: periodic,
        },
        aggregate("anti_slop", zh ? "全程 anti_slop" : "anti_slop every checkpoint", "anti_slop", "blue", 2),
      ];
      if (series.some((item) => !item || item.values.some((v) => !Number.isFinite(v)))) return false;

      const legend = document.createElement("div");
      legend.className = "ar-chart-legend";
      series.forEach((item) => {
        const label = document.createElement("span");
        const key = svgNode("svg", { viewBox: "0 0 28 14", "aria-hidden": "true" });
        key.appendChild(svgNode("path", { d: "M1,7H27", class: "ar-chart-line " + SERIES[item.category] }));
        key.appendChild(marker(item.shape, 14, 7, item.category));
        label.append(key, document.createTextNode(item.short + " · n=" + item.n));
        legend.appendChild(label);
      });
      plot.before(legend);

      return () => {
        const width = Math.max(280, plot.clientWidth);
        const height = 350;
        const margin = { left: 34, right: width < 600 ? 112 : 154, top: 16, bottom: 36 };
        const maximum = Math.ceil(Math.max(80, ...series.flatMap((item) => item.max || item.values)) / 20) * 20;
        const x = (i) => margin.left + (i / 7) * (width - margin.left - margin.right);
        const y = (v) => height - margin.bottom - (v / maximum) * (height - margin.top - margin.bottom);
        const svg = makeSVG(
          width,
          height,
          zh ? "circuit_eval 三种策略的最高函数复杂度" : "Peak function complexity for three strategies on circuit_eval"
        );
        for (let tick = 0; tick <= maximum; tick += 20) {
          svg.appendChild(svgNode("path", { d: `M${x(0)},${y(tick)}H${x(7)}`, class: "ar-chart-grid" }));
          textNode(svg, margin.left - 9, y(tick) + 4, tick, { "text-anchor": "end" });
        }
        for (let i = 0; i < 8; i++) textNode(svg, x(i), height - 12, "C" + (i + 1), { "text-anchor": "middle" });
        const pathFor = (values) => values.map((v, i) => `${i ? "L" : "M"}${x(i)},${y(v)}`).join("");
        series
          .filter((item) => item.n > 1)
          .forEach((item) => {
            const lower = item.min
              .map((v, i) => [x(i), y(v)])
              .reverse()
              .map(([px, py]) => `L${px},${py}`)
              .join("");
            svg.appendChild(svgNode("path", { d: pathFor(item.max) + lower + "Z", class: "ar-chart-band " + SERIES[item.category] }));
          });
        series.forEach((item) => {
          svg.appendChild(svgNode("path", { d: pathFor(item.values), class: "ar-chart-line " + SERIES[item.category] }));
          if (item.n === 1) [1, 3, 5].forEach((i) => svg.appendChild(marker(1, x(i), y(item.values[i]), item.category)));
          const final = item.values[7];
          svg.appendChild(marker(item.shape, x(7), y(final), item.category));
          svg.appendChild(svgNode("path", { d: `M${x(7) + 7},${y(final)}h9`, class: "ar-chart-line " + SERIES[item.category] }));
          textNode(svg, x(7) + 22, y(final) - 6, item.short, { class: "ar-chart-end-label" });
          textNode(svg, x(7) + 22, y(final) + 14, final.toFixed(1), { class: "ar-chart-end-value" });
        });
        const crosshair = svgNode("path", { class: "ar-chart-crosshair", visibility: "hidden" });
        svg.appendChild(crosshair);
        const hit = svgNode("rect", {
          x: x(0) - 6,
          y: margin.top,
          width: x(7) - x(0) + 12,
          height: height - margin.top - margin.bottom + 8,
          class: "ar-chart-hit",
          tabindex: 0,
          role: "slider",
          "aria-label": zh ? "查看关卡数据（左右方向键切换）" : "Inspect checkpoint (left and right arrow keys)",
          "aria-valuemin": 1,
          "aria-valuemax": 8,
          "aria-valuenow": 8,
          "aria-orientation": "horizontal",
          "aria-describedby": tooltip.id,
        });
        const readout = (index) =>
          series.map((item) => {
            const scope =
              item.n > 1
                ? zh
                  ? `均值 ${item.values[index].toFixed(1)}，范围 ${item.min[index]}–${item.max[index]}`
                  : `mean ${item.values[index].toFixed(1)}, range ${item.min[index]}–${item.max[index]}`
                : item.values[index] + ([1, 3, 5].includes(index) ? (zh ? "（重构后）" : " (after refactoring)") : "");
            return `${item.label}: ${scope}; n=${item.n}`;
          });
        let selected = 7;
        const inspect = (index, clientX, clientY) => {
          selected = Math.max(0, Math.min(7, index));
          crosshair.setAttribute("d", `M${x(selected)},${margin.top}V${height - margin.bottom}`);
          crosshair.setAttribute("visibility", "visible");
          const items = readout(selected);
          hit.setAttribute("aria-valuenow", selected + 1);
          hit.setAttribute("aria-valuetext", "C" + (selected + 1) + "; " + items.join("; "));
          show("C" + (selected + 1) + " · CC", items, clientX, clientY);
        };
        hit.setAttribute("aria-valuetext", "C8; " + readout(7).join("; "));
        const inspectKeyboard = () => {
          const rect = svg.getBoundingClientRect();
          inspect(selected, rect.left + x(selected), rect.top + margin.top);
        };
        const inspectPointer = (event) => {
          const rect = svg.getBoundingClientRect();
          const px = ((event.clientX - rect.left) * width) / rect.width;
          inspect(Math.round(((px - margin.left) / (x(7) - x(0))) * 7), event.clientX, event.clientY);
        };
        hit.addEventListener("pointermove", inspectPointer);
        hit.addEventListener("pointerdown", inspectPointer);
        hit.addEventListener("focus", inspectKeyboard);
        hit.addEventListener("blur", () => {
          hide();
          crosshair.setAttribute("visibility", "hidden");
        });
        hit.addEventListener("pointerleave", (event) => {
          if (event.pointerType === "mouse" && document.activeElement !== hit) {
            hide();
            crosshair.setAttribute("visibility", "hidden");
          }
        });
        hit.addEventListener("keydown", (event) => {
          if (!["ArrowLeft", "ArrowRight", "Home", "End"].includes(event.key)) return;
          event.preventDefault();
          selected = event.key === "Home" ? 0 : event.key === "End" ? 7 : Math.max(0, Math.min(7, selected + (event.key === "ArrowRight" ? 1 : -1)));
          inspectKeyboard();
        });
        svg.appendChild(hit);
        plot.replaceChildren(svg);
      };
    };

    const refactor = () => {
      if (rows.length !== 2 || rows.some((row) => row.length !== 4)) return false;
      const pairs = [];
      for (const row of rows) {
        const changes = Array.from(row[3].matchAll(/(\d+)\s*→\s*(\d+)/g));
        const counts = row[2].match(/\d+\s*\/\s*\d+/g) || [];
        if (changes.length !== number(row[1]) || !counts.length) return false;
        changes.forEach((match, i) =>
          pairs.push({
            label: row[0] + " #" + (i + 1),
            before: Number(match[1]),
            after: Number(match[2]),
            tests: counts.length === changes.length ? counts[i] : counts[0],
          })
        );
      }
      if (pairs.length !== 6) return false;
      const legend = document.createElement("div");
      legend.className = "ar-chart-legend ar-chart-legend-pair";
      [
        [zh ? "重构前" : "Before", true],
        [zh ? "重构后" : "After", false],
      ].forEach(([label, before]) => {
        const item = document.createElement("span");
        const key = svgNode("svg", { viewBox: "0 0 28 14", "aria-hidden": "true" });
        key.appendChild(
          svgNode("circle", {
            cx: 14,
            cy: 7,
            r: 4.5,
            class: before ? "ar-chart-marker ar-chart-marker-open ar-chart-series-orange" : "ar-chart-marker ar-chart-series-blue",
          })
        );
        item.append(key, document.createTextNode(label));
        legend.appendChild(item);
      });
      plot.before(legend);
      return () => {
        const width = Math.max(280, plot.clientWidth);
        const height = 370;
        const left = width < 600 ? 122 : 146;
        const right = width - 34;
        const maximum = Math.ceil(Math.max(40, ...pairs.map((pair) => Math.max(pair.before, pair.after))) / 10) * 10;
        const x = (v) => left + (v / maximum) * (right - left);
        const y = (i) => 36 + i * 45 + (i >= 3 ? 18 : 0);
        const svg = makeSVG(
          width,
          height,
          zh ? "六次独立重构前后的最高函数复杂度" : "Peak function complexity before and after six isolated refactoring sessions"
        );
        for (let tick = 0; tick <= maximum; tick += 10) {
          svg.appendChild(svgNode("path", { d: `M${x(tick)},16V326`, class: "ar-chart-grid" }));
          textNode(svg, x(tick), 348, tick, { "text-anchor": "middle" });
        }
        textNode(svg, (left + right) / 2, 368, zh ? "最高函数复杂度（CC）" : "Peak function complexity (CC)", { "text-anchor": "middle" });
        pairs.forEach((pair, i) => {
          const group = svgNode("g", { tabindex: 0, role: "img", class: "ar-chart-refactor-row", "aria-describedby": tooltip.id });
          const details = [
            (zh ? "最高 CC：" : "Peak CC: ") + `${pair.before} → ${pair.after}`,
            zh ? "原有测试结果不变" : "Existing test results preserved",
            (zh ? "测试：" : "Tests: ") + pair.tests + " → " + pair.tests,
          ];
          group.setAttribute("aria-label", pair.label + "; " + details.join("; "));
          group.appendChild(svgNode("rect", { x: 0, y: y(i) - 18, width, height: 36, class: "ar-chart-row-hit" }));
          textNode(group, left - 14, y(i) + 4, pair.label, { "text-anchor": "end", class: "ar-chart-strategy" });
          group.appendChild(svgNode("path", { d: `M${x(pair.after)},${y(i)}H${x(pair.before)}`, class: "ar-chart-pair-connector" }));
          group.appendChild(
            svgNode("circle", { cx: x(pair.before), cy: y(i), r: 4.5, class: "ar-chart-marker ar-chart-marker-open ar-chart-series-orange" })
          );
          group.appendChild(svgNode("circle", { cx: x(pair.after), cy: y(i), r: 4.5, class: "ar-chart-marker ar-chart-series-blue" }));
          textNode(group, x(pair.after) - 10, y(i) + 4, pair.after, { "text-anchor": "end", class: "ar-chart-value" });
          textNode(group, x(pair.before) + 10, y(i) + 4, pair.before, { class: "ar-chart-value" });
          const reveal = (event) => {
            const rect = group.getBoundingClientRect();
            show(pair.label, details, event.clientX ?? rect.left + x(pair.after), event.clientY ?? rect.top);
          };
          group.addEventListener("pointermove", reveal);
          group.addEventListener("pointerdown", reveal);
          group.addEventListener("focus", reveal);
          group.addEventListener("blur", hide);
          group.addEventListener("pointerleave", (event) => {
            if (event.pointerType === "mouse" && document.activeElement !== group) hide();
          });
          svg.appendChild(group);
        });
        plot.replaceChildren(svg);
      };
    };

    const cost = () => {
      if (rows.length !== 4 || rows.some((row) => row.length !== 5)) return false;
      const strategies = rows.map((row) => ({
        label: row[0].replace(/^\d+\.\s*/, ""),
        runs: number(row[1]),
        cc: number(row[2]),
        range: row[2],
        pass: row[3],
        cost: number(row[4]),
      }));
      if (strategies.some((s) => ![s.runs, s.cc, s.cost].every(Number.isFinite))) return false;
      const panels = [
        { key: "cc", title: zh ? "末关最高函数复杂度 · CC" : "Final peak complexity · CC", max: 80, ticks: [0, 20, 40, 60, 80] },
        { key: "cost", title: zh ? "8 关总费用 · USD" : "Total cost · USD", max: 50, ticks: [0, 10, 20, 30, 40, 50] },
      ].map((metric) => {
        const panel = document.createElement("div");
        panel.className = "ar-chart-panel";
        const title = document.createElement("p");
        title.className = "ar-chart-panel-title";
        title.textContent = metric.title;
        const canvas = document.createElement("div");
        panel.append(title, canvas);
        plot.appendChild(panel);
        return { ...metric, canvas };
      });
      plot.classList.add("ar-chart-panels");

      return () => {
        panels.forEach((metric) => {
          const width = Math.max(260, metric.canvas.clientWidth);
          const height = 308;
          const left = 4;
          const right = width - 12;
          const x = (v) => left + (v / metric.max) * (right - left - 52);
          const svg = makeSVG(width, height, metric.title);
          metric.ticks.forEach((tick) => {
            // Short tick marks below the shared zero baseline keep grid ink
            // out of the strategy labels above each thin bar.
            svg.appendChild(svgNode("path", { d: `M${x(tick)},275v5`, class: "ar-chart-grid" }));
            textNode(svg, x(tick), 298, metric.key === "cost" ? "$" + tick : tick, { "text-anchor": tick === 0 ? "start" : "middle" });
          });
          svg.appendChild(svgNode("path", { d: `M${left},275H${x(metric.max)}`, class: "ar-chart-grid" }));
          strategies.forEach((s, i) => {
            const y = 22 + i * 66;
            const value = metric.key === "cost" ? "$" + s.cost.toFixed(2) : s.cc.toFixed(1);
            const group = svgNode("g", { tabindex: 0, role: "img", class: "ar-chart-bar-group", "aria-describedby": tooltip.id });
            const details = [
              (zh ? "末关复杂度：" : "Final CC: ") + s.range,
              (zh ? "总费用：$" : "Total cost: $") + s.cost.toFixed(2),
              (zh ? "通过率：" : "Pass rate: ") + s.pass,
              (zh ? "运行次数：" : "Runs: ") + s.runs,
            ];
            group.setAttribute("aria-label", s.label + "; " + details.join("; "));
            group.appendChild(svgNode("rect", { x: 0, y: y - 17, width, height: 58, class: "ar-chart-bar-hit" }));
            textNode(group, left, y, s.label, { class: "ar-chart-strategy" });
            textNode(group, right, y + 25, value, { "text-anchor": "end", class: "ar-chart-value" });
            // Leave space for the endpoint value; both panels retain true
            // zero baselines and a common scale across their four rows.
            const barWidth = (s[metric.key] / metric.max) * (right - left - 52);
            group.appendChild(
              svgNode("path", {
                d: `M${left},${y + 10}h${Math.max(0, barWidth - 4)}q4,0 4,4v10q0,4 -4,4H${left}Z`,
                class: "ar-chart-bar ar-chart-series-blue",
              })
            );
            const reveal = (event) => {
              const rect = group.getBoundingClientRect();
              show(s.label, details, event.clientX ?? rect.left, event.clientY ?? rect.top);
            };
            group.addEventListener("pointermove", reveal);
            group.addEventListener("pointerdown", reveal);
            group.addEventListener("pointerleave", (event) => {
              if (event.pointerType === "mouse" && document.activeElement !== group) hide();
            });
            group.addEventListener("focus", reveal);
            group.addEventListener("blur", hide);
            svg.appendChild(group);
          });
          metric.canvas.replaceChildren(svg);
        });
      };
    };

    const renderers = { trajectory, refactor, cost };
    const draw = renderers[figure.dataset.chart]?.();
    if (!draw) return; // Leave source tables expanded when data is missing.
    figure.hidden = false;
    draw();
    source.open = false;
    let previousWidth = plot.clientWidth;
    new ResizeObserver(() => {
      if (Math.abs(plot.clientWidth - previousWidth) < 1) return;
      previousWidth = plot.clientWidth;
      hide();
      draw();
    }).observe(plot);
    let printOpen;
    window.addEventListener("beforeprint", () => {
      printOpen = source.open;
      source.open = true;
    });
    window.addEventListener("afterprint", () => (source.open = printOpen));
  });
})();
