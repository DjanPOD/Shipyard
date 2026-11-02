import { createContext } from "react";

import type { User } from "../lib/api";

export type AuthSession = {
    accessToken: string;
    user: User;
};

export type AuthContextValue = {
    session: AuthSession | null;
    login: (email: string, password: string) => Promise<void>;
    logout: () => void;
};

export const AuthContext = createContext<AuthContextValue | undefined>(
    undefined,
);