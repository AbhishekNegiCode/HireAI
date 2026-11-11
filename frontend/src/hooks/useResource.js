import { useState, useEffect, useCallback } from "react";
import { api, errorMessage } from "../services/api";
export function useResource(url) {
  const [data, setData] = useState(null),
    [loading, setLoading] = useState(true),
    [error, setError] = useState("");
  const reload = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const result = await api.get(url);
      setData(result.data);
    } catch (e) {
      setError(errorMessage(e));
    } finally {
      setLoading(false);
    }
  }, [url]);
  useEffect(() => {
    reload();
  }, [reload]);
  return { data, loading, error, reload, setData };
}
