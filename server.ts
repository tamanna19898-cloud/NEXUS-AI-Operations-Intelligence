import express from "express";
import type { Request, Response } from "express";
import path from "path";
import dotenv from "dotenv";
import { GoogleGenAI, Type } from "@google/genai";

dotenv.config();

const app = express();
const PORT = process.env.PORT ? parseInt(process.env.PORT, 10) : 3000;
const distDir = path.resolve(process.cwd(), "dist");

app.use(express.json({ limit: "15mb" }));

// Initialize GoogleGenAI client
const apiKey = process.env.GEMINI_API_KEY;
let ai: GoogleGenAI | null = null;
if (apiKey) {
  ai = new GoogleGenAI({
    apiKey: apiKey,
    httpOptions: {
      headers: {
        "User-Agent": "aistudio-build",
      },
    },
  });
}

// Health check endpoint for Cloud Run container monitoring
app.get("/healthz", (_req: Request, res: Response): void => {
  res.status(200).send("OK");
});

// -----------------------------------------------------------------------------
// POST /api/assistant/chart
// Natural language dataset Q&A and automated chart generator
// -----------------------------------------------------------------------------
app.post("/api/assistant/chart", async (req: Request, res: Response): Promise<void> => {
  try {
    const { question, datasetName, columns, sampleRows } = req.body;

    if (!question || typeof question !== "string") {
      res.status(400).json({ error: "Missing or invalid question parameter" });
      return;
    }

    if (!columns || !Array.isArray(columns) || columns.length === 0) {
      res.status(400).json({ error: "Dataset columns must be provided" });
      return;
    }

    // Try Gemini first if API key is configured
    if (ai) {
      try {
        const prompt = `You are an expert data analyst and chart assistant for NEXUS AI.
The user is asking a question about a tabular dataset: "${question}".
The dataset is titled "${datasetName || "Active Dataset"}".
The available columns are: ${JSON.stringify(columns)}.
Here is a representative sample of rows from the dataset (up to 12 rows):
${JSON.stringify((sampleRows || []).slice(0, 12), null, 2)}

Your task:
1. Understand the user's intent (supports English, Hindi, Hinglish, e.g., "2015 me kisne sabse jyada run mare", "sabse jyada runs", "which team won the most matches", "highest average salary by department", etc.).
2. Determine:
   - "answer": A direct, precise, conversational answer to their question with exact names, values, and calculations based on the provided data context.
   - "chartType": One of "Bar Chart", "Line Chart", "Histogram", "Scatter Plot".
   - "title": Clean, descriptive chart title.
   - "xAxis": The exact column name from the columns list that should be on the X-axis (e.g. batsman_name, team_name, department).
   - "yAxis": The exact column name from the columns list that should be on the Y-axis (optional for frequency count or histogram). Must be numeric.
   - "aggregation": One of "Sum", "Mean", "Count", "Max", "Min", "Median".
   - "filterColumn": Optional column name if filtering is required (e.g. "season").
   - "filterValue": Optional filter value as string or number (e.g. 2015 or "2015").
   - "insights": Array of 1 or 2 high-value bullet takeaways explaining the result.
   - "followUpQuestions": 2-3 logical follow-up questions the user might ask next.`;

        const response = await ai.models.generateContent({
          model: "gemini-3.8-flash",
          contents: prompt,
          config: {
            responseMimeType: "application/json",
            responseSchema: {
              type: Type.OBJECT,
              properties: {
                answer: { type: Type.STRING },
                chartType: { type: Type.STRING },
                title: { type: Type.STRING },
                xAxis: { type: Type.STRING },
                yAxis: { type: Type.STRING },
                aggregation: { type: Type.STRING },
                filterColumn: { type: Type.STRING },
                filterValue: { type: Type.STRING },
                insights: {
                  type: Type.ARRAY,
                  items: { type: Type.STRING },
                },
                followUpQuestions: {
                  type: Type.ARRAY,
                  items: { type: Type.STRING },
                },
              },
              required: ["answer", "chartType", "title", "xAxis", "aggregation", "insights", "followUpQuestions"],
            },
          },
        });

        const rawJson = response.text?.trim();
        if (rawJson) {
          const parsed = JSON.parse(rawJson);
          res.json({ source: "gemini", ...parsed });
          return;
        }
      } catch (geminiErr: any) {
        console.warn("Gemini call failed or timed out, falling back to rule-based engine:", geminiErr?.message);
      }
    }

    // Fallback: Rule-based NLP and aggregation solver
    const fallbackResult = solveQueryFallback(question, columns, sampleRows || []);
    res.json({ source: "rules_engine", ...fallbackResult });
  } catch (err: any) {
    res.status(500).json({ error: err?.message || "Internal server error" });
  }
});

