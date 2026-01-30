"use client"

import React, { useEffect, useState } from "react"

type Pool = {
  name: string
  hours: Record<string, string>
  source_url: string
  fetched_at: string
}

export default function Page() {
  const [pools, setPools] = useState<Pool[] | null>(null)
  const [error, setError] = useState<string | null>(null)

  // Allow overriding API base in development via NEXT_PUBLIC_API_BASE.
  // If not set, a relative URL is used so deployment on Vercel works out of the box.
  const API_BASE = (process.env.NEXT_PUBLIC_API_BASE as string) || ""

  useEffect(() => {
    fetch(`${API_BASE}/api/pools`)
      .then((res) => {
        if (!res.ok) throw new Error(res.statusText)
        return res.json()
      })
      .then((data) => setPools(data))
      .catch((err) => setError(String(err)))
  }, [])

  if (error) return <div>Fehler: {error}</div>
  if (!pools) return <div>Lade...</div>

  const todayWeekday = new Date().toLocaleDateString("de-DE", { weekday: "long" })

  return (
    <main style={{ fontFamily: "Arial, sans-serif", padding: 24 }}>
      <h1>Berliner Bäder — Öffnungszeiten</h1>
      <p>Heute: {todayWeekday}</p>
      <ul>
        {pools.map((pool, idx) => (
          <li key={idx} style={{ marginBottom: 12 }}>
            <strong>{pool.name}</strong>
            <div>Heute: {pool.hours[todayWeekday] ?? "Keine Daten"}</div>
            <div style={{ fontSize: 12 }}>
              Quelle: <a href={pool.source_url}>{pool.source_url}</a>
            </div>
            <div style={{ fontSize: 12 }}>Aktualisiert: {pool.fetched_at}</div>
          </li>
        ))}
      </ul>
    </main>
  )
}
