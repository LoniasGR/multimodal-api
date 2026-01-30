import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import MultimodalMap from "@/components/MultimodalMap/MultimodalMap.tsx";
import "./index.css";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { createBrowserRouter } from "react-router";
import { RouterProvider } from "react-router/dom";
import { UserProvider } from "./context/UserContext";

const root = document.getElementById("root") as HTMLElement;
const queryClient = new QueryClient();

const router = createBrowserRouter([
	{
		path: "/",
		element: <MultimodalMap />,
	},
]);

createRoot(root).render(
	<StrictMode>
		<QueryClientProvider client={queryClient}>
			<UserProvider>
				<RouterProvider router={router} />,
			</UserProvider>
		</QueryClientProvider>
	</StrictMode>,
);