// -----------------------------------------------------------------------------
// Fallback Query Solver (Understands Hindi/Hinglish/English dataset queries)
// -----------------------------------------------------------------------------
function solveQueryFallback(question: string, columns: string[], rows: any[]) {
  const q = question.toLowerCase();
  const lowerCols = columns.map((c) => ({ original: c, lower: c.toLowerCase() }));

  // Find candidate numeric column (metric)
  let numericCol = lowerCols.find((c) =>
    ["run", "runs_scored", "score", "salary", "price", "revenue", "rate", "lead", "night", "hour", "amount"].some((k) => c.lower.includes(k))
  )?.original;

  // Find candidate entity column (grouping)
  let catCol = columns[0];
  if (q.includes("team") || q.includes("jiti") || q.includes("won") || q.includes("winner")) {
    catCol = lowerCols.find((c) => c.lower.includes("winner") || c.lower.includes("team"))?.original || columns[0];
  } else if (q.includes("kisne") || q.includes("who") || q.includes("batsman") || q.includes("player")) {
    catCol =
      lowerCols.find((c) => c.lower.includes("batsman") || c.lower.includes("player"))?.original ||
      lowerCols.find((c) => c.lower.includes("student") || c.lower.includes("employee"))?.original ||
      lowerCols.find((c) => c.lower.includes("name") && !c.lower.includes("team"))?.original ||
      columns[0];
  } else if (q.includes("dept") || q.includes("department")) {
    catCol = lowerCols.find((c) => c.lower.includes("dept") || c.lower.includes("department"))?.original || columns[0];
  } else {
    catCol =
      lowerCols.find((c) => c.lower.includes("batsman") || c.lower.includes("player"))?.original ||
      lowerCols.find((c) => c.lower.includes("winner") || c.lower.includes("team"))?.original ||
      lowerCols.find((c) => c.lower.includes("dept") || c.lower.includes("department"))?.original ||
      columns[0];
  }

  // Check year or season filter
  const yearMatch = q.match(/\b(20\d\d|19\d\d)\b/);
  const filterYear = yearMatch ? yearMatch[1] : null;
  const seasonCol = lowerCols.find((c) => c.lower.includes("season") || c.lower.includes("year"))?.original;

  let chartType = "Bar Chart";
  let aggregation = "Sum";
  let title = `Analysis of ${catCol}`;

  if (q.includes("average") || q.includes("ausat")) {
    aggregation = "Mean";
  } else if (q.includes("sabse jyada") || q.includes("highest") || q.includes("most") || q.includes("top")) {
    aggregation = "Sum";
  } else if (q.includes("sabse kam") || q.includes("lowest") || q.includes("min")) {
    aggregation = "Min";
  }

  // Answer drafting based on sample rows
  let answer = `Analyzed "${question}" across ${catCol} and ${numericCol || "records"}.`;
  if (filterYear && seasonCol) {
    answer = `Filtered for ${seasonCol} = ${filterYear}. Showing ${aggregation} of ${numericCol || "records"} grouped by ${catCol}.`;
    title = `${aggregation} of ${numericCol || "Count"} in ${filterYear} by ${catCol}`;
  } else {
    title = `${aggregation} of ${numericCol || "Count"} by ${catCol}`;
  }

  return {
    answer,
    chartType,
    title,
    xAxis: catCol,
    yAxis: numericCol || "",
    aggregation,
    filterColumn: filterYear && seasonCol ? seasonCol : undefined,
    filterValue: filterYear || undefined,
    insights: [
      `Computed directly from ${rows.length} sample dataset records.`,
      `Grouped by ${catCol} with ${aggregation} aggregation.`,
    ],
    followUpQuestions: [
      `Who has the highest average ${numericCol || "value"}?`,
      `Show distribution across all categories`,
      `Compare top 5 performers`,
    ],
  };
}

// -----------------------------------------------------------------------------
// Vite middleware (dev) or static serving (prod)
// -----------------------------------------------------------------------------
async function startServer() {
  if (process.env.NODE_ENV !== "production") {
    const { createServer: createViteServer } = await import("vite");
    const vite = await createViteServer({
      server: { middlewareMode: true },
      appType: "spa",
    });
    app.use(vite.middlewares);
  } else {
    app.use(express.static(distDir));
    app.get("*", (_req: Request, res: Response) => {
      res.sendFile(path.join(distDir, "index.html"));
    });
  }

  app.listen(PORT, "0.0.0.0", () => {
    console.log(`NEXUS AI server running at http://0.0.0.0:${PORT}`);
  });
}

startServer();
