"use strict";

Chart.defaults.color = "#8b949e";
Chart.defaults.borderColor = "rgba(48,54,61,1)";

const up = "#26a269";
const down = "#f14c4c";
const accent = "#58a6ff";

const kpiSel = {
  precio: document.getElementById("kpiPrecio"),
  fecha: document.getElementById("kpiFecha"),
  variacion: document.getElementById("kpiVariacion"),
  rsi: document.getElementById("kpiRsi"),
  rsiNote: document.getElementById("kpiRsiNote"),
  atr: document.getElementById("kpiAtr"),
  senal: document.getElementById("kpiSenal"),
  prob: document.getElementById("kpiProb"),
  sl: document.getElementById("kpiSl"),
  tp: document.getElementById("kpiTp"),
  riesgo: document.getElementById("kpiRiesgo"),
};

const statusEl = document.getElementById("status");
const errorBox = document.getElementById("errorBox");

const charts = {};
const chartDefs = {
  price: {
    canvas: "chartPrice",
    labels: [],
    datasets: [
      { label: "Cierre", data: [], borderColor: accent, backgroundColor: accent },
      { label: "SMA20", data: [], borderColor: "#d29922", backgroundColor: "#d29922" },
      { label: "SMA50", data: [], borderColor: "#bc4c9a", backgroundColor: "#bc4c9a" },
    ],
    spanGaps: true,
  },
  rsi: {
    canvas: "chartRsi",
    labels: [],
    datasets: [
      { label: "RSI14", data: [], borderColor: "#6fddff", backgroundColor: "#6fddff", fill: false },
      { label: "Sobrecompra 70", data: [], borderColor: "rgba(241,76,76,0.5)", pointRadius: 0, borderDash: [4, 4] },
      { label: "Sobreventa 30", data: [], borderColor: "rgba(38,162,105,0.5)", pointRadius: 0, borderDash: [4, 4] },
    ],
    spanGaps: true,
  },
  macd: {
    canvas: "chartMacd",
    labels: [],
    datasets: [
      { type: "bar", label: "Histograma", data: [], backgroundColor: [], borderColor: [] },
      { label: "Señal MACD", data: [], borderColor: "#d29922", backgroundColor: "#d29922", fill: false },
    ],
    spanGaps: true,
  },
  backtest: {
    canvas: "chartBacktest",
    labels: [],
    datasets: [
      { label: "Estrategia", data: [], borderColor: accent, backgroundColor: accent },
      { label: "Buy & Hold", data: [], borderColor: "#d29922", backgroundColor: "#d29922" },
    ],
    spanGaps: true,
  },
};

