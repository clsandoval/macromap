# MacroMaps Backend API 🗺️

A Flask-based backend server providing restaurant discovery and comprehensive menu analysis with AI-powered nutritional information extraction. This documentation is designed for frontend developers to understand exactly how to integrate with the API.

## 🏗️ System Architecture

```mermaid
graph TB
    subgraph "Frontend Layer"
        FE[Frontend Application<br/>React/Mobile App]
    end
    
    subgraph "API Layer - Flask Backend"
        API[Flask Server<br/>localhost:5000]
        
        subgraph "Route Modules"
            SCAN[/scan-nearby<br/>Restaurant Discovery]
            REST[/restaurants<br/>Restaurant Endpoints]
            MENU[/menu-items<br/>Menu Endpoints]
            HEALTH[/health<br/>Health Check]
        end
    end
    
    subgraph "Data Layer"
        DB[(Supabase Database<br/>PostgreSQL)]
        APIFY[Apify API<br/>Google Places Data]
        AI[OpenAI API<br/>Menu Analysis]
    end
    
    FE -->|HTTP Requests| API
    SCAN -->|Background Processing| APIFY
    SCAN -->|Store Data| DB
    MENU -->|AI Processing| AI
    REST -->|Query Data| DB
    MENU -->|Query Data| DB
```

## 📋 Complete API Reference

### Base URL
```
http://localhost:5000
```

### Authentication
No authentication required for any endpoints.

---

## 🔍 Restaurant Discovery

### POST /scan-nearby

**Primary Use Case:** Initial restaurant discovery when user opens the app or changes location.

**How it works:**
1. Returns cached restaurants within 5km radius immediately
2. Triggers background Apify processing to fetch new restaurants if needed
3. Each restaurant includes menu items if processing is complete

#### Request
```typescript
interface ScanNearbyRequest {
  latitude: number;
  longitude: number;
  radius?: number; // Currently ignored - fixed at 5km
}
```

#### Example Request
```typescript
const response = await fetch('http://localhost:5000/scan-nearby', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    latitude: 37.7749,
    longitude: -122.4194
  })
});

const data = await response.json();
```

#### Response Schema
```typescript
interface ScanNearbyResponse {
  success: boolean;
  message: string;
  restaurants: Restaurant[];
  searchLocation: {
    latitude: number;
    longitude: number;
    radius_km: number;
  };
  processing_summary: {
    total_restaurants: number;
    completed: number;
    pending: number;
    processing: number;
    new: number;
    restaurants_with_menu: number;
  };
  background_processing: {
    status: "started" | "skipped";
    message: string;
  };
  data_source: "cached" | "none";
}

interface Restaurant {
  // Basic Info
  name: string;
  address: string;
  phone: string;
  website: string;
  
  // Location & Distance
  location: {
    lat: number;
    lng: number;
  };
  distance_km: number;
  
  // Ratings & Classification
  rating: number | null;
  reviewsCount: number;
  category: string;
  priceLevel: "$" | "$$" | "$$$" | "$$$$" | "";
  
  // Schedule
  openingHours: string[];
  
  // Identifiers
  placeId: string;
  url: string; // Google Maps URL
  
  // Images
  imageUrls: string[];
  images: {
    exterior?: string[];
    interior?: string[];
    menu?: string[];
  };
  
  // Processing Status
  processing_status: "pending" | "processing" | "finished" | "error";
  has_menu_items: boolean;
  
  // Menu Items (if available)
  menuItems: MenuItem[];
  
  // Timestamps
  created_at: string;
  updated_at: string;
}
```

