import { useEffect, useRef, useState } from "react";
import Select from "react-select";
import {
  createChart,
  CandlestickSeries,
} from "lightweight-charts";

function App() {
  const chartRef = useRef(null);
  const chartInstance = useRef(null);
  const seriesRef = useRef(null);

  const [symbols, setSymbols] = useState([]);
  const [symbol, setSymbol] = useState(null);

  const [ohlc, setOhlc] = useState({
    open: "-",
    high: "-",
    low: "-",
    close: "-",
  });

  const [tf, setTf] = useState("D");

  useEffect(() => {
    const chart = createChart(chartRef.current, {
      width: window.innerWidth,
      height: window.innerHeight - 48,
      layout: {
        background: { color: "#131722" },
        textColor: "#d1d4dc",
      },
      grid: {
        vertLines: { color: "#131722" },
        horzLines: { color: "#131722" },
      },
      rightPriceScale: {
        borderColor: "#2a2e39",
      },
      timeScale: {
        borderColor: "#2a2e39",
      },
      crosshair: {
        mode: 1,
      },
    });

    const series = chart.addSeries(CandlestickSeries);

    seriesRef.current = series;
    chartInstance.current = chart;

    chart.subscribeCrosshairMove((param) => {
      if (!param.time || !param.seriesData.size) return;

      const data = param.seriesData.get(series);

      if (data) {
        setOhlc({
          open: data.open,
          high: data.high,
          low: data.low,
          close: data.close,
        });
      }
    });

    window.addEventListener("resize", () => {
      chart.applyOptions({
        width: window.innerWidth,
        height: window.innerHeight - 48,
      });
    });

    return () => chart.remove();
  }, []);

  useEffect(() => {
    fetch("http://127.0.0.1:8000/api/symbols")
      .then((res) => res.json())
      .then((data) => {
        const options = data.map((item) => ({
          value: item,
          label: item,
        }));

        setSymbols(options);

        if (options.length > 0) {
          setSymbol(options[0]);
        }
      });
  }, []);

  useEffect(() => {
    if (!symbol || !seriesRef.current) return;

    fetch(
      `http://127.0.0.1:8000/api/history?symbol=${symbol.value}&tf=${tf}`
    )
      .then((res) => res.json())
      .then((data) => {
        const isIntraday = ["1m", "5m", "15m", "1H"].includes(tf);

        const formatted = data.map((row) => ({
          time: isIntraday
            ? Math.floor(new Date(row.time).getTime() / 1000)
            : row.time.slice(0, 10),

          open: Number(row.open),
          high: Number(row.high),
          low: Number(row.low),
          close: Number(row.close),
        }));

        seriesRef.current.setData(formatted);
        chartInstance.current.timeScale().fitContent();
      });
  }, [symbol, tf]);

  const selectStyles = {
    control: (base) => ({
      ...base,
      backgroundColor: "#1e222d",
      borderColor: "#363a45",
      minHeight: "32px",
      minWidth: 180,
      boxShadow: "none",
    }),
    singleValue: (base) => ({
      ...base,
      color: "#fff",
    }),
    input: (base) => ({
      ...base,
      color: "#fff",
    }),
    menu: (base) => ({
      ...base,
      backgroundColor: "#1e222d",
      zIndex: 9999,
    }),
    menuPortal: (base) => ({
      ...base,
      zIndex: 9999,
    }),
    option: (base, state) => ({
      ...base,
      backgroundColor: state.isFocused
        ? "#2a2e39"
        : "#1e222d",
      color: "white",
    }),
  };

  const tfBtn = {
    background: "transparent",
    color: "#b2b5be",
    border: "none",
    cursor: "pointer",
    padding: "0 8px",
    fontSize: "13px",
  };

  return (
    <>
      <div
        style={{
          height: "48px",
          background: "#131722",
          borderBottom: "1px solid #2a2e39",
          display: "flex",
          alignItems: "center",
          padding: "0 10px",
          gap: "12px",
        }}
      >
        <div
          style={{
            color: "white",
            fontWeight: "700",
            fontSize: "16px",
          }}
        >
          Quant Lab
        </div>

        <Select
          options={symbols}
          value={symbol}
          onChange={setSymbol}
          styles={selectStyles}
          menuPortalTarget={document.body}
          menuPosition="fixed"
          isSearchable
        />

        <div className="tf-group">
          {["1m","5m","15m","1H","D","W","M"].map((item) => (
            <button
              key={item}
              onClick={() => setTf(item)}
              className={`tf-btn ${tf === item ? "active" : ""}`}
            >
              {item}
            </button>
          ))}
        </div>
      </div>

      <div style={{ position: "relative" }}>
        <div
          style={{
            position: "absolute",
            top: "8px",
            left: "12px",
            zIndex: 10,
            color: "#d1d4dc",
            fontSize: "13px",
            background: "rgba(19,23,34,0.8)",
            padding: "4px 8px",
            borderRadius: "4px",
          }}
        >
          <strong>{symbol?.value}</strong>{" "}
          O {ohlc.open} H {ohlc.high} L {ohlc.low} C {ohlc.close}
        </div>

        <div ref={chartRef}></div>
      </div>
    </>
  );
}

export default App;
