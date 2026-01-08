import {
  createContext,
  useContext,
  useState,
  useEffect,
  ReactNode,
  useCallback,
} from "react";
import type { UserProfile } from "../services/api";
import {
  getMyProfile,
  login as apiLogin,
  logout as apiLogout,
} from "../services/api";
import type { ApiError } from "../services/http";

interface AuthContextType {
  user: UserProfile | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  loading: boolean;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const accessTokenKey = "eventsec_access_token";

  const localLogout = useCallback(() => {
    setUser(null);
    if (typeof window !== "undefined") {
      window.localStorage.removeItem(accessTokenKey);
    }
  }, []);

  const logout = useCallback(() => {
    localLogout();
    apiLogout().catch(() => {
      /* ignore network errors */
    });
  }, [localLogout]);

  const login = async (email: string, password: string) => {
    const response = await apiLogin(email, password);
    if (typeof window !== "undefined") {
      window.localStorage.setItem(accessTokenKey, response.access_token);
    }
    setUser(response.user);
  };

  useEffect(() => {
    getMyProfile()
      .then((profile) => {
        setUser(profile);
      })
      .catch((err: ApiError) => {
        if (err.status === 401) {
          localLogout();
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
        login,
        logout,
        loading,
        isAuthenticated: !!user,
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
