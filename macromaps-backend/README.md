# MacroMaps Backend Server 🗺️

A Flask-based backend server for the MacroMaps application that provides restaurant discovery and comprehensive menu analysis capabilities with AI-powered nutritional information extraction.

## 🚀 Features

### Core Functionality
- **Restaurant Discovery**: Find nearby restaurants using GPS coordinates
- **Real-time Data**: Integration with Apify API for Google Places data extraction
- **Mock Mode**: Development-friendly mock data generation for testing
- **AI-Powered Menu Analysis**: Complete pipeline for menu image processing and nutritional extraction
- **Smart Image Processing**: Prioritized processing of menu-likely images (URLs with `/p/` prioritized over `/gps-cs-s/`)
- **Database Integration**: Supabase integration for persistent data storage
- **CORS Support**: Cross-origin resource sharing enabled for frontend integration
- **Parallel Processing**: Multi-threaded menu processing for optimal performance

### Advanced Menu Processing
- **Image Classification**: AI-powered identification of menu images vs. other restaurant photos
- **Menu Item Extraction**: Detailed extraction of menu items with prices and descriptions
- **Nutritional Analysis**: AI-estimated macronutrient breakdown (calories, protein, carbs, fat)
- **Menu Consolidation**: Intelligent merging of menu items from multiple images
- **Cost-Optimized Processing**: Uses `gpt-4.1-nano` for classification and `gpt-4.1` for detailed analysis

### API Capabilities
- Location-based restaurant search within customizable radius
- Restaurant data including ratings, reviews, contact information
- Complete menu items with detailed nutritional breakdown
- Restaurant images and photo metadata with smart prioritization
- Opening hours and contact information
- Price level indicators
- Processing status tracking for restaurants

## 🏗️ System Architecture

```mermaid
graph TB
    %% Frontend/Client Layer
    Client[🌐 Frontend Client<br/>React/Mobile App]
    
    %% Main Flask Application
    Flask[🐍 Flask Server<br/>main.py<br/>Port: 5000]
    
    %% API Endpoints
    Health[🏥 /health<br/>Health Check]
    ScanNearby[📍 /scan-nearby<br/>Restaurant Discovery<br/>+ Auto Menu Processing]
    
    %% Decision Logic
    MockCheck{Mock Mode?<br/>mock: true/false}
    
    %% Core Utilities
    MockUtils[🎭 Mock Utils<br/>mock_utils.py<br/>Generate Fake Data]
    ApifyUtils[🔍 Apify Utils<br/>apify_utils.py<br/>Real Restaurant Data]
    SupabaseUtils[🗄️ Supabase Utils<br/>supabase_utils.py<br/>Database Operations]
    
    %% Processing Pipeline
    RestaurantProcessor[🏭 Restaurant Processor<br/>restaurant_processing.py<br/>Background Threading]
    MenuProcessor[🤖 Menu Processor<br/>menu_processing.py<br/>AI-Powered Analysis]
    LLMUtils[🧠 LLM Utils<br/>llm_utils.py<br/>Menu Analysis]
    
    %% External Services
    ApifyAPI[🌍 Apify API<br/>Google Places Crawler<br/>compass/crawler-google-places]
    SupabaseDB[(🗃️ Supabase Database<br/>PostgreSQL<br/>• restaurants table<br/>• menu_items table)]
    OpenAI[🧠 OpenAI API<br/>GPT Models<br/>Menu Analysis]
    
    %% Data Processing
    DataFormat[📋 Data Formatting<br/>• Standardize Structure<br/>• Add Nutritional Info<br/>• Generate Menu Items]
    
    %% Response Assembly
    Response[📦 JSON Response<br/>• Restaurant List<br/>• Menu Items<br/>• Nutritional Data<br/>• Processing Status]
    
    %% Flow Connections
    Client -->|HTTP Request POST /scan-nearby| Flask
    Client -->|HTTP Request GET /health| Flask
    
    Flask --> Health
    Flask --> ScanNearby
    
    ScanNearby --> MockCheck
    
    %% Mock Mode Path
    MockCheck -->|Yes| MockUtils
    MockUtils --> DataFormat
    
    %% Real API Mode Path
    MockCheck -->|No| ApifyUtils
    ApifyUtils -->|API Call Location + Radius| ApifyAPI
    ApifyAPI -->|Restaurant Data + Images| ApifyUtils
    ApifyUtils --> DataFormat
    ApifyUtils --> RestaurantProcessor
    
    %% Background Processing Pipeline
    RestaurantProcessor -->|Spawn Thread per Restaurant| MenuProcessor
    MenuProcessor -->|Image Classification & Analysis| LLMUtils
    LLMUtils -->|AI Menu Analysis| OpenAI
    MenuProcessor -->|Save Menu Items| SupabaseUtils
    
    %% Database Integration
    SupabaseUtils <-->|Query/Store Data| SupabaseDB
    DataFormat --> SupabaseUtils
    
    %% Response Flow
    DataFormat --> Response
    Health --> Response
    Response -->|JSON Response| Client
    
    %% Styling
    classDef client fill:#e1f5fe
    classDef flask fill:#f3e5f5
    classDef utils fill:#e8f5e8
    classDef processing fill:#fff9c4
    classDef external fill:#fff3e0
    classDef database fill:#fce4ec
    classDef decision fill:#f1f8e9
    
    class Client client
    class Flask,Health,ScanNearby flask
    class MockUtils,ApifyUtils,SupabaseUtils,LLMUtils utils
    class RestaurantProcessor,MenuProcessor processing
    class ApifyAPI,OpenAI external
    class SupabaseDB database
    class MockCheck decision
```

