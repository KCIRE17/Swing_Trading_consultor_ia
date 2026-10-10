/* =====================================================================
 * Kinetic Alpha - router y vistas 4 y 5
 *
 * -_enlaza_ el control segmentado de rango con el input oculto #period
 *   que app.js ya leia como un <select>.
 * -_enlaza_ la navegacion por hash (#/descriptiva, ...) con switchTab.
 * -pinta_ el panel de salud desde /api/health.
 * -pinta_ la vista de screener, alimentada por el evento ka:data.
 * ===================================================================== */

(function () {
  "use strict";

  const ROUTES = ["descriptiva", "predictiva", "prescriptiva", "screener", "metodologia"];

  const byId = (id) => document.getElementById(id);
  const esc = (v) =>
    String(v == null ? "" : v).replace(/[&<>"']/g, (c) => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
    })[c]);

  const num = (v, d = 2) => (typeof v === "number" && isFinite(v) ? v.toFixed(d) : "—");
  const pct = (v, d = 2) =>
    typeof v === "number" && isFinite(v) ? `${v >= 0 ? "+" : ""}${v.toFixed(d)}%` : "—";

  function compactNum(v) {
    if (typeof v !== "number" || !isFinite(v)) return "—";
    const a = Math.abs(v);
    if (a >= 1e12) return (v / 1e12).toFixed(2) + "T";
    if (a >= 1e9) return (v / 1e9).toFixed(2) + "B";
    if (a >= 1e6) return (v / 1e6).toFixed(2) + "M";
    if (a >= 1e3) return (v / 1e3).toFixed(1) + "K";
    return String(v);
  }

  /* ---------------- 1. routing por hash ---------------- */

  function routeFromHash() {
    const raw = (location.hash || "").replace(/^#\/?/, "").split("?")[0].trim();
    return ROUTES.includes(raw) ? raw : "descriptiva";
  }

  function applyRoute(name, push) {
    if (!ROUTES.includes(name)) name = "descriptiva";

    document.querySelectorAll(".tab-panel").forEach((p) => {
      p.classList.toggle("active", p.dataset.panel === name);
    });
    document.querySelectorAll(".tab").forEach((a) => {
      if (a.dataset.tab === name) a.setAttribute("aria-current", "page");
      else a.removeAttribute("aria-current");
    });

    // app.js mantiene los charts; hay que redimensionar al mostrar
    if (window.__kaCharts) {
      Object.values(window.__kaCharts).forEach((c) => {
        try {
          if (c && c.update) c.update();
        } catch (_) {
          /* un chart aun no inicializado no debe romper la navegacion */
        }
      });
    }
    if (name === "screener") renderScreener();

    if (push && routeFromHash() !== name) {
      location.hash = `#/${name}`;
    }
  }

  function bindRouter() {
    document.querySelectorAll(".tab").forEach((a) => {
      a.addEventListener("click", (ev) => {
        ev.preventDefault();
        applyRoute(a.dataset.tab, true);
      });
    });
    window.addEventListener("hashchange", () => applyRoute(routeFromHash(), false));
    applyRoute(routeFromHash(), false);
  }

  /* ---------------- 2. control de rango ---------------- */

  function bindPeriod() {
    const seg = byId("periodSeg");
    const hidden = byId("period");
    if (!seg || !hidden) return;

    seg.addEventListener("click", (ev) => {
      const btn = ev.target.closest("button[data-period]");
      if (!btn) return;
      seg.querySelectorAll("button").forEach((b) =>
        b.setAttribute("aria-pressed", String(b === btn)));
      hidden.value = btn.dataset.period;
      const runBtn = byId("runBtn");
      if (runBtn) runBtn.click();
    });
  }

  /* ---------------- 3. panel de salud ---------------- */

  function dot(node, cls) {
    if (!node) return;
    const base = cls.replace(/\s*ka-dot-\w+/g, "").trim();
    node.className = base + " " + cls;
  }

  function setHealth() {
    fetch("/api/health", { headers: { Accept: "application/json" } })
      .then((r) => (r.ok ? r.json() : null))
      .then((h) => {
        if (!h) throw new Error("health");
        const put = (id, ok, on, off, kind) => {
          const v = byId(id);
          if (v) {
            v.textContent = ok ? on : off;
            v.className = "ka-health-v " + (ok ? kind : "ka-v-sell");
          }
        };
        put("hDb", h.base_de_datos, "Online", "Offline", "ka-v-buy");
        put("hMl", h.sentimiento_modelo, "Activo", "Inactivo", "ka-v-buy");
        put("hGemini", h.gemini_key_present, "Conectado", "Sin clave", "ka-v-ai");

        const items = document.querySelectorAll("#health .ka-health-item .ka-dot");
        const st = [h.base_de_datos, h.sentimiento_modelo, h.gemini_key_present];
        items.forEach((d, i) => {
          d.className = "ka-dot " + (st[i] ? (i === 2 ? "ka-dot-ai" : "ka-dot-ok") : "ka-dot-off");
        });

        const feed = byId("hFeed");
        if (feed) feed.textContent = h.base_de_datos ? "Supabase / Yahoo" : "Yahoo Finance";
      })
      .catch(() => {
        const v = byId("hFeed");
        if (v) v.textContent = "sin conexión";
      });
  }

  /* ---------------- 4. vista de screener ---------------- */

  let screenerSort = "change_pct";
  let screenerRows = [];

  function sigChip(senal) {
    const s = String(senal || "").toUpperCase();
    if (s.startsWith("COMPRA")) return '<span class="ka-chip ka-chip-buy">Compra</span>';
    if (s.startsWith("VENTA")) return '<span class="ka-chip ka-chip-sell">Venta</span>';
    return '<span class="ka-chip ka-chip-hold">Mantener</span>';
  }

  function renderScreener() {
    const box = byId("screenerTable");
    if (!box) return;

    const list = (screenerRows || []).filter((c) => c && !c.error);
    if (!list.length) {
      box.innerHTML =
        '<div class="ka-empty">' +
        '<svg class="ka-i" aria-hidden="true"><use href="/icons/sprite.svg#i-insights"></use></svg>' +
        '<p class="ka-body-md">Sin datos de screener todavía. Presioná <b>Analizar</b>.</p></div>';
      return;
    }

    const dir = (v) => (v >= 0 ? 1 : -1);
    const sorted = [...list].sort((a, b) => {
      const k = screenerSort;
      const av = a[k], bv = b[k];
      if (typeof av === "number" && typeof bv === "number") return (bv - av) * dir(1);
      return String(av ?? "").localeCompare(String(bv ?? ""));
    });

    const ups = list.filter((c) => (c.change_pct || 0) > 0).length;
    const downs = list.filter((c) => (c.change_pct || 0) < 0).length;
    const su = byId("screenerUp"), sd = byId("screenerDown");
    if (su) su.textContent = `${ups} al alza`;
    if (sd) sd.textContent = `${downs} a la baja`;

    const rows = sorted
      .map((c) => {
        const up = (c.change_pct || 0) >= 0;
        return `
        <tr>
          <td><span class="ka-num" style="color:var(--ka-on-surface)">${esc(c.ticker)}</span></td>
          <td class="ka-muted">${esc(c.nombre || "")}</td>
          <td class="num">${num(c.close)}</td>
          <td class="num" style="color:${up ? "var(--ka-primary)" : "var(--ka-error)"}">${pct(c.change_pct)}</td>
          <td class="num">${compactNum(c.volume)}</td>
          <td class="num">${num(c.rsi14, 1)}</td>
          <td class="num" style="color:${(c.macd_hist || 0) >= 0 ? "var(--ka-primary)" : "var(--ka-error)"}">${num(c.macd_hist, 3)}</td>
          <td class="num">${num(c.atr14)}</td>
          <td>${sigChip(c.senal)}</td>
        </tr>`;
      })
      .join("");

    box.innerHTML = `
      <table class="ka-table">
        <thead>
          <tr>
            <th>Ticker</th><th>Empresa</th>
            <th class="num">Cierre</th><th class="num">Var</th><th class="num">Volumen</th>
            <th class="num">RSI</th><th class="num">MACD-H</th><th class="num">ATR</th>
            <th>Señal</th>
          </tr>
        </thead>
        <tbody>${rows}</tbody>
      </table>`;
  }

  function bindScreenerSort() {
    const seg = byId("screenerSort");
    if (!seg) return;
    seg.addEventListener("click", (ev) => {
      const btn = ev.target.closest("button[data-sort]");
      if (!btn) return;
      seg.querySelectorAll("button").forEach((b) =>
        b.setAttribute("aria-pressed", String(b === btn)));
      screenerSort = btn.dataset.sort;
      renderScreener();
    });
  }

  /* ---------------- arranque ---------------- */

  document.addEventListener("DOMContentLoaded", () => {
    bindRouter();
    bindPeriod();
    bindScreenerSort();
    setHealth();
    setInterval(setHealth, 60000);

    window.addEventListener("ka:data", (ev) => {
      const d = ev.detail || {};
      screenerRows = (d.screener && d.screener.companies) || [];
      renderScreener();
    });

    if (window.__kaData) {
      screenerRows = (window.__kaData.screener && window.__kaData.screener.companies) || [];
    }
  });
})();
