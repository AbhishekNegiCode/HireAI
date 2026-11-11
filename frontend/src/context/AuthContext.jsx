import { createContext, useContext, useEffect, useState } from "react";
import { api, setCsrf } from "../services/api";
const AuthContext = createContext(null);
export function AuthProvider({ children }) {
  const [user, setUser] = useState(null),
    [loading, setLoading] = useState(true);
  useEffect(() => {
    api
      .get("/auth/me")
      .then(({ data }) => {
        setUser(data.user);
        setCsrf(data.csrf_token);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);
  const authenticate = async (path, values) => {
    const { data } = await api.post(`/auth/${path}`, values);
    setUser(data.user);
    setCsrf(data.csrf_token);
    return data.user;
  };
  const logout = async () => {
    await api.post("/auth/logout");
    setUser(null);
    setCsrf("");
  };
  return (
    <AuthContext.Provider
      value={{ user, loading, authenticate, logout, setUser }}
    >
      {children}
    </AuthContext.Provider>
  );
}
export const useAuth = () => useContext(AuthContext);