#### Example Response
```json
{
  "success": true,
  "message": "Found 8 cached restaurants within 5.0km",
  "restaurants": [
    {
      "name": "Tony's Little Star Pizza",
      "address": "846 Divisadero St, San Francisco, CA 94117",
      "rating": 4.2,
      "reviewsCount": 1847,
      "category": "Pizza restaurant",
      "phone": "+1-415-441-1001",
      "website": "https://tonys-little-star.com",
      "priceLevel": "$$",
      "openingHours": [
        "Monday: 5:00 – 11:00 PM",
        "Tuesday: 5:00 – 11:00 PM",
        "Wednesday: 5:00 – 11:00 PM"
      ],
      "location": {
        "lat": 37.7749,
        "lng": -122.4194
      },
      "placeId": "ChIJd8BlQ2BZwokRAFUEcm_qrcA",
      "url": "https://maps.google.com/?cid=123456789",
      "distance_km": 0.3,
      "imageUrls": [
        "https://lh5.googleusercontent.com/p/AF1QipN..."
      ],
      "images": {
        "exterior": ["https://lh5.googleusercontent.com/p/exterior1.jpg"],
        "menu": ["https://lh5.googleusercontent.com/p/menu1.jpg"]
      },
      "processing_status": "finished",
      "has_menu_items": true,
      "menuItems": [
        {
          "id": "550e8400-e29b-41d4-a716-446655440000",
          "name": "Margherita Pizza",
          "description": "Fresh mozzarella, tomato sauce, basil",
          "price": 18.50,
          "currency": "USD",
          "calories": 320,
          "protein": 14.2,
          "carbs": 42.1,
          "fat": 11.8,
          "category": "Pizza"
        }
      ]
    }
  ],
  "processing_summary": {
    "total_restaurants": 8,
    "completed": 8,
    "restaurants_with_menu": 6
  }
}
```

---

## 🏪 Restaurant Endpoints

### GET /restaurants

**Use Case:** Paginated browsing of restaurants with sorting options.

#### Query Parameters
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `latitude` | `number` | ✅ | - | Search center latitude |
| `longitude` | `number` | ✅ | - | Search center longitude |
| `page` | `number` | ❌ | `1` | Page number (1-based) |
| `limit` | `number` | ❌ | `20` | Items per page (max 100) |
| `radius` | `number` | ❌ | `10.0` | Search radius in km (0.1-50) |
| `sort_by` | `string` | ❌ | `"distance"` | Sort criteria |

#### Sort Options
- `distance` - Closest restaurants first
- `rating` - Highest rated first
- `reviews_count` - Most reviewed first
- `name` - Alphabetical order

#### Example Usage
```typescript
// Get first page of restaurants sorted by rating
const getTopRatedRestaurants = async (lat: number, lng: number) => {
  const params = new URLSearchParams({
    latitude: lat.toString(),
    longitude: lng.toString(),
    page: '1',
    limit: '10',
    sort_by: 'rating'
  });
  
  const response = await fetch(`http://localhost:5000/restaurants?${params}`);
  return response.json();
};

// Load more restaurants (pagination)
const loadMoreRestaurants = async (lat: number, lng: number, page: number) => {
  const params = new URLSearchParams({
    latitude: lat.toString(),
    longitude: lng.toString(),
    page: page.toString(),
    limit: '20'
  });
  
  const response = await fetch(`http://localhost:5000/restaurants?${params}`);
  return response.json();
};
```

#### Response Schema
```typescript
interface RestaurantsResponse {
  success: boolean;
  data: Restaurant[]; // Same Restaurant interface as above (without menuItems)
  pagination: {
    page: number;
    limit: number;
    total: number;
    total_pages: number;
    has_next: boolean;
    has_prev: boolean;
  };
  search_params: {
    latitude: number;
    longitude: number;
    radius_km: number;
    sort_by: string;
  };
}
```

### GET /restaurants/\<restaurant_id\>

**Use Case:** Get detailed information for a specific restaurant.

#### Path Parameters
- `restaurant_id` - Restaurant UUID or Google place_id

#### Example Usage
```typescript
const getRestaurantDetails = async (restaurantId: string) => {
  const response = await fetch(`http://localhost:5000/restaurants/${restaurantId}`);
  return response.json();
};

