# Menu Processing Pipeline

This document describes the threaded menu image classification and analysis system for MacroMaps.

## Overview

The menu processing pipeline is designed to efficiently process restaurant images to extract menu information using parallel threading. The system follows this workflow:

1. **Restaurant Loop**: Iterate through restaurant IDs and pull images from Supabase
2. **Image Classification**: Classify each image in parallel to determine if it's a menu
3. **Menu Analysis**: For images classified as menus, extract menu items in parallel
4. **Aggregation**: Consolidate all menu items for each restaurant
5. **Database Storage**: Save final menu items to Supabase

## Architecture

### Threading Model

The system uses a hierarchical threading approach:

- **Main Thread Pool**: Processes multiple restaurants in parallel (default: 10 workers)
- **Classification Thread Pool**: Classifies images for each restaurant (default: 5 workers)
- **Analysis Thread Pool**: Analyzes menu images for each restaurant (default: 3 workers)

### Key Components

#### `MenuProcessor` Class
Main orchestrator that manages the entire pipeline.

```python
from tasks.menu_processing import MenuProcessor

processor = MenuProcessor(
    max_workers=10,           # Restaurant-level parallelism
    classification_workers=5, # Image classification parallelism
    analysis_workers=3        # Menu analysis parallelism
)
```

#### Data Classes

- `ImageClassificationResult`: Result of menu image classification
- `MenuAnalysisResult`: Result of menu item extraction
- `RestaurantProcessingResult`: Complete processing result for a restaurant

## Usage

### 1. Process All Pending Restaurants

```python
from tasks.menu_processing import run_menu_processing_pipeline

# Process all restaurants with status='pending'
results = run_menu_processing_pipeline()
```

### 2. Process Specific Restaurants

```python
# Process specific restaurant IDs
restaurant_ids = ["place_id_1", "place_id_2", "place_id_3"]
results = run_menu_processing_pipeline(
    restaurant_ids=restaurant_ids,
    max_workers=5
)
```

### 3. Via Flask API

```bash
# Start processing in background
curl -X POST http://localhost:5000/process-menus \
  -H "Content-Type: application/json" \
  -d '{"background": true, "max_workers": 10}'

# Process specific restaurants synchronously
curl -X POST http://localhost:5000/process-menus \
  -H "Content-Type: application/json" \
  -d '{
    "restaurant_ids": ["place_id_1", "place_id_2"],
    "background": false,
    "max_workers": 5
  }'
```

### 4. Advanced Usage

```python
processor = MenuProcessor(max_workers=15, classification_workers=10, analysis_workers=5)

# Get restaurants to process
pending_restaurants = processor.get_restaurants_to_process("pending")

# Process single restaurant
result = processor.process_restaurant_images("place_id_123")

# Process all with custom settings
results = processor.process_all_restaurants(restaurant_ids=pending_restaurants)
```

## Processing Flow

### Per Restaurant Processing

For each restaurant, the system:

1. **Retrieve Images**: Get all image URLs from Supabase
2. **Classify Images**: Use LLM to classify each image as menu/non-menu in parallel
3. **Filter Menu Images**: Keep only images classified as menus
4. **Analyze Menus**: Extract menu items from menu images in parallel
5. **Aggregate Items**: Use LLM to consolidate and deduplicate menu items
6. **Save to Database**: Insert final menu items into Supabase

### Error Handling

- Individual image processing errors don't stop the entire restaurant
- Restaurant processing errors don't stop the entire batch
- Comprehensive error logging and reporting
- Graceful degradation when LLM APIs are unavailable

## Configuration

### Environment Variables

```bash
# Required
OPENAI_API_KEY=your_openai_api_key
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key

# Optional
MENU_PROCESSOR_MAX_WORKERS=10
MENU_PROCESSOR_CLASSIFICATION_WORKERS=5
MENU_PROCESSOR_ANALYSIS_WORKERS=3
```

### Worker Tuning

