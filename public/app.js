"use strict";

Chart.defaults.color = "#8b949e";
Chart.defaults.borderColor = "rgba(48,54,61,1)";

const up = "#26a269";
const down = "#f14c4c";
const accent = "#58a6ff";

function byId(id) {
  return document.getElementById(id);
}

const charts = {};
const chartDefs = {
  price: {
    canvas: "chartPrice",
    datasets: [
      { label: "Precio de cierre", data: [], borderColor: accent, backgroundColor: "rgba(88,166,255,0.08)", fill: true },
      { label: "Promedio 20 días (SMA20)", data: [], borderColor: "#d29922", backgroundColor: "#d29922" },
      { label: "Promedio 50 días (SMA50)", data: [], borderColor: "#bc4c9a", backgroundColor: "#bc4c9a" },
    ],
    spanGaps: true,
    tooltipExtra: (ctx) =>
      ctx.dataset.label === "Precio de cierre"
        ? "precio con el que cerró ese día"
        : ctx.dataset.label.includes("20")
          ? "precio promedio de los últimos 20 días"
          : "precio promedio de los últimos 50 días",
  },
  rsi: {
    canvas: "chartRsi",
    datasets: [
      { label: "Fuerza del movimiento (RSI)", data: [], borderColor: "#6fddff", backgroundColor: "rgba(111,221,255,0.08)", fill: true },
      { label: "Zona de compra intensa (70)", data: [], borderColor: "rgba(241,76,76,0.5)", pointRadius: 0, borderDash: [5, 5], tooltip: false },
      { label: "Zona de venta intensa (30)", data: [], borderColor: "rgba(38,162,105,0.5)", pointRadius: 0, borderDash: [5, 5], tooltip: false },
    ],
    spanGaps: true,
    tooltipExtra: (ctx) =>
      ctx.parsed.y >= 70
        ? "compra muy intensa: la subida fue fuerte, es probable una corrección"
        : ctx.parsed.y <= 30
          ? "venta muy intensa: la caída fue fuerte, es probable un rebote"
          : "zona normal, sin extremos",
  },
  macd: {
    canvas: "chartMacd",
    datasets: [
      { type: "bar", label: "Impulso (barras)", data: [], backgroundColor: [], borderColor: [] },
      { label: "Línea de referencia", data: [], borderColor: "#d29922", backgroundColor: "#d29922", fill: false },
    ],
    spanGaps: true,
    tooltipExtra: (ctx) =>
      ctx.dataset.type === "bar"
        ? (ctx.parsed.y >= 0 ? "impulso alcista (barras verdes)" : "impulso bajista (barras rojas)")
        : "línea de referencia del impulso",
  },
  backtest: {
    canvas: "chartBacktest",
    datasets: [
      { label: "Con la estrategia", data: [], borderColor: accent, backgroundColor: "rgba(88,166,255,0.08)", fill: true },
      { label: "Mantenerse sin operar", data: [], borderColor: "#d29922", backgroundColor: "#d29922" },
    ],
    spanGaps: true,
    tooltipExtra: (ctx) =>
      ctx.dataset.label.startsWith("Con la estrategia")
        ? "evolución de S/1.00 aplicando la estrategia"
        : "evolución de S/1.00 sin operar",
  },
};