// Works with both UUID and place_id
await getRestaurantDetails('550e8400-e29b-41d4-a716-446655440001');
await getRestaurantDetails('ChIJd8BlQ2BZwokRAFUEcm_qrcA');
```

#### Response Schema
```typescript
interface SingleRestaurantResponse {
  success: boolean;
  data: Restaurant; // Full restaurant object without menuItems
}
```

---

## 🍽️ Menu Item Endpoints

### GET /menu-items

**Use Case:** Advanced menu item search across all restaurants with powerful sorting capabilities.

#### Key Features
- **Cross-restaurant search** - Find menu items from all restaurants in area
- **Advanced sorting** - Including ratio-based sorting (e.g., protein/fat ratio)
- **Nutritional filtering** - Sort by calories, protein, etc.
- **Value sorting** - Sort by calories per dollar, protein per calorie, etc.

#### Query Parameters
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `latitude` | `number` | ✅ | - | Search center latitude |
| `longitude` | `number` | ✅ | - | Search center longitude |
| `page` | `number` | ❌ | `1` | Page number (1-based) |
| `limit` | `number` | ❌ | `20` | Items per page (max 100) |
| `radius` | `number` | ❌ | `10.0` | Search radius in km |
| `sort_by` | `string` | ❌ | `"restaurant_distance"` | Sort criteria |
| `sort_order` | `string` | ❌ | `"asc"` | `"asc"` or `"desc"` |
| `restaurant_id` | `string` | ❌ | - | Filter by specific restaurant |

#### Advanced Sort Options

**Standard Fields:**
- `restaurant_distance` - Distance from search center
- `price` - Item price
- `calories` - Caloric content
- `protein`, `carbs`, `fat`, `fiber`, `sugar`, `sodium` - Nutritional values
- `name` - Alphabetical order

**Ratio-Based Sorting (Advanced):**
Format: `field1/field2` where both fields are from: `protein`, `carbs`, `fat`, `fiber`, `sugar`, `sodium`, `calories`, `price`

Examples:
- `protein/fat` - Protein to fat ratio (lean options)
- `protein/calories` - Protein per calorie (protein efficiency)
- `calories/price` - Calories per dollar (value meals)
- `fiber/carbs` - Fiber to carb ratio (complex carbs)

#### Example Usage Patterns

```typescript
// Find high-protein items nearby
const getHighProteinItems = async (lat: number, lng: number) => {
  const params = new URLSearchParams({
    latitude: lat.toString(),
    longitude: lng.toString(),
    sort_by: 'protein',
    sort_order: 'desc',
    limit: '20'
  });
  
  return fetch(`http://localhost:5000/menu-items?${params}`).then(r => r.json());
};

// Find best protein-to-fat ratio items (lean protein)
const getLeanProteinItems = async (lat: number, lng: number) => {
  const params = new URLSearchParams({
    latitude: lat.toString(),
    longitude: lng.toString(),
    sort_by: 'protein/fat',
    sort_order: 'desc',
    limit: '20'
  });
  
  return fetch(`http://localhost:5000/menu-items?${params}`).then(r => r.json());
};

// Find best value meals (calories per dollar)
const getValueMeals = async (lat: number, lng: number) => {
  const params = new URLSearchParams({
    latitude: lat.toString(),
    longitude: lng.toString(),
    sort_by: 'calories/price',
    sort_order: 'desc',
    limit: '20'
  });
  
  return fetch(`http://localhost:5000/menu-items?${params}`).then(r => r.json());
};

// Find items from specific restaurant
const getRestaurantMenuItems = async (lat: number, lng: number, restaurantId: string) => {
  const params = new URLSearchParams({
    latitude: lat.toString(),
    longitude: lng.toString(),
    restaurant_id: restaurantId,
    sort_by: 'calories',
    sort_order: 'asc'
  });
  
  return fetch(`http://localhost:5000/menu-items?${params}`).then(r => r.json());
};
```

#### Response Schema
```typescript
interface MenuItem {
  // Identifiers
  id: string; // UUID
  restaurant_id: string;
  restaurant_name: string;
  restaurant_distance_km: number;
  restaurant_place_id: string;
  
  // Basic Info
  name: string;
  description: string | null;
  price: number | null;
  currency: string;
  
  // Nutritional Data (AI-generated)
  calories: number | null;
  serving_size: number | null; // grams
  protein: number | null; // grams
  carbs: number | null; // grams
  fat: number | null; // grams
  fiber: number | null; // grams
  sugar: number | null; // grams
  sodium: number | null; // milligrams
  
  // Classifications
  dietary_tags: string[]; // ["vegetarian", "gluten-free", etc.]
  allergens: string[]; // ["nuts", "dairy", "gluten", etc.]
  spice_level: string | null; // "mild", "medium", "hot"
  
  // Menu Organization
  category: string; // "Pizza", "Appetizers", "Entrees", etc.
  subcategory: string | null;
  menu_section: string | null;
  
  // Metadata
  confidence_score: number; // AI confidence (0.0-1.0)
  is_available: boolean;
  seasonal: boolean;
  
