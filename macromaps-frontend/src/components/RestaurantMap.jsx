import React from 'react';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

// Fix for default markers in react-leaflet
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
    iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
    iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

// Custom restaurant icon
const restaurantIcon = new L.Icon({
    iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-red.png',
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    shadowSize: [41, 41]
});

// User location icon
const userIcon = new L.Icon({
    iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-blue.png',
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    shadowSize: [41, 41]
});

const RestaurantMap = ({ restaurants, userLocation, onClose }) => {
    if (!restaurants || restaurants.length === 0) {
        return null;
    }

    // Calculate map center and bounds
    const allLocations = [
        userLocation,
        ...restaurants.map(r => ({ lat: r.location.lat, lng: r.location.lng }))
    ];

    const bounds = L.latLngBounds(allLocations.map(loc => [loc.lat, loc.lng]));
    const center = bounds.getCenter();

    const formatRating = (rating) => {
        return rating ? `⭐ ${rating.toFixed(1)}` : 'No rating';
    };

    const formatPriceLevel = (priceLevel) => {
        if (!priceLevel) return '';
        return ` • ${priceLevel}`;
    };

    return (
        <div className="map-overlay">
            <div className="map-container">
                <div className="map-header">
                    <h2>Nearby Restaurants</h2>
                    <button className="close-button" onClick={onClose}>
                        ×
                    </button>
                </div>

                <MapContainer
                    bounds={bounds}
                    boundsOptions={{ padding: [20, 20] }}
                    style={{ height: '500px', width: '100%' }}
                    className="restaurant-map"
                >
                    <TileLayer
                        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                    />

                    {/* User location marker */}
                    <Marker position={[userLocation.lat, userLocation.lng]} icon={userIcon}>
                        <Popup>
                            <div className="popup-content">
                                <strong>Your Location</strong>
                            </div>
                        </Popup>
                    </Marker>

                    {/* Restaurant markers */}
                    {restaurants.map((restaurant, index) => (
                        <Marker
                            key={index}
                            position={[restaurant.location.lat, restaurant.location.lng]}
                            icon={restaurantIcon}
                        >
                            <Popup>
                                <div className="popup-content">
                                    <h3>{restaurant.name}</h3>
                                    <p className="restaurant-category">{restaurant.category}</p>
                                    <p className="restaurant-rating">
                                        {formatRating(restaurant.rating)}
                                        {restaurant.reviewsCount > 0 && ` (${restaurant.reviewsCount} reviews)`}
                                        {formatPriceLevel(restaurant.priceLevel)}
                                    </p>
                                    <p className="restaurant-address">{restaurant.address}</p>
                                    {restaurant.phone && (
                                        <p className="restaurant-phone">📞 {restaurant.phone}</p>
                                    )}
                                    {restaurant.website && (
                                        <p className="restaurant-website">
                                            <a href={restaurant.website} target="_blank" rel="noopener noreferrer">
                                                🌐 Visit Website
                                            </a>
                                        </p>
                                    )}
                                    {restaurant.url && (
                                        <p className="restaurant-maps">
                                            <a href={restaurant.url} target="_blank" rel="noopener noreferrer">
                                                📍 View on Google Maps
                                            </a>
                                        </p>
                                    )}
                                </div>
                            </Popup>
                        </Marker>
                    ))}
                </MapContainer>

                <div className="map-legend">
                    <div className="legend-item">
                        <img src="https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-blue.png" alt="User" width="20" />
                        <span>Your Location</span>
                    </div>
                    <div className="legend-item">
                        <img src="https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-red.png" alt="Restaurant" width="20" />
                        <span>Restaurants</span>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default RestaurantMap; 