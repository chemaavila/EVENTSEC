import {
  createContext,
  useContext,
  useState,
  useEffect,
  ReactNode,
  useCallback,
} from "react";
import type { UserProfile } from "../services/api";
import { getMyProfile, login as apiLogin, type ApiError } from "../services/api";

interface AuthContextType {
  user: UserProfile | null;
  token: string | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  loading: boolean;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const logout = useCallback(() => {
    setToken(null);
    setUser(null);
    localStorage.removeItem("auth_token");
    localStorage.removeItem("auth_user");
  }, []);

  const login = async (email: string, password: string) => {
    const response = await apiLogin(email, password);
    setToken(response.access_token);
    setUser(response.user);
    localStorage.setItem("auth_token", response.access_token);
    localStorage.setItem("auth_user", JSON.stringify(response.user));
  };

  useEffect(() => {
    const storedToken = localStorage.getItem("auth_token");
    const storedUser = localStorage.getItem("auth_user");

    if (storedUser) {
      try {
        setUser(JSON.parse(storedUser));
      } catch {
        localStorage.removeItem("auth_user");
      }
    }

    if (!storedToken) {
      setLoading(false);
      return;
    }

    setToken(storedToken);
    getMyProfile()
      .then((profile) => {
        setUser(profile);
        localStorage.setItem("auth_user", JSON.stringify(profile));
      })
      .catch((err: ApiError) => {
        if (err.status === 401) {
          logout();
        } else {
          console.error(err);
        }
      })
      .finally(() => {
        setLoading(false);
      });
  }, [logout]);

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        login,
        logout,
        loading,
        isAuthenticated: !!user && !!token,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}

