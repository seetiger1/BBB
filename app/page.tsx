"use client"

import React, { useEffect, useState } from "react"

type Pool = {
  name: string
  hours: Record<string, string[] | string>
  source_url: string
  fetched_at: string
}

export default function Page() {
  const [pools, setPools] = useState<Pool[] | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [rawResponse, setRawResponse] = useState<string | null>(null)

  // Allow overriding API base in development via NEXT_PUBLIC_API_BASE.
  // If not set, a relative URL is used so deployment on Vercel works out of the box.
  const API_BASE = (process.env.NEXT_PUBLIC_API_BASE as string) || ""
  const fetchUrl = `${API_BASE}/api/pools`

  useEffect(() => {
    let mounted = true
    const load = async () => {
      try {
        const res = await fetch(fetchUrl)
        setRawResponse(`status:${res.status} statusText:${res.statusText}`)
        if (!res.ok) {
          const text = await res.text()
          if (!mounted) return
          setRawResponse(text)
          setError(`HTTP ${res.status} ${res.statusText}`)
          return
        }
        const data = await res.json()
        if (!mounted) return
        setPools(data)
      } catch (err: any) {
        if (!mounted) return
        setError(err?.message ?? String(err))
      }
    }

    load()
    return () => {
      mounted = false
    }
  }, [fetchUrl])

  if (error) {
    return (
      <main style={{ fontFamily: "Arial, sans-serif", padding: 24 }}>
        <h1>Fehler beim Laden</h1>
        <p style={{ color: "red" }}>Fehler: {error}</p>
        <div style={{ backgroundColor: "#f0f0f0", padding: 12, borderRadius: 4, marginTop: 16 }}>
          <p style={{ fontSize: 12, margin: 0 }}>
            <strong>Debug Info:</strong><br />
            Fetch-URL: <code>{fetchUrl}</code><br />
            Status: {rawResponse}
          </p>
        </div>
        <p style={{ fontSize: 12, marginTop: 16 }}>
          Prüfe: Läuft API auf Port 8000? Wurde NEXT_PUBLIC_API_BASE gesetzt?
        </p>
      </main>
    )
  }
  if (!pools) {
    return (
      <main style={{ fontFamily: "Arial, sans-serif", padding: 24 }}>
        <p>⏳ Laden...</p>
        <p style={{ fontSize: 12 }}>Fetch-URL: <code>{fetchUrl}</code></p>
      </main>
    )
  }

  const todayWeekday = new Date().toLocaleDateString("de-DE", { weekday: "long" })

  return (
    <main
      style={{
        fontFamily: "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif",
        padding: "24px",
        maxWidth: "1000px",
        margin: "0 auto",
        backgroundColor: "#f9f9f9",
        minHeight: "100vh",
      }}
    >
      <header style={{ marginBottom: 32 }}>
        <h1 style={{ color: "#0066cc", marginBottom: 8 }}>🏊 Berliner Bäder — Öffnungszeiten</h1>
        <p style={{ color: "#666", fontSize: 16, margin: 0 }}>
          Alle Wochentage (heute: <strong>{todayWeekday}</strong>)
        </p>
      </header>

      <div
        style={{
          display: "grid",
          gap: "20px",
        }}
      >
        {pools.map((pool, idx) => (
          <div
            key={idx}
            style={{
              backgroundColor: "white",
              border: "1px solid #ddd",
              borderRadius: "8px",
              padding: "20px",
              boxShadow: "0 2px 4px rgba(0,0,0,0.05)",
            }}
          >
            <h2 style={{ color: "#0066cc", marginTop: 0, marginBottom: 20, fontSize: 20 }}>
              {pool.name}
            </h2>

            {/* Weekday grid */}
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))",
                gap: "12px",
                marginBottom: 20,
              }}
            >
              {["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"].map(
                (day) => {
                  const isToday = day === todayWeekday
                  const hoursData = pool.hours[day]
                  const hoursArray = Array.isArray(hoursData) ? hoursData : hoursData ? [hoursData] : []

                  return (
                    <div
                      key={day}
                      style={{
                        padding: "12px",
                        borderRadius: "6px",
                        border: isToday ? "2px solid #0066cc" : "1px solid #e0e0e0",
                        backgroundColor: isToday ? "#e8f4f8" : "#f5f5f5",
                        fontWeight: isToday ? 600 : 400,
                      }}
                    >
                      <p style={{ margin: "0 0 6px 0", color: "#333", fontSize: 13 }}>
                        {isToday ? "📍 " : ""}{day}
                      </p>
                      <div style={{ fontSize: 12, color: "#555" }}>
                        {hoursArray.length === 0 ? (
                          <span style={{ color: "#999" }}>Keine Daten</span>
                        ) : (
                          hoursArray.map((hour, i) => (
                            <div
                              key={i}
                              style={{
                                marginBottom: i < hoursArray.length - 1 ? "4px" : 0,
                                whiteSpace: "pre-wrap",
                                wordBreak: "break-word",
                                lineHeight: "1.4",
                              }}
                            >
                              {hour}
                            </div>
                          ))
                        )}
                      </div>
                    </div>
                  )
                }
              )}
            </div>

            <div style={{ borderTop: "1px solid #eee", paddingTop: 12 }}>
              <p style={{ margin: 0, fontSize: 12, color: "#888" }}>
                <strong>Quelle:</strong>{" "}
                <a
                  href={pool.source_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  style={{ color: "#0066cc", textDecoration: "none" }}
                >
                  {pool.source_url.replace("https://", "").replace(/\/$/, "")}
                </a>
              </p>
              <p style={{ margin: "4px 0 0 0", fontSize: 12, color: "#aaa" }}>
                Aktualisiert: {new Date(pool.fetched_at).toLocaleString("de-DE")}
              </p>
            </div>
          </div>
        ))}
      </div>

      <footer style={{ marginTop: 40, paddingTop: 20, borderTop: "1px solid #ddd", textAlign: "center", color: "#888", fontSize: 12 }}>
        <p>Daten werden täglich aktualisiert. Bei Fragen: siehe GitHub Repo.</p>
      </footer>
    </main>
  )
}
