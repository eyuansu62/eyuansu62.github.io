// Behaviour for _layouts/post.liquid: builds the contents rail from the post's
// h2/h3 headings and highlights the section being read, turns kramdown
// footnotes into hover popovers, and wires the citation copy button.
// Without JS the post still reads top to bottom; the rail just stays hidden.
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

  // ---- contents rail ------------------------------------------------------
  const toc = document.querySelector(".ar-toc");
  const links = new Map();
  if (toc && ordered.filter((h) => h.tagName === "H2").length >= 2) {
    const root = document.createElement("ol");
    let sub = null;
    ordered.forEach((h) => {
      const li = document.createElement("li");
      const a = document.createElement("a");
      a.href = "#" + h.id;
      a.textContent = h.textContent.trim();
      li.appendChild(a);
      links.set(h.id, a);
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

    // Highlight the last heading that has scrolled past the top third.
    let ticking = false;
    const update = () => {
      ticking = false;
      const line = window.innerHeight * 0.3;
      let current = ordered[0];
      for (const h of ordered) {
        if (h.getBoundingClientRect().top - line <= 0) current = h;
        else break;
      }
      links.forEach((a, id) => a.classList.toggle("active", id === current.id));
      // Keep the active link visible when the rail itself scrolls.
      const active = links.get(current.id);
      if (active && toc.scrollHeight > toc.clientHeight) {
        const r = active.getBoundingClientRect();
        const t = toc.getBoundingClientRect();
        if (r.top < t.top || r.bottom > t.bottom) active.scrollIntoView({ block: "nearest" });
      }
    };
    const onScroll = () => {
      if (!ticking) {
        ticking = true;
        requestAnimationFrame(update);
      }
    };
    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", onScroll);
    update();
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