## 🔄 Data Flow Diagram

```mermaid
sequenceDiagram
    participant C as 🌐 Client
    participant F as 🐍 Flask Server
    participant M as 🎭 Mock Utils
    participant A as 🔍 Apify Utils
    participant API as 🌍 Apify API
    participant RP as 🏭 Restaurant Processor
    participant MP as 🤖 Menu Processor
    participant LLM as 🧠 LLM Utils
    participant S as 🗄️ Supabase
    participant DB as 🗃️ Database
    
    Note over C,DB: Restaurant Discovery + Auto Menu Processing Flow
    
    C->>F: POST /scan-nearby<br/>{lat, lng, mock}
    
    alt Mock Mode (mock: true)
        F->>M: Generate mock restaurants
        M->>M: Create realistic data<br/>within radius
        M->>F: Return mock restaurants<br/>with menu items
    else Real API Mode (mock: false)
        F->>A: Extract restaurants<br/>(lat, lng)
        A->>API: Call Google Places<br/>Crawler Actor
        Note over API: Scrape Google Places<br/>• Restaurant details<br/>• Reviews & ratings<br/>• Opening hours<br/>• Image URLs<br/>• Basic data
        API->>A: Return raw restaurant data
        A->>A: Format & standardize<br/>restaurant data
        A->>S: Store restaurants with<br/>status = 'pending'
        S->>DB: Insert new restaurants
        DB->>S: Confirmation
        
        %% Trigger background processing
        A->>RP: trigger_restaurant_processing<br/>(restaurant_data)
        Note over RP: Extract place_ids<br/>Start background thread
        
        par Background Menu Processing
            loop For each restaurant
                RP->>S: Update status to 'processing'
                RP->>MP: process_restaurant_images<br/>(place_id)
                
                MP->>S: Get image URLs<br/>for restaurant
                S->>MP: Return image_urls array
                
                MP->>MP: Sort images by priority<br/>/p/ > /gps-cs-s/ > others
                
                par Image Classification (Parallel)
                    MP->>LLM: classify_menu_image<br/>(gpt-4.1-nano)
                    LLM->>MP: is_menu: true/false
                end
                
                MP->>MP: Filter menu images<br/>from classification results
                
                par Menu Analysis (Parallel)
                    MP->>LLM: analyze_menu_image<br/>(gpt-4.1, 5000 tokens)
                    LLM->>MP: menu_items with<br/>prices, descriptions, macros
                end
                
                MP->>LLM: aggregate_menu_items<br/>(consolidate duplicates)
                LLM->>MP: final_menu_items
                
                MP->>S: Save menu_items<br/>to database
                S->>DB: Insert menu items
                RP->>S: Update status to 'finished'
            end
        end
        
        A->>F: Formatted restaurants<br/>+ processing status
    end
    
    F->>F: Assemble final response<br/>• Restaurant data<br/>• Processing status<br/>• Search location
    
    F->>C: JSON Response<br/>{success, restaurants[],<br/>menu_processing: {...}}
    
    Note over C,DB: Background processing continues<br/>Menu items saved asynchronously
    
    Note over C,DB: Health Check Flow
    C->>F: GET /health
    F->>C: {status: "healthy"}
```

## 🧩 Component Architecture

