import React, { useState, useMemo, useEffect, useRef, useCallback } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { ChevronUp, ChevronDown, Eye, EyeOff } from 'lucide-react';

// Fix for default markers in react-leaflet
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
    iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
    iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

// Map invalidation component to fix tile loading issues
const MapInvalidator = () => {
    const map = useMap();

    useEffect(() => {
        const invalidateMap = () => {
            setTimeout(() => {
                map.invalidateSize();
                // Force a second invalidation for larger containers
                setTimeout(() => {
                    map.invalidateSize();
                }, 200);
            }, 100);
        };

        // Invalidate size when component mounts
        invalidateMap();

        // Also invalidate on window resize
        window.addEventListener('resize', invalidateMap);

        // Force refresh tiles if they don't load initially
        const forceRefresh = () => {
            setTimeout(() => {
                const tileLayer = map.eachLayer((layer) => {
                    if (layer.options && layer.options.attribution) {
                        layer.redraw();
                    }
                });
            }, 500);
        };

        forceRefresh();

        return () => {
            window.removeEventListener('resize', invalidateMap);
        };
    }, [map]);

    return null;
};

// Component to control map programmatically
const MapController = ({ center }) => {
    const map = useMap();

    useEffect(() => {
        if (center) {
            map.setView(center, map.getZoom(), {
                animate: true,
                duration: 0.5
            });
        }
    }, [map, center]);

    return null;
};

// Create ranking icon with number
const createRankingIcon = (ranking, isHighlighted = false) => {
    const bgColor = isHighlighted ? '#22c55e' : '#1f2937';
    const circleColor = isHighlighted ? '#16a34a' : '#3b82f6';

    const svgString = `
        <svg width="32" height="40" viewBox="0 0 32 40" xmlns="http://www.w3.org/2000/svg">
            <path d="M16 0C7.16 0 0 7.16 0 16C0 28 16 40 16 40S32 28 32 16C32 7.16 24.84 0 16 0Z" fill="${bgColor}"/>
            <circle cx="16" cy="16" r="10" fill="${circleColor}"/>
            <text x="16" y="21" font-family="Arial, sans-serif" font-size="12" font-weight="bold" text-anchor="middle" fill="white">${ranking}</text>
        </svg>
    `;

    return new L.DivIcon({
        html: svgString,
        className: 'custom-ranking-marker',
        iconSize: [32, 40],
        iconAnchor: [16, 40],
        popupAnchor: [0, -40]
    });
};

