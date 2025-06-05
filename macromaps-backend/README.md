# MacroMap Backend

Flask backend that integrates with Apify's Google Maps Scraper to find restaurants based on user location.

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Get Apify API Token (for live mode only):**
   - Sign up for a free account at [https://apify.com/](https://apify.com/)
   - Go to your account settings and get your API token
   - Set the environment variable:
     ```bash
     export APIFY_API_TOKEN=your_actual_token_here
     ```
   - Or on Windows:
     ```cmd
     set APIFY_API_TOKEN=your_actual_token_here
     ```

3. **Run the server:**
   ```bash
   python main.py
   ```

The server will start on `http://localhost:5000`

## API Endpoints

### POST /scan-nearby
Finds restaurants near the provided coordinates.

**Request Body:**
```json
{
  "latitude": 40.7128,
  "longitude": -74.0060,
  "timestamp": "2025-01-10T12:00:00.000Z",
  "accuracy": 10,
  "mock": false
}
```

**Parameters:**
- `latitude` (required): User's latitude coordinate
- `longitude` (required): User's longitude coordinate  
- `timestamp` (optional): Request timestamp
- `accuracy` (optional): GPS accuracy in meters
- `mock` (optional): If `true`, returns mock data instead of calling Apify API

**Mock Mode Response:**
```json
{
  "success": true,
  "message": "Found 10 restaurants (MOCK DATA)",
  "restaurants": [...],
  "searchLocation": {
    "latitude": 40.7128,
    "longitude": -74.0060
  },
  "mock": true
}
```

**Live Mode Response:**
```json
{
  "success": true,
  "message": "Found 10 restaurants",
  "restaurants": [
    {
      "name": "Restaurant Name",
      "address": "123 Main St, City, State",
      "rating": 4.5,
      "reviewsCount": 150,
      "category": "Restaurant",
      "phone": "+1-555-123-4567",
      "website": "https://restaurant.com",
      "priceLevel": "$$",
      "openingHours": [...],
      "location": {
        "lat": 40.7128,
        "lng": -74.0060
      },
      "placeId": "ChIJ...",
      "url": "https://maps.google.com/..."
    }
  ],
  "searchLocation": {
    "latitude": 40.7128,
    "longitude": -74.0060
  }
}
```

### GET /health
Health check endpoint to verify the server is running.

## Mock Mode

Mock mode generates realistic fake restaurant data for development and testing without consuming Apify credits:

- **🧪 Mock restaurants**: 10 diverse restaurants with realistic names and data
- **📍 Location scatter**: Restaurants randomly distributed within 2km radius
- **⚡ Fast response**: Instant results (no API waiting time)
- **💰 Free**: No API credits consumed
- **🎯 Realistic data**: Includes ratings, reviews, phone numbers, websites, etc.

Mock restaurants include various cuisines:
- Italian, Chinese, Mexican, Thai, Indian
- Fast food, pizza, sushi, steakhouse
- Coffee shops, health food, vegan options

## Notes

- **Mock Mode**: Perfect for development - generates 10 fake restaurants instantly
- **Live Mode**: Uses real Apify Google Maps Scraper - requires API token and consumes credits
- Requests in live mode may take 30-120 seconds to complete
- Free Apify accounts have usage limits - check your account dashboard for details 