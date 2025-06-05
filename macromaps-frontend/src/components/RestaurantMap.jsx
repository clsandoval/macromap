import React, { useState, useMemo } from 'react';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { ChevronUp, ChevronDown } from 'lucide-react';

// Fix for default markers in react-leaflet
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
    iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
    iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

// Create modern restaurant icon
const createRestaurantIcon = () => {
    const svgString = `
        <svg width="32" height="40" viewBox="0 0 32 40" xmlns="http://www.w3.org/2000/svg">
            <path d="M16 0C7.16 0 0 7.16 0 16C0 28 16 40 16 40S32 28 32 16C32 7.16 24.84 0 16 0Z" fill="#22c55e"/>
            <circle cx="16" cy="16" r="10" fill="white"/>
            <path d="M20 12H12C11.45 12 11 12.45 11 13V19C11 19.55 11.45 20 12 20H20C20.55 20 21 19.55 21 19V13C21 12.45 20.55 12 20 12ZM19 18H13V14H19V18Z" fill="#22c55e"/>
            <path d="M16 9C17.1 9 18 9.9 18 11V12H14V11C14 9.9 14.9 9 16 9Z" fill="#22c55e"/>
        </svg>
    `;

    return new L.DivIcon({
        html: svgString,
        className: 'custom-restaurant-marker',
        iconSize: [32, 40],
        iconAnchor: [16, 40],
        popupAnchor: [0, -40]
    });
};

// Create modern user location icon
const createUserIcon = () => {
    const svgString = `
        <svg width="28" height="36" viewBox="0 0 28 36" xmlns="http://www.w3.org/2000/svg">
            <path d="M14 0C6.27 0 0 6.27 0 14C0 24.5 14 36 14 36S28 24.5 28 14C28 6.27 21.73 0 14 0Z" fill="#3b82f6"/>
            <circle cx="14" cy="14" r="8" fill="white"/>
            <circle cx="14" cy="14" r="4" fill="#3b82f6"/>
        </svg>
    `;

    return new L.DivIcon({
        html: svgString,
        className: 'custom-user-marker',
        iconSize: [28, 36],
        iconAnchor: [14, 36],
        popupAnchor: [0, -36]
    });
};

const restaurantIcon = createRestaurantIcon();
const userIcon = createUserIcon();

// Helper function to get value for sorting
const getSortValue = (item, field) => {
    switch (field) {
        case 'name':
            return item.name?.toLowerCase() || '';
        case 'calories':
            return item.nutrition?.calories || 0;
        case 'protein':
            return item.nutrition?.protein || 0;
        case 'carbs':
            return item.nutrition?.carbs || 0;
        case 'fat':
            return item.nutrition?.fat || 0;
        case 'price':
            return item.price || 0;
        case 'distance':
            return item.restaurantDistance || 0;
        case 'rating':
            return item.restaurantRating || 0;
        default:
            return 0;
    }
};

// Calculate ratio for menu items
const calculateRatio = (item, numerator, denominator) => {
    const numValue = getSortValue(item, numerator);
    const denValue = getSortValue(item, denominator);

    if (denValue === 0) return 0;
    return numValue / denValue;
};