// Create modern restaurant icon
const createRestaurantIcon = (isHighlighted = false) => {
    const pinColor = isHighlighted ? '#16a34a' : '#22c55e';
    const iconColor = isHighlighted ? '#22c55e' : '#22c55e';

    const svgString = `
        <svg width="32" height="40" viewBox="0 0 32 40" xmlns="http://www.w3.org/2000/svg">
            <path d="M16 0C7.16 0 0 7.16 0 16C0 28 16 40 16 40S32 28 32 16C32 7.16 24.84 0 16 0Z" fill="${pinColor}"/>
            <circle cx="16" cy="16" r="10" fill="white"/>
            <path d="M20 12H12C11.45 12 11 12.45 11 13V19C11 19.55 11.45 20 12 20H20C20.55 20 21 19.55 21 19V13C21 12.45 20.55 12 20 12ZM19 18H13V14H19V18Z" fill="${iconColor}"/>
            <path d="M16 9C17.1 9 18 9.9 18 11V12H14V11C14 9.9 14.9 9 16 9Z" fill="${iconColor}"/>
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
            // Handle both backend format (flat) and potential nested format
            return item.calories || item.nutrition?.calories || 0;
        case 'protein':
            return item.protein || item.nutrition?.protein || 0;
        case 'carbs':
            return item.carbs || item.nutrition?.carbs || 0;
        case 'fat':
            return item.fat || item.nutrition?.fat || 0;
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
    const [isExpanded, setIsExpanded] = useState(false);
    const [isMobile, setIsMobile] = useState(false);
    const [showMobileDropdown, setShowMobileDropdown] = useState(false);
    const [showRatioNumeratorDropdown, setShowRatioNumeratorDropdown] = useState(false);
    const [showRatioDenominatorDropdown, setShowRatioDenominatorDropdown] = useState(false);

    // Map control state
    const [mapCenter, setMapCenter] = useState(null);
    const [centeredRestaurant, setCenteredRestaurant] = useState(null);

    // Touch handling refs
    const touchStartY = useRef(0);
    const touchStartTime = useRef(0);
    const sidebarRef = useRef(null);

    // Function to center map on a restaurant
    const centerMapOnRestaurant = useCallback((restaurant) => {
        setMapCenter([restaurant.location.lat, restaurant.location.lng]);
        setCenteredRestaurant(restaurant);
    }, []);

    // Check if we're on mobile
    useEffect(() => {
        const checkIsMobile = () => {
            setIsMobile(window.innerWidth <= 768);
        };

        checkIsMobile();
        window.addEventListener('resize', checkIsMobile);

        return () => window.removeEventListener('resize', checkIsMobile);
    }, []);

    // Close mobile dropdown when clicking outside
    useEffect(() => {
        const handleClickOutside = (event) => {
            if (!event.target.closest('.mobile-dropdown-container')) {
                setShowMobileDropdown(false);
                setShowRatioNumeratorDropdown(false);
                setShowRatioDenominatorDropdown(false);
            }
        };

        document.addEventListener('touchstart', handleClickOutside);
        document.addEventListener('click', handleClickOutside);

        return () => {
            document.removeEventListener('touchstart', handleClickOutside);
            document.removeEventListener('click', handleClickOutside);
        };
    }, []);

    // Handle touch events for sliding panel
    const handleTouchStart = (e) => {
        if (!isMobile) return;

        // Ignore touches on interactive elements
        const target = e.target;
        if (target.tagName === 'SELECT' || target.tagName === 'BUTTON' || target.tagName === 'INPUT' ||
            target.closest('.sort-controls') || target.closest('.view-toggle') || target.closest('.ratio-config')) {
            return;
        }

        touchStartY.current = e.touches[0].clientY;
        touchStartTime.current = Date.now();
    };

    const handleTouchMove = (e) => {
        if (!isMobile) return;

        // Ignore touches on interactive elements
        const target = e.target;
        if (target.tagName === 'SELECT' || target.tagName === 'BUTTON' || target.tagName === 'INPUT' ||
            target.closest('.sort-controls') || target.closest('.view-toggle') || target.closest('.ratio-config')) {
            return;
        }

        // Don't call preventDefault as it conflicts with passive listeners
        // Instead, we'll use CSS touch-action to control scrolling behavior
        const touchY = e.touches[0].clientY;
        const deltaY = touchStartY.current - touchY;

        // Store the delta for use in touchend
        touchStartY.current = deltaY;
    };

    const handleTouchEnd = (e) => {
        if (!isMobile) return;

        // Ignore touches on interactive elements
        const target = e.changedTouches[0].target || e.target;
        if (target.tagName === 'SELECT' || target.tagName === 'BUTTON' || target.tagName === 'INPUT' ||
            target.closest('.sort-controls') || target.closest('.view-toggle') || target.closest('.ratio-config')) {
            return;
        }

        const touchEndY = e.changedTouches[0].clientY;
        const deltaY = touchStartY.current - touchEndY;
        const touchDuration = Date.now() - touchStartTime.current;

        // Determine if it's a swipe gesture
        const isSwipe = Math.abs(deltaY) > 50 && touchDuration < 300;
        const isTap = Math.abs(deltaY) < 10 && touchDuration < 200;

        if (isSwipe) {
            // Swipe up = expand, swipe down = collapse
            if (deltaY > 0) {
                setIsExpanded(true);
            } else {
                setIsExpanded(false);
            }
        } else if (isTap) {
            // Tap to toggle
            setIsExpanded(!isExpanded);
        }
    };

    // Handle click on sidebar header (for desktop and as fallback)
    const handleSidebarHeaderClick = (e) => {
        // Don't toggle if clicking on interactive elements
        const target = e.target;
        if (target.tagName === 'SELECT' || target.tagName === 'BUTTON' || target.tagName === 'INPUT' ||
            target.closest('.sort-controls') || target.closest('.view-toggle') || target.closest('.ratio-config')) {
            return;
        }

        if (isMobile) {
            setIsExpanded(!isExpanded);
        }
    };

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
                    // Normalize the menu item data structure to handle backend format
                    const normalizedItem = {
                        ...item,
                        // Ensure nutrition data is accessible in the expected format
                        nutrition: {
                            calories: item.calories || item.nutrition?.calories || 0,
                            protein: item.protein || item.nutrition?.protein || 0,
                            carbs: item.carbs || item.nutrition?.carbs || 0,
                            fat: item.fat || item.nutrition?.fat || 0,
                            fiber: item.fiber || item.nutrition?.fiber || 0,
                            sugar: item.sugar || item.nutrition?.sugar || 0,
                            sodium: item.sodium || item.nutrition?.sodium || 0,
                        },
                        // Handle availability field (backend uses is_available)
                        available: item.is_available !== undefined ? item.is_available : (item.available !== undefined ? item.available : true),
                        // Ensure price is a number
                        price: parseFloat(item.price) || 0,
                        // Handle dietary tags
                        dietary_tags: item.dietary_tags || [],
                        allergens: item.allergens || [],
                        // Add restaurant context
                        restaurantName: restaurant.name,
                        restaurantDistance: restaurant.distance,
                        restaurantLocation: restaurant.location,
                        restaurantCategory: restaurant.category,
                        restaurantRating: restaurant.rating,
                        // Ensure we have a unique ID
                        id: item.id || `${restaurant.placeId}_${item.name}_${items.length}`,
                    };
                    items.push(normalizedItem);
                });
            }
        });
        return items;
    }, [restaurantsWithDistance]);

    // Sort restaurants
    const sortedRestaurants = useMemo(() => {
        let restaurantsToSort = [...restaurantsWithDistance];

        return restaurantsToSort.sort((a, b) => {
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
        let menuItemsToSort = [...allMenuItems];

        return menuItemsToSort.sort((a, b) => {
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
    }, [allMenuItems, sortField, sortDirection]);

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

    // Generate a unique key for the MapContainer to force re-render when needed
    const mapKey = useMemo(() => {
        return `map-${restaurants?.length || 0}-${userLocation?.lat || 0}-${userLocation?.lng || 0}`;
    }, [restaurants, userLocation]);

    // Effect to handle map tile loading in larger containers
    useEffect(() => {
        // Force a small delay to ensure DOM is fully rendered before map initialization
        const timer = setTimeout(() => {
            const mapContainers = document.querySelectorAll('.restaurant-map .leaflet-container');
            mapContainers.forEach((container) => {
                // Trigger a resize event to force Leaflet to recalculate
                const event = new Event('resize');
                window.dispatchEvent(event);
            });
        }, 300);

        return () => clearTimeout(timer);
    }, [bounds, mapKey]);

    // Determine if we should show rankings (when sorted by anything other than distance)
    const shouldShowRankings = useMemo(() => {
        return sortField !== 'distance';
    }, [sortField]);

    // Calculate restaurant rankings for restaurant view
    const restaurantRankings = useMemo(() => {
        const rankings = new Map();
        sortedRestaurants.forEach((restaurant, index) => {
            rankings.set(restaurant.name, index + 1);
        });
        return rankings;
    }, [sortedRestaurants]);

    // Calculate restaurant rankings for menu items view (based on highest ranking menu item)
    const menuItemRestaurantRankings = useMemo(() => {
        if (viewMode !== 'menu_items') return new Map();

        const restaurantBestRankings = new Map();
        sortedMenuItems.forEach((item, index) => {
            const restaurantName = item.restaurantName;
            if (!restaurantBestRankings.has(restaurantName)) {
                restaurantBestRankings.set(restaurantName, index + 1);
            }
        });

        return restaurantBestRankings;
    }, [sortedMenuItems, viewMode]);

    // Count visible items - optimized for performance
    const visibleCounts = useMemo(() => {
        return {
            restaurants: restaurantsWithDistance.length,
            menuItems: allMenuItems.length,
            totalRestaurants: restaurantsWithDistance.length,
            totalMenuItems: allMenuItems.length
        };
    }, [restaurantsWithDistance, allMenuItems]);

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
            {sortedRestaurants.map((restaurant, index) => {
                const ranking = restaurantRankings.get(restaurant.name);
                const isHighlighted = centeredRestaurant && centeredRestaurant.placeId === restaurant.placeId;

                return (
                    <div
                        key={restaurant.placeId || index}
                        className={`restaurant-item ${selectedRestaurant === restaurant ? 'selected' : ''}`}
                        onClick={() => {
                            setSelectedRestaurant(selectedRestaurant === restaurant ? null : restaurant);
                            centerMapOnRestaurant(restaurant);
                        }}
                    >
                        <div className="restaurant-item-header">
                            <div className="restaurant-name-section">
                                {shouldShowRankings && ranking && (
                                    <span className="restaurant-ranking">#{ranking}</span>
                                )}
                                <h4 className="restaurant-name">{restaurant.name}</h4>
                            </div>
                            <div className="restaurant-distance">{formatDistance(restaurant.distance)}</div>

                            {/* Show processing status if not finished */}
                            {restaurant.processing_status && restaurant.processing_status !== 'finished' && (
                                <div className="processing-status">
                                    <span className={`status-badge ${restaurant.processing_status}`}>
                                        {restaurant.processing_status === 'pending' && '⏳ Processing Menu'}
                                        {restaurant.processing_status === 'processing' && '🔄 Extracting Items'}
                                        {restaurant.processing_status === 'new' && '🆕 New'}
                                    </span>
                                </div>
                            )}
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
                                {restaurant.has_menu_items === false && restaurant.processing_status === 'finished' && (
                                    <span className="no-menu-badge"> (No menu available)</span>
                                )}
                            </div>
                        </div>

                        {selectedRestaurant === restaurant && (
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
                );
            })}
            {sortedRestaurants.length === 0 && (
                <div className="no-results">
                    <p>No restaurants found.</p>
                </div>
            )}
        </div>
    );

    // Render menu items view
    const renderMenuItemsView = () => (
        <div className="menu-items-list">
            {sortedMenuItems.length === 0 ? (
                <div className="no-menu-items">
                    <p>No menu items available yet.</p>
                    <p>Menu processing may still be in progress for some restaurants.</p>
                </div>
            ) : (
                sortedMenuItems.map((item, index) => {
                    // Find the restaurant for this menu item
                    const restaurant = restaurantsWithDistance.find(r => r.name === item.restaurantName);
                    const hasIncompleteData = !item.price || item.price === 0;

                    return (
                        <div
                            key={item.id || index}
                            className={`menu-item ${!item.available ? 'unavailable' : ''} ${hasIncompleteData ? 'incomplete-data' : ''}`}
                            onClick={() => restaurant && centerMapOnRestaurant(restaurant)}
                        >
                            <div className="menu-item-header">
                                <div className="menu-item-main">
                                    <div className="menu-item-name-section">
                                        {shouldShowRankings && (
                                            <span className="menu-item-ranking">#{index + 1}</span>
                                        )}
                                        <h4 className="menu-item-name">{item.name}</h4>
                                        {hasIncompleteData && (
                                            <span className="incomplete-data-badge">Incomplete Data</span>
                                        )}
                                    </div>
                                    <div className="menu-item-restaurant">{item.restaurantName}</div>
                                    {item.description && (
                                        <div className="menu-item-description">{item.description}</div>
                                    )}
                                </div>
                                <div className="menu-item-price">
                                    {hasIncompleteData ? (
                                        <span className="price-unavailable">Price N/A</span>
                                    ) : (
                                        <>
                                            ${typeof item.price === 'number' ? item.price.toFixed(2) : (parseFloat(item.price) || 0).toFixed(2)}
                                            {item.currency && item.currency !== 'USD' && (
                                                <span className="currency"> {item.currency}</span>
                                            )}
                                        </>
                                    )}
                                </div>
                            </div>

                            <div className="menu-item-nutrition">
                                <div className="nutrition-main">
                                    <span className="calories">{item.nutrition?.calories || item.calories || 0} cal</span>
                                    <span className="protein">{item.nutrition?.protein || item.protein || 0}g protein</span>
                                    <span className="carbs">{item.nutrition?.carbs || item.carbs || 0}g carbs</span>
                                    <span className="fat">{item.nutrition?.fat || item.fat || 0}g fat</span>
                                </div>
                                {(item.nutrition?.fiber || item.fiber) && (
                                    <div className="nutrition-additional">
                                        <span className="fiber">{item.nutrition?.fiber || item.fiber}g fiber</span>
                                        {(item.nutrition?.sugar || item.sugar) && (
                                            <span className="sugar">{item.nutrition?.sugar || item.sugar}g sugar</span>
                                        )}
                                        {(item.nutrition?.sodium || item.sodium) && (
                                            <span className="sodium">{item.nutrition?.sodium || item.sodium}mg sodium</span>
                                        )}
                                    </div>
                                )}
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

                            {item.allergens && item.allergens.length > 0 && (
                                <div className="allergen-info">
                                    <span className="allergens-label">⚠️ Contains: </span>
                                    {item.allergens.map((allergen, allergenIndex) => (
                                        <span key={allergenIndex} className="allergen-tag">{allergen}</span>
                                    ))}
                                </div>
                            )}

                            <div className="menu-item-meta">
                                <span className="restaurant-distance">{formatDistance(item.restaurantDistance)}</span>
                                {item.spice_level && (
                                    <span className="spice-level">🌶️ {item.spice_level}</span>
                                )}
                                {item.category && (
                                    <span className="menu-category">{item.category}</span>
                                )}
                                {!item.available && (
                                    <span className="unavailable-badge">Currently Unavailable</span>
                                )}
                                {item.seasonal && (
                                    <span className="seasonal-badge">🍂 Seasonal</span>
                                )}
                            </div>
                        </div>
                    );
                })
            )}
        </div>
    );

    // Mobile dropdown options
    const getMobileDropdownOptions = () => {
        if (viewMode === 'restaurants') {
            return [
                { value: 'distance', label: 'Distance' },
                { value: 'rating', label: 'Rating' },
                { value: 'name', label: 'Name' },
                { value: 'priceLevel', label: 'Price' }
            ];
        } else {
            return [
                { value: 'calories', label: 'Calories' },
                { value: 'protein', label: 'Protein' },
                { value: 'price', label: 'Price' },
                { value: 'distance', label: 'Distance' },
                { value: 'ratio', label: '📊 Ratio' }
            ];
        }
    };

    const handleMobileDropdownSelect = (value) => {
        handleSort(value);
        setShowMobileDropdown(false);
    };

    // Custom mobile dropdown component
    const MobileDropdown = () => {
        const options = getMobileDropdownOptions();
        const currentOption = options.find(opt => opt.value === sortField);

        return (
            <div className="mobile-dropdown-container">
                <button
                    className="mobile-dropdown-trigger"
                    onClick={() => setShowMobileDropdown(!showMobileDropdown)}
                    type="button"
                >
                    <span>{currentOption?.label || 'Sort'}</span>
                    <ChevronDown size={16} className={`dropdown-arrow ${showMobileDropdown ? 'rotated' : ''}`} />
                </button>

                {showMobileDropdown && (
                    <div className="mobile-dropdown-menu">
                        {options.map((option) => (
                            <button
                                key={option.value}
                                className={`mobile-dropdown-option ${sortField === option.value ? 'active' : ''}`}
                                onClick={() => handleMobileDropdownSelect(option.value)}
                                type="button"
                            >
                                {option.label}
                            </button>
                        ))}
                    </div>
                )}
            </div>
        );
    };

    // Ratio dropdown options
    const getRatioNumeratorOptions = () => [
        { value: 'protein', label: 'Protein (g)' },
        { value: 'calories', label: 'Calories' },
        { value: 'carbs', label: 'Carbs (g)' },
        { value: 'fat', label: 'Fat (g)' }
    ];

    const getRatioDenominatorOptions = () => [
        { value: 'price', label: 'Price ($)' },
        { value: 'calories', label: 'Calories' },
        { value: 'protein', label: 'Protein (g)' },
        { value: 'carbs', label: 'Carbs (g)' },
        { value: 'fat', label: 'Fat (g)' }
    ];

    // Custom mobile dropdown component for ratio numerator
    const RatioNumeratorMobileDropdown = () => {
        const options = getRatioNumeratorOptions();
        const currentOption = options.find(opt => opt.value === ratioNumerator);

        return (
            <div className="mobile-dropdown-container">
                <button
                    className="mobile-dropdown-trigger ratio-dropdown"
                    onClick={() => {
                        setShowRatioNumeratorDropdown(!showRatioNumeratorDropdown);
                        setShowRatioDenominatorDropdown(false);
                        setShowMobileDropdown(false);
                    }}
                    type="button"
                >
                    <span>{currentOption?.label || 'Select'}</span>
                    <ChevronDown size={16} className={`dropdown-arrow ${showRatioNumeratorDropdown ? 'rotated' : ''}`} />
                </button>

                {showRatioNumeratorDropdown && (
                    <div className="mobile-dropdown-menu">
                        {options.map((option) => (
                            <button
                                key={option.value}
                                className={`mobile-dropdown-option ${ratioNumerator === option.value ? 'active' : ''}`}
                                onClick={() => {
                                    setRatioNumerator(option.value);
                                    setShowRatioNumeratorDropdown(false);
                                }}
                                type="button"
                            >
                                {option.label}
                            </button>
                        ))}
                    </div>
                )}
            </div>
        );
    };

    // Custom mobile dropdown component for ratio denominator
    const RatioDenominatorMobileDropdown = () => {
        const options = getRatioDenominatorOptions();
        const currentOption = options.find(opt => opt.value === ratioDenominator);

        return (
            <div className="mobile-dropdown-container">
                <button
                    className="mobile-dropdown-trigger ratio-dropdown"
                    onClick={() => {
                        setShowRatioDenominatorDropdown(!showRatioDenominatorDropdown);
                        setShowRatioNumeratorDropdown(false);
                        setShowMobileDropdown(false);
                    }}
                    type="button"
                >
                    <span>{currentOption?.label || 'Select'}</span>
                    <ChevronDown size={16} className={`dropdown-arrow ${showRatioDenominatorDropdown ? 'rotated' : ''}`} />
                </button>

                {showRatioDenominatorDropdown && (
                    <div className="mobile-dropdown-menu">
                        {options.map((option) => (
                            <button
                                key={option.value}
                                className={`mobile-dropdown-option ${ratioDenominator === option.value ? 'active' : ''}`}
                                onClick={() => {
                                    setRatioDenominator(option.value);
                                    setShowRatioDenominatorDropdown(false);
                                }}
                                type="button"
                            >
                                {option.label}
                            </button>
                        ))}
                    </div>
                )}
            </div>
        );
    };

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
                    <div
                        ref={sidebarRef}
                        className={`restaurant-sidebar ${isExpanded ? 'expanded' : ''}`}
                        onTouchStart={handleTouchStart}
                        onTouchMove={handleTouchMove}
                        onTouchEnd={handleTouchEnd}
                    >
                        <div className="sidebar-header" onClick={handleSidebarHeaderClick}>
                            <h3>
                                {!isMobile || isExpanded ? (
                                    viewMode === 'restaurants'
                                        ? `Restaurants (${visibleCounts.restaurants})`
                                        : `Menu Items (${visibleCounts.menuItems})`
                                ) : (
                                    // Simplified count for collapsed mobile view
                                    viewMode === 'restaurants'
                                        ? `${visibleCounts.restaurants} restaurants`
                                        : `${visibleCounts.menuItems} menu items`
                                )}
                            </h3>

                            {(!isMobile || isExpanded) && (
                                <div className="header-controls">
                                    <div className="sort-controls">
                                        <span className="sort-label">Sort by:</span>
                                        <div className="sort-dropdown-container">
                                            {isMobile ? (
                                                <MobileDropdown />
                                            ) : (
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
                                            )}
                                            <div className="sort-direction-indicator">
                                                {sortDirection === 'asc' ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            )}
                        </div>

                        {/* Ratio Configuration */}
                        {showRatioSort && viewMode === 'menu_items' && (
                            <div className="ratio-config">
                                <div className="ratio-selectors">
                                    {isMobile ? (
                                        <>
                                            <RatioNumeratorMobileDropdown />
                                            <span className="ratio-divider">÷</span>
                                            <RatioDenominatorMobileDropdown />
                                        </>
                                    ) : (
                                        <>
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
                                            <span className="ratio-divider">÷</span>
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
                                        </>
                                    )}
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
                                key={mapKey}
                                bounds={bounds}
                                boundsOptions={{ padding: [20, 20] }}
                                style={{ height: '100%', width: '100%' }}
                                className="restaurant-map"
                                zoomControl={true}
                                preferCanvas={false}
                                worldCopyJump={true}
                                maxBounds={[[-90, -180], [90, 180]]}
                                maxBoundsViscosity={1.0}
                                whenCreated={(mapInstance) => {
                                    // Force invalidation after map creation
                                    setTimeout(() => {
                                        mapInstance.invalidateSize();
                                    }, 100);
                                }}
                            >
                                <MapInvalidator />
                                <MapController center={mapCenter || [userLocation.lat, userLocation.lng]} />
                                <TileLayer
                                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                                    subdomains={['a', 'b', 'c']}
                                    maxZoom={19}
                                    minZoom={1}
                                    tileSize={256}
                                    zoomOffset={0}
                                    detectRetina={true}
                                    updateWhenIdle={false}
                                    updateWhenZooming={false}
                                    keepBuffer={2}
                                    crossOrigin={true}
                                    errorTileUrl="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
                                />

                                {/* User location marker */}
                                <Marker position={[userLocation.lat, userLocation.lng]} icon={userIcon}>
                                    <Popup>
                                        <div className="popup-content">
                                            <h3>📍 Your Location</h3>
                                        </div>
                                    </Popup>
                                </Marker>

                                {/* Restaurant markers */}
                                {sortedRestaurants.map((restaurant, index) => {
                                    const ranking = restaurantRankings.get(restaurant.name);
                                    const isHighlighted = centeredRestaurant && centeredRestaurant.placeId === restaurant.placeId;

                                    // Determine which icon to use
                                    let markerIcon;
                                    if (ranking) {
                                        markerIcon = createRankingIcon(ranking, isHighlighted);
                                    } else {
                                        markerIcon = createRestaurantIcon(isHighlighted);
                                    }

                                    return (
                                        <Marker
                                            key={`${restaurant.placeId}-${index}-${shouldShowRankings}-${viewMode}-${sortField}-${sortDirection}-${isHighlighted}`}
                                            position={[restaurant.location.lat, restaurant.location.lng]}
                                            icon={markerIcon}
                                        >
                                            <Popup>
                                                <div className="popup-content">
                                                    <h3>{restaurant.name}</h3>
                                                    {shouldShowRankings && ranking && (
                                                        <p className="popup-ranking">
                                                            #{ranking} in current {viewMode === 'restaurants' ? 'restaurant' : 'menu item'} ranking
                                                        </p>
                                                    )}
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
                                    );
                                })}
                            </MapContainer>
                        )}

                        {/* Map Legend */}
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
                                    {shouldShowRankings ? (
                                        <svg width="16" height="20" viewBox="0 0 32 40" fill="none" xmlns="http://www.w3.org/2000/svg">
                                            <path d="M16 0C7.16 0 0 7.16 0 16C0 28 16 40 16 40S32 28 32 16C32 7.16 24.84 0 16 0Z" fill="#1f2937" />
                                            <circle cx="16" cy="16" r="10" fill="#3b82f6" />
                                            <text x="16" y="21" fontFamily="Arial, sans-serif" fontSize="10" fontWeight="bold" textAnchor="middle" fill="white">#</text>
                                        </svg>
                                    ) : (
                                        <svg width="16" height="20" viewBox="0 0 32 40" fill="none" xmlns="http://www.w3.org/2000/svg">
                                            <path d="M16 0C7.16 0 0 7.16 0 16C0 28 16 40 16 40S32 28 32 16C32 7.16 24.84 0 16 0Z" fill="#22c55e" />
                                            <circle cx="16" cy="16" r="10" fill="white" />
                                            <path d="M20 12H12C11.45 12 11 12.45 11 13V19C11 19.55 11.45 20 12 20H20C20.55 20 21 19.55 21 19V13C21 12.45 20.55 12 20 12ZM19 18H13V14H19V18Z" fill="#22c55e" />
                                            <path d="M16 9C17.1 9 18 9.9 18 11V12H14V11C14 9.9 14.9 9 16 9Z" fill="#22c55e" />
                                        </svg>
                                    )}
                                </div>
                                <span>
                                    {shouldShowRankings
                                        ? (viewMode === 'restaurants'
                                            ? 'Restaurant Rankings'
                                            : 'Menu Item Rankings')
                                        : 'Restaurants'
                                    }
                                </span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default RestaurantMap; 