import type { RecommendationRequest } from "@/types/recommendation";

export default async function recommendation(req: RecommendationRequest) {
	const request = {
		user_id: "leonidas",
		...req

	}
	const response = await fetch("http://localhost:8000/recommendation/", {
		method: "POST",
		headers: {
			"Content-Type": "application/json"
		},
		body: JSON.stringify(request),
	});
	if (!response.ok) throw new Error(`Error on request ${response.body}`);
	return response.json();
}