```mermaid
graph LR
    subgraph "🐍 Flask Application"
        Main[main.py<br/>• Route definitions<br/>• CORS setup<br/>• Error handling]
    end
    
    subgraph "🛠️ Utility Layer"
        direction TB
        ApifyUtil[apify_utils.py<br/>• API integration<br/>• Data extraction<br/>• Response formatting]
        MockUtil[mock_utils.py<br/>• Fake data generation<br/>• Realistic restaurants<br/>• Menu item creation]
        SupaUtil[supabase_utils.py<br/>• Database operations<br/>• Distance calculations<br/>• Data persistence]
        LLMUtil[llm_utils.py<br/>• AI menu analysis<br/>• Nutrition enhancement<br/>• Image classification]
    end
    
    subgraph "🏭 Processing Pipeline"
        direction TB
        RestaurantProc[restaurant_processing.py<br/>• Background threading<br/>• Status management<br/>• Parallel processing]
        MenuProc[menu_processing.py<br/>• Image classification<br/>• Menu extraction<br/>• AI consolidation]
    end
    
    subgraph "🌐 External APIs"
        direction TB
        Apify[Apify API<br/>• Google Places data<br/>• Restaurant scraping<br/>• Image URL extraction]
        Supabase[Supabase<br/>• PostgreSQL database<br/>• Real-time features<br/>• Restaurant & menu storage]
        OpenAIAPI[OpenAI API<br/>• GPT models<br/>• Menu analysis<br/>• Nutrition insights]
    end
    
    subgraph "🧪 Testing Layer"
        direction TB
        TestApify[test_apify.py<br/>• API integration tests<br/>• Response validation]
        TestMenu[test_menu_processing.py<br/>• Menu pipeline tests<br/>• Cost tracking<br/>• Smart image selection]
        TestModels[test_models.py<br/>• Data model tests<br/>• Nutrition calculations]
    end
    
    Main --> ApifyUtil
    Main --> MockUtil
    Main --> RestaurantProc
    
    ApifyUtil --> Apify
    ApifyUtil --> RestaurantProc
    RestaurantProc --> MenuProc
    MenuProc --> LLMUtil
    MenuProc --> SupaUtil
    LLMUtil --> OpenAIAPI
    SupaUtil --> Supabase
    
    TestApify --> ApifyUtil
    TestMenu --> MenuProc
    TestMenu --> RestaurantProc
    TestModels --> MockUtil
    TestModels --> SupaUtil
```

## 🎯 Ideal System Workflow

### 📋 Complete Restaurant Processing Pipeline

```mermaid
flowchart TD
    Start([🔍 User Scan Request<br/>POST /scan-nearby])
    
    CheckDB{🗄️ Check Supabase<br/>Restaurants in radius<br/>status = 'finished'}
    
    HasFinished{Found finished<br/>restaurants?}
    
    ReturnExisting[📤 Return existing<br/>finished restaurants]
    
    ApifyCall[🌍 Hit Apify API<br/>Extract new restaurant data<br/>in scan circle]
    
    ParallelProcess[⚡ Parallel Processing<br/>Push each restaurant<br/>to Supabase]
    
    UpdateStatus1[📝 Mark restaurants as<br/>status = 'processing']
    
    MenuPipeline[🤖 Start Menu Analysis Pipeline<br/>For each restaurant]
    
    GetImages[📸 Get image URLs<br/>from Supabase<br/>restaurant.image_urls]
    
    ClassifyMenus[🔍 Classify Images<br/>Which are menu images?]
    
    ExtractItems[📋 Extract Menu Items<br/>• Item name<br/>• Price only]
    
    MergeMenus[🧠 LLM Merge<br/>Combine all menu items<br/>into final menu]
    
    MacroAnalysis[🍎 LLM Macro Analysis<br/>Estimate nutritional info<br/>per menu item]
    
    SaveMenuItems[💾 Push Menu Items<br/>to Supabase<br/>with restaurant_id]
    
    MarkComplete[✅ Mark Restaurant<br/>status = 'finished']
    
    FinalResponse[📤 Return Complete<br/>Restaurant + Menu Data]
    
    Start --> CheckDB
    CheckDB --> HasFinished
    
    HasFinished -->|Yes| ReturnExisting
    HasFinished -->|No| ApifyCall
    
    ApifyCall --> ParallelProcess
    ParallelProcess --> UpdateStatus1
    UpdateStatus1 --> MenuPipeline
    
    MenuPipeline --> GetImages
    GetImages --> ClassifyMenus
    ClassifyMenus --> ExtractItems
    ExtractItems --> MergeMenus
    MergeMenus --> MacroAnalysis
    MacroAnalysis --> SaveMenuItems
    SaveMenuItems --> MarkComplete
    MarkComplete --> FinalResponse
    
    ReturnExisting --> FinalResponse
```

### 🔄 Detailed Processing Steps

