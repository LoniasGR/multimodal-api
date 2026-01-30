export interface RecommendationRequest {
	origin: string;
	destination: string;
	mode: string;
	walk: boolean;
	car: boolean;
	escooter: boolean;
	sea_vessel: boolean;
}