function initCharts() {
  Object.values(chartDefs).forEach((def) => {
    const ctx = document.getElementById(def.canvas).getContext("2d");
    const isBar = def.datasets.some((d) => d.type === "bar");
    charts[def.canvas] = new Chart(ctx, {
      type: "line",
      data: { labels: [], datasets: def.datasets },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        spanGaps: def.spanGaps,
        plugins: {
          legend: { labels: { usePointStyle: true, boxWidth: 8, font: { size: 11 } } },
        },
        scales: {
          x: {
            ticks: { maxTicksLimit: 10, font: { size: 10 } },
            grid: { display: false },
          },
          y: {
            ticks: { font: { size: 10 } },
            grid: { color: "rgba(140,160,190,0.1)" },
          },
        },
        elements: {
          point: { radius: 0 },
          line: { borderWidth: 1.5, tension: 0.25 },
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

function fmt(value, digits = 2) {
  if (value === null || value === undefined || Number.isNaN(+value)) return "--";
  return Number(value).toLocaleString("en-US", { minimumFractionDigits: digits, maximumFractionDigits: digits });
}

async function run() {
  const ticker = document.getElementById("ticker").value.trim().toUpperCase() || "SPY";
  const period = document.getElementById("period").value;
  const imageUrl = document.getElementById("imageUrl").value.trim();

  setStatus("Descargando datos y calculando...");
  hideError();

  const query = `?ticker=${encodeURIComponent(ticker)}&period=${encodeURIComponent(period)}`;
  const signalQuery = imageUrl ? `${query}&image_url=${encodeURIComponent(imageUrl)}` : query;

  try {
    const [indicatorsData, signalData, arimaData, btData] = await Promise.all([
      apiGet(`/api/indicators${query}`),
      apiGet(`/api/signal${signalQuery}`),
      apiGet(`/api/forecast${query}`),
      apiGet(`/api/backtest?ticker=${encodeURIComponent(ticker)}&period=1y`),
    ]);

    renderKpis(signalData);
    renderCharts(indicatorsData);
    renderArima(arimaData.forecast, ticker);
    renderIA(signalData);
    renderBacktest(btData.backtest);
    setStatus(`Listo · ${ticker} · ${new Date().toLocaleTimeString()}`);
  } catch (err) {
    showError(err.message);
    setStatus("Error");
  }
}

function renderKpis(data) {
  const ctx = data.contexto_tecnico;
  const senal = data.senal;
  const ia = data.analisis_ia;

  kpiSel.precio.textContent = fmt(ctx.close);
  kpiSel.precio.className = "value " + (ctx.change_pct >= 0 ? "up" : "down");
  kpiSel.fecha.textContent = ctx.date || "";
  kpiSel.variacion.textContent = `${fmt(ctx.change_pct)} %`;
  kpiSel.variacion.className = "value " + (ctx.change_pct >= 0 ? "up" : "down");

  kpiSel.rsi.textContent = fmt(ctx.rsi14);
  const rsi = ctx.rsi14;
  kpiSel.rsiNote.textContent = rsi >= 70 ? "Sobrecompra" : rsi <= 35 ? "Sobreventa" : "Zona neutra";

  kpiSel.atr.textContent = fmt(ctx.atr14);

  const signalClass = senal.direccion === "BUY" ? "sig-buy" : senal.direccion === "SELL" ? "sig-sell" : "sig-hold";
  kpiSel.senal.textContent = senal.direccion;
  kpiSel.senal.className = "value " + signalClass;
  kpiSel.prob.textContent = !ia.probabilidad ? "--" : `${Math.round(ia.probabilidad * 100)} % confianza`;

  kpiSel.sl.textContent = fmt(senal.stop_loss);
  kpiSel.tp.textContent = fmt(senal.take_profit);
  kpiSel.riesgo.textContent = ia.nivel_riesgo || "--";
}

function renderCharts(data) {
  const s = data.series;
  updateChart("price", s.dates, [s.close, s.sma20, s.sma50]);
  const rsiConst70 = s.rsi14.map(() => 70);
  const rsiConst30 = s.rsi14.map(() => 30);
  updateChart("rsi", s.dates, [s.rsi14, rsiConst70, rsiConst30]);
  updateChart("macd", s.dates, [s.macd_hist, s.macd_signal]);
}

function renderArima(forecast, ticker) {
  const box = document.getElementById("arimaBox");
  if (!forecast || !forecast.forecast) {
    box.innerHTML = '<p style="color: var(--muted);">Pronóstico ARIMA no disponible.</p>';
    return;
  }
  const dates = (forecast.forecast_dates || []).join(" · ");
  const chips = forecast.forecast
    .map((v, i) => `<div class="forecast-chip"><b>${fmt(v, 4)}</b>Día ${i + 1}</div>`)
    .join("");
  const order = forecast.order ? `(${forecast.order.p},${forecast.order.d},${forecast.order.q})` : "-";
  box.innerHTML = `
    <p><b>${ticker}</b> · Promedio proyectado (cierre): <b style="color: var(--accent);">${fmt(forecast.next_close, 4)}</b>
    · Orden ARIMA ${order} · ADF p-value: ${fmt(forecast.adf_pvalue)}</p>
    <div class="forecast-list">${chips}</div>
    <p style="color: var(--muted); margin-top: 8px;">Ruedas proyectadas: ${dates}</p>`;
}

function renderIA(data) {
  const box = document.getElementById("iaBox");
  const ia = data.analisis_ia;
  const signalClass = data.senal.direccion === "BUY" ? "sig-buy" : data.senal.direccion === "SELL" ? "sig-sell" : "sig-hold";
  const label = ia.con_imagen ? "con imagen de noticia" : "solo contexto técnico";
  box.innerHTML = `
    <div style="display:flex; flex-wrap:wrap; gap:16px; align-items:center; margin-bottom:10px;">
      <h3 class="${signalClass}" style="font-size: 20px;">${ia.prediccion}</h3>
      <span class="${signalClass}"><b>${fmt(ia.probabilidad)}</b> probabilidad</span>
      <span>Riesgo: <b>${ia.nivel_riesgo}</b></span>
      <span style="color: var(--muted); font-size: 12px;">Fuente: ${ia.fuente} · ${label}</span>
    </div>
    <h3>Resumen de la noticia</h3>
    <p class="ai-summary">${ia.resumen_noticia}</p>
    <h3 style="margin-top: 12px;">Justificación técnica</h3>
    <p class="ai-summary">${ia.justificacion_tecnica}</p>
    ${(data.senal.razones || []).map((r) => `<div class="reason">${r}</div>`).join("")}`;
}

function renderBacktest(bt) {
  const metrics = document.getElementById("btMetrics");
  const trades = document.getElementById("btTrades");
  if (!bt || !bt.disponible) {
    metrics.innerHTML = `<p style="color: var(--muted);">${bt?.mensaje || "Backtest no disponible."}</p>`;
    trades.innerHTML = "";
    updateChart("backtest", [], [[], []]);
    return;
  }
  const card = (label, value, cls = "") =>
    `<div class="kpi"><div class="label">${label}</div><div class="value ${cls}">${value}</div></div>`;
  metrics.innerHTML =
    card("Win Rate", `${(bt.win_rate * 100).toFixed(1)} %`) +
    card("Operaciones", bt.n_trades) +
    card("Retorno Estrategia", `${bt.total_return_pct} %`, bt.total_return_pct >= 0 ? "up" : "down") +
    card("Buy & Hold", `${bt.buy_hold_return_pct} %`, bt.buy_hold_return_pct >= 0 ? "up" : "down") +
    card("Máx. Drawdown", `${bt.max_drawdown_pct} %`, "down") +
    card("Sharpe", fmt(bt.sharpe_ratio));

  if (bt.curva && bt.curva.dates && bt.curva.dates.length) {
    updateChart("backtest", bt.curva.dates, [bt.curva.estrategia, bt.curva.buy_hold]);
  } else {
    updateChart("backtest", [], [[], []]);
  }

  if (!bt.trades || !bt.trades.length) {
    trades.innerHTML = '<p style="color: var(--muted); padding: 8px;">Sin operaciones en la ventana de prueba.</p>';
    return;
  }
  const rows = bt.trades
    .map(
      (t) => `<tr>
        <td>${t.entrada}</td><td>${t.salida}</td>
        <td class="${t.resultado >= 0 ? "up" : "down"}">${(t.resultado * 100).toFixed(2)} %</td>
        <td>${t.razon_salida}</td><td>${t.barras}</td>
      </tr>`
    )
    .join("");
  trades.innerHTML = `<table>
    <thead><tr><th>Entrada</th><th>Salida</th><th>Resultado</th><th>Salida por</th><th>Barras</th></tr></thead>
    <tbody>${rows}</tbody></table>`;
}

function setStatus(text) {
  statusEl.textContent = text;
}

function showError(message) {
  errorBox.textContent = `Error: ${message}`;
  errorBox.classList.remove("hidden");
}

function hideError() {
  errorBox.classList.add("hidden");
}

document.getElementById("runBtn").addEventListener("click", run);
document.getElementById("ticker").addEventListener("keydown", (e) => {
  if (e.key === "Enter") run();
});

initCharts();
run();