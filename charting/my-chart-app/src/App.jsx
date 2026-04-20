import { useEffect, useRef, useState } from "react";
import Select from "react-select";
import { createChart, CandlestickSeries } from "lightweight-charts";

function App() {
  const chartRef = useRef(null);
  const chartInstance = useRef(null);
  const seriesRef = useRef(null);

  const [symbols, setSymbols] = useState([]);
  const [symbol, setSymbol] = useState(null);

  useEffect(() => {
    const chart = createChart(chartRef.current, {
      width: window.innerWidth,
      height: window.innerHeight - 56,
      layout: {
        background: { color: "#020617" },
        textColor: "#cbd5e1",
      },
      grid: {
        vertLines: { color: "#1e293b" },
        horzLines: { color: "#1e293b" },
      },
    });

    const series = chart.addSeries(CandlestickSeries);

    chartInstance.current = chart;
    seriesRef.current = series;

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
        setSymbol(options[0]);
      });
  }, []);

  useEffect(() => {
    if (!symbol || !seriesRef.current) return;

    fetch(
      `http://127.0.0.1:8000/api/history?symbol=${symbol.value}`
    )
      .then((res) => res.json())
      .then((data) => {
        const formatted = data.map((row) => ({
          time: row.time.slice(0, 10),
          open: Number(row.open),
          high: Number(row.high),
          low: Number(row.low),
          close: Number(row.close),
        }));

        seriesRef.current.setData(formatted);
        chartInstance.current.timeScale().fitContent();
      });
  }, [symbol]);

  const customStyles = {
    control: (base) => ({
      ...base,
      backgroundColor: "#111827",
      borderColor: "#374151",
      minWidth: 220,
    }),

    menuPortal: (base) => ({
      ...base,
      zIndex: 9999,
    }),

    menu: (base) => ({
      ...base,
      backgroundColor: "#111827",
      zIndex: 9999,
    }),

    option: (base, state) => ({
      ...base,
      backgroundColor: state.isFocused
        ? "#1f2937"
        : "#111827",
      color: "white",
    }),

    singleValue: (base) => ({
      ...base,
      color: "white",
    }),

    input: (base) => ({
      ...base,
      color: "white",
    }),
  };

  return (
    <>
      <div
        style={{
          height: "56px",
          background: "#0f172a",
          display: "flex",
          alignItems: "center",
          padding: "0 12px",
          borderBottom: "1px solid #1e293b",
        }}
      >
        <div
          style={{
            color: "white",
            fontWeight: "600",
            marginRight: "12px",
          }}
        >
          Quant Lab
        </div>

        <Select
          options={symbols}
          value={symbol}
          onChange={setSymbol}
          styles={customStyles}
          isSearchable={true}
          menuPortalTarget={document.body}
          menuPosition = "fixed"
        />
      </div>

      <div ref={chartRef}></div>
    </>
  );
}

export default App;