  // Timestamps
  created_at: string;
  updated_at: string;
  
  // Calculated Ratio (only present for ratio sorts)
  calculated_ratio?: {
    value: number;
    numerator: string;
    denominator: string;
    display: string; // "protein/fat"
  };
}

interface MenuItemsResponse {
  success: boolean;
  data: MenuItem[];
  pagination: {
    page: number;
    limit: number;
    total: number;
    total_pages: number;
    has_next: boolean;
    has_prev: boolean;
  };
  search_params: {
    latitude: number;
    longitude: number;
    radius_km: number;
    sort_by: string;
    sort_order: string;
    restaurant_id: string | null;
  };
}
```

#### Example Response (Protein/Fat Ratio Sort)
```json
{
  "success": true,
  "data": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "restaurant_id": "550e8400-e29b-41d4-a716-446655440001",
      "restaurant_name": "Tony's Little Star Pizza",
      "restaurant_distance_km": 0.3,
      "restaurant_place_id": "ChIJd8BlQ2BZwokRAFUEcm_qrcA",
      "name": "Grilled Chicken Salad",
      "description": "Grilled chicken breast over mixed greens",
      "price": 14.50,
      "currency": "USD",
      "calories": 285,
      "serving_size": 350.0,
      "protein": 32.5,
      "carbs": 12.2,
      "fat": 8.1,
      "fiber": 4.2,
      "sugar": 6.1,
      "sodium": 420.0,
      "dietary_tags": ["gluten-free"],
      "allergens": ["dairy"],
      "spice_level": null,
      "category": "Salads",
      "subcategory": "Main Salads",
      "menu_section": "Entrees",
      "confidence_score": 0.94,
      "is_available": true,
      "seasonal": false,
      "calculated_ratio": {
        "value": 4.01,
        "numerator": "protein",
        "denominator": "fat",
        "display": "protein/fat"
      },
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T10:30:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 156,
    "total_pages": 8,
    "has_next": true,
    "has_prev": false
  }
}
```

### GET /restaurants/\<restaurant_id\>/menu

**Use Case:** Get all menu items for a specific restaurant with sorting.

#### Path Parameters
- `restaurant_id` - Restaurant UUID or Google place_id

#### Query Parameters
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `latitude` | `number` | ✅ | - | For distance calculation |
| `longitude` | `number` | ✅ | - | For distance calculation |
| `page` | `number` | ❌ | `1` | Page number |
| `limit` | `number` | ❌ | `50` | Items per page (max 100) |
| `sort_by` | `string` | ❌ | `"name"` | Sort criteria |
| `sort_order` | `string` | ❌ | `"asc"` | Sort order |

#### Sort Options
All nutritional fields and ratios (same as `/menu-items`) except `restaurant_distance`.

#### Example Usage
```typescript
const getRestaurantMenu = async (
  restaurantId: string, 
  lat: number, 
  lng: number,
  sortBy: string = 'calories'
) => {
  const params = new URLSearchParams({
    latitude: lat.toString(),
    longitude: lng.toString(),
    sort_by: sortBy,
    sort_order: 'asc',
    limit: '50'
  });
  
  const response = await fetch(
    `http://localhost:5000/restaurants/${restaurantId}/menu?${params}`
  );
  return response.json();
};
```

#### Response Schema
```typescript
interface RestaurantMenuResponse {
  success: boolean;
  restaurant: {
    id: string;
    name: string;
    place_id: string;
    distance_km: number;
  };
  data: MenuItem[]; // Same MenuItem interface
  pagination: PaginationInfo;
  search_params: {
    latitude: number;
    longitude: number;
    sort_by: string;
    sort_order: string;
    restaurant_id: string;
  };
}
```

---

## 🏥 Health Check

### GET /health

**Use Case:** Check if the API server is running.

#### Example Usage
```typescript
const checkHealth = async () => {
  const response = await fetch('http://localhost:5000/health');
  return response.json();
};
```

#### Response
```json
{
  "status": "healthy",
  "message": "MacroMap backend is running"
}
```

---

## 🎯 Frontend Integration Patterns

### 1. Restaurant Discovery Flow

```typescript
interface UseRestaurantDiscovery {
  restaurants: Restaurant[];
  loading: boolean;
  error: string | null;
  discoverRestaurants: (lat: number, lng: number) => Promise<void>;
  loadMoreRestaurants: (page: number) => Promise<void>;
}

