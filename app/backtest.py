import numpy as np
import pandas as pd

TRAIN_RATIO = 0.70
FRICTION = 0.001
MAX_HOLD_BARS = 10
SL_MULTIPLIER = 1.5
TP_MULTIPLIER = 3.0
RSI_ENTRY_FLOOR = 35.0


def run(frame, arima_forecast=None):
    work = frame.dropna(subset=["Close", "SMA50", "ATR14", "RSI14"])
    if len(work) < 60:
        return {
            "disponible": False,
            "mensaje": "Serie insuficiente para backtesting (minimo 60 velas validas)",
        }

    close = work["Close"].to_numpy(dtype=float)
    high = work["High"].to_numpy(dtype=float)
    low = work["Low"].to_numpy(dtype=float)
    sma50 = work["SMA50"].to_numpy(dtype=float)
    rsi14 = work["RSI14"].to_numpy(dtype=float)
    atr14 = work["ATR14"].to_numpy(dtype=float)
    macd_hist = work["MACD_HIST"].to_numpy(dtype=float) if "MACD_HIST" in work else np.zeros(len(work))

    n_train = int(len(work) * TRAIN_RATIO)
    trades = []
    equity = np.ones(len(work))
    open_position = None

    for i in range(n_train, len(work)):
        if open_position is None:
            oversold_recovery = rsi14[i - 1] <= RSI_ENTRY_FLOOR and rsi14[i] > RSI_ENTRY_FLOOR
            momentum_breakout = rsi14[i] > RSI_ENTRY_FLOOR and rsi14[i] <= 70 and macd_hist[i] > 0
            above_trend = close[i] > sma50[i]
            if above_trend and (oversold_recovery or momentum_breakout):
                open_position = {
                    "entry_bar": i,
                    "entry_price": close[i],
                    "stop_loss": close[i] - SL_MULTIPLIER * atr14[i],
                    "take_profit": close[i] + TP_MULTIPLIER * atr14[i],
                }
            equity[i] = equity[i - 1]
            continue

        exit_price = None
        exit_reason = None
        held = i - open_position["entry_bar"]

        if low[i] <= open_position["stop_loss"]:
            exit_price = open_position["stop_loss"]
            exit_reason = "stop_loss"
        elif high[i] >= open_position["take_profit"]:
            exit_price = open_position["take_profit"]
            exit_reason = "take_profit"
        elif held >= MAX_HOLD_BARS:
            exit_price = close[i]
            exit_reason = "tiempo_maximo"

        if exit_price is not None:
            raw_return = exit_price / open_position["entry_price"] - 1.0
            net_return = raw_return - FRICTION
            trades.append(
                {
                    "entrada": round(open_position["entry_price"], 4),
                    "salida": round(exit_price, 4),
                    "resultado": round(net_return, 6),
                    "razon_salida": exit_reason,
                    "barras": held + 1,
                }
            )
            equity[i] = equity[i - 1] * (1.0 + net_return)
            open_position = None
        else:
            equity[i] = equity[i - 1]

    if open_position is not None:
        final = close[-1]
        net_return = final / open_position["entry_price"] - 1.0 - FRICTION
        trades.append(
            {
                "entrada": round(open_position["entry_price"], 4),
                "salida": round(final, 4),
                "resultado": round(net_return, 6),
                "razon_salida": "fin_simulacion",
                "barras": len(work) - open_position["entry_bar"],
            }
        )

    strat_equity = equity[n_train:]
    strat_returns = np.diff(strat_equity) / strat_equity[:-1]
    wins = [t for t in trades if t["resultado"] > 0]
    win_rate = len(wins) / len(trades) if trades else 0.0
    total_return = float(strat_equity[-1] / strat_equity[0] - 1.0)
    buy_hold_return = float(close[-1] / close[n_train] - 1.0)

    peak = np.maximum.accumulate(strat_equity)
    drawdown = strat_equity / peak - 1.0
    max_drawdown = float(drawdown.min())

    if len(strat_returns) > 1 and float(np.std(strat_returns)) > 0:
        sharpe = float(np.mean(strat_returns) / np.std(strat_returns) * np.sqrt(252))
    else:
        sharpe = 0.0

    forecast_note = None
    if arima_forecast:
        predicted_up = arima_forecast[-1] > arima_forecast[0]
        if len(close) >= 6:
            actual_up = close[-1] > close[-6]
            forecast_note = "Concuerda" if predicted_up == actual_up else "Difirio"
        else:
            forecast_note = "Sin referencia"

    test_dates = work.index[n_train:]
    buy_hold_curve = close[n_train:] / close[n_train]
    return {
        "disponible": True,
        "config": {
            "train_ratio": TRAIN_RATIO,
            "friccion": FRICTION,
            "max_hold_barras": MAX_HOLD_BARS,
            "sl_multiplo_atr": SL_MULTIPLIER,
            "tp_multiplo_atr": TP_MULTIPLIER,
            "n_train": n_train,
            "n_test": len(work) - n_train,
        },
        "n_trades": len(trades),
        "n_ganadoras": len(wins),
        "win_rate": round(win_rate, 4),
        "total_return_pct": round(total_return * 100, 4),
        "buy_hold_return_pct": round(buy_hold_return * 100, 4),
        "max_drawdown_pct": round(max_drawdown * 100, 4),
        "sharpe_ratio": round(sharpe, 4),
        "exceso_retorno_pct": round((total_return - buy_hold_return) * 100, 4),
        "arima_coincide": forecast_note,
        "trades": trades[-20:],
        "curva": {
            "dates": [d.strftime("%Y-%m-%d") if hasattr(d, "strftime") else str(d) for d in test_dates],
            "estrategia": [round(v, 6) for v in strat_equity],
            "buy_hold": [round(v, 6) for v in buy_hold_curve],
        },
    }