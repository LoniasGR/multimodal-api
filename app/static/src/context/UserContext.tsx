import type React from "react";
import { createContext, type ReactNode, useContext, useState } from "react";

// Define types
interface User {
	username: string;
	name: string;
	age_group: string;
	sex: string;
	location: {
		latitude: number;
		longitude: number;
	};
	is_available: boolean;
	role: string;
}

interface UserContextType {
	user: User | undefined;
	accessToken?: string;
	login: (username: string, password: string) => void;
	logout: () => void;
	isLoggedIn: boolean;
}

// Create context with undefined default
const UserContext = createContext<UserContextType | undefined>(undefined);

// Provider component
interface UserProviderProps {
	children: ReactNode;
}

export const UserProvider: React.FC<UserProviderProps> = ({ children }) => {
	const [user, setUser] = useState<User | undefined>(undefined);
	const [accessToken, setAccessToken] = useState<string | undefined>(undefined);

    if(localStorage.getItem("user") && !user) {
        const storedUser = JSON.parse(localStorage.getItem("user")!);
        setUser(storedUser);
    }
    if(localStorage.getItem("access_token") && !accessToken) {
        const storedToken = localStorage.getItem("access_token")!;
        setAccessToken(storedToken);
    }

	const login = async (username: string, password: string) => {
		const formData = new FormData();
		formData.append("grant_type", "password");
		formData.append("username", username);
		formData.append("password", password);
		const response = await fetch("http://localhost:8000/auth/token", {
			method: "POST",
			body: formData,
		});

		if (!response.ok) {
			throw new Error("Login failed");
		}

		const data = await response.json();
		// Store token in localStorage or sessionStorage
		localStorage.setItem("access_token", data.access_token);
		setAccessToken(data.access_token);

		// Fetch user info
		const userResponse = await fetch("http://localhost:8000/users/me", {
			headers: {
				Authorization: `Bearer ${data.access_token}`,
			},
		});

		const userData = await userResponse.json();
		setUser({
			username: userData.username,
			name: userData.name,
			age_group: userData.age_group,
			sex: userData.sex,
			location: userData.location,
			is_available: userData.is_available,
			role: userData.role,
		});
		localStorage.setItem("user", JSON.stringify(userData));
	};

	const logout = () => {
		// TODO
	};

	return (
		<UserContext.Provider
			value={{
				user,
				accessToken,
				login,
				logout,
				isLoggedIn: user !== undefined,
			}}
		>
			{children}
		</UserContext.Provider>
	);
};

// Custom hook with runtime check
export const useUser = (): UserContextType => {
	const context = useContext(UserContext);
	if (context === undefined) {
		throw new Error("useUser must be used within a UserProvider");
	}
	return context;
};
