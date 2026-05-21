import React, { createContext, useContext, useState, useEffect } from 'react';
import { useNavigate } from 'react-router';
import { api, API_BASE_URL } from '../../api/client';

interface User {
    id: string;
    username: string;
    email: string;
    role: string;
    is_active: boolean;
}

interface AuthContextType {
    user: User | null;
    token: string | null;
    login: (token: string) => Promise<void>;
    logout: () => void;
    isLoading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const [user, setUser] = useState<User | null>(null);
    const [token, setToken] = useState<string | null>(localStorage.getItem('token'));
    const [isLoading, setIsLoading] = useState(true);
    const navigate = useNavigate();

    useEffect(() => {
        const initAuth = async () => {
            if (token) {
                try {
                    // Set token globally for API calls
                    api.setToken(token);

                    // Fetch current user details
                    const response = await fetch(`${API_BASE_URL}/auth/me`, {
                        headers: { Authorization: `Bearer ${token}` }
                    });

                    if (response.ok) {
                        const userData = await response.json();
                        setUser(userData);
                    } else {
                        // Token invalid or expired
                        handleLogout();
                    }
                } catch (error) {
                    console.error("Failed to fetch user:", error);
                    handleLogout();
                }
            }
            setIsLoading(false);
        };

        initAuth();
    }, [token]);

    const handleLogin = async (newToken: string) => {
        localStorage.setItem('token', newToken);
        setToken(newToken);
        api.setToken(newToken);

        try {
            const response = await fetch(`${API_BASE_URL}/auth/me`, {
                headers: { Authorization: `Bearer ${newToken}` }
            });
            if (response.ok) {
                const userData = await response.json();
                setUser(userData);
                navigate('/');
            } else {
                handleLogout();
            }
        } catch {
            handleLogout();
        }
    };

    const handleLogout = () => {
        localStorage.removeItem('token');
        setToken(null);
        setUser(null);
        api.setToken(null);
        navigate('/login');
    };

    return (
        <AuthContext.Provider value={{ user, token, login: handleLogin, logout: handleLogout, isLoading }}>
            {!isLoading && children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
};
