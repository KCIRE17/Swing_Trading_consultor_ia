"use strict";

Chart.defaults.color = "#8b949e";
Chart.defaults.borderColor = "rgba(48,54,61,1)";

const up = "#26a269";
const down = "#f14c4c";
const accent = "#58a6ff";
const cyan = "#6fddff";
const yellow = "#d29922";
const purple = "#bc4c9a";

const state = {};

function byId(id) {
  return document.getElementById(id);
}

const charts = {};
const chartDefs = {
  price: {
    canvas: "chartPrice",
    datasets: [
      { label: "Precio de cierre", data: [], borderColor: accent, backgroundColor: "rgba(88,166,255,0.08)", fill: true },
      { label: "Promedio 20 días (SMA20)", data: [], borderColor: yellow, backgroundColor: yellow, tooltipExtra: () => "precio promedio de los últimos 20 días" },
      { label: "Promedio 50 días (SMA50)", data: [], borderColor: purple, backgroundColor: purple, tooltipExtra: () => "precio promedio de los últimos 50 días" },
      { label: "Banda inferior (-1 ATR)", data: [], legendHidden: true, tooltip: false, borderWidth: 0, pointRadius: 0 },
      { label: "Banda superior (+1 ATR)", data: [], fill: "-1", backgroundColor: "rgba(210,153,34,0.16)", legendHidden: true, tooltip: false, borderWidth: 0, pointRadius: 0 },
    ],
    spanGaps: true,
  },
  rsi: {
    canvas: "chartRsi",
    datasets: [
      { label: "Fuerza del movimiento (RSI)", data: [], borderColor: cyan, backgroundColor: "rgba(111,221,255,0.08)", fill: true },
      { label: "Compra intensa (70)", data: [], borderColor: "rgba(241,76,76,0.5)", pointRadius: 0, borderDash: [5, 5], tooltip: false },
      { label: "Venta intensa (30)", data: [], borderColor: "rgba(38,162,105,0.5)", pointRadius: 0, borderDash: [5, 5], tooltip: false },
    ],
    spanGaps: true,
    tooltipExtra: (ctx) =>
      ctx.parsed.y >= 70
        ? "compra muy intensa: subida fuerte, probable corrección"
        : ctx.parsed.y <= 30
          ? "venta muy intensa: caída fuerte, probable rebote"
          : "zona normal, sin extremos",
  },
  macd: {
    canvas: "chartMacd",
    datasets: [
      { type: "bar", label: "Impulso (barras)", data: [], backgroundColor: [], borderColor: [] },
      { label: "Línea de referencia", data: [], borderColor: yellow, backgroundColor: yellow, fill: false },
    ],
    spanGaps: true,
    tooltipExtra: (ctx) =>
      ctx.dataset.type === "bar"
        ? (ctx.parsed.y >= 0 ? "impulso alcista" : "impulso bajista")
        : "línea de referencia del impulso",
  },
  volume: {
    canvas: "chartVolume",
    datasets: [{ type: "bar", label: "Volumen", data: [], backgroundColor: [], borderColor: [] }],
    spanGaps: true,
    tooltipExtra: (ctx) => (ctx.parsed.y >= 0 ? "acciones negociadas" : "acciones negociadas"),
  },
  returns: {
    canvas: "chartReturns",
    datasets: [{ type: "bar", label: "Frecuencia", data: [], backgroundColor: "rgba(88,166,255,0.75)", borderColor: accent }],
    spanGaps: true,
    tooltipExtra: (ctx) => `retornos entre ${ctx.parsed.x}% y ${ctx.parsed.x + 1}%`,
  },
  forecast: {
    canvas: "chartForecast",
    datasets: [
      { label: "Límite inferior", data: [], legendHidden: true, tooltip: false, borderWidth: 0, pointRadius: 0 },
      { label: "Cono de incertidumbre", data: [], fill: "-1", backgroundColor: "rgba(210,153,34,0.18)", legendHidden: true, tooltip: false, borderWidth: 0, pointRadius: 0 },
      { label: "Pronóstico ARIMA (5 días)", data: [], borderColor: cyan, borderDash: [6, 4], pointRadius: 3, backgroundColor: cyan, tooltipExtra: () => "precio proyectado por el modelo ARIMA" },
      { label: "Precio histórico", data: [], borderColor: accent, pointRadius: 0 },
    ],
    spanGaps: true,
  },
  backtest: {
    canvas: "chartBacktest",
    datasets: [
      { label: "Con la estrategia", data: [], borderColor: accent, backgroundColor: "rgba(88,166,255,0.08)", fill: true },
      { label: "Mantenerse sin operar", data: [], borderColor: yellow, backgroundColor: yellow },
    ],
    spanGaps: true,
    tooltipExtra: (ctx) =>
      ctx.dataset.label.startsWith("Con la estrategia")
        ? "evolución de S/1.00 aplicando la estrategia"
        : "evolución de S/1.00 sin operar",
  },
  forecastOnly: null,
};

function initCharts() {
  Object.values(chartDefs).filter(Boolean).forEach((def) => {
    const canvas = byId(def.canvas);
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    const datasets = def.datasets.map((d) => ({
      ...d,
      pointRadius: d.pointRadius === 0 || d.tooltip === false ? 0 : 3,
      pointHoverRadius: d.tooltip === false ? 0 : 5,
      pointBackgroundColor: d.borderColor,
      pointBorderColor: d.borderColor,
      fill: d.fill === true ? "origin" : d.fill,
    }));
    charts[def.canvas] = new Chart(ctx, {
      type: "line",
      data: { labels: [], datasets },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        spanGaps: def.spanGaps,
        interaction: { mode: "index", intersect: false },
        plugins: {
          legend: {
            display: def.legendHidden ? false : true,
            labels: {
              usePointStyle: true,
              boxWidth: 8,
              font: { size: 11 },
              filter: (item, data) => !data.datasets[item.datasetIndex].legendHidden,
            },
          },
          tooltip: { callbacks: { title: tooltipTitle, label: tooltipLabel } },
        },
        scales: {
          x: { ticks: { maxTicksLimit: 10, font: { size: 10 } }, grid: { display: false } },
          y: { ticks: { font: { size: 10 } }, grid: { color: "rgba(140,160,190,0.1)" } },
        },
        elements: {
          point: { radius: 0 },
          line: { borderWidth: 1.8, tension: 0.3 },
          bar: { borderRadius: 2 },
        },
      },
    });
  });
}

function updateChart(key, labels, datasetsData) {
  const chart = charts[chartDefs[key]?.canvas];
  if (!chart) return;
  chart.data.labels = labels;
  chartDefs[key].datasets.forEach((def, i) => {
    chart.data.datasets[i].data = datasetsData[i] || [];
    if (def.type === "bar") {
      chart.data.datasets[i].backgroundColor = datasetsData[i].map((v) => (v >= 0 ? up : down));
      chart.data.datasets[i].borderColor = datasetsData[i].map((v) => (v >= 0 ? up : down));
    }
  });
  chart.update();
}

async function apiGet(path) {
  const response = await fetch(path, { headers: { Accept: "application/json" } });
  return _parse(response);
}

async function _parse(response) {
  const text = await response.text();
  if (!response.ok) {
    let detail = text.slice(0, 200);
    try {
      const body = JSON.parse(text);
      detail = body.detail?.mensaje || body.detail || text.slice(0, 200);
    } catch (_) {}
    throw new Error(`HTTP ${response.status}: ${detail}`);
  }
  return JSON.parse(text);
}

