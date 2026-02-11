export const extendBoundsFromGeoJSON = (bounds, geojson) => {
    geojson.features.forEach(feature => {
        const geometry = feature.geometry;

        const extract = (coords) => {
            if (typeof coords[0] === "number") {
                bounds.extend(coords);
            } else {
                coords.forEach(extract);
            }
        };

        extract(geometry.coordinates);
    });
};
