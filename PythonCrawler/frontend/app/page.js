"use client";

import { useState } from "react";
import Button from "@mui/material/Button";
import Stack from "@mui/material/Stack";
import TextField from "@mui/material/TextField";
import { callCrawler } from "./fetchCrawlerInfo";

function Header({ title }) {
  return <h1>{title || "Default title"}</h1>;
}

function tryParseJson(value) {
  if (!value || typeof value !== "string") return null;
  try {
    return JSON.parse(value);
  } catch {
    return null;
  }
}

export default function HomePage() {
  const [loading, setLoading] = useState(false);
  const [crawlerData, setCrawlerData] = useState(null);
  const [error, setError] = useState(null);

  const [url, setUrl] = useState("http://juice-shop:3000/#/");
  const [maxPages, setMaxPages] = useState(10);

  async function handleCrawler() {
    try {
      setLoading(true);
      setError(null);

      const data = await callCrawler({
        url,
        maxPages: Number(maxPages),
      });

      setCrawlerData(data);
    } catch (err) {
      console.error("Crawler Error:", err);
      setError(err.message || "Unbekannter Fehler");
    } finally {
      setLoading(false);
    }
  }

  const targets = crawlerData?.db_results?.targets || [];

  let totalForms = 0;
  let totalVulns = 0;
  let totalCreds = 0;

  for (const entry of targets) {
    totalForms += entry.forms?.length || 0;
    totalVulns += entry.vulnerabilities?.length || 0;
    totalCreds += entry.credentials?.length || 0;
  }

  const run = crawlerData?.db_results?.run;
  const reportPath = run?.[5];
  const reportCreatedAt = run?.[6];

  const reportFilename = reportPath
    ? reportPath.split(/[\\/]/).pop()
    : null;

  const reportBaseUrl =
    process.env.NEXT_PUBLIC_REPORT_BASE_URL || "http://localhost:8000";

  const reportDownloadUrl = reportFilename
    ? `${reportBaseUrl}/reports/${encodeURIComponent(reportFilename)}`
    : null;

  return (
    <div>
      <Header title="Crawler Dashboard" />

      <Stack direction="column" spacing={2} sx={{ maxWidth: 500, mt: 2 }}>
        <TextField
          label="Crawler URL"
          variant="outlined"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          fullWidth
        />

        <TextField
          label="Max Pages"
          variant="outlined"
          type="number"
          value={maxPages}
          onChange={(e) => setMaxPages(e.target.value)}
          inputProps={{ min: 1 }}
          fullWidth
        />

        <Button
          variant="outlined"
          onClick={handleCrawler}
          disabled={loading || !url.trim()}
        >
          {loading ? "Running..." : "Run Crawler"}
        </Button>
      </Stack>

      {loading && (
        <div style={{ marginTop: "20px" }}>
          <p>Fetching crawler data...</p>
        </div>
      )}

      {error && (
        <div style={{ marginTop: "20px", color: "red" }}>
          <strong>Fehler:</strong> {error}
        </div>
      )}

      {crawlerData && (
        <div style={{ marginTop: "20px" }}>
          <h2>Zusammenfassung</h2>
          <p>Run ID: {crawlerData.run_id}</p>
          <p>Targets: {targets.length}</p>
          <p>Forms: {totalForms}</p>
          <p>Vulnerabilities: {totalVulns}</p>
          <p>Credentials: {totalCreds}</p>

          {reportDownloadUrl && (
            <div style={{ marginTop: "20px", marginBottom: "20px" }}>
              <h2>Report</h2>
              <p><strong>Datei:</strong> {reportFilename}</p>
              <p><strong>Erstellt am:</strong> {reportCreatedAt || "unbekannt"}</p>

              <Button
                variant="contained"
                component="a"
                href={reportDownloadUrl}
                target="_blank"
                rel="noopener noreferrer"
              >
                Report herunterladen
              </Button>
            </div>
          )}

          <div style={{ padding: "12px", overflowX: "auto" }}>
          <h2>Run</h2>
            {JSON.stringify(crawlerData.db_results?.run, null, 2)}
          </div>

          <h2>Targets</h2>
          {targets.map((entry, index) => {
            const target = entry.target;
            const targetUrl = target?.[2];
            const headersJson = target?.[3];
            const parsedHeaders = tryParseJson(headersJson);

            return (
              <div
                key={index}
                style={{
                  border: "1px solid #ccc",
                  padding: "16px",
                  marginBottom: "20px",
                  borderRadius: "8px",
                }}
              >
                <h3>TARGET #{index + 1}</h3>

                <p><strong>Target ID:</strong> {target?.[0]}</p>
                <p><strong>Run ID:</strong> {target?.[1]}</p>
                <p><strong>URL:</strong> {targetUrl}</p>

                <details>
                  <summary>Headers anzeigen</summary>
                  <pre style={{ background: "rgb(28, 49, 71)", padding: "12px", overflowX: "auto" }}>
                    {JSON.stringify(parsedHeaders ?? headersJson, null, 2)}
                  </pre>
                </details>

                <h4>Forms</h4>
                {entry.forms?.length ? (
                  <ul>
                    {entry.forms.map((form, formIndex) => {
                      const parsedForm = tryParseJson(form?.[6]);

                      return (
                        <li key={formIndex} style={{ marginBottom: "12px" }}>
                          <div><strong>Form ID:</strong> {form?.[0]}</div>
                          <div><strong>URL:</strong> {form?.[2]}</div>
                          <div><strong>Intent:</strong> {form?.[5]}</div>

                          <details>
                            <summary>Form anzeigen</summary>
                            <pre style={{ background: "#000000", padding: "12px", overflowX: "auto" }}>
                              {JSON.stringify(parsedForm ?? form, null, 2)}
                            </pre>
                          </details>
                        </li>
                      );
                    })}
                  </ul>
                ) : (
                  <p>Keine Forms vorhanden.</p>
                )}

                <h4>Vulnerabilities</h4>
                {entry.vulnerabilities?.length ? (
                  <ul>
                    {entry.vulnerabilities.map((vuln, vulnIndex) => (
                      <li key={vulnIndex} style={{ marginBottom: "12px" }}>
                        <div><strong>Typ:</strong> {vuln?.[4]}</div>
                        <div><strong>Severity:</strong> {vuln?.[5]}</div>
                        <div><strong>Parameter:</strong> {vuln?.[6]}</div>
                        <div><strong>Payload:</strong> {vuln?.[7]}</div>
                        <div><strong>Evidence:</strong> {vuln?.[8]}</div>
                        <div><strong>Status:</strong> {vuln?.[9]}</div>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p>Keine Vulnerabilities vorhanden.</p>
                )}

                <h4>Credentials</h4>
                {entry.credentials?.length ? (
                  <ul>
                    {entry.credentials.map((cred, credIndex) => (
                      <li key={credIndex} style={{ marginBottom: "12px" }}>
                        <div><strong>Token:</strong> {cred?.[3]}</div>
                        <div><strong>Username/Payload:</strong> {cred?.[4]}</div>
                        <div><strong>Password:</strong> {cred?.[5]}</div>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p>Keine Credentials vorhanden.</p>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}