/* Trade Scanner — client-side CSV + Excel parse + buy/sell scan. No server. */

const ALIASES = {
  date: ["date", "time", "datetime", "timestamp", "tradedate", "dt", "day"],
  symbol: ["symbol", "ticker", "instrument", "asset", "stock", "pair", "security", "name"],
  side: ["side", "action", "type", "buysell", "direction", "signal", "order", "bs"],
  quantity: ["qty", "quantity", "shares", "size", "amount", "units", "fillqty", "filled"],
  price: ["price", "fill", "fillprice", "avgprice", "last", "px", "rate"],
  open: ["open", "openprice"],
  high: ["high", "highprice"],
  low: ["low", "lowprice"],
  close: ["close", "adjclose", "closing", "lastclose"],
  volume: ["volume", "vol"],
  notes: ["notes", "note", "comment", "comments", "memo", "description", "desc", "reason", "text"],
};

const SIDE_PATTERNS = [
  { side: "COVER", re: /\b(cover(ing|ed)?|buy\s*to\s*cover|btc)\b/i },
  { side: "SHORT", re: /\b(short(ed|ing)?|sell\s*short|ss)\b/i },
  { side: "BUY", re: /\b(buy|bought|buying|long|accumulate|accumulation|bullish|bid|bto)\b/i },
  { side: "SELL", re: /\b(sell|sold|selling|dump|distribute|distribution|bearish|ask|sto)\b/i },
  { side: "HOLD", re: /\b(hold|holding|wait|neutral)\b/i },
  { side: "WATCH", re: /\b(watch|watchlist|monitor)\b/i },
];

function detectDelimiter(firstLine) {
  const counts = [
    [",", (firstLine.match(/,/g) || []).length],
    [";", (firstLine.match(/;/g) || []).length],
    ["\t", (firstLine.match(/\t/g) || []).length],
    ["|", (firstLine.match(/\|/g) || []).length],
  ].sort((a, b) => b[1] - a[1]);
  return counts[0][1] > 0 ? counts[0][0] : ",";
}

function parseLine(line, delimiter) {
  const out = [];
  let cur = "";
  let inQuotes = false;
  for (let i = 0; i < line.length; i++) {
    const ch = line[i];
    if (ch === '"') {
      if (inQuotes && line[i + 1] === '"') {
        cur += '"';
        i++;
      } else inQuotes = !inQuotes;
    } else if (ch === delimiter && !inQuotes) {
      out.push(cur.trim());
      cur = "";
    } else cur += ch;
  }
  out.push(cur.trim());
  return out;
}

function parseCsv(text) {
  const normalized = text.replace(/^\uFEFF/, "").replace(/\r\n/g, "\n").replace(/\r/g, "\n");
  const rawLines = normalized.split("\n").filter((l) => l.trim().length > 0);
  if (!rawLines.length) return { headers: [], rows: [] };
  const delimiter = detectDelimiter(rawLines[0]);
  const parsed = rawLines.map((l) => parseLine(l, delimiter));
  const headerCount = parsed[0].length;
  const looksLikeHeader = parsed[0].some((cell) => /[A-Za-z]/.test(cell));
  if (looksLikeHeader) {
    const headers = parsed[0].map((h, i) => h || `col_${i + 1}`);
    const rows = parsed.slice(1).map((r) => {
      const padded = r.slice();
      while (padded.length < headerCount) padded.push("");
      return padded.slice(0, headerCount);
    });
    return { headers, rows };
  }
  const headers = Array.from({ length: headerCount }, (_, i) => `col_${i + 1}`);
  return { headers, rows: parsed };
}