1. **Initial Scan Request**
   - User sends GPS coordinates + radius
   - Backend receives scan request with location data

2. **Database Check Phase**
   - Query Supabase for restaurants within scan radius
   - Filter for `status = 'finished'` restaurants
   - Return immediately if sufficient data exists

3. **Data Acquisition Phase**
   - Hit Apify API with location + radius parameters
   - Extract new restaurant data from Google Places
   - Parallel processing: Push each restaurant to Supabase
   - Include complete image URL arrays for each restaurant

4. **Menu Analysis Pipeline** (Parallel Processing)
   - **Image Classification**: Identify which images are menu photos
   - **Menu Extraction**: Extract item names and prices from menu images
   - **Menu Consolidation**: LLM merges all extracted items into final menu
   - **Nutritional Analysis**: LLM estimates macros (calories, protein, carbs, fat)

5. **Data Persistence Phase**
   - Push enriched menu items to Supabase with restaurant associations
   - Update restaurant status to `'finished'`
   - Return complete restaurant + menu data to client

## 🗃️ Database Schema

### 🏪 Restaurants Table

```sql
CREATE TABLE restaurants (
    -- Primary Identifiers
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    place_id VARCHAR(255) UNIQUE NOT NULL,
    
    -- Basic Information
    name VARCHAR(500) NOT NULL,
    address TEXT,
    phone VARCHAR(50),
    website TEXT,
    
    -- Location Data
    latitude DECIMAL(10, 8) NOT NULL,
    longitude DECIMAL(11, 8) NOT NULL,
    
    -- Rating & Reviews
    rating DECIMAL(3, 2),
    reviews_count INTEGER DEFAULT 0,
    
    -- Classification
    category VARCHAR(200),
    price_level VARCHAR(10), -- $, $$, $$$, $$$$
    
    -- Operating Hours (JSON array)
    opening_hours JSONB,
    
    -- Image Data
    image_urls TEXT[], -- Array of direct image URLs
    images JSONB, -- Detailed image objects with metadata
    
    -- Processing Status
    status VARCHAR(20) DEFAULT 'pending', -- pending, processing, finished, error
    processing_started_at TIMESTAMP,
    processing_completed_at TIMESTAMP,
    
    -- External References
    google_maps_url TEXT,
    apify_run_id VARCHAR(100),
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- Indexes for performance
    INDEX idx_restaurants_location (latitude, longitude),
    INDEX idx_restaurants_status (status),
    INDEX idx_restaurants_place_id (place_id)
);
```

### 🍽️ Menu Items Table

```sql
CREATE TABLE menu_items (
    -- Primary Identifiers
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    restaurant_id UUID NOT NULL REFERENCES restaurants(id) ON DELETE CASCADE,
    
    -- Basic Item Information
    name VARCHAR(300) NOT NULL,
    description TEXT,
    price DECIMAL(10, 2),
    currency VARCHAR(3),
    
    -- Nutritional Information (LLM Generated)
    calories INTEGER,
    protein DECIMAL(5, 2), -- grams
    carbs DECIMAL(5, 2), -- grams  
    fat DECIMAL(5, 2), -- grams
    fiber DECIMAL(5, 2), -- grams
    sugar DECIMAL(5, 2), -- grams
    sodium DECIMAL(8, 2), -- milligrams
    
    -- Dietary Classifications
    dietary_tags TEXT[], -- vegetarian, vegan, gluten-free, etc.
    allergens TEXT[], -- nuts, dairy, gluten, etc.
    spice_level VARCHAR(20), -- mild, medium, hot, etc.
    
    -- Menu Organization
    category VARCHAR(100), -- appetizers, mains, desserts, etc.
    subcategory VARCHAR(100),
    menu_section VARCHAR(100),
    
    -- Processing Metadata
    extracted_from_image_url TEXT, -- Which image this item was extracted from
    confidence_score DECIMAL(3, 2), -- AI confidence in extraction (0.00-1.00)
    llm_processed BOOLEAN DEFAULT FALSE,
    
    -- Availability
    is_available BOOLEAN DEFAULT TRUE,
    seasonal BOOLEAN DEFAULT FALSE,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- Indexes for performance
    INDEX idx_menu_items_restaurant (restaurant_id),
    INDEX idx_menu_items_category (category),
    INDEX idx_menu_items_dietary (dietary_tags),
    INDEX idx_menu_items_nutrition (calories, protein, carbs, fat)
);
```

### 🔗 Supporting Tables