function esc(value) {
  return String(value ?? "").replace(/[&<>"']/g, (c) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
  })[c]);
}

function fmt(value, digits = 2) {
  if (value === null || value === undefined || Number.isNaN(+value)) return "--";
  return Number(value).toLocaleString("en-US", { minimumFractionDigits: digits, maximumFractionDigits: digits });
}

function pct(value, digits = 2) {
  if (value === null || value === undefined || Number.isNaN(+value)) return "--";
  const v = Number(value);
  return `${v >= 0 ? "+" : ""}${v.toFixed(digits)}%`;
}

function pointRadius(ctx) {
  const arr = ctx.dataset.data;
  return ctx.dataIndex === arr.length - 1 && ctx.chart.canvas.id !== "chartMacd" ? 4 : 0;
}

function tooltipTitle(items) {
  return items.length ? String(items[0].label) : "";
}

function tooltipLabel(ctx) {
  const def = Object.values(chartDefs).find((d) => d && d.canvas === ctx.chart.canvas.id);
  if (def && def.tooltip === false) return null;
  const extra = def?.tooltipExtra ? def.tooltipExtra(ctx) : "";
  return `${ctx.dataset.label}: ${fmt(ctx.parsed.y)}${extra ? ` — ${extra}` : ""}`;
}

const rsiBandsPlugin = {
  id: "rsiBands",
  afterDatasetsDraw(chart) {
    if (chart.canvas.id !== "chartRsi") return;
    const area = chart.chartArea;
    const y70 = chart.scales.y.getPixelForValue(70);
    const y30 = chart.scales.y.getPixelForValue(30);
    const ctx = chart.ctx;
    ctx.save();
    ctx.fillStyle = "rgba(241,76,76,0.06)";
    ctx.fillRect(area.left, area.top, area.width, Math.max(0, y70 - area.top));
    ctx.fillStyle = "rgba(38,162,105,0.06)";
    ctx.fillRect(area.left, y30, area.width, Math.max(0, area.bottom - y30));
    ctx.restore();
  },
};
Chart.register(rsiBandsPlugin);

/* ---------------- Pestañas ---------------- */

function switchTab(name) {
  document.querySelectorAll(".tab").forEach((btn) => btn.classList.toggle("active", btn.dataset.tab === name));
  document.querySelectorAll(".tab-panel").forEach((panel) => panel.classList.toggle("active", panel.dataset.panel === name));
  Object.values(charts).forEach((c) => c.update());
}

function bindTabs() {
  document.querySelectorAll(".tab").forEach((btn) => {
    btn.addEventListener("click", () => switchTab(btn.dataset.tab));
  });
}

/* ---------------- KPIs ---------------- */

function kpiCard(label, value, sub = "", cls = "") {
  return `<div class="kpi"><div class="label">${esc(label)}</div><div class="value ${cls}">${value}</div>${sub ? `<div class="sub">${esc(sub)}</div>` : ""}</div>`;
}

/* ---------------- Consejos por gráfico ---------------- */

const adviceColor = { Apto: "ok", "Precaución": "warn", "No invertir": "danger" };

function adviceHtml(advice) {
  if (!advice) return "";
  const cls = adviceColor[advice.recomendacion] || "warn";
  return `
    <div class="advice-card ${cls}">
      <div class="advice-top"><span class="advice-badge ${cls}">${esc(advice.recomendacion)}</span></div>
      <p>${esc(advice.descripcion)}</p>
      ${advice.advertencia ? `<p class="advice-warn-text"><b>Recomendación:</b> ${esc(advice.advertencia)}</p>` : ""}
    </div>`;
}

function renderAdvice(id, advice) {
  const el = byId(id);
  if (el) el.innerHTML = adviceHtml(advice);
}

/* ---------------- Etiquetas amigables ---------------- */

function sigLabel(d) {
  return d === "BUY" ? "Compra" : d === "SELL" ? "Venta" : "Mantener";
}

function prediccionLabel(p) {
  if (p === "ALCISTA") return "Alcista";
  if (p === "BAJISTA") return "Bajista";
  if (p === "NEUTRAL") return "Sin dirección clara";
  return p;
}

function sentimientoLabel(code) {
  return { POS: "Positivo", NEU: "Neutral", NEG: "Negativo" }[code] || code;
}

/* ---------------- Screener (selección de empresa) ---------------- */

const COMPANIES = [
  { t: "SPY", n: "S&P 500 ETN" },
  { t: "AAPL", n: "Apple" },
  { t: "NVDA", n: "NVIDIA" },
  { t: "MSFT", n: "Microsoft" },
  { t: "AMZN", n: "Amazon" },
  { t: "TSLA", n: "Tesla" },
  { t: "GOOGL", n: "Alphabet (Google)" },
  { t: "META", n: "Meta" },
];
const SCREENER = COMPANIES;

function fillCompanySelects() {
  const options = COMPANIES.map((c) => `<option value="${c.t}">${c.n} (${c.t})</option>`).join("");
  const top = byId("ticker");
  if (top) top.innerHTML = options;
}

/* ---------------- Velas japonesas ---------------- */

let candleState = null;

function _roundRect(ctx, x, y, w, h, r) {
  const rr = Math.max(0, Math.min(r, w / 2, h / 2));
  ctx.beginPath();
  if (typeof ctx.roundRect === "function") {
    ctx.roundRect(x, y, w, h, rr);
  } else {
    ctx.rect(x, y, w, h);
  }
}

function renderCandlestick(dates, opens, highs, lows, closes) {
  const canvas = byId("chartCandle");
  if (!canvas || !canvas.parentNode) return;
  const dpr = window.devicePixelRatio || 1;
  const rect = canvas.parentNode.getBoundingClientRect();
  const w = rect.width || 600;
  const h = rect.height || 320;
  canvas.width = w * dpr;
  canvas.height = h * dpr;
  canvas.style.width = `${w}px`;
  canvas.style.height = `${h}px`;
  const ctx = canvas.getContext("2d");
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

  const n = Math.min(dates.length, 80);
  const start = dates.length - n;
  const candles = [];
  let minP = Infinity;
  let maxP = -Infinity;
  for (let i = start; i < dates.length; i++) {
    const o = opens[i], hh = highs[i], l = lows[i], c = closes[i];
    if (o == null || hh == null || l == null || c == null) continue;
    candles.push({ date: dates[i], open: o, high: hh, low: l, close: c });
    minP = Math.min(minP, l);
    maxP = Math.max(maxP, hh);
  }
  if (!candles.length) {
    ctx.fillStyle = "#8b949e";
    ctx.font = "13px Segoe UI";
    ctx.fillText("Sin datos OHLC disponibles.", 16, 24);
    candleState = null;
    return;
  }

  const padL = 56, padR = 12, padT = 16, padB = 24;
  const plotW = w - padL - padR;
  const plotH = h - padT - padB;
  const range = maxP - minP || 1;
  const slot = plotW / candles.length;
  const bodyW = Math.max(2, Math.min(14, slot * 0.6));

  candleState = { canvas, dpr, w, h, candles, minP, maxP, range, padL, padR, padT, padB, plotH, slot, bodyW };

  drawCandleBase(null, null);
  if (!canvas._candleBound) {
    canvas._candleBound = true;
    canvas.addEventListener("mousemove", (e) => {
      const r = canvas.getBoundingClientRect();
      drawCandleBase(e.clientX - r.left, e.clientY - r.top);
    });
    canvas.addEventListener("mouseleave", () => drawCandleBase(null, null));
    window.addEventListener("resize", () => {
      if (candleState && candleState._data) {
        const d = candleState._data;
        renderCandlestick(d.dates, d.opens, d.highs, d.lows, d.closes);
      }
    });
  }
  candleState._data = { dates, opens, highs, lows, closes };
}

