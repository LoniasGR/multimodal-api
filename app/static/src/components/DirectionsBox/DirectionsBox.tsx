import { useMutation } from "@tanstack/react-query";
import { useGeolocated } from "react-geolocated";
import { useAppForm } from "@/hooks/navigation-form";
import recommendation from "@/services/recommendation";
import type { RecommendationRequest } from "@/types/recommendation";

interface DirectionsBoxProps {
	setGeoJSON: (value: string) => void;
}

export default function DirectionsBox({ setGeoJSON }: DirectionsBoxProps) {
	const { mutateAsync } = useMutation({
		mutationFn: recommendation,
	});

	const { coords, isGeolocationAvailable, isGeolocationEnabled } =
		useGeolocated({
			positionOptions: {
				enableHighAccuracy: true,
			},
			userDecisionTimeout: 5000,
		});

	const defaultValues: RecommendationRequest = {
		origin:
			isGeolocationAvailable && isGeolocationEnabled && coords
				? `{${coords.latitude}, ${coords.longitude}}`
				: "",
		destination: "",
		mode: "total_duration",
		walk: false,
		car: false,
		escooter: false,
		sea_vessel: false,
	};

	const form = useAppForm({
		defaultValues: defaultValues,
		onSubmit: async ({ value }) => {
			// Do something with form data
			await mutateAsync(value, {
				onSuccess: (data) => {
					setGeoJSON(data);
				},
			});
			alert(JSON.stringify(value, null, 2));
		},
	});
	return (
		<form
			className="leaflet-overlay-pane relative w-xs bg-white mt-2 ml-2 pointer-events-auto"
			onSubmit={(e) => {
				e.preventDefault();
				form.handleSubmit();
			}}
		>
			<div className="pt-2 flex">
				<form.AppField name="origin">
					{(field) => (
						<field.TextField
							label="Origin Latitude"
							placeholder="{latitude, longitude}"
						/>
					)}
				</form.AppField>
			</div>
			<div className="flex">
				<form.AppField name="destination">
					{(field) => (
						<field.TextField
							label="Destination"
							placeholder="{latitude, longitude}"
						/>
					)}
				</form.AppField>
			</div>
			<form.AppField
				name="mode"
				validators={{
					onBlur: ({ value }) => {
						if (!value || value.trim().length === 0) {
							return "Mode is required";
						}
						return undefined;
					},
				}}
			>
				{(field) => (
					<field.Select
						label="Focus on parameter"
						values={[
							{ label: "Edges", value: "edges" },
							{ label: "Total Distance", value: "total_distance" },
							{ label: "Total Duration", value: "total_duration" },
							{ label: "Total Cost", value: "total_cost" },
							{ label: "Walk Count", value: "walk_count" },
							{ label: "Walk Distance", value: "walk_distance" },
							{ label: "Car Count", value: "car_count" },
							{ label: "Car Distance", value: "car_distance" },
							{ label: "E-scooter Count", value: "escooter_count" },
							{ label: "E-scooter Distance", value: "escooter_distance" },
							{ label: "Sea Vessel Count", value: "se_vessel_count" },
							{ label: "Sea Vessel Distance", value: "se_vessel_distance" },
						]}
						placeholder="Select a Parameter"
					/>
				)}
			</form.AppField>
			<div className="flex ml-5 flex-col">
				<h1 className="text-xl font-bold tracking-tight text-balance mb-2 mt-2">
					Exclude vehicles
				</h1>
				<div className="flex flex-col justify-center gap-1 mb-5">
					<form.AppField name="walk">
						{(field) => <field.PickOne label="walk" value="Walking" />}
					</form.AppField>
					<form.AppField name="car">
						{(field) => <field.PickOne label="car" value="Car" />}
					</form.AppField>
					<form.AppField name="escooter">
						{(field) => <field.PickOne label="escooter" value="E-Scooter" />}
					</form.AppField>
					<form.AppField name="sea_vessel">
						{(field) => <field.PickOne label="sea_vessel" value="Sea Vessel" />}
					</form.AppField>
				</div>
			</div>
			<form.AppForm>
				<div className="flex pb-2">
					<form.SubmitButton label="Go" />
				</div>
			</form.AppForm>
		</form>
	);
}