#### Image Processing Log
```sql
CREATE TABLE image_processing_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    restaurant_id UUID NOT NULL REFERENCES restaurants(id),
    image_url TEXT NOT NULL,
    is_menu_image BOOLEAN,
    classification_confidence DECIMAL(3, 2),
    processing_status VARCHAR(20), -- pending, processing, completed, failed
    extracted_items_count INTEGER DEFAULT 0,
    processed_at TIMESTAMP DEFAULT NOW()
);
```

#### Processing Queue
```sql
CREATE TABLE processing_queue (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    restaurant_id UUID NOT NULL REFERENCES restaurants(id),
    task_type VARCHAR(50) NOT NULL, -- menu_extraction, nutrition_analysis
    priority INTEGER DEFAULT 5,
    status VARCHAR(20) DEFAULT 'pending', -- pending, processing, completed, failed
    attempts INTEGER DEFAULT 0,
    max_attempts INTEGER DEFAULT 3,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    started_at TIMESTAMP,
    completed_at TIMESTAMP
);
```

## 🔧 Configuration Parameters

### Apify Settings
```python
APIFY_CONFIG = {
    "actor_id": "compass/crawler-google-places",
    "search_radius_km": 2.0,
    "max_places_per_search": 20,
    "max_images_per_place": 50,
    "include_menu_data": True,
    "include_reviews": False,
    "language": "en"
}
```

### Menu Processing Settings
```python
MENU_PROCESSING_CONFIG = {
    # AI Model Configuration
    "classification_model": "gpt-4.1-nano",     # Cost-optimized for yes/no classification
    "analysis_model": "gpt-4.1",               # High-accuracy for detailed extraction
    "aggregation_model": "gpt-4.1",            # Menu consolidation and deduplication
    
    # Token Limits
    "classification_max_tokens": 1000,          # Sufficient for classification
    "analysis_max_tokens": 5000,               # Increased for complex menus
    "aggregation_max_tokens": 3000,            # Menu consolidation
    
    # Processing Configuration
    "image_classification_confidence_threshold": 0.7,
    "max_concurrent_restaurants": 10,
    "classification_workers": 5,                # Parallel image classification
    "analysis_workers": 3,                     # Parallel menu analysis
    "retry_attempts": 3,
    
    # Image Prioritization
    "priority_url_patterns": {
        "/p/": 0,          # Highest priority (Google Photos direct links)
        "/gps-cs-s/": 1,   # Medium priority (Google Street View)
        "default": 2       # Lowest priority (other sources)
    }
}
```

### Database Connection Pools
```python
DATABASE_CONFIG = {
    "supabase_pool_size": 20,
    "max_connections": 100,
    "connection_timeout": 30,
    "query_timeout": 60
}
```

## 🚧 Implementation Roadmap

### ✅ Currently Implemented
- [x] Basic Flask server with CORS support
- [x] `/health` endpoint for server monitoring
- [x] `/scan-nearby` endpoint with basic functionality
- [x] Mock data generation system (`mock_utils.py`)
- [x] Basic Apify API integration (`apify_utils.py`)
- [x] Supabase connection utilities (`supabase_utils.py`)
- [x] Basic error handling and logging
- [x] Development testing framework
- [x] **Complete Menu Processing Pipeline** (`tasks/menu_processing.py`)
- [x] **AI-Powered Image Classification** (menu vs. non-menu images)
- [x] **Menu Item Extraction** with prices, descriptions, and nutritional analysis
- [x] **Smart Image Prioritization** (URLs with `/p/` prioritized over `/gps-cs-s/`)
- [x] **Parallel Processing** with configurable worker threads
- [x] **LLM Integration** for menu analysis and nutritional estimation
- [x] **Menu Consolidation** with duplicate detection and merging
- [x] **Cost-Optimized Processing** using `gpt-4.1-nano` for classification
- [x] **Enhanced Testing Suite** with realistic menu processing tests
- [x] **Comprehensive Database Schema** for restaurants and menu items

### 🔨 Still Needs Implementation

#### 🗄️ **Database Layer Enhancements**
- [ ] **Complete Database Migration System**
  ```python
  # Implement proper database migrations
  # Set up automated schema updates
  # Add database versioning system
  ```

- [ ] **Smart Restaurant Lookup Optimization**
  ```python
  # supabase_utils.py enhancements
  def get_finished_restaurants_in_radius(lat, lng, radius_km):
      # Enhanced geospatial queries with PostGIS
      # Implement intelligent caching strategies
      # Add proximity-based relevance scoring
  ```

#### 🔄 **Production Infrastructure**
- [ ] **Background Job Queue Integration**
  ```python
  # Implement Celery or similar task queue
  # Add Redis for job management
  # Handle long-running menu processing tasks
  ```