function _scale(s) {
  return (p) => s.padT + s.plotH - ((p - s.minP) / s.range) * s.plotH;
}

function drawCandleBase(mx, my) {
  const s = candleState;
  if (!s) return;
  const { canvas, dpr, w, h, candles, minP, maxP, range, padL, padR, padT, padB, plotH, slot, bodyW } = s;
  const ctx = canvas.getContext("2d");
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.clearRect(0, 0, w, h);
  const yy = _scale(s);

  ctx.strokeStyle = "rgba(140,160,190,0.12)";
  ctx.fillStyle = "#8b949e";
  ctx.font = "10px Segoe UI";
  ctx.textBaseline = "alphabetic";
  for (let g = 0; g <= 4; g++) {
    const gy = padT + (plotH / 4) * g;
    ctx.beginPath();
    ctx.moveTo(padL, gy);
    ctx.lineTo(w - padR, gy);
    ctx.stroke();
    ctx.fillText((maxP - (range / 4) * g).toFixed(2), 4, gy + 3);
  }

  let hoverIdx = null;
  if (mx != null) {
    const idx = Math.floor((mx - padL) / slot);
    if (idx >= 0 && idx < candles.length) hoverIdx = idx;
  }

  candles.forEach((c, idx) => {
    const cx = padL + slot * idx + slot / 2;
    const bullish = c.close >= c.open;
    const color = bullish ? up : down;
    ctx.strokeStyle = color;
    ctx.globalAlpha = idx === hoverIdx ? 1 : 0.55;
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(cx, yy(c.high));
    ctx.lineTo(cx, yy(c.low));
    ctx.stroke();
    const yo = yy(c.open);
    const yc = yy(c.close);
    const top = Math.min(yo, yc);
    const bh = Math.max(2, Math.abs(yc - yo));
    ctx.globalAlpha = idx === hoverIdx ? 1 : 0.9;
    ctx.fillStyle = color;
    _roundRect(ctx, cx - bodyW / 2, top, bodyW, bh, 2);
    ctx.fill();
    ctx.globalAlpha = 1;
  });

  if (hoverIdx != null) {
    const cx = padL + slot * hoverIdx + slot / 2;
    ctx.strokeStyle = "rgba(230,237,243,0.35)";
    ctx.setLineDash([4, 4]);
    ctx.beginPath();
    ctx.moveTo(cx, padT);
    ctx.lineTo(cx, padT + plotH);
    ctx.stroke();
    ctx.setLineDash([]);

    const lastC = candles[candles.length - 1];
    ctx.fillStyle = "#e6edf3";
    ctx.font = "11px Segoe UI";
    ctx.fillText(
      String(lastC.close.toFixed(2)),
      padL + slot * (candles.length - 1) + slot / 2 - bodyW / 2,
      yy(lastC.close) - 6
    );

    if (mx != null && my != null) drawCandleTooltip(ctx, mx, my, candles[hoverIdx]);
  }
}

function drawCandleTooltip(ctx, mx, my, c) {
  const s = candleState;
  const bullish = c.close >= c.open;
  const rows = [
    [c.date, "#8b949e"],
    [`Apertura: ${c.open.toFixed(2)}`, "#e6edf3"],
    [`Máximo: ${c.high.toFixed(2)}`, "#e6edf3"],
    [`Mínimo: ${c.low.toFixed(2)}`, "#e6edf3"],
    [`Cierre: ${c.close.toFixed(2)}`, bullish ? up : down],
    [bullish ? "La vela subió (verde)" : "La vela bajó (rojo)", bullish ? up : down],
  ];
  ctx.font = "12px Segoe UI";
  const padX = 10, padY = 8, lineH = 15;
  const tw = Math.max(...rows.map(([t]) => ctx.measureText(t).width)) + padX * 2;
  const th = rows.length * lineH + padY * 2 - 4;
  let bx = mx + 14;
  let by = my - th - 10;
  if (bx + tw > s.w - 8) bx = mx - tw - 14;
  if (by < 8) by = my + 14;
  ctx.fillStyle = "rgba(13,17,23,0.95)";
  ctx.strokeStyle = "#30363d";
  _roundRect(ctx, bx, by, tw, th, 6);
  ctx.fill();
  ctx.stroke();
  ctx.textBaseline = "top";
  rows.forEach(([txt, color], i) => {
    ctx.fillStyle = color;
    ctx.fillText(txt, bx + padX, by + padY + i * lineH);
  });
  ctx.textBaseline = "alphabetic";
}

/* ================= VISTA 1 · DESCRIPTIVA ================= */

function renderDescriptiva(ind, screenerData) {
  const ult = ind.ultimo;
  const s = ind.series;
  const upCls = ult.change_pct >= 0 ? "up" : "down";
  const rsiNote = ult.rsi14 >= 70 ? "Compra muy intensa" : ult.rsi14 <= 35 ? "Venta muy intensa" : "Zona normal";
  const kpi = byId("kpisDescr");
  kpi.innerHTML =
    kpiCard("Precio", fmt(ult.close), ult.date || "", upCls) +
    kpiCard("Variación diaria", pct(ult.change_pct), "", upCls) +
    kpiCard("Fuerza (RSI)", fmt(ult.rsi14, 1), rsiNote) +
    kpiCard("Volatilidad (ATR)", fmt(ult.atr14)) +
    kpiCard("Volumen", fmt(ult.volume, 0)) +
    kpiCard("Media 20/50", `${fmt(ult.sma20)} / ${fmt(ult.sma50)}`) +
    kpiCard("Proveedor", ind.meta?.proveedor || "--", ind.meta?.ultima_fecha || "--");

  renderMarketBoard(screenerData);

  const lower = s.close.map((_, i) => (s.atr14[i] != null && s.close[i] != null ? s.close[i] - s.atr14[i] : null));
  const upper = s.close.map((_, i) => (s.atr14[i] != null && s.close[i] != null ? s.close[i] + s.atr14[i] : null));
  updateChart("price", s.dates, [s.close, s.sma20, s.sma50, lower, upper]);
  updateChart("rsi", s.dates, [s.rsi14, s.rsi14.map(() => 70), s.rsi14.map(() => 30)]);
  updateChart("macd", s.dates, [s.macd_hist, s.macd_signal]);
  updateChart("volume", s.dates, [s.volume]);

  const hist = returnsHistogram(s.close);
  updateChart("returns", hist.labels, [hist.counts]);

  renderCandlestick(s.dates, s.open, s.high, s.low, s.close);

  renderAdvice("advicePrecio", ind.asesoria?.precio);
  renderAdvice("advicePrecioCandle", ind.asesoria?.precio);
  renderAdvice("adviceRsi", ind.asesoria?.rsi);
  renderAdvice("adviceMacd", ind.asesoria?.macd);
}

