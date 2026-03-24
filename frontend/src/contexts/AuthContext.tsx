import React, { createContext, useContext, useState, useEffect, ReactNode } from "react";
import { getUser, clearTokens, getAccessToken } from "@/lib/api";

interface User {
  id: string;
  full_name: string;
  email: string;
  role: string;
  company: string;
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  setUserState: (user: User | null) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  isAuthenticated: false,
  setUserState: () => {},
  logout: () => {},
});

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(getUser());

  const isAuthenticated = !!user && !!getAccessToken();

  const setUserState = (u: User | null) => {
    setUser(u);
  };

  const logout = () => {
    clearTokens();
    setUser(null);
    window.location.href = "/";
  };

  return (
    <AuthContext.Provider value={{ user, isAuthenticated, setUserState, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