- [ ] **API Rate Limiting & Caching**
  ```python
  # Implement Redis-based caching
  # Add API rate limiting
  # Cache processed menu data
  ```

#### ⚡ **Enhanced API Endpoints**
- [ ] **Processing Status Endpoint**
  ```python
  @app.route("/processing-status/<restaurant_id>", methods=["GET"])
  def get_processing_status(restaurant_id):
      # Return current processing stage
      # Estimated completion time
      # Error states if any
  ```

- [ ] **Menu Data Endpoint**
  ```python
  @app.route("/restaurant/<place_id>/menu", methods=["GET"])
  def get_restaurant_menu(place_id):
      # Return detailed menu with nutritional data
      # Support filtering by dietary requirements
      # Include confidence scores
  ```

### 🎯 **Success Metrics**
- **Response Time**: < 2 seconds for existing data, < 30 seconds for new processing
- **Accuracy**: > 90% menu extraction accuracy, > 85% nutrition estimation
- **Reliability**: > 99% uptime, < 1% failed processing rate
- **Scalability**: Handle 1000+ concurrent requests, process 100+ restaurants simultaneously

## 📋 Prerequisites

- Python 3.12 or higher
- Apify API token (for real restaurant data)
- Supabase account and credentials (for data persistence)
- OpenAI API key (for advanced menu analysis)

## 🛠️ Installation

### 1. Clone the repository
```bash
git clone <repository-url>
cd macromaps-backend
```

### 2. Set up Python environment
```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate
```

### 3. Install dependencies
```bash
# Using pip
pip install -r requirements.txt

# Or using uv (recommended)
uv pip install -r requirements.txt
```

### 4. Environment Configuration
Create a `.env` file in the project root:
```env
APIFY_API_TOKEN=your-apify-token-here
SUPABASE_URL=your-supabase-url-here
SUPABASE_KEY=your-supabase-anon-key-here
OPENAI_API_KEY=your-openai-api-key-here
```

### 5. Get API Keys