const useRestaurantDiscovery = (): UseRestaurantDiscovery => {
  const [restaurants, setRestaurants] = useState<Restaurant[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [currentLocation, setCurrentLocation] = useState<{lat: number, lng: number} | null>(null);

  const discoverRestaurants = async (lat: number, lng: number) => {
    setLoading(true);
    setError(null);
    setCurrentLocation({ lat, lng });
    
    try {
      // Step 1: Get immediate cached results
      const response = await fetch('http://localhost:5000/scan-nearby', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ latitude: lat, longitude: lng })
      });
      
      const data = await response.json();
      
      if (data.success) {
        setRestaurants(data.restaurants);
        
        // Step 2: Background processing will continue
        if (data.background_processing.status === 'started') {
          console.log('Background processing started for new restaurants');
        }
      } else {
        setError(data.error || 'Failed to discover restaurants');
      }
    } catch (err) {
      setError('Network error occurred');
    } finally {
      setLoading(false);
    }
  };

  const loadMoreRestaurants = async (page: number) => {
    if (!currentLocation) return;
    
    setLoading(true);
    try {
      const params = new URLSearchParams({
        latitude: currentLocation.lat.toString(),
        longitude: currentLocation.lng.toString(),
        page: page.toString(),
        limit: '20'
      });
      
      const response = await fetch(`http://localhost:5000/restaurants?${params}`);
      const data = await response.json();
      
      if (data.success) {
        if (page === 1) {
          setRestaurants(data.data);
        } else {
          setRestaurants(prev => [...prev, ...data.data]);
        }
      }
    } catch (err) {
      setError('Failed to load restaurants');
    } finally {
      setLoading(false);
    }
  };

  return { restaurants, loading, error, discoverRestaurants, loadMoreRestaurants };
};
```

### 2. Advanced Menu Search Hook

```typescript
interface MenuSearchFilters {
  sortBy: string;
  sortOrder: 'asc' | 'desc';
  restaurantId?: string;
}

interface UseMenuSearch {
  menuItems: MenuItem[];
  loading: boolean;
  error: string | null;
  pagination: PaginationInfo | null;
  searchMenuItems: (lat: number, lng: number, filters: MenuSearchFilters) => Promise<void>;
  loadMoreItems: (page: number) => Promise<void>;
}

const useMenuSearch = (): UseMenuSearch => {
  const [menuItems, setMenuItems] = useState<MenuItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pagination, setPagination] = useState<PaginationInfo | null>(null);
  const [currentSearch, setCurrentSearch] = useState<{
    lat: number;
    lng: number;
    filters: MenuSearchFilters;
  } | null>(null);

  const searchMenuItems = async (
    lat: number, 
    lng: number, 
    filters: MenuSearchFilters
  ) => {
    setLoading(true);
    setError(null);
    setCurrentSearch({ lat, lng, filters });
    
    try {
      const params = new URLSearchParams({
        latitude: lat.toString(),
        longitude: lng.toString(),
        sort_by: filters.sortBy,
        sort_order: filters.sortOrder,
        page: '1',
        limit: '20',
        ...(filters.restaurantId && { restaurant_id: filters.restaurantId })
      });
      
      const response = await fetch(`http://localhost:5000/menu-items?${params}`);
      const data = await response.json();
      
      if (data.success) {
        setMenuItems(data.data);
        setPagination(data.pagination);
      } else {
        setError(data.error || 'Failed to search menu items');
      }
    } catch (err) {
      setError('Network error occurred');
    } finally {
      setLoading(false);
    }
  };

  const loadMoreItems = async (page: number) => {
    if (!currentSearch) return;
    
    setLoading(true);
    try {
      const params = new URLSearchParams({
        latitude: currentSearch.lat.toString(),
        longitude: currentSearch.lng.toString(),
        sort_by: currentSearch.filters.sortBy,
        sort_order: currentSearch.filters.sortOrder,
        page: page.toString(),
        limit: '20',
        ...(currentSearch.filters.restaurantId && { 
          restaurant_id: currentSearch.filters.restaurantId 
        })
      });
      
      const response = await fetch(`http://localhost:5000/menu-items?${params}`);
      const data = await response.json();
      
      if (data.success) {
        setMenuItems(prev => [...prev, ...data.data]);
        setPagination(data.pagination);
      }
    } catch (err) {
      setError('Failed to load more items');
    } finally {
      setLoading(false);
    }
  };

  return { menuItems, loading, error, pagination, searchMenuItems, loadMoreItems };
};
```

### 3. Smart Filter Component

```typescript
interface MenuFilterProps {
  onFilterChange: (filters: MenuSearchFilters) => void;
  currentFilters: MenuSearchFilters;
}

