// Behaviour for _layouts/post.liquid: builds the contents list from the post's
// h2/h3 headings, turns kramdown footnotes into hover popovers, and wires the
// citation copy button. Without JS the post still reads top to bottom; the
// contents list just stays hidden.
(function () {
  "use strict";

  const main = document.querySelector(".ar-main");
  if (!main) return;

  // ---- heading ids --------------------------------------------------------
  // kramdown's auto ids drop CJK characters, which can leave headings with an
  // empty or duplicate id. Give every heading a stable, unique one.
  const headings = Array.from(main.querySelectorAll("h2, h3")).filter((h) => !h.closest(".footnotes, .publications"));
  const seen = new Set();
  headings.forEach((h, i) => {
    let id = h.id && !seen.has(h.id) ? h.id : "";
    if (!id) {
      id = "section-" + (i + 1);
      while (seen.has(id) || document.getElementById(id)) id += "-x";
      h.id = id;
    }
    seen.add(id);
  });

  // ---- tables scroll sideways on narrow screens --------------------------
  main.querySelectorAll("table").forEach((t) => {
    if (t.parentElement.classList.contains("ar-table")) return;
    const wrap = document.createElement("div");
    wrap.className = "ar-table";
    t.parentNode.insertBefore(wrap, t);
    wrap.appendChild(t);
  });

  // ---- footnotes -> Notes section ----------------------------------------
  const notes = main.querySelector(".footnotes");
  if (notes) {
    const h2 = document.createElement("h2");
    h2.id = "notes";
    h2.textContent = main.dataset.notesLabel || "Notes";
    notes.querySelector("hr")?.remove();
    notes.parentNode.insertBefore(h2, notes);
    // Keep Notes ahead of References / Citation, which the layout appends.
    const anchor = main.querySelector("#references, #citation");
    if (anchor) {
      main.insertBefore(notes, anchor);
      main.insertBefore(h2, notes);
    }
  }
  const ordered = Array.from(main.querySelectorAll("h2, h3")).filter((h) => h.id && !h.closest(".footnotes, .publications"));

  // ---- contents list ------------------------------------------------------
  // Entries are as short as the heading allows: the section number goes, and
  // the label stops at the first break in the sentence (a colon, dash, comma,
  // bracket or question mark), keeping a lead-in such as "Step 1:" or "第一步：".
  // A post can name its own label per heading with toc_labels in front matter.
  // The full heading is the link's tooltip.
  const NUMBER = /^(?:\d+\s*[.、]\s*|\d+\s+[—–-]\s+|[〇一二三四五六七八九十]+、\s*)/;
  const LEAD = /^(?:(?:step|finding|part)\s*\d+|第[一二三四五六七八九十\d]+[步部章节]|发现\s*\d+)\s*[:：]\s*/i;
  const BREAK = /\s+[—–]\s+|——|[:：，]|,\s|\s?[（(]|[?？]/;
  const shorten = (heading) => {
    const text = heading.replace(NUMBER, "");
    const lead = (text.match(LEAD) || [""])[0];
    let rest = text.slice(lead.length);
    const cut = rest.match(BREAK);
    if (cut && cut.index > 0) rest = rest.slice(0, cut.index) + (/[?？]/.test(cut[0]) ? cut[0] : "");
    return (lead + rest).trim() || heading;
  };

  const toc = document.querySelector(".ar-toc");
  // Keys are written in the source, where kramdown has not yet curled quotes.
  const plain = (t) => t.replace(/[‘’]/g, "'").replace(/[“”]/g, '"');
  const labels = new Map();
  try {
    Object.entries(JSON.parse(toc?.dataset.labels || "{}")).forEach(([k, v]) => labels.set(plain(k), v));
  } catch (e) {}
  if (toc && ordered.filter((h) => h.tagName === "H2").length >= 2) {
    const root = document.createElement("ol");
    let sub = null;
    ordered.forEach((h) => {
      const li = document.createElement("li");
      const a = document.createElement("a");
      const full = h.textContent.trim();
      a.href = "#" + h.id;
      a.textContent = labels.get(plain(full)) || shorten(full);
      if (a.textContent !== full) a.title = full;
      li.appendChild(a);
      if (h.tagName === "H3" && root.lastElementChild) {
        if (!sub) {
          sub = document.createElement("ol");
          root.lastElementChild.appendChild(sub);
        }
        sub.appendChild(li);
      } else {
        sub = null;
        root.appendChild(li);
      }
    });
    toc.appendChild(root);
    toc.hidden = false;
  } else if (toc) {
    toc.remove();
  }

  // ---- footnote popovers --------------------------------------------------
  let pop = null;
  const hide = () => {
    pop?.remove();
    pop = null;
  };
  const show = (ref) => {
    const target = document.getElementById(decodeURIComponent(ref.hash.slice(1)));
    if (!target) return;
    hide();
    pop = document.createElement("div");
    pop.className = "ar-fnpop";
    pop.setAttribute("role", "tooltip");
    pop.innerHTML = target.innerHTML;
    document.body.appendChild(pop);
    const r = ref.getBoundingClientRect();
    const w = pop.offsetWidth;
    const left = Math.max(12, Math.min(r.left + window.scrollX - w / 2, window.scrollX + document.documentElement.clientWidth - w - 12));
    pop.style.left = left + "px";
    pop.style.top = r.bottom + window.scrollY + 8 + "px";
  };
  main.querySelectorAll("a.footnote, sup[role='doc-noteref'] a").forEach((ref) => {
    ref.addEventListener("mouseenter", () => show(ref));
    ref.addEventListener("focus", () => show(ref));
    ref.addEventListener("mouseleave", hide);
    ref.addEventListener("blur", hide);
  });
  window.addEventListener("scroll", hide, { passive: true });

  // ---- citation copy ------------------------------------------------------
  document.querySelectorAll(".ar-copy").forEach((btn) => {
    const label = btn.textContent;
    btn.addEventListener("click", () => {
      const code = btn.parentElement.querySelector("pre");
      navigator.clipboard?.writeText(code.innerText).then(() => {
        btn.textContent = btn.dataset.done || "Copied";
        setTimeout(() => (btn.textContent = label), 1600);
      });
    });
  });
})();