function renderMarketBoard(screenerData) {
  const box = byId("marketBoard");
  if (!box) return;
  const list = screenerData?.companies || [];
  if (!list.length) {
    box.innerHTML = '<p style="color: var(--muted);">Tablero no disponible.</p>';
    return;
  }
  box.innerHTML = list
    .map((c) => {
      const err = c.error ? '<div class="m-err">error</div>' : "";
      const upCls = (c.change_pct || 0) >= 0 ? "up" : "down";
      const sigCls = c.senal ? `sig-${c.senal.toLowerCase()}` : "";
      return `
      <div class="m-cell ${sigCls}" title="${esc(c.nombre)}">
        <div class="m-ticker">${esc(c.ticker)}</div>
        <div class="m-price ${upCls}">${fmt(c.close)}</div>
        <div class="m-sub">${pct(c.change_pct)}</div>
        <div class="m-sub">RSI ${fmt(c.rsi14, 1)}${c.senal ? ` · ${sigLabel(c.senal)}` : ""}</div>
        ${err}
      </div>`;
    })
    .join("");
}

function returnsHistogram(closes) {
  const rets = [];
  for (let i = 1; i < closes.length; i++) {
    const a = closes[i - 1], b = closes[i];
    if (a == null || b == null || !a) continue;
    const r = ((b / a) - 1) * 100;
    if (Number.isFinite(r) && Math.abs(r) < 15) rets.push(r);
  }
  if (!rets.length) return { labels: [], counts: [] };
  const min = Math.floor(Math.min(...rets));
  const max = Math.ceil(Math.max(...rets));
  if (max - min > 18) return { labels: [], counts: [] };
  const buckets = {};
  for (let b = min; b < max; b++) buckets[b] = 0;
  rets.forEach((r) => {
    const b = Math.floor(r);
    if (buckets[b] != null) buckets[b]++;
  });
  const labels = Object.keys(buckets).map(Number).sort((a, b) => a - b);
  return { labels: labels.map((b) => `${b}%`), counts: labels.map((b) => buckets[b]) };
}

/* ================= VISTA 2 · PREDICTIVA ================= */

function renderPredictiva(fore, sig, newsData) {
  const f = fore?.forecast || {};
  const ia = sig?.analisis_ia || {};
  const ctx = sig?.contexto_tecnico || {};
  const sentTone = sig?.senal?.sentimiento_noticias || "NEUTRAL";
  const expected = (f.next_close != null && f.last_close) ? ((f.next_close / f.last_close) - 1) * 100 : null;

  const kpi = byId("kpisPred");
  kpi.innerHTML =
    kpiCard("Pronóstico 5 días", fmt(f.next_close, 4), "", expected >= 0 ? "up" : "down") +
    kpiCard("Variación esperada", pct(expected), "modelo ARIMA") +
    kpiCard("Dirección IA", prediccionLabel(ia.prediccion), `${fmt((ia.probabilidad || 0) * 100, 0)}% confianza`, sigClass("pred", ia.prediccion === "ALCISTA" ? "buy" : ia.prediccion === "BAJISTA" ? "sell" : "hold")) +
    kpiCard("Probabilidad IA", fmt((ia.probabilidad || 0) * 100, 0) + " %") +
    kpiCard("Nivel de riesgo", ia.nivel_riesgo || "--") +
    kpiCard("Sentimiento noticias", sentimientoTone(sentTone));

  renderForecast(fore, ctx.atr14);
  renderIA(sig);
  renderNews(newsData);
}

function sigClass(prefix, key) {
  return `sig-${key}`;
}

function sentimientoTone(tone) {
  const map = {
    POSITIVO: ["Positivo", up],
    LIGERAMENTE_POSITIVO: ["Levemente positivo", up],
    NEUTRAL: ["Neutral", "#8b949e"],
    LIGERAMENTE_NEGATIVO: ["Levemente negativo", down],
    NEGATIVO: ["Negativo", down],
  };
  const [label, color] = map[tone] || ["--", "#8b949e"];
  return `<span style="color:${color};">${esc(label)}</span>`;
}

function renderForecast(fore, atr) {
  const f = fore?.forecast || {};
  const box = byId("forecastChips");
  if (box) {
    if (f.forecast && f.forecast.length) {
      const chip = (v, i) => `<div class="forecast-chip"><b>${fmt(v, 4)}</b>Día ${i + 1}</div>`;
      box.innerHTML = f.forecast.map((v, i) => chip(v, i)).join("");
    } else {
      box.innerHTML = '<p style="color: var(--muted);">Pronóstico ARIMA no disponible.</p>';
    }
  }

  const chart = charts["chartForecast"];
  if (chart && f.forecast_dates && f.forecast) {
    const histDates = (state.lastSeries?.dates || []).slice(-10);
    const histClose = (state.lastSeries?.close || []).slice(-10);
    const labels = histDates.concat(f.forecast_dates.slice(0, f.forecast.length));
    const hist = histClose.map((v) => (v == null ? null : v));
    const fut = [].concat(hist.map(() => null), f.forecast);
    const atrV = atr || (state.lastAtr ?? 1);
    const lower = fut.map((v) => (v == null ? null : v - atrV));
    const upper = fut.map((v) => (v == null ? null : v + atrV));
    updateChart("forecast", labels, [lower, upper, fut, hist]);
  }

  renderAdvice("adviceArima", fore?.forecast?.asesoria);
}

function renderIA(sig) {
  const box = byId("iaBox");
  if (!box) return;
  const ia = sig?.analisis_ia || {};
  const cls = ia.prediccion === "ALCISTA" ? "sig-buy" : ia.prediccion === "BAJISTA" ? "sig-sell" : "sig-hold";
  const fuente = ia.fuente === "gemini"
    ? '<span class="badge-gemini">Gemini</span>'
    : '<span class="badge-rules">Reglas cuantitativas (sin clave de API)</span>';
  box.innerHTML = `
    <div style="display:flex; flex-wrap:wrap; gap:14px; align-items:center; margin-bottom:12px;">
      <h3 class="${cls}" style="font-size:20px; margin:0;">${esc(prediccionLabel(ia.prediccion))}</h3>
      <span class="${cls}"><b>${fmt((ia.probabilidad || 0) * 100, 0)}%</b> de probabilidad</span>
      <span>Riesgo: <b>${esc(ia.nivel_riesgo)}</b></span>
      ${fuente}
    </div>
    <h3>Conclusión cualitativa</h3>
    <p class="ai-summary">${esc(ia.conclusion_cualitativa || "")}</p>
    <h3 style="margin-top:12px;">Justificación técnica</h3>
    <p class="ai-summary">${esc(ia.justificacion_tecnica || "")}</p>`;
}