function initCharts() {
  Object.values(chartDefs).forEach((def) => {
    const canvas = byId(def.canvas);
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    const datasets = def.datasets.map((d) => ({
      ...d,
      pointRadius: d.pointRadius === 0 || d.tooltip === false ? 0 : pointRadius,
      pointHoverRadius: d.tooltip === false ? 0 : 5,
      pointBackgroundColor: d.borderColor,
      pointBorderColor: d.borderColor,
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
          legend: { labels: { usePointStyle: true, boxWidth: 8, font: { size: 11 } } },
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
  const chart = charts[chartDefs[key].canvas];
  if (!chart) return;
  chart.data.labels = labels;
  chartDefs[key].datasets.forEach((def, i) => {
    chart.data.datasets[i].data = datasetsData[i];
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

async function apiPost(path, formData) {
  const response = await fetch(path, { method: "POST", body: formData, headers: { Accept: "application/json" } });
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

function seCal(value) {
  return value === null || value === undefined || Number.isNaN(+value) ? "--" : `${Number(value).toFixed(2)}`;
}

/* ---------------- Helper visuales Chart.js ---------------- */

function pointRadius(ctx) {
  const arr = ctx.dataset.data;
  return ctx.dataIndex === arr.length - 1 && ctx.chart.canvas.id !== "chartMacd" ? 4 : 0;
}

function tooltipTitle(items) {
  return items.length ? String(items[0].label) : "";
}

function tooltipLabel(ctx) {
  const def = Object.values(chartDefs).find((d) => d.canvas === ctx.chart.canvas.id);
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

function renderKpis(data) {
  const ctx = data.contexto_tecnico;
  const senal = data.senal;
  const ia = data.analisis_ia;

  const h1 = document.querySelector("header h1");
  if (h1) h1.textContent = `${data.nombre || ctx.ticker} (${ctx.ticker}) · DSS Swing Trading`;

  const upCls = ctx.change_pct >= 0 ? "up" : "down";
  const signalClass = senal.direccion === "BUY" ? "sig-buy" : senal.direccion === "SELL" ? "sig-sell" : "sig-hold";
  const rsiNote = ctx.rsi14 >= 70 ? "Compra muy intensa" : ctx.rsi14 <= 35 ? "Venta muy intensa" : "Zona normal";

  const html =
    kpiCard("Precio", fmt(ctx.close), ctx.date || "", upCls) +
    kpiCard("Variación diaria", `${fmt(ctx.change_pct)} %`, "", upCls) +
    kpiCard("Fuerza del movimiento", fmt(ctx.rsi14), rsiNote) +
    kpiCard("Movimiento típico", fmt(ctx.atr14)) +
    kpiCard("Señal", sigLabel(senal.direccion), !ia.probabilidad ? "" : `${Math.round(ia.probabilidad * 100)} % confianza`, signalClass) +
    kpiCard("Tope de pérdida", fmt(senal.stop_loss)) +
    kpiCard("Objetivo de ganancia", fmt(senal.take_profit)) +
    kpiCard("Nivel de riesgo", ia.nivel_riesgo || "--");

  ["kpisTop", "kpisResumen"].forEach((id) => {
    const el = byId(id);
    if (el) el.innerHTML = html;
  });
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

/* ---------------- Screener (selección de empresa) ---------------- */

const COMPANIES = [
  { t: "SPY", n: "S&P 500" },
  { t: "AAPL", n: "Apple" },
  { t: "NVDA", n: "NVIDIA" },
  { t: "MSFT", n: "Microsoft" },
  { t: "AMZN", n: "Amazon" },
  { t: "TSLA", n: "Tesla" },
  { t: "GOOGL", n: "Alphabet (Google)" },
  { t: "META", n: "Meta" },
];

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
      lastC.close.toFixed(2),
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

/* ---------------- Análisis principal ---------------- */

async function run() {
  const tickerInput = byId("ticker");
  const ticker = (tickerInput?.value.trim().toUpperCase() || "SPY") ;
  const period = byId("period")?.value || "6mo";
  const imageUrl = byId("imageUrl")?.value.trim() || "";
  const fileInput = byId("imageFile");
  const selectedFile = fileInput?.files?.[0] || null;

  const btn = byId("runBtn");
  const status = byId("status");
  if (btn) btn.disabled = true;
  setStatus("Descargando datos y calculando señal...");
  hideError();

  showImagePreview(selectedFile || (imageUrl ? { url: imageUrl } : null));

  try {
    const indicatorsP = apiGet(`/api/indicators?ticker=${encodeURIComponent(ticker)}&period=${encodeURIComponent(period)}`);
    const signalP = buildSignalRequest(ticker, period, imageUrl, selectedFile);
    const arimaP = apiGet(`/api/forecast?ticker=${encodeURIComponent(ticker)}&period=${encodeURIComponent(period)}`);
    const btP = apiGet(`/api/backtest?ticker=${encodeURIComponent(ticker)}&period=1y`);

    const [indicatorsData, signalData, arimaData, btData] = await Promise.all([indicatorsP, signalP, arimaP, btP]);

    renderKpis(signalData);
    renderCharts(indicatorsData);
    renderArima(arimaData.forecast, ticker);
    renderIA(signalData, selectedFile || imageUrl);
    renderNarracion(signalData);
    renderFuente(indicatorsData.meta, signalData.nombre, ticker);

    renderAdvice("advicePrecio", indicatorsData.asesoria?.precio);
    renderAdvice("advicePrecioCandle", indicatorsData.asesoria?.precio);
    renderAdvice("adviceRsi", indicatorsData.asesoria?.rsi);
    renderAdvice("adviceMacd", indicatorsData.asesoria?.macd);
    renderAdvice("adviceArima", arimaData.forecast?.asesoria);

    renderBacktest(btData.backtest);

    setStatus(`Listo · ${ticker} · ${new Date().toLocaleTimeString()}`);
  } catch (err) {
    showError(err.message);
    setStatus("Error");
  } finally {
    if (btn) btn.disabled = false;
  }
}

function buildSignalRequest(ticker, period, imageUrl, file) {
  if (file) {
    const fd = new FormData();
    fd.append("ticker", ticker);
    fd.append("period", period);
    fd.append("file", file, file.name);
    return apiPost("/api/signal", fd);
  }
  const q = `?ticker=${encodeURIComponent(ticker)}&period=${encodeURIComponent(period)}`;
  const signalQuery = imageUrl ? `${q}&image_url=${encodeURIComponent(imageUrl)}` : q;
  return apiGet(`/api/signal${signalQuery}`);
}

function showImagePreview(source) {
  const viewer = byId("imageViewer");
  if (!viewer) return;
  if (!source) {
    viewer.innerHTML = `<p style="color: var(--muted);">Sin imagen. Adjunta una noticia (URL o archivo) y ejecuta "Analizar".</p>`;
    return;
  }
  const img = document.createElement("img");
  if (source instanceof File) {
    img.src = URL.createObjectURL(source);
  } else {
    img.src = source.url;
  }
  img.alt = "Imagen de noticia financiera";
  viewer.innerHTML = "";
  viewer.appendChild(img);
}

function renderCharts(data) {
  const s = data.series;
  updateChart("price", s.dates, [s.close, s.sma20, s.sma50]);
  updateChart("rsi", s.dates, [s.rsi14, s.rsi14.map(() => 70), s.rsi14.map(() => 30)]);
  updateChart("macd", s.dates, [s.macd_hist, s.macd_signal]);
  renderCandlestick(s.dates, s.open, s.high, s.low, s.close);
}

function renderArima(forecast, ticker) {
  const box = byId("arimaBox");
  if (!box) return;
  if (!forecast || !forecast.forecast) {
    box.innerHTML = '<p style="color: var(--muted);">Pronóstico ARIMA no disponible.</p>';
    return;
  }
  const dates = (forecast.forecast_dates || []).join(" · ");
  const chips = forecast.forecast
    .map((v, i) => `<div class="forecast-chip"><b>${fmt(v, 4)}</b>Día ${i + 1}</div>`)
    .join("");
  box.innerHTML = `
    <p><b>${esc(ticker)}</b> · Proyección del próximo cierre: <b style="color: var(--accent);">${fmt(forecast.next_close, 4)}</b></p>
    <div class="forecast-list">${chips}</div>
    <p style="color: var(--muted); margin-top: 8px;">Días de mercado proyectados: ${dates}</p>`;
}

function renderIA(data, imageSource) {
  const box = byId("iaBox");
  if (!box) return;
  const ia = data.analisis_ia;
  const signalClass = data.senal.direccion === "BUY" ? "sig-buy" : data.senal.direccion === "SELL" ? "sig-sell" : "sig-hold";
  const label = ia.con_imagen ? "con imagen de noticia" : "solo con datos de mercado";
  box.innerHTML = `
    <div style="display:flex; flex-wrap:wrap; gap:16px; align-items:center; margin-bottom:10px;">
      <h3 class="${signalClass}" style="font-size: 20px;">${esc(prediccionLabel(ia.prediccion))}</h3>
      <span class="${signalClass}"><b>${fmt(ia.probabilidad)}</b> probabilidad</span>
      <span>Riesgo: <b>${esc(ia.nivel_riesgo)}</b></span>
      <span style="color: var(--muted); font-size: 12px;">Fuente: ${esc(ia.fuente)} · ${label}</span>
    </div>
    <h3>Resumen de la noticia</h3>
    <p class="ai-summary">${esc(ia.resumen_noticia)}</p>
    <h3 style="margin-top: 12px;">Explicación de la decisión</h3>
    <p class="ai-summary">${esc(ia.justificacion_tecnica)}</p>
    ${(data.senal.razones || []).map((r) => `<div class="reason">${esc(r)}</div>`).join("")}`;
}

function renderNarracion(data) {
  const box = byId("narracionBox");
  if (!box) return;
  const narracion = data.narracion;
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
      <h3 style="margin:0;">${esc(data.nombre || data.ticker)}</h3> ${etiqueta}
    </div>
    <p class="narracion-text">${esc(narracion.parrafo)}</p>
    ${bullets ? `<ul class="narracion-bullets">${bullets}</ul>` : ""}`;
}

function renderFuente(meta, nombre, ticker) {
  const box = byId("fuenteBox");
  if (!box) return;
  if (!meta) {
    box.innerHTML = '<p style="color: var(--muted);">Metadatos de la fuente no disponibles.</p>';
    return;
  }
  const card = (label, value) =>
    `<div class="kpi"><div class="label">${esc(label)}</div><div class="value" style="font-size:18px;">${esc(value)}</div></div>`;
  box.innerHTML =
    card("Proveedor", meta.proveedor) +
    card("Formato", meta.tipo) +
    card("Periodo", meta.period_solicitado) +
    card("Registros diarios", meta.n_velas) +
    card("Última fecha", meta.ultima_fecha || "--") +
    card("Empresa", `${nombre || ticker}`);
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

  renderAdvice("adviceBacktest", bt.asesoria || null);

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

/* ---------------- Pestaña Metodología ---------------- */

const TDSP_PHASES = [
  {
    fase: "Fase 1 · Comprensión del negocio",
    detalle: "Definición de objetivos analíticos, reglas de Swing Trading (posiciones de 3 a 10 ruedas bursátiles), horizonte temporal y dimensionamiento del riesgo.",
    entregable: "Especificación de alcance y reglas operativas.",
  },
  {
    fase: "Fase 2 · Adquisición y comprensión de datos",
    detalle: "Extracción de series OHLCV mediante yfinance y captura de imágenes de noticias financieras. Verificación de integridad, calidad y limpieza temporal.",
    entregable: "Repositorio de tablas limpias e imágenes indexadas.",
  },
  {
    fase: "Fase 3 · Modelado",
    detalle: "Ingeniería de características (SMA, RSI, MACD, ATR), calibración del benchmark ARIMA(p,d,q) y orquestación de peticiones multimodales a Gemini Flash.",
    entregable: "Contratos JSON validados y pronósticos econométricos.",
  },
  {
    fase: "Fase 4 · Despliegue",
    detalle: "Motor de señales con Stop-Loss y Take-Profit, simulación histórica (backtesting) y construcción del panel interactivo que estás viendo.",
    entregable: "Dashboard desplegado en Vercel (costo S/ 0.00).",
  },
  {
    fase: "Fase 5 · Aceptación del cliente",
    detalle: "Validación de Win Rate, retorno frente a ARIMA y frente a Buy & Hold; verificación del cumplimiento de las especificaciones operativas.",
    entregable: "Informe final y presentación ejecutiva.",
  },
];

const PIPELINE_STEPS = [
  { paso: "1", titulo: "Fuentes de datos", texto: "yfinance (OHLCV) e imágenes de noticias financieras públicas." },
  { paso: "2", titulo: "Ingesta y ETL", texto: "Limpieza de series, cálculo de indicadores y normalización de imágenes (JPEG ≤ 1024 px)." },
  { paso: "3", titulo: "Modelado dual", texto: "Indicadores técnicos + benchmark ARIMA (ADF/AIC) + inferencia multimodal Gemini Flash." },
  { paso: "4", titulo: "Señal y Backtesting", texto: "BUY/HOLD/SELL con SL 1.5·ATR y TP 3·ATR; simulación 70/15/15 con fricción 0.1%." },
  { paso: "5", titulo: "Panel interactivo", texto: "Dashboard web en Vercel con KPIs, gráficos, inferencia IA, backtesting y esta guía metodológica." },
];

const CHAIN_VALUES = ["Dato crudo", "Información", "Modelado dual", "Señal filtrada", "Decisión informada"];

const V_LAYOUT = [
  { letra: "Volumen", texto: "Millones de puntos OHLCV históricos + repositorio de imágenes de prensa (megas a gigas)." },
  { letra: "Velocidad", texto: "Procesamiento por lotes al cierre del mercado y cortes de 4 h, acorde al ciclo del Swing Trading." },
  { letra: "Variedad", texto: "Tablas numéricas continuas (OHLCV) conviven con objetos binarios visuales (imágenes)." },
];

const TOOLS = [
  ["yfinance / Kaggle", "Cotizaciones OHLCV"],
  ["Python · Pandas · NumPy", "Limpieza e indicadores"],
  ["statsmodels ARIMA", "Benchmark econométrico"],
  ["Gemini Flash API", "Motor multimodal"],
  ["Pillow", "Normalización de imágenes"],
  ["Parquet/JSON + Vercel", "Almacenamiento y hosting"],
  ["Chart.js + HTML/JS", "Panel interactivo"],
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
    chain.innerHTML = CHAIN_VALUES.map(
      (c) => `<div class="chain-node">${esc(c)}</div>`
    ).join('<div class="chain-arrow">→</div>');
  }

  const vs = byId("vsBox");
  if (vs) {
    vs.innerHTML = V_LAYOUT.map(
      (v) => `
      <div class="vs-card">
        <div class="vs-letter">${esc(v.letra[0])}</div>
        <div><b>${esc(v.letra)}</b><p class="hint">${esc(v.texto)}</p></div>
      </div>`
    ).join("");
  }

  const tools = byId("toolsBox");
  if (tools) {
    tools.innerHTML = TOOLS.map(
      ([h, d]) => `<div class="tool-item"><b>${esc(h)}</b><span class="hint">${esc(d)}</span></div>`
    ).join("");
  }

  const ethic = byId("ethicBox");
  if (ethic) ethic.textContent = ETHIC_TEXT;
}

/* ---------------- Pestaña Diccionario ---------------- */

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
      ["Señal BUY (Compra)", "El sistema sugiere comprar: predicción alcista con alta probabilidad, precio sobre su media y RSI en zona razonable."],
      ["Señal HOLD (Mantener)", "Sin confirmación suficiente: se espera antes de abrir o cerrar una posición."],
      ["Señal SELL (Venta)", "El sistema sugiere salir o vender: predicción bajista con alta probabilidad."],
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
  box.innerHTML = GLOSSARY.map(
    (g) => `
      <div class="glossary-group">
        <h3>${esc(g.grupo)}</h3>
        <div class="glossary-grid">
          ${g.items
            .map(
              ([term, def]) => `
              <details class="glossary-item">
                <summary>${esc(term)}</summary>
                <p>${esc(def)}</p>
              </details>`
            )
            .join("")}
        </div>
      </div>`
  ).join("");
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