import { useCallback, useState, type ReactNode } from "react";

import { loginAccount } from "../lib/api";
import { AuthContext, type AuthSession } from "./auth-context";

export function AuthProvider({ children }: {children: ReactNode}) {
    const [session, setSession] = useState<AuthSession | null>(null);
    
    async function login(email: string, password: string): Promise<void> {
        const result = await loginAccount({ email, password});

        setSession({
            accessToken: result.access_token,
            user: result.user,
        });
    }

    const logout = useCallback((): void => {
        setSession(null);
    }, []);

    return (
        <AuthContext.Provider value={{session, login, logout}}>
            {children}
        </AuthContext.Provider>
    );
}