const RestaurantMap = ({ restaurants, userLocation, onClose }) => {
    const [sortField, setSortField] = useState('distance');
    const [sortDirection, setSortDirection] = useState('asc');
    const [selectedRestaurant, setSelectedRestaurant] = useState(null);
    const [viewMode, setViewMode] = useState('restaurants'); // 'restaurants' or 'menu_items'
    const [showRatioSort, setShowRatioSort] = useState(false);
    const [ratioNumerator, setRatioNumerator] = useState('protein');
    const [ratioDenominator, setRatioDenominator] = useState('price');

    // Calculate distance between two points in km
    const calculateDistance = (lat1, lng1, lat2, lng2) => {
        const R = 6371; // Earth's radius in km
        const dLat = (lat2 - lat1) * Math.PI / 180;
        const dLng = (lng2 - lng1) * Math.PI / 180;
        const a =
            Math.sin(dLat / 2) * Math.sin(dLat / 2) +
            Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
            Math.sin(dLng / 2) * Math.sin(dLng / 2);
        const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
        return R * c;
    };

    // Add distance to restaurants
    const restaurantsWithDistance = useMemo(() => {
        if (!restaurants || restaurants.length === 0) {
            return [];
        }
        return restaurants.map(restaurant => ({
            ...restaurant,
            distance: calculateDistance(
                userLocation.lat,
                userLocation.lng,
                restaurant.location.lat,
                restaurant.location.lng
            )
        }));
    }, [restaurants, userLocation]);

    // Create flat list of menu items with restaurant info
    const allMenuItems = useMemo(() => {
        const items = [];
        restaurantsWithDistance.forEach(restaurant => {
            if (restaurant.menuItems && restaurant.menuItems.length > 0) {
                restaurant.menuItems.forEach(item => {
                    items.push({
                        ...item,
                        restaurantName: restaurant.name,
                        restaurantDistance: restaurant.distance,
                        restaurantLocation: restaurant.location,
                        restaurantCategory: restaurant.category,
                        restaurantRating: restaurant.rating
                    });
                });
            }
        });
        return items;
    }, [restaurantsWithDistance]);

    // Sort restaurants
    const sortedRestaurants = useMemo(() => {
        return [...restaurantsWithDistance].sort((a, b) => {
            let aValue, bValue;

            switch (sortField) {
                case 'name':
                    aValue = a.name.toLowerCase();
                    bValue = b.name.toLowerCase();
                    break;
                case 'rating':
                    aValue = a.rating || 0;
                    bValue = b.rating || 0;
                    break;
                case 'reviewsCount':
                    aValue = a.reviewsCount || 0;
                    bValue = b.reviewsCount || 0;
                    break;
                case 'distance':
                    aValue = a.distance;
                    bValue = b.distance;
                    break;
                case 'priceLevel':
                    aValue = a.priceLevel ? a.priceLevel.length : 0;
                    bValue = b.priceLevel ? b.priceLevel.length : 0;
                    break;
                default:
                    aValue = a.distance;
                    bValue = b.distance;
            }

            if (sortDirection === 'asc') {
                return aValue < bValue ? -1 : aValue > bValue ? 1 : 0;
            } else {
                return aValue > bValue ? -1 : aValue < bValue ? 1 : 0;
            }
        });
    }, [restaurantsWithDistance, sortField, sortDirection]);

    // Sort menu items
    const sortedMenuItems = useMemo(() => {
        return [...allMenuItems].sort((a, b) => {
            let aValue, bValue;

            if (sortField === 'ratio') {
                aValue = calculateRatio(a, ratioNumerator, ratioDenominator);
                bValue = calculateRatio(b, ratioNumerator, ratioDenominator);
            } else {
                aValue = getSortValue(a, sortField);
                bValue = getSortValue(b, sortField);
            }

            if (sortDirection === 'asc') {
                return aValue < bValue ? -1 : aValue > bValue ? 1 : 0;
            } else {
                return aValue > bValue ? -1 : aValue < bValue ? 1 : 0;
            }
        });
    }, [allMenuItems, sortField, sortDirection, ratioNumerator, ratioDenominator]);

    // Calculate map bounds
    const bounds = useMemo(() => {
        if (!restaurants || restaurants.length === 0 || !userLocation) {
            return null;
        }
        const allLocations = [
            userLocation,
            ...restaurantsWithDistance.map(r => ({ lat: r.location.lat, lng: r.location.lng }))
        ];
        return L.latLngBounds(allLocations.map(loc => [loc.lat, loc.lng]));
    }, [restaurants, restaurantsWithDistance, userLocation]);

    // Early return after all hooks are declared
    if (!restaurants || restaurants.length === 0) {
        return null;
    }

    const handleSort = (field) => {
        if (field === 'ratio') {
            setShowRatioSort(true);
            setSortField('ratio');
            setSortDirection('desc'); // Ratios usually want highest first
        } else {
            setShowRatioSort(false);
            if (sortField === field) {
                setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
            } else {
                setSortField(field);
                setSortDirection(field === 'calories' || field === 'protein' || field === 'price' ? 'desc' : 'asc');
            }
        }
    };

    const handleSortChange = (e) => {
        const field = e.target.value;
        handleSort(field);
    };

    const getSortLabel = (field) => {
        const labels = {
            distance: 'Distance',
            rating: 'Rating',
            name: 'Name',
            priceLevel: 'Price',
            calories: 'Calories',
            protein: 'Protein',
            price: 'Price',
            ratio: '📊 Ratio'
        };
        return labels[field] || field;
    };

    const formatRating = (rating) => {
        return rating ? `⭐ ${rating.toFixed(1)}` : 'No rating';
    };

    const formatPriceLevel = (priceLevel) => {
        return priceLevel || 'N/A';
    };

    const formatDistance = (distance) => {
        return distance < 1 ? `${Math.round(distance * 1000)}m` : `${distance.toFixed(1)}km`;
    };

    const formatRatio = (item, numerator, denominator) => {
        const ratio = calculateRatio(item, numerator, denominator);
        if (ratio === 0) return 'N/A';

        const numLabel = numerator === 'protein' ? 'g' : numerator === 'calories' ? 'cal' : '';
        const denLabel = denominator === 'price' ? '$' : denominator === 'calories' ? 'cal' : 'g';

        return `${ratio.toFixed(2)} ${numLabel}/${denLabel}`;
    };

    // Render restaurants view
    const renderRestaurantsView = () => (
        <div className="restaurant-list">
            {sortedRestaurants.map((restaurant, index) => (
                <div
                    key={index}
                    className={`restaurant-item ${selectedRestaurant === index ? 'selected' : ''}`}
                    onClick={() => setSelectedRestaurant(selectedRestaurant === index ? null : index)}
                >
                    <div className="restaurant-item-header">
                        <h4 className="restaurant-name">{restaurant.name}</h4>
                        <div className="restaurant-distance">{formatDistance(restaurant.distance)}</div>
                    </div>

                    <div className="restaurant-item-details">
                        <div className="restaurant-meta">
                            <span className="restaurant-rating">{formatRating(restaurant.rating)}</span>
                            {restaurant.reviewsCount > 0 && (
                                <span className="restaurant-reviews">({restaurant.reviewsCount})</span>
                            )}
                            <span className="restaurant-price">{formatPriceLevel(restaurant.priceLevel)}</span>
                        </div>
                        <div className="restaurant-category">{restaurant.category}</div>
                        <div className="menu-items-count">
                            {restaurant.menuItems?.length || 0} menu items
                        </div>
                    </div>

                    {selectedRestaurant === index && (
                        <div className="restaurant-item-expanded">
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
                    )}
                </div>
            ))}
        </div>
    );

    // Render menu items view
    const renderMenuItemsView = () => (
        <div className="menu-items-list">
            {sortedMenuItems.map((item, index) => (
                <div
                    key={item.id || index}
                    className={`menu-item ${!item.available ? 'unavailable' : ''}`}
                >
                    <div className="menu-item-header">
                        <div className="menu-item-main">
                            <h4 className="menu-item-name">{item.name}</h4>
                            <div className="menu-item-restaurant">{item.restaurantName}</div>
                        </div>
                        <div className="menu-item-price">${item.price}</div>
                    </div>

                    <div className="menu-item-nutrition">
                        <div className="nutrition-main">
                            <span className="calories">{item.nutrition?.calories || 0} cal</span>
                            <span className="protein">{item.nutrition?.protein || 0}g protein</span>
                            <span className="carbs">{item.nutrition?.carbs || 0}g carbs</span>
                            <span className="fat">{item.nutrition?.fat || 0}g fat</span>
                        </div>
                        {sortField === 'ratio' && (
                            <div className="ratio-display">
                                <span className="ratio-value">
                                    📊 {formatRatio(item, ratioNumerator, ratioDenominator)}
                                </span>
                            </div>
                        )}
                    </div>

                    {item.dietary_tags && item.dietary_tags.length > 0 && (
                        <div className="dietary-tags">
                            {item.dietary_tags.map((tag, tagIndex) => (
                                <span key={tagIndex} className="dietary-tag">{tag}</span>
                            ))}
                        </div>
                    )}

                    <div className="menu-item-meta">
                        <span className="restaurant-distance">{formatDistance(item.restaurantDistance)}</span>
                        {item.spice_level && (
                            <span className="spice-level">🌶️ {item.spice_level}</span>
                        )}
                        {!item.available && (
                            <span className="unavailable-badge">Currently Unavailable</span>
                        )}
                    </div>
                </div>
            ))}
        </div>
    );

    return (
        <div className="map-overlay">
            <div className="map-container-with-sidebar">
                <div className="map-header">
                    <h2>Nearby Restaurants</h2>
                    <div className="view-toggle">
                        <button
                            className={`toggle-option ${viewMode === 'restaurants' ? 'active' : ''}`}
                            onClick={() => setViewMode('restaurants')}
                        >
                            🏪 Restaurants
                        </button>
                        <button
                            className={`toggle-option ${viewMode === 'menu_items' ? 'active' : ''}`}
                            onClick={() => setViewMode('menu_items')}
                        >
                            🍽️ Menu Items
                        </button>
                    </div>
                    <button className="close-button" onClick={onClose}>
                        ×
                    </button>
                </div>

                <div className="map-content">
                    {/* Restaurant/Menu Items List Sidebar */}
                    <div className="restaurant-sidebar">
                        <div className="sidebar-header">
                            <h3>
                                {viewMode === 'restaurants'
                                    ? `Restaurant List (${sortedRestaurants.length})`
                                    : `Menu Items (${sortedMenuItems.length})`
                                }
                            </h3>
                            <div className="sort-controls">
                                <span className="sort-label">Sort by:</span>
                                <div className="sort-dropdown-container">
                                    <select
                                        value={sortField}
                                        onChange={handleSortChange}
                                        className="sort-dropdown"
                                    >
                                        {viewMode === 'restaurants' ? (
                                            <>
                                                <option value="distance">Distance</option>
                                                <option value="rating">Rating</option>
                                                <option value="name">Name</option>
                                                <option value="priceLevel">Price</option>
                                            </>
                                        ) : (
                                            <>
                                                <option value="calories">Calories</option>
                                                <option value="protein">Protein</option>
                                                <option value="price">Price</option>
                                                <option value="distance">Distance</option>
                                                <option value="ratio">📊 Ratio</option>
                                            </>
                                        )}
                                    </select>
                                    <div className="sort-direction-indicator">
                                        {sortDirection === 'asc' ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* Ratio Configuration */}
                        {showRatioSort && viewMode === 'menu_items' && (
                            <div className="ratio-config">
                                <div className="ratio-selectors">
                                    <select
                                        value={ratioNumerator}
                                        onChange={(e) => setRatioNumerator(e.target.value)}
                                        className="ratio-select"
                                    >
                                        <option value="protein">Protein (g)</option>
                                        <option value="calories">Calories</option>
                                        <option value="carbs">Carbs (g)</option>
                                        <option value="fat">Fat (g)</option>
                                    </select>
                                    <span className="ratio-divider">/</span>
                                    <select
                                        value={ratioDenominator}
                                        onChange={(e) => setRatioDenominator(e.target.value)}
                                        className="ratio-select"
                                    >
                                        <option value="price">Price ($)</option>
                                        <option value="calories">Calories</option>
                                        <option value="protein">Protein (g)</option>
                                        <option value="carbs">Carbs (g)</option>
                                        <option value="fat">Fat (g)</option>
                                    </select>
                                </div>
                                <div className="ratio-examples">
                                    <span className="ratio-example">
                                        Popular: Protein/Price, Protein/Calories
                                    </span>
                                </div>
                            </div>
                        )}

                        {viewMode === 'restaurants' ? renderRestaurantsView() : renderMenuItemsView()}
                    </div>

                    {/* Map */}
                    <div className="map-section">
                        {bounds && (
                            <MapContainer
                                key="restaurant-map"
                                bounds={bounds}
                                boundsOptions={{ padding: [20, 20] }}
                                style={{ height: '100%', width: '100%' }}
                                className="restaurant-map"
                                zoomControl={true}
                                preferCanvas={true}
                            >
                                <TileLayer
                                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
                                    url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
                                    subdomains="abcd"
                                    maxZoom={20}
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
                                {sortedRestaurants.map((restaurant, index) => (
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
                                                    {restaurant.priceLevel && ` • ${restaurant.priceLevel}`}
                                                </p>
                                                <p className="restaurant-distance">📍 {formatDistance(restaurant.distance)} away</p>
                                                <p className="menu-items-count">🍽️ {restaurant.menuItems?.length || 0} menu items</p>
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
                        )}
                    </div>
                </div>

                <div className="map-legend">
                    <div className="legend-item">
                        <div className="legend-icon user-legend-icon">
                            <svg width="16" height="20" viewBox="0 0 28 36" fill="none" xmlns="http://www.w3.org/2000/svg">
                                <path d="M14 0C6.27 0 0 6.27 0 14C0 24.5 14 36 14 36S28 24.5 28 14C28 6.27 21.73 0 14 0Z" fill="#3b82f6" />
                                <circle cx="14" cy="14" r="8" fill="white" />
                                <circle cx="14" cy="14" r="4" fill="#3b82f6" />
                            </svg>
                        </div>
                        <span>Your Location</span>
                    </div>
                    <div className="legend-item">
                        <div className="legend-icon restaurant-legend-icon">
                            <svg width="16" height="20" viewBox="0 0 32 40" fill="none" xmlns="http://www.w3.org/2000/svg">
                                <path d="M16 0C7.16 0 0 7.16 0 16C0 28 16 40 16 40S32 28 32 16C32 7.16 24.84 0 16 0Z" fill="#22c55e" />
                                <circle cx="16" cy="16" r="10" fill="white" />
                                <path d="M20 12H12C11.45 12 11 12.45 11 13V19C11 19.55 11.45 20 12 20H20C20.55 20 21 19.55 21 19V13C21 12.45 20.55 12 20 12ZM19 18H13V14H19V18Z" fill="#22c55e" />
                                <path d="M16 9C17.1 9 18 9.9 18 11V12H14V11C14 9.9 14.9 9 16 9Z" fill="#22c55e" />
                            </svg>
                        </div>
                        <span>Restaurants</span>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default RestaurantMap; 