declare module '@mapbox/maki' {
	const layouts: string[];
    const svgArray: string[];

    export type Maki = {
        layouts: string[];
        svgArray: string[];
    };

    export const maki: Maki;
}