function renderNews(newsData) {
  const agg = byId("newsAgg");
  const list = byId("newsList");
  const items = newsData?.noticias || [];
  const counts = { POS: 0, NEU: 0, NEG: 0 };
  items.forEach((n) => { if (counts[n.sentimiento] != null) counts[n.sentimiento]++; });
  const total = items.length;
  const bar = (label, value, color) => `
    <div class="news-bar-row"><span>${label}</span>
      <div class="news-track"><div class="news-fill" style="width:${total ? (value / total) * 100 : 0}%; background:${color};"></div></div>
      <b>${value}</b></div>`;
  agg.innerHTML = total
    ? `<div class="metrics" style="grid-template-columns:repeat(3, minmax(90px,1fr));">
        ${bar("Positivas", counts.POS, up)}
        ${bar("Neutrales", counts.NEU, "#8b949e")}
        ${bar("Negativas", counts.NEG, down)}
       </div>`
    : '<p style="color: var(--muted);">Sin noticias aún. El ETL de GitHub Actions (cron 22:00 UTC) las cargará diariamente.</p>';

  list.innerHTML = items.length
    ? items.map((n) => {
        const cls = n.sentimiento === "POS" ? "n-pos" : n.sentimiento === "NEG" ? "n-neg" : "n-neu";
        return `
        <div class="news-item">
          <span class="news-badge ${cls}">${esc(sentimientoLabel(n.sentimiento))}</span>
          <div class="news-body">
            <a href="${esc(n.url)}" target="_blank" rel="noopener">${esc(n.titulo)}</a>
            <div class="news-meta">${esc(n.publisher || "")} · ${esc((n.fecha || "").slice(0, 10))} · ${Math.round((n.prob_pos || 0) * 100)}%+ / ${Math.round((n.prob_neu || 0) * 100)}%0 / ${Math.round((n.prob_neg || 0) * 100)}%-</div>
          </div>
        </div>`;
      }).join("")
    : "";
}

function renderCompare(forecasts, currentTicker) {
  const box = byId("compareBox");
  if (!box) return;
  const rows = forecasts
    .map((r) => {
      const f = r?.forecast || {};
      const exp = (f.next_close != null && f.last_close) ? ((f.next_close / f.last_close) - 1) * 100 : null;
      const cls = exp >= 0 ? "up" : exp < 0 ? "down" : "";
      return `
      <tr>
        <td><b>${esc(r.ticker)}</b>${r.ticker === currentTicker ? ' <span class="badge-rules">actual</span>' : ""}</td>
        <td>${fmt(f.last_close)}</td>
        <td>${fmt(f.next_close, 4)}</td>
        <td class="${cls}">${pct(exp)}</td>
        <td>${esc(f.method || "--")}</td>
        <td>${f.aic != null ? fmt(f.aic, 1) : "--"}</td>
      </tr>`;
    })
    .join("");
  box.innerHTML = `<table>
    <thead><tr><th>Empresa</th><th>Cierre</th><th>Pronóstico 5d</th><th>Var. esperada</th><th>Modelo</th><th>AIC</th></tr></thead>
    <tbody>${rows}</tbody></table>`;
}

/* ================= VISTA 3 · PRESCRIPTIVA ================= */

function renderPrescriptiva(sig, bt, ind, fore) {
  const senal = sig?.senal || {};
  const ia = sig?.analisis_ia || {};
  const ctx = sig?.contexto_tecnico || {};
  const dirCls = `sig-${senal.direccion?.toLowerCase()}`;

  const kpi = byId("kpisPres");
  kpi.innerHTML =
    kpiCard("Señal", sigLabel(senal.direccion), `${pct(ctx.change_pct)} hoy`, dirCls) +
    kpiCard("Recomendación IA", esc(senal.recomendacion_ia), (ia.probabilidad || 0) * 100 + "% confianza", dirCls) +
    kpiCard("Stop Loss", fmt(senal.stop_loss), "cierre - 1.5·ATR") +
    kpiCard("Take Profit", fmt(senal.take_profit), "cierre + 3·ATR") +
    kpiCard("Ratio R/B", fmt(senal.ratio_riesgo_beneficio), "1 : 2") +
    kpiCard("Riesgo", esc(senal.nivel_riesgo || "--"));

  const hero = byId("signalHero");
  hero.innerHTML = `
    <div class="hero-left">
      <div class="hero-signal ${dirCls}">${sigLabel(senal.direccion)}</div>
      <div class="hero-sub">${esc(sig.nombre || sig.ticker)} · ${esc(senal.direccion)}</div>
    </div>
    <div class="hero-levels">
      <div class="kpi"><div class="label">Stop Loss</div><div class="value down">${fmt(senal.stop_loss)}</div></div>
      <div class="kpi"><div class="label">Entrada</div><div class="value" style="color:var(--text);">${fmt(ctx.close)}</div></div>
      <div class="kpi"><div class="label">Take Profit</div><div class="value up">${fmt(senal.take_profit)}</div></div>
    </div>`;

  renderRecommend(senal, ia);
  renderChecklist(ctx, ia, fore, senal);
  renderMatrix(senal, ia);
  bindPosition(senal, ctx);

  renderNarracion(sig);
  renderBacktest(bt);
}

function renderRecommend(senal, ia) {
  const box = byId("recommendBox");
  if (!box) return;
  const razones = (senal.razones || []).map((r) => `<div class="reason">✓ ${esc(r)}</div>`).join("");
  const advertencias = (senal.advertencias || []).map((a) => `<div class="reason warn-text">⚠ ${esc(a)}</div>`).join("");
  box.innerHTML = `
    <div style="display:flex; flex-wrap:wrap; gap:10px; align-items:center; margin-bottom:10px;">
      <span class="rec-pill rec-${(ia.recomendacion || "MANTENER").toLowerCase()}">${esc(ia.recomendacion || "MANTENER")}</span>
      <span>Dirección: <b>${esc(prediccionLabel(ia.prediccion))}</b></span>
      <span>Probabilidad: <b>${fmt((ia.probabilidad || 0) * 100, 0)}%</b></span>
      <span>Riesgo: <b>${esc(ia.nivel_riesgo)}</b></span>
    </div>
    <p class="narracion-text">${esc(ia.conclusion_cualitativa || "")}</p>
    ${razones}
    ${advertencias}
    ${ia.justificacion_tecnica ? `<p class="ai-summary" style="color: var(--muted);">${esc(ia.justificacion_tecnica)}</p>` : ""}`;
}

function renderChecklist(ctx, ia, fore, senal) {
  const box = byId("checklistBox");
  if (!box) return;
  const items = [];
  items.push({
    label: "Precio sobre SMA50 (tendencia de mediano plazo)",
    ok: ctx.close != null && ctx.sma50 != null && ctx.close > ctx.sma50,
    detalle: ctx.sma50 != null ? `cierre ${fmt(ctx.close)} vs SMA50 ${fmt(ctx.sma50)}` : "SMA50 no disponible",
  });
  items.push({
    label: "RSI sin sobrecompra (<70)",
    ok: ctx.rsi14 != null && ctx.rsi14 < 70,
    detalle: ctx.rsi14 != null ? `RSI ${fmt(ctx.rsi14, 1)}` : "RSI no disponible",
  });
  items.push({
    label: "Probabilidad de la IA ≥ 65%",
    ok: (ia.probabilidad || 0) >= 0.65,
    detalle: `${fmt((ia.probabilidad || 0) * 100, 0)}%`,
  });
  const exp = fore?.forecast?.next_close != null && fore?.forecast?.last_close
    ? ((fore.forecast.next_close / fore.forecast.last_close) - 1) * 100 : null;
  items.push({
    label: "ARIMA proyecta dirección (var ≥ ±0.5%)",
    ok: exp != null && Math.abs(exp) >= 0.5,
    detalle: exp != null ? pct(exp) : "sin proyección",
  });
  const tone = senal.sentimiento_noticias;
  items.push({
    label: "Noticias sin sesgo claramente negativo",
    ok: tone != null && !["NEGATIVO", "LIGERAMENTE_NEGATIVO"].includes(tone),
    detalle: tone || "sin datos",
  });
  box.innerHTML = items.map((it) => `
    <div class="check-row ${it.ok ? "check-ok" : "check-no"}">
      <span class="check-mark">${it.ok ? "✓" : "✗"}</span>
      <span class="check-label">${esc(it.label)}</span>
      <span class="check-det">${esc(it.detalle)}</span>
    </div>`).join("");
}