const MenuFilter: React.FC<MenuFilterProps> = ({ onFilterChange, currentFilters }) => {
  const [sortBy, setSortBy] = useState(currentFilters.sortBy);
  const [sortOrder, setSortOrder] = useState(currentFilters.sortOrder);
  
  const sortOptions = [
    // Distance & Basic
    { value: 'restaurant_distance', label: 'Distance', category: 'Location' },
    { value: 'price', label: 'Price', category: 'Basic' },
    { value: 'name', label: 'Name', category: 'Basic' },
    
    // Nutritional
    { value: 'calories', label: 'Calories', category: 'Nutrition' },
    { value: 'protein', label: 'Protein', category: 'Nutrition' },
    { value: 'carbs', label: 'Carbs', category: 'Nutrition' },
    { value: 'fat', label: 'Fat', category: 'Nutrition' },
    { value: 'fiber', label: 'Fiber', category: 'Nutrition' },
    { value: 'sodium', label: 'Sodium', category: 'Nutrition' },
    
    // Advanced Ratios
    { value: 'protein/fat', label: 'Protein/Fat Ratio', category: 'Ratios' },
    { value: 'protein/calories', label: 'Protein per Calorie', category: 'Ratios' },
    { value: 'calories/price', label: 'Calories per Dollar', category: 'Ratios' },
    { value: 'fiber/carbs', label: 'Fiber/Carb Ratio', category: 'Ratios' },
  ];
  
  const groupedOptions = sortOptions.reduce((acc, option) => {
    if (!acc[option.category]) {
      acc[option.category] = [];
    }
    acc[option.category].push(option);
    return acc;
  }, {} as Record<string, typeof sortOptions>);
  
  const handleApplyFilters = () => {
    onFilterChange({
      sortBy,
      sortOrder: sortOrder as 'asc' | 'desc'
    });
  };
  
  return (
    <div className="menu-filter">
      <div className="filter-section">
        <label htmlFor="sort-by">Sort By:</label>
        <select 
          id="sort-by"
          value={sortBy} 
          onChange={(e) => setSortBy(e.target.value)}
        >
          {Object.entries(groupedOptions).map(([category, options]) => (
            <optgroup key={category} label={category}>
              {options.map(option => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </optgroup>
          ))}
        </select>
      </div>
      
      <div className="filter-section">
        <label htmlFor="sort-order">Order:</label>
        <select 
          id="sort-order"
          value={sortOrder} 
          onChange={(e) => setSortOrder(e.target.value)}
        >
          <option value="desc">Highest First</option>
          <option value="asc">Lowest First</option>
        </select>
      </div>
      
      <button onClick={handleApplyFilters} className="apply-filters-btn">
        Apply Filters
      </button>
    </div>
  );
};
```

### 4. Pagination Component

```typescript
interface PaginationProps {
  pagination: PaginationInfo;
  onPageChange: (page: number) => void;
  loading?: boolean;
}

const Pagination: React.FC<PaginationProps> = ({ 
  pagination, 
  onPageChange, 
  loading = false 
}) => {
  const { page, total_pages, has_prev, has_next, total } = pagination;
  
  const getPageNumbers = () => {
    const pages = [];
    const maxPages = 5;
    let start = Math.max(1, page - Math.floor(maxPages / 2));
    let end = Math.min(total_pages, start + maxPages - 1);
    
    if (end - start + 1 < maxPages) {
      start = Math.max(1, end - maxPages + 1);
    }
    
    for (let i = start; i <= end; i++) {
      pages.push(i);
    }
    
    return pages;
  };
  
  return (
    <div className="pagination">
      <div className="pagination-info">
        Showing page {page} of {total_pages} ({total} total items)
      </div>
      
      <div className="pagination-controls">
        <button 
          disabled={!has_prev || loading} 
          onClick={() => onPageChange(page - 1)}
          className="pagination-btn"
        >
          Previous
        </button>
        
        {getPageNumbers().map(pageNum => (
          <button
            key={pageNum}
            disabled={loading}
            onClick={() => onPageChange(pageNum)}
            className={`pagination-btn ${pageNum === page ? 'active' : ''}`}
          >
            {pageNum}
          </button>
        ))}
        
        <button 
          disabled={!has_next || loading} 
          onClick={() => onPageChange(page + 1)}
          className="pagination-btn"
        >
          Next
        </button>
      </div>
    </div>
  );
};
```

---

## ⚠️ Error Handling

All endpoints return consistent error responses:

### HTTP Status Codes
- `200` - Success
- `400` - Bad Request (invalid parameters)
- `404` - Not Found (restaurant not found)
- `500` - Internal Server Error

### Error Response Format
```typescript
interface ErrorResponse {
  error: string;
  details?: string; // Additional error information
}
```

### Example Error Responses
```json
// Missing required parameters
{
  "error": "Missing required parameters: latitude and longitude"
}

// Invalid sort parameter
{
  "error": "Invalid sort_by. Must be one of: distance, rating, reviews_count, name or a ratio like 'protein/fat'"
}

// Restaurant not found
{
  "error": "Restaurant not found"
}

// Internal server error
{
  "error": "Internal server error",
  "details": "Database connection failed"
}
```

### Frontend Error Handling Pattern
```typescript
const handleApiCall = async (apiCall: () => Promise<Response>) => {
  try {
    const response = await apiCall();
    const data = await response.json();
    
    if (!response.ok) {
      throw new Error(data.error || `HTTP ${response.status}`);
    }
    
    if (!data.success) {
      throw new Error(data.error || 'API call failed');
    }
    
    return data;
  } catch (error) {
    console.error('API Error:', error);
    throw error;
  }
};
```

---

## 🚀 Performance Best Practices

### 1. Caching Strategy
- **Restaurant Discovery**: First call returns cached results immediately
- **Background Processing**: New data fetched asynchronously
- **Client-Side Caching**: Cache responses for 5-10 minutes

### 2. Pagination Best Practices
- Use reasonable page sizes (10-50 items)
- Implement infinite scroll for better UX
- Show loading states during page transitions

### 3. Location Updates
- Debounce location updates to avoid excessive API calls
- Only trigger new searches when location changes significantly (>1km)

### 4. Optimistic Loading
```typescript
const optimisticSearch = async (lat: number, lng: number, filters: MenuSearchFilters) => {
  // Show previous results immediately
  setLoading(true);
  
  try {
    // Start the API call
    const newResults = await searchMenuItems(lat, lng, filters);
    
    // Update with new results
    setMenuItems(newResults.data);
  } catch (error) {
    // Keep previous results on error
    setError('Failed to load new results');
  } finally {
    setLoading(false);
  }
};
```

---

## 🔧 Setup and Development

### Prerequisites
- Python 3.12+
- Node.js 18+ (for frontend)
- Environment variables configured

### Environment Variables
```env
APIFY_API_TOKEN=your-apify-token-here
SUPABASE_URL=your-supabase-url-here  
SUPABASE_KEY=your-supabase-anon-key-here
OPENAI_API_KEY=your-openai-api-key-here
```

### Running the Backend
```bash
# Install dependencies
pip install -r requirements.txt

# Start development server
python main.py

# Server runs on http://localhost:5000
```

### Testing API Endpoints
```bash
# Health check
curl http://localhost:5000/health

# Restaurant discovery
curl -X POST http://localhost:5000/scan-nearby \
  -H "Content-Type: application/json" \
  -d '{"latitude": 37.7749, "longitude": -122.4194}'

# Get restaurants with pagination
curl "http://localhost:5000/restaurants?latitude=37.7749&longitude=-122.4194&page=1&limit=10"

# Get menu items with ratio sorting
curl "http://localhost:5000/menu-items?latitude=37.7749&longitude=-122.4194&sort_by=protein/fat&sort_order=desc"
```

---

## 📞 Support

For questions about API integration:
1. Check the examples in this documentation
2. Test endpoints with curl commands above  
3. Review error messages for debugging hints
4. Open an issue for bugs or feature requests

---

**Built for MacroMaps Frontend Integration** 🗺️
