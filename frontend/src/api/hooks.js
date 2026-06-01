import { useCallback, useEffect, useState } from "react";
import api from "./client";

// Fetch a list endpoint and give back items + a reload function.
export function useCollection(path) {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);

  const reload = useCallback(async () => {
    setLoading(true);
    try {
      const r = await api.get(path);
      setItems(r.data.results ?? r.data);
    } catch {
      setItems([]);
    } finally {
      setLoading(false);
    }
  }, [path]);

  useEffect(() => { reload(); }, [reload]);
  return { items, loading, reload };
}

// Turn an API error into a friendly, readable message.
export function extractError(err) {
  const d = err?.response?.data;
  if (!d) return "Something went wrong. Please try again.";
  if (typeof d === "string") return d;
  if (d.detail) return d.detail;
  const parts = [];
  for (const k in d) {
    const v = d[k];
    parts.push(Array.isArray(v) ? v.join(" ") : String(v));
  }
  return parts.join(" ") || "Please check the form and try again.";
}