Choose worker counts based on:
- **API Rate Limits**: OpenAI has rate limits that may require fewer workers
- **System Resources**: More workers = more memory and CPU usage
- **Cost Considerations**: More parallel requests = higher API costs

Recommended starting configurations:
- **Development**: `max_workers=3, classification_workers=2, analysis_workers=1`
- **Production**: `max_workers=10, classification_workers=5, analysis_workers=3`
- **High-throughput**: `max_workers=20, classification_workers=10, analysis_workers=5`

## LLM Functions

### Image Classification

Uses OpenAI's vision models to determine if an image shows a menu:

```python
from utils.llm_utils import classify_menu_image

result = classify_menu_image("https://example.com/image.jpg")
# Returns: {
#   "is_menu": True,
#   "confidence_level": "high",
#   "reasoning": "Clear menu with items and prices visible",
#   "image_type": "menu"
# }
```

### Menu Analysis

Extracts menu items with nutritional estimates:

```python
from utils.llm_utils import analyze_menu_image

result = analyze_menu_image("https://example.com/menu.jpg")
# Returns: {
#   "menu_items": [
#     {
#       "name": "Caesar Salad",
#       "description": "Romaine lettuce with caesar dressing",
#       "price": 12.99,
#       "category": "salads",
#       "calories": 350,
#       "protein": 8.5,
#       "carbs": 12.0,
#       "fat": 28.0
#     }
#   ],
#   "total_items": 1,
#   "has_prices": True,
#   "has_descriptions": True
# }
```

### Menu Aggregation

Consolidates menu items from multiple sources:

```python
from utils.llm_utils import aggregate_menu_items

consolidated = aggregate_menu_items(all_menu_items, "place_id_123")
# Returns deduplicated and cleaned menu items
```

## Database Schema

### Menu Items Table

```sql
CREATE TABLE menu_items (
    id BIGSERIAL PRIMARY KEY,
    place_id TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    price NUMERIC,
    category TEXT,
    calories INTEGER,
    protein NUMERIC,
    carbs NUMERIC,
    fat NUMERIC,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Restaurant Status Updates

The system updates restaurant status to 'finished' after successful processing.

## Monitoring and Logging

### Log Levels

- **INFO**: Processing progress, completion summaries
- **ERROR**: Individual failures, API errors
- **DEBUG**: Detailed processing steps (when enabled)

### Metrics Tracked

- Processing time per restaurant
- Images processed vs menu images found
- Menu items extracted per restaurant
- Success/failure rates
- API token usage (when available)

## Performance Considerations

### Optimization Tips

1. **Batch Size**: Process restaurants in batches to manage memory
2. **Rate Limiting**: Respect OpenAI API rate limits
3. **Caching**: Consider caching classification results for duplicate images
4. **Resource Monitoring**: Monitor memory usage with large image batches

### Scaling

For high-volume processing:
- Deploy multiple instances with different restaurant ID ranges
- Use Redis for distributed coordination
- Implement circuit breakers for API failures
- Add metrics collection (Prometheus/Grafana)

## Example Results

```python
{
    "place_id_123": RestaurantProcessingResult(
        place_id="place_id_123",
        total_images=15,
        menu_images_found=4,
        total_menu_items=23,
        processing_time=45.2,
        error=None
    ),
    "place_id_456": RestaurantProcessingResult(
        place_id="place_id_456",
        total_images=8,
        menu_images_found=0,
        total_menu_items=0,
        processing_time=12.1,
        error="No menu images found"
    )
}
```

## Error Scenarios

Common errors and solutions:

1. **No images found**: Restaurant has no images in database
2. **API rate limits**: Reduce worker counts or add delays
3. **Invalid image URLs**: Images may be expired or inaccessible
4. **LLM parsing errors**: Fallback to basic extraction methods
5. **Database connection issues**: Implement retry logic

## Running Examples

See `examples/menu_processing_example.py` for comprehensive usage examples:

```bash
cd macromaps-backend
 