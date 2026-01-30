import { useState } from "react";
import { useGeolocated } from "react-geolocated";
import { MapContainer, Marker, TileLayer, ZoomControl } from "react-leaflet";
import { GeoJSON } from "react-leaflet/GeoJSON";
import DirectionsBox from "@/components/DirectionsBox/DirectionsBox";
import { position } from "@/lib/constants";
import { point2layer } from "@/lib/leaflet-utils";
import "leaflet/dist/leaflet.css";
import LoginPrompt from "@/components/Login/LoginPromt";
import { useUser } from "@/context/UserContext";

export default function MultimodalMap() {
	const [geojson, setGeoJSON] = useState("");
  const { isLoggedIn } = useUser();

	const { coords, isGeolocationAvailable, isGeolocationEnabled } =
		useGeolocated({
			positionOptions: {
				enableHighAccuracy: true,
			},
			watchPosition: true,
			userDecisionTimeout: 5000,
		});

	return (
		<MapContainer
			className="h-screen w-screen"
			center={position}
			zoom={13}
			scrollWheelZoom={true}
			zoomControl={false}
		>
			<TileLayer
				attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
				url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
			/>
			{isLoggedIn ? <DirectionsBox setGeoJSON={setGeoJSON} /> : <LoginPrompt />}

			<ZoomControl position="bottomleft" />
			{geojson !== "" && (
				<GeoJSON data={JSON.parse(geojson)} pointToLayer={point2layer} />
			)}
			{isGeolocationAvailable && isGeolocationEnabled && coords && (
				<Marker position={[coords.latitude, coords.longitude]} />
			)}
		</MapContainer>
	);
}