#### Apify API Token
1. Sign up at [Apify.com](https://apify.com/)
2. Get your free API token from the dashboard
3. Add it to your `.env` file

#### Supabase Credentials
1. Create a project at [Supabase](https://supabase.com/)
2. Get your project URL and anon key
3. Add them to your `.env` file

#### OpenAI API Key (Optional)
1. Get your API key from [OpenAI](https://openai.com/)
2. Add it to your `.env` file for advanced menu analysis

## 🚀 Running the Server

### Development Mode
```bash
python main.py
```

The server will start on `http://localhost:5000` with debug mode enabled.

### Production Mode
```bash
# Set environment variables
export FLASK_ENV=production
export FLASK_DEBUG=False

# Run with gunicorn (recommended for production)
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 main:app
```

## 📚 API Documentation

### Base URL
```
http://localhost:5000
```

### Endpoints

#### 1. Health Check
```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "message": "MacroMap backend is running"
}
```

#### 2. Scan Nearby Restaurants (with Auto Menu Processing)
```http
POST /scan-nearby
```

**Request Body:**
```json
{
  "latitude": 40.7128,
  "longitude": -74.0060,
  "mock": false  // Optional: set to true for mock data
}
```

**Response (Success):**
```json
{
  "success": true,
  "message": "Found 10 restaurants",
  "restaurants": [
    {
      "name": "Example Restaurant",
      "address": "123 Main St, New York, NY 10001",
      "rating": 4.5,
      "reviewsCount": 156,
      "category": "Italian restaurant",
      "phone": "+1-555-123-4567",
      "website": "https://example-restaurant.com",
      "priceLevel": "$$",
      "openingHours": [
        "Monday: 11:00 AM–10:00 PM",
        "Tuesday: 11:00 AM–10:00 PM",
        "..."
      ],
      "location": {
        "lat": 40.7128,
        "lng": -74.0060
      },
      "placeId": "ChIJExample123",
      "url": "https://maps.google.com/?cid=123456789",
      "menuItems": [],  // Will be populated asynchronously
      "images": [],
      "imageUrls": [
        "https://lh3.googleusercontent.com/p/...",
        "https://lh3.googleusercontent.com/gps-cs-s/..."
      ]
    }
  ],
  "searchLocation": {
    "latitude": 40.7128,
    "longitude": -74.0060
  },
  "menu_processing": {
    "triggered": true,
    "restaurants_count": 10,
    "message": "Menu processing started for 10 restaurants"
  }
}
```

**Response (Error):**
```json
{
  "error": "Missing latitude or longitude in request"
}
```

### Automatic Menu Processing
When you call `/scan-nearby` with real data (not mock mode), the following happens automatically:

1. **Restaurant Discovery**: Apify extracts restaurant data and saves to database with `status: 'pending'`
2. **Background Processing**: Each restaurant gets processed in a separate background thread
3. **Menu Analysis**: Images are classified, menus extracted, and nutritional data generated
4. **Database Updates**: Menu items are saved and restaurant status updated to `'finished'`

The initial response returns immediately with restaurant data, while menu processing continues in the background. You can check restaurant status or query menu items separately once processing completes.

## 🗂️ Project Structure

```
macromaps-backend/
├── main.py                     # Main Flask application
├── requirements.txt            # Python dependencies
├── pyproject.toml             # Project configuration
├── uv.lock                    # UV lock file
├── .env                       # Environment variables (create this)
├── .python-version            # Python version specification
├── tasks/                     # Processing pipeline tasks
│   ├── __init__.py
│   ├── restaurant_processing.py # Restaurant processing orchestrator
│   └── menu_processing.py     # Complete menu processing pipeline
├── utils/                     # Utility modules
│   ├── __init__.py
│   ├── apify_utils.py         # Apify API integration
│   ├── mock_utils.py          # Mock data generation
│   ├── supabase_utils.py      # Database operations
│   └── llm_utils.py           # LLM integration for menu analysis
├── tests/                     # Test files
│   ├── test_apify.py          # Apify API tests
│   ├── test_models.py         # Model tests
│   ├── test_menu_processing.py # Menu processing pipeline tests
│   └── example.json           # Example API responses
├── MENU_PROCESSING.md         # Detailed menu processing documentation
└── README.md                  # This file
```

## 🧪 Testing

### Run API Tests
```bash
# Test Apify integration
python tests/test_apify.py

# Test menu processing pipeline with 10 random images
python tests/test_menu_processing.py

# Run all tests
python -m pytest tests/
```

### Menu Processing Tests
The `test_menu_processing.py` provides comprehensive testing of the AI-powered menu pipeline:

```bash
# Run menu processing tests
cd macromaps-backend
python tests/test_menu_processing.py
```

**Test Features:**
- **Smart Image Selection**: Prioritizes `/p/` URLs over `/gps-cs-s/` URLs for testing
- **Cost Tracking**: Monitors token usage and API costs across all models
- **Detailed Reporting**: Shows classification results, menu extraction, and nutritional data
- **Realistic Testing**: Uses actual restaurant data from `example.json`

**Sample Test Output:**
```
📊 Image distribution: 15 /p/ URLs, 25 /gps-cs-s/ URLs, 5 other URLs
   Selected 5 /p/ URLs (high menu probability)
   Selected 3 /gps-cs-s/ URLs (medium menu probability)
   Selected 2 additional URLs

🍽️ TESTING IMAGE CLASSIFICATION
   ✅ Result: MENU | Confidence: high | $0.0012 (150 tokens)
   📋 ALL MENU ITEMS (8 items):
      1. Margherita Pizza
         💰 Price: 14.99
         🏷️ Category: pizza
         🔥 Calories: 280
         🥗 Macros: Protein: 12g, Carbs: 36g, Fat: 10g
```

### Manual Testing
```bash
# Test health endpoint
curl http://localhost:5000/health

# Test restaurant search (mock mode)
curl -X POST http://localhost:5000/scan-nearby \
  -H "Content-Type: application/json" \
  -d '{"latitude": 40.7128, "longitude": -74.0060, "mock": true}'
```

## 🔧 Configuration

### Environment Variables
| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `APIFY_API_TOKEN` | Apify API token for restaurant data | Yes | `your-apify-token-here` |
| `SUPABASE_URL` | Supabase project URL | Yes | `your-supabase-url-here` |
| `SUPABASE_KEY` | Supabase anon key | Yes | `your-supabase-key-here` |
| `OPENAI_API_KEY` | OpenAI API key for menu analysis | No | None |
| `FLASK_ENV` | Flask environment | No | `development` |
| `FLASK_DEBUG` | Enable debug mode | No | `True` |

### Apify Configuration
The server uses the `compass/crawler-google-places` actor with the following settings:
- Search radius: 1km (configurable)
- Maximum places per search: 2 (configurable)
- Includes opening hours, images, and menu data
- Excludes personal data for privacy

## 📊 Database Schema

### Restaurants Table
- `place_id` (Primary Key): Google Places ID
- `name`: Restaurant name
- `address`: Full address
- `latitude`, `longitude`: GPS coordinates
- `rating`: Average rating
- `status`: Processing status (`pending`, `processing`, `finished`)
- Additional metadata fields

### Menu Items Table
- `id` (Primary Key): Unique identifier
- `place_id` (Foreign Key): Links to restaurant
- `name`: Menu item name
- `calories`: Caloric content
- `protein`, `carbs`, `fat`: Macronutrient breakdown
- `price`: Item price
- `description`: Item description
- `dietary_tags`: Array of dietary labels
- `allergens`: Array of allergen information

## 🛡️ Error Handling

The API implements comprehensive error handling:
- **400 Bad Request**: Missing required parameters
- **500 Internal Server Error**: API failures or server errors
- **Graceful Degradation**: Falls back to mock data when APIs are unavailable

## 🚀 Development

### Adding New Features
1. Create utility functions in the `utils/` directory
2. Add corresponding tests in the `tests/` directory
3. Update the main Flask routes in `main.py`
4. Update this README with new functionality

### Code Style
- Follow PEP 8 guidelines
- Use meaningful variable names
- Add docstrings to all functions
- Include type hints where appropriate

## 📝 Troubleshooting

### Common Issues

#### "Missing API Token" Warning
```bash
WARNING: Please set your APIFY_API_TOKEN environment variable
```
**Solution**: Add your Apify API token to the `.env` file

#### "Database query failed"
**Solution**: Check your Supabase credentials and internet connection

#### "Apify API error"
**Solution**: Verify your API token and check Apify service status

### Debug Mode
Enable debug mode for detailed error messages:
```bash
export FLASK_DEBUG=True
python main.py
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Update documentation
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🔮 Future Enhancements

- [ ] Advanced menu analysis with LLM integration
- [ ] Real-time nutritional calculations
- [ ] User preference learning
- [ ] Restaurant recommendation engine
- [ ] Multi-language support
- [ ] Caching layer for improved performance
- [ ] GraphQL API endpoints
- [ ] WebSocket support for real-time updates

## 📞 Support

For support, please:
1. Check the troubleshooting section
2. Review the test files for usage examples
3. Open an issue on the repository

---

Made with ❤️ for the MacroMaps project

## 🤖 Menu Processing Pipeline

### Overview
The menu processing pipeline is a sophisticated AI-powered system that extracts nutritional information from restaurant images. It uses a multi-stage approach with intelligent prioritization and parallel processing.

### Pipeline Stages

#### 1. **Image Prioritization & Sorting**
```python
# URLs are sorted by menu likelihood:
# Priority 0: URLs with "/p/" (highest menu probability)
# Priority 1: URLs with "/gps-cs-s/" (medium probability)  
# Priority 2: Other URLs (lowest probability)
```

#### 2. **Image Classification** (Cost-Optimized)
- **Model**: `gpt-4.1-nano` (85% cost reduction vs. gpt-4.1)
- **Purpose**: Identify which images contain actual menus
- **Output**: Boolean classification with confidence scores
- **Parallel Processing**: Up to 5 concurrent classifications

#### 3. **Menu Analysis** (High-Detail)
- **Model**: `gpt-4.1` with 5000 token limit
- **Purpose**: Extract detailed menu items with nutritional data
- **Output**: Complete menu items with prices, descriptions, macros
- **Parallel Processing**: Up to 3 concurrent analyses

#### 4. **Menu Consolidation**
- **AI-Powered Deduplication**: Removes duplicate items across images
- **Price Reconciliation**: Resolves conflicting pricing information
- **Category Standardization**: Normalizes menu categories

### Usage Example
```python
from tasks.menu_processing import MenuProcessor

# Initialize processor with custom workers
processor = MenuProcessor(
    max_workers=10,
    classification_workers=5,
    analysis_workers=3
)

# Process a single restaurant
result = processor.process_restaurant_images("place_id_123")

# Process multiple restaurants
results = processor.process_all_restaurants(["place_1", "place_2"])

# Or process all pending restaurants
results = processor.process_all_restaurants()
```

### Configuration Options
```python
# Menu Processing Settings
MENU_PROCESSING_CONFIG = {
    "classification_model": "gpt-4.1-nano",  # Cost-optimized
    "analysis_model": "gpt-4.1",             # High-accuracy
    "max_tokens_analysis": 5000,             # Increased for complex menus
    "classification_workers": 5,             # Parallel image classification
    "analysis_workers": 3,                   # Parallel menu analysis
    "max_workers": 10                        # Overall parallelization
}
```

### Performance Metrics
- **Cost Efficiency**: 85% reduction in classification costs
- **Processing Speed**: Up to 10x faster with parallel processing
- **Menu Detection**: Prioritizes high-probability menu images first
- **Accuracy**: Maintains high accuracy with optimized models