/** Convert a 2-D array (from Excel / SheetJS) into the same {headers, rows} shape. */
function parseArray(data) {
  if (!data || !data.length) return { headers: [], rows: [] };
  const normalized = data.map((row) =>
    (row || []).map((cell) => {
      if (cell == null || cell === "") return "";
      if (cell instanceof Date) return cell.toISOString().slice(0, 10);
      return String(cell).trim();
    })
  );
  const headerCount = Math.max(...normalized.map((r) => r.length), 0);
  const looksLikeHeader = normalized[0].some((cell) => /[A-Za-z]/.test(cell));
  if (looksLikeHeader) {
    const headers = normalized[0].map((h, i) => h || `col_${i + 1}`);
    while (headers.length < headerCount) headers.push(`col_${headers.length + 1}`);
    const rows = normalized.slice(1).map((r) => {
      const padded = r.slice();
      while (padded.length < headerCount) padded.push("");
      return padded.slice(0, headerCount);
    });
    return { headers, rows };
  }
  const headers = Array.from({ length: headerCount }, (_, i) => `col_${i + 1}`);
  return { headers, rows: normalized };
}

function normHeader(h) {
  return String(h).toLowerCase().replace(/[^a-z0-9]+/g, "");
}

function detectColumns(headers) {
  const map = {};
  const used = new Set();
  const normalized = headers.map((h) => ({ raw: h, key: normHeader(h) }));
  Object.keys(ALIASES).forEach((field) => {
    for (const alias of ALIASES[field]) {
      const hit = normalized.find((h) => !used.has(h.raw) && (h.key === alias || h.key.endsWith(alias)));
      if (hit) {
        map[field] = hit.raw;
        used.add(hit.raw);
        return;
      }
    }
  });
  return map;
}

function parseNumber(v) {
  if (v == null || v === "") return undefined;
  const cleaned = String(v).replace(/[$,%\s]/g, "").replace(/^\((.+)\)$/, "-$1");
  const n = Number(cleaned);
  return Number.isFinite(n) ? n : undefined;
}

function detectSide(text) {
  if (!text) return undefined;
  const s = String(text);
  for (const p of SIDE_PATTERNS) {
    if (p.re.test(s)) return p.side;
  }
  return undefined;
}

function notional(side, qty, price) {
  const q = parseNumber(qty);
  const p = parseNumber(price);
  if (!Number.isFinite(q) || !Number.isFinite(p)) return 0;
  const sign = side === "SELL" || side === "SHORT" ? -1 : 1;
  return sign * Math.abs(q) * p;
}

function sma(arr, period, i) {
  if (i < period - 1) return undefined;
  let sum = 0;
  for (let j = i - period + 1; j <= i; j++) sum += arr[j];
  return sum / period;
}

function rsi(closes, period, i) {
  if (i < period) return undefined;
  let gains = 0;
  let losses = 0;
  for (let j = i - period + 1; j <= i; j++) {
    const diff = closes[j] - closes[j - 1];
    if (diff > 0) gains += diff;
    else losses -= diff;
  }
  if (losses === 0) return 100;
  const rs = gains / losses;
  return 100 - 100 / (1 + rs);
}