function renderMatrix(senal, ia) {
  const box = byId("matrixBox");
  if (!box) return;
  const rows = ["BUY", "HOLD", "SELL"];
  const cols = ["AUMENTAR", "MANTENER", "RETIRAR"];
  const cell = (s, r) => {
    let cls = "mz-neu";
    if (s === "BUY" && r === "AUMENTAR") cls = "mz-buy";
    else if (s === "BUY" && r === "RETIRAR") cls = "mz-conflict";
    else if (s === "SELL" && r === "RETIRAR") cls = "mz-sell";
    else if (s === "SELL" && r === "AUMENTAR") cls = "mz-conflict";
    else if (r === "AUMENTAR") cls = "mz-mild-up";
    else if (r === "RETIRAR") cls = "mz-mild-down";
    else cls = "mz-neu";
    return `<td class="${cls}">${cellLabel(s, r)}</td>`;
  };
  const cellLabel = (s, r) => {
    if (s === "BUY" && r === "AUMENTAR") return "Comprar fuerte";
    if (s === "SELL" && r === "RETIRAR") return "Salir / vender";
    if ((s === "BUY" && r === "RETIRAR") || (s === "SELL" && r === "AUMENTAR")) return "Conflicto";
    if (s === "HOLD") return "Esperar confirmación";
    if (r === "MANTENER") return "Mantener bajo control";
    return "Cautela";
  };
  const highlight = (s, r) => (senal.direccion === s && ia.recomendacion === r) ? " mz-current" : "";
  box.innerHTML = `
    <table class="matrix">
      <thead><tr><th>Señal \\ IA</th>${cols.map((c) => `<th>${esc(c)}</th>`).join("")}</tr></thead>
      <tbody>
        ${rows.map((s) => `<tr><td><b>${esc(sigLabel(s))}</b></td>${cols.map((r) => `<td class="${cellCls(s, r)}${highlight(s, r)}">${cellLabel(s, r)}</td>`).join("")}</tr>`).join("")}
      </tbody>
    </table>
    <p class="hint">La celda resaltada es la combinación actual: <b>${esc(sigLabel(senal.direccion))} × ${esc(ia.recomendacion)}</b>.</p>`;
}

function cellCls(s, r) {
  if (s === "BUY" && r === "AUMENTAR") return "mz-buy";
  if (s === "SELL" && r === "RETIRAR") return "mz-sell";
  if ((s === "BUY" && r === "RETIRAR") || (s === "SELL" && r === "AUMENTAR")) return "mz-conflict";
  if (r === "AUMENTAR") return "mz-mild-up";
  if (r === "RETIRAR") return "mz-mild-down";
  return "mz-neu";
}

function bindPosition(senal, ctx) {
  const box = byId("positionBox");
  if (!box) return;
  const input = byId("capitalInput");
  const render = () => {
    const capital = Number(input?.value || 10000);
    const close = ctx.close;
    const sl = senal.stop_loss;
    const riskPct = 1.0;
    if (close == null || sl == null || sl >= close) {
      if (close == null || sl == null) {
        box.innerHTML = '<p style="color: var(--muted);">Sin niveles SL/cierre para dimensionar.</p>';
        return;
      }
      box.innerHTML = '<p style="color: var(--muted);">El Stop Loss es mayor que el precio (señal de venta): no se dimensiona compra.</p>';
      return;
    }
    const riskAmount = (capital * riskPct) / 100;
    const distance = close - sl;
    const units = Math.floor(riskAmount / distance);
    const needed = units * close;
    box.innerHTML = `
      <div class="metrics">
        <div class="kpi"><div class="label">Capital</div><div class="value">S/ ${fmt(capital, 0)}</div></div>
        <div class="kpi"><div class="label">Riesgo a asumir</div><div class="value down">S/ ${fmt(riskAmount, 2)}</div></div>
        <div class="kpi"><div class="label">Distancia al SL</div><div class="value">${fmt(distance)}</div></div>
        <div class="kpi"><div class="label">Unidades</div><div class="value">${fmt(units, 0)}</div></div>
        <div class="kpi"><div class="label">Monto (S/ ${fmt(close)})</div><div class="value">S/ ${fmt(needed, 0)}</div></div>
      </div>
      <p class="hint">Solo compra: se arriesga el <b>1% del capital</b> en la distancia al Stop Loss. No es recomendación de compra.</p>`;
  };
  render();
  if (!input.dataset.bound) {
    input.addEventListener("input", render);
    input.dataset.bound = "1";
  }
}

function renderNarracion(data) {
  const box = byId("narracionBox");
  if (!box) return;
  const narracion = data?.narracion;
  if (!narracion || !narracion.parrafo) {
    box.innerHTML = '<p style="color: var(--muted);">Interpretación no disponible.</p>';
    return;
  }
  const bullets = (narracion.bullets || []).map((b) => `<li>${esc(b)}</li>`).join("");
  const etiqueta = narracion.fuente === "gemini"
    ? '<span class="badge-gemini">Enriquecida por Gemini</span>'
    : '<span class="badge-rules">Generada por reglas</span>';
  box.innerHTML = `
    <div style="display:flex; align-items:center; gap:10px; flex-wrap:wrap; margin-bottom:8px;">
      <h3 style="margin:0;">${esc(data?.nombre || data?.ticker)}</h3> ${etiqueta}
    </div>
    <p class="narracion-text">${esc(narracion.parrafo)}</p>
    ${bullets ? `<ul class="narracion-bullets">${bullets}</ul>` : ""}`;
}

function renderBacktest(bt) {
  const metrics = byId("btMetrics");
  const trades = byId("btTrades");
  if (!metrics || !trades) return;
  if (!bt || !bt.disponible) {
    metrics.innerHTML = `<p style="color: var(--muted);">${esc(bt?.mensaje || "Backtest no disponible.")}</p>`;
    trades.innerHTML = "";
    updateChart("backtest", [], [[], []]);
    renderAdvice("adviceBacktest", bt?.asesoria || null);
    return;
  }
  const card = (label, value, cls = "") =>
    `<div class="kpi"><div class="label">${esc(label)}</div><div class="value ${cls}">${value}</div></div>`;
  metrics.innerHTML =
    card("Acierto de la estrategia", `${(bt.win_rate * 100).toFixed(1)} %`) +
    card("Operaciones simuladas", bt.n_trades) +
    card("Ganancia de la estrategia", `${bt.total_return_pct} %`, bt.total_return_pct >= 0 ? "up" : "down") +
    card("Mantenerse sin operar", `${bt.buy_hold_return_pct} %`, bt.buy_hold_return_pct >= 0 ? "up" : "down") +
    card("Caída máxima", `${bt.max_drawdown_pct} %`, "down") +
    card("Rendimiento por riesgo", fmt(bt.sharpe_ratio));

  if (bt.curva && bt.curva.dates && bt.curva.dates.length) {
    updateChart("backtest", bt.curva.dates, [bt.curva.estrategia, bt.curva.buy_hold]);
  } else {
    updateChart("backtest", [], [[], []]);
  }

  renderAdvice("adviceBacktest", bt?.asesoria || null);

  if (!bt.trades || !bt.trades.length) {
    trades.innerHTML = '<p style="color: var(--muted); padding: 8px;">Sin operaciones en la ventana de prueba.</p>';
    return;
  }
  const rows = bt.trades
    .map(
      (t) => `<tr>
        <td>${t.entrada}</td><td>${t.salida}</td>
        <td class="${t.resultado >= 0 ? "up" : "down"}">${(t.resultado * 100).toFixed(2)} %</td>
        <td>${esc(t.razon_salida)}</td><td>${t.barras}</td>
      </tr>`
    )
    .join("");
  trades.innerHTML = `<table>
    <thead><tr><th>Entrada</th><th>Salida</th><th>Resultado</th><th>Motivo de salida</th><th>Días</th></tr></thead>
    <tbody>${rows}</tbody></table>`;
}

/* ---------------- Análisis principal ---------------- */

async function run() {
  const ticker = byId("ticker")?.value.trim().toUpperCase() || "SPY";
  const period = byId("period")?.value || "6mo";
  const btn = byId("runBtn");
  const t = encodeURIComponent(ticker);
  const p = encodeURIComponent(period);

  if (btn) btn.disabled = true;
  setStatus("Recopilando datos y calculando señales...");
  hideError();

  try {
    const [ind, screenerData, sig, fore, newsData, bt] = await Promise.all([
      apiGet(`/api/indicators?ticker=${t}&period=${p}`),
      apiGet(`/api/screener?tickers=${SCREENER.map((c) => c.t).join(",")}&period=${p}`),
      apiGet(`/api/signal?ticker=${t}&period=${p}`),
      apiGet(`/api/forecast?ticker=${t}&period=${p}`),
      apiGet(`/api/news?ticker=${t}`),
      apiGet(`/api/backtest?ticker=${t}`),
    ]);

    const compares = await Promise.all(
      SCREENER.map((c) =>
        c.t === ticker ? Promise.resolve(fore) : apiGet(`/api/forecast?ticker=${c.t}&period=6mo`)
      )
    );

    state.lastSeries = ind.series;
    state.lastAtr = ind.ultimo?.atr14;

    renderDescriptiva(ind, screenerData);
    renderPredictiva(fore, sig, newsData);
    renderPrescriptiva(sig, bt, ind, fore);
    renderCompare(compares, ticker);

    document.querySelector("header h1 .light").textContent = `· ${sig.nombre || ticker}`;
    setStatus(`Listo · ${ticker} · ${new Date().toLocaleTimeString()}`);
  } catch (err) {
    showError(err.message);
    setStatus("Error");
  } finally {
    if (btn) btn.disabled = false;
  }
}

/* ---------------- Estado / errores ---------------- */

function setStatus(text) {
  const el = byId("status");
  if (el) el.textContent = text;
}

function showError(message) {
  const el = byId("errorBox");
  if (el) {
    el.textContent = `Error: ${message}`;
    el.classList.remove("hidden");
  }
}

function hideError() {
  const el = byId("errorBox");
  if (el) el.classList.add("hidden");
}

/* ---------------- Metodología (footer) ---------------- */

const TDSP_PHASES = [
  {
    fase: "Fase 1 · Comprensión del negocio",
    detalle: "Definición de objetivos analíticos, reglas de Swing Trading (posiciones de 3 a 10 ruedas bursátiles), horizonte temporal y dimensionamiento del riesgo.",
    entregable: "Especificación de alcance y reglas operativas.",
  },
  {
    fase: "Fase 2 · Adquisición y comprensión de datos",
    detalle: "Extracción de series OHLCV y titulares de noticias mediante yfinance dentro del ETL en GitHub Actions. Verificación de integridad, calidad y limpieza temporal.",
    entregable: "Tablas en Supabase: ohlcv, news, forecast_snapshots.",
  },
  {
    fase: "Fase 3 · Modelado",
    detalle: "Ingeniería de características (SMA, RSI, MACD, ATR), calibración del benchmark ARIMA(p,d,q), entrenamiento del modelo de sentimiento (TF-IDF + Regresión Logística) y lectura cualitativa con Gemini Flash.",
    entregable: "Modelo de sentimiento + pronósticos econométricos + contratos JSON validados.",
  },
  {
    fase: "Fase 4 · Despliegue",
    detalle: "Motor de señales con Stop-Loss y Take-Profit, simulación histórica (backtesting) y panel de 3 vistas (Descriptiva, Predictiva, Prescriptiva).",
    entregable: "Dashboard desplegado en Vercel (costo S/ 0.00) con datos persistentes en Supabase.",
  },
  {
    fase: "Fase 5 · Aceptación del cliente",
    detalle: "Validación de Win Rate, retorno frente a ARIMA y frente a Buy & Hold; verificación del cumplimiento de las especificaciones operativas.",
    entregable: "Informe final y presentación ejecutiva.",
  },
];

const PIPELINE_STEPS = [
  { paso: "1", titulo: "Disparo", texto: "GitHub Actions: cron 22:00 UTC, manual o push a main." },
  { paso: "2", titulo: "Entrenamiento ML", texto: "TF-IDF + Regresión Logística sobre 12 mil+ titulares financieros (sentimiento)." },
  { paso: "3", titulo: "ETL", texto: "OHLCV + indicadores, ARIMA 5 días y noticias clasificadas → Supabase." },
  { paso: "4", titulo: "API y decisión", texto: "Vercel lee Supabase; Gemini aporta lectura cualitativa; reglas emiten señal." },
  { paso: "5", titulo: "Panel 3 vistas", texto: "Descriptiva, Predictiva y Prescriptiva con Chart.js." },
];

const CHAIN_VALUES = ["Dato crudo", "Información", "Modelado dual", "Señal filtrada", "Decisión informada"];

const V_LAYOUT = [
  { letra: "Volumen", texto: "Series OHLCV históricas, titulares de noticias y snapshots de pronóstico (filas por día por ticker)." },
  { letra: "Velocidad", texto: "Procesamiento en lotes diario al cierre del mercado (cron en la nube), acorde al ciclo del Swing Trading." },
  { letra: "Variedad", texto: "Datos numéricos continuos (OHLCV), texto de noticias y salidas estructuradas JSON del modelo y de la IA." },
];

const TOOLS = [
  ["yfinance", "Cotizaciones OHLCV + titulares"],
  ["Python · Pandas · NumPy", "Limpieza e indicadores"],
  ["statsmodels ARIMA", "Pronóstico econométrico"],
  ["scikit-learn", "Sentimiento de noticias (ML clásico)"],
  ["Gemini Flash API", "Análisis cualitativo"],
  ["Supabase Postgres", "Almacenamiento en la nube"],
  ["GitHub Actions", "ETL y entrenamiento programados"],
  ["Vercel", "Hosting serverless + CDN"],
  ["Chart.js + HTML/JS", "Panel interactivo 3 vistas"],
];

const ETHIC_TEXT =
  "Prototipo académico de investigación analítica. No cuenta con pasarelas a brokers, no ejecuta órdenes con dinero real " +
  "ni constituye asesoría de inversión personalizada. Las señales son simulaciones cuantitativas de apoyo al juicio de un analista humano.";

