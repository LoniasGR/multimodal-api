import { layouts, svgArray } from "@mapbox/maki";
import type * as geojson from "geojson";
import L, { DivIcon, type DivIconOptions } from "leaflet";

// biome-ignore-start lint/suspicious/noExplicitAny: Types provided by leaflet
export function point2layer(
	f: geojson.Feature<geojson.Point, any>,
	latlon: L.LatLng,
): L.Layer {
	// biome-ignore-end lint/suspicious/noExplicitAny: reasons
	var fp = f.properties || {};
	var symbol = fp["marker-symbol"] ? `${fp["marker-symbol"]}` : "";
	var color = fp["marker-color"] || "#fff";
	var svg = svgArray[layouts.indexOf(symbol)];
	const coloredSvg = svg.replace(/<path/g, `<path fill="${color}"`);
	return new L.Marker(latlon, {
		icon: new DivIcon({
			html: coloredSvg,
			iconSize: undefined,
			className:
				"rounded-full border border-black bg-white w-5 h-5 align-center justify-items-center",
		} as DivIconOptions),
	});
}