function scanTable(table, fileName = "upload") {
  const { headers, rows: rawRows } = table;
  const columns = detectColumns(headers);
  const colIndex = {};
  Object.keys(columns).forEach((k) => {
    colIndex[k] = headers.indexOf(columns[k]);
  });

  const rows = rawRows.map((r, idx) => {
    const get = (field) => {
      const i = colIndex[field];
      return i >= 0 ? r[i] : undefined;
    };
    const sideRaw = get("side");
    const notes = get("notes");
    const side = detectSide(sideRaw) || detectSide(notes) || undefined;
    return {
      index: idx,
      date: get("date"),
      symbol: get("symbol"),
      side,
      quantity: parseNumber(get("quantity")),
      price: parseNumber(get("price")),
      open: parseNumber(get("open")),
      high: parseNumber(get("high")),
      low: parseNumber(get("low")),
      close: parseNumber(get("close")),
      volume: parseNumber(get("volume")),
      notes,
      raw: r,
    };
  });

  const signals = [];
  const push = (s) => signals.push(s);

  rows.forEach((row) => {
    if (row.side) {
      push({
        rowIndex: row.index,
        date: row.date,
        symbol: row.symbol,
        side: row.side,
        reason: row.notes || `Explicit ${row.side}`,
        strength: 90,
        price: row.price ?? row.close,
        source: "blotter",
      });
    }
  });

  const bySymbol = {};
  rows.forEach((row) => {
    const tag = row.symbol || "_default";
    if (!bySymbol[tag]) bySymbol[tag] = [];
    bySymbol[tag].push(row);
  });

  Object.keys(bySymbol).forEach((tag) => {
    const series = bySymbol[tag];
    const closes = series.map((r) => r.close ?? r.price);
    const volumes = series.map((r) => r.volume);
    series.forEach((row, i) => {
      const c = closes[i];
      if (!Number.isFinite(c)) return;

      const r = rsi(closes, 14, i);
      if (Number.isFinite(r)) {
        if (r <= 30) {
          push({
            rowIndex: row.index,
            date: row.date,
            symbol: tag,
            side: "BUY",
            reason: `RSI ${r.toFixed(0)} oversold`,
            strength: 68,
            price: c,
            source: "technical",
          });
        } else if (r >= 70) {
          push({
            rowIndex: row.index,
            date: row.date,
            symbol: tag,
            side: "SELL",
            reason: `RSI ${r.toFixed(0)} overbought`,
            strength: 68,
            price: c,
            source: "technical",
          });
        }
      }

      if (i >= 3 && Number.isFinite(closes[i - 3])) {
        const ret = (c - closes[i - 3]) / closes[i - 3];
        if (ret <= -0.04) {
          push({
            rowIndex: row.index,
            date: row.date,
            symbol: tag,
            side: "SELL",
            reason: `3-bar drop ${(ret * 100).toFixed(1)}%`,
            strength: 58,
            price: c,
            source: "technical",
          });
        } else if (ret >= 0.05) {
          push({
            rowIndex: row.index,
            date: row.date,
            symbol: tag,
            side: "BUY",
            reason: `3-bar rally +${(ret * 100).toFixed(1)}%`,
            strength: 58,
            price: c,
            source: "technical",
          });
        }
      }

      const vol = volumes[i];
      const volSma = sma(
        volumes.map((v) => (Number.isFinite(v) ? v : 0)),
        10,
        i
      );
      if (Number.isFinite(vol) && volSma && vol > volSma * 1.7 && i > 0) {
        const up = c > closes[i - 1];
        push({
          rowIndex: row.index,
          date: row.date,
          symbol: tag,
          side: up ? "BUY" : "SELL",
          reason: `Volume ${((vol / volSma) * 100).toFixed(0)}% of 10-bar average`,
          strength: 55,
          price: c,
          source: "technical",
        });
      }
    });
  });

  const count = (side) => signals.filter((s) => s.side === side).length;
  let buyNotional = 0;
  let sellNotional = 0;
  rows.forEach((row) => {
    const side = row.side || (signals.find((s) => s.rowIndex === row.index) || {}).side;
    const n = notional(side, row.quantity, row.price ?? row.close);
    if (n > 0) buyNotional += n;
    if (n < 0) sellNotional += -n;
  });
  const ohlcScore = [columns.open, columns.high, columns.low, columns.close].filter(Boolean).length;
  const mode = columns.side && ohlcScore < 3 ? "blotter" : ohlcScore >= 3 ? "ohlcv" : "mixed";
  const symbols = Array.from(new Set(rows.map((r) => r.symbol).filter(Boolean)));

  return {
    fileName,
    scannedAt: new Date().toISOString(),
    table,
    columns,
    rows,
    signals,
    summary: {
      buys: count("BUY"),
      sells: count("SELL"),
      shorts: count("SHORT"),
      covers: count("COVER"),
      holds: count("HOLD"),
      watches: count("WATCH"),
      netNotional: buyNotional - sellNotional,
      buyNotional,
      sellNotional,
      rowCount: rows.length,
      signalCount: signals.length,
      symbols,
      mode,
    },
  };
}

function scanCsv(text, fileName = "upload.csv") {
  const table = parseCsv(text);
  return scanTable(table, fileName);
}

/** Scan a 2-D array (headers in first row preferred). Useful for Excel. */
function scanArray(data, fileName = "upload.xlsx") {
  const table = parseArray(data);
  return scanTable(table, fileName);
}

window.TradeScanner = {
  parseCsv,
  parseArray,
  scanCsv,
  scanArray,
  scanTable,
};