function renderMetodologia() {
  const stepper = byId("tdspStepper");
  if (stepper) {
    stepper.innerHTML = `
      <div class="stepper-nav">
        ${TDSP_PHASES.map((p, i) => `<button class="step-btn ${i === 0 ? "active" : ""}" data-step="${i}">${i + 1}</button>`).join("")}
      </div>
      <div class="stepper-body"></div>
      <div class="stepper-controls">
        <button class="step-prev" disabled>← Anterior</button>
        <button class="step-next">Siguiente →</button>
      </div>`;

    let current = 0;
    const body = stepper.querySelector(".stepper-body");
    const btns = stepper.querySelectorAll(".step-btn");
    const prev = stepper.querySelector(".step-prev");
    const next = stepper.querySelector(".step-next");

    const render = () => {
      const p = TDSP_PHASES[current];
      body.innerHTML = `
        <h3>${esc(p.fase)}</h3>
        <p>${esc(p.detalle)}</p>
        <div class="deliverable"><b>Entregable:</b> ${esc(p.entregable)}</div>`;
      btns.forEach((b, i) => b.classList.toggle("active", i === current));
      prev.disabled = current === 0;
      next.textContent = current === TDSP_PHASES.length - 1 ? "Finalizar ✓" : "Siguiente →";
    };
    btns.forEach((b) => b.addEventListener("click", () => { current = +b.dataset.step; render(); }));
    prev.addEventListener("click", () => { if (current > 0) { current--; render(); } });
    next.addEventListener("click", () => { if (current < TDSP_PHASES.length - 1) { current++; render(); } });
    render();
  }

  const flow = byId("pipelineFlow");
  if (flow) {
    flow.innerHTML = PIPELINE_STEPS.map(
      (s) => `
      <div class="pipe-step">
        <div class="pipe-num">${s.paso}</div>
        <div><b>${esc(s.titulo)}</b><div class="hint">${esc(s.texto)}</div></div>
      </div>`
    ).join('<div class="pipe-arrow">→</div>');
  }

  const chain = byId("chainFlow");
  if (chain) {
    chain.innerHTML = CHAIN_VALUES.map((c) => `<div class="chain-node">${esc(c)}</div>`).join('<div class="chain-arrow">→</div>');
  }

  const vs = byId("vsBox");
  if (vs) {
    vs.innerHTML = V_LAYOUT.map((v) => `
      <div class="vs-card">
        <div class="vs-letter">${esc(v.letra[0])}</div>
        <div><b>${esc(v.letra)}</b><p class="hint">${esc(v.texto)}</p></div>
      </div>`).join("");
  }

  const tools = byId("toolsBox");
  if (tools) {
    tools.innerHTML = TOOLS.map(([h, d]) => `<div class="tool-item"><b>${esc(h)}</b><span class="hint">${esc(d)}</span></div>`).join("");
  }

  const ethic = byId("ethicBox");
  if (ethic) ethic.textContent = ETHIC_TEXT;
}

/* ---------------- Diccionario (footer) ---------------- */

const GLOSSARY = [
  {
    grupo: "Conceptos de Swing Trading",
    items: [
      ["Swing Trading", "Estilo de inversión en el que se mantiene una posición de 3 a 10 días hábiles, buscando capturar movimientos de mediana duración en lugar de segundos o años."],
      ["Vela (OHLC)", "Representación gráfica de un día: la línea vertical va del máximo al mínimo, y el cuerpo va del precio de apertura (Open) al de cierre (Close)."],
      ["Tendencia", "Dirección general del precio: sube (alcista), baja (bajista) o se mueve de lado (lateral)."],
      ["Buy & Hold", "Estrategia pasiva: comprar y mantener el activo sin operar. Se usa como referencia para comparar si la estrategia activa vale la pena."],
      ["Volatilidad", "Tamaño de los movimientos del precio. Más volatilidad = más riesgo y más oportunidad."],
      ["Benchmark", "Modelo o referencia de comparación (aquí, ARIMA) para saber si el sistema predice mejor que lo básico."],
    ],
  },
  {
    grupo: "Indicadores técnicos",
    items: [
      ["SMA20 / SMA50", "Promedio del precio de cierre de los últimos 20 y 50 días. Ayudan a ver la tendencia suavizando el ruido diario."],
      ["RSI 14", "Mide la fuerza del movimiento de 0 a 100. Mayor a 70 = sobrecompra (posible caída); menor a 30 = sobreventa (posible rebote)."],
      ["MACD", "Compara dos medias rápidas y lentas para medir el impulso (momentum). Barras verdes = fuerza alcista; rojas = fuerza bajista."],
      ["ATR 14", "Rango Verdadero Medio: mide cuánto se mueve el precio en promedio. Se usa para calcular dónde poner el Stop Loss y el Take Profit."],
      ["ARIMA", "Modelo estadístico que estudia el historial de precios para proyectar un valor futuro probable. Es nuestra línea base de comparación."],
    ],
  },
  {
    grupo: "Señales y decisiones",
    items: [
      ["Señal BUY (Compra)", "El sistema sugiere comprar: la IA recomienda AUMENTAR y la confluencia técnica acompaña."],
      ["Señal HOLD (Mantener)", "Sin confirmación suficiente: se espera antes de abrir o cerrar una posición."],
      ["Señal SELL (Venta)", "El sistema sugiere salir o vender: la IA recomienda RETIRAR la posición."],
      ["Recomendación AUMENTAR / RETIRAR / MANTENER", "Lectura cualitativa de la IA para ajustar la exposición, no solo abrir o cerrar."],
      ["Stop Loss", "Precio límite de protección. Si el precio cae hasta ahí, la operación se cierra para limitar la pérdida (aquí: cierre - 1.5 × ATR)."],
      ["Take Profit", "Precio objetivo donde se toma la ganancia (aquí: cierre + 3 × ATR)."],
      ["Ratio 1 : 2", "Por cada unidad que arriesgas, esperas ganar el doble. Típico del Swing Trading bien gestionado."],
    ],
  },
  {
    grupo: "Backtesting y riesgo",
    items: [
      ["Backtesting", "Simular la estrategia con datos históricos para ver cómo habría funcionado antes de usarla con dinero real."],
      ["Win Rate", "Porcentaje de operaciones simuladas que terminaron en ganancia."],
      ["Máximo Drawdown", "La caída más grande del capital simulado desde su punto más alto. Mide lo mal que puede ponerse la racha."],
      ["Sharpe Ratio", "Indica si el retorno compensa el riesgo asumido. Un valor más alto suele ser mejor."],
      ["Fricción", "Costo simulado de operar (comisiones/derrapes), aquí 0.1% por operación, para que la simulación sea realista."],
    ],
  },
];

function renderGlossary() {
  const box = byId("glossaryBox");
  if (!box) return;
  box.innerHTML = GLOSSARY.map((g) => `
      <div class="glossary-group">
        <h3>${esc(g.grupo)}</h3>
        <div class="glossary-grid">
          ${g.items.map(([term, def]) => `
              <details class="glossary-item">
                <summary>${esc(term)}</summary>
                <p>${esc(def)}</p>
              </details>`).join("")}
        </div>
      </div>`).join("");
}

/* ---------------- Inicialización ---------------- */

document.addEventListener("DOMContentLoaded", () => {
  bindTabs();
  fillCompanySelects();
  initCharts();
  renderMetodologia();
  renderGlossary();
  run();
});