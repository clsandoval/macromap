import React, { useState } from 'react';
import { Zap, Search, MapPin, AlertCircle } from 'lucide-react';
import { Button } from './components/ui/button';
import RestaurantMap from './components/RestaurantMap';
import './App.css';

function App() {
  const [isScanning, setIsScanning] = useState(false);
  const [error, setError] = useState(null);
  const [restaurants, setRestaurants] = useState(null);
  const [userLocation, setUserLocation] = useState(null);
  const [showMap, setShowMap] = useState(false);
  const [mockMode, setMockMode] = useState(true); // Default to mock mode for development

  const handleScanNearby = async () => {
    setIsScanning(true);
    setError(null);
    setRestaurants(null);
    setShowMap(false);

    try {
      // Check if geolocation is supported
      if (!navigator.geolocation) {
        throw new Error('Geolocation is not supported by this browser');
      }

      // Get user's location
      const position = await new Promise((resolve, reject) => {
        navigator.geolocation.getCurrentPosition(
          resolve,
          reject,
          {
            enableHighAccuracy: true,
            timeout: 10000,
            maximumAge: 300000 // 5 minutes
          }
        );
      });

      const { latitude, longitude } = position.coords;
      const userLoc = { lat: latitude, lng: longitude };
      setUserLocation(userLoc);

      console.log('User location:', { latitude, longitude });
      console.log('Mock mode:', mockMode ? 'ENABLED' : 'DISABLED');

      // Make POST request to backend endpoint
      const response = await fetch('http://127.0.0.1:5000', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          latitude,
          longitude,
          timestamp: new Date().toISOString(),
          accuracy: position.coords.accuracy,
          mock: mockMode  // Add mock flag
        })
      });

      if (!response.ok) {
        // Try to get error details from backend response
        const errorData = await response.json().catch(() => null);
        const errorMessage = errorData?.error || `HTTP error! status: ${response.status}`;
        throw new Error(errorMessage);
      }

      const data = await response.json();
      console.log('API Response:', data);

      if (data.success && data.restaurants) {
        // Store restaurants and show map
        setRestaurants(data.restaurants);
        setShowMap(true);

        // Also show a brief success message
        const restaurantCount = data.restaurants.length;
        const modeText = data.mock ? ' (using mock data)' : '';
        console.log(`Found ${restaurantCount} restaurants nearby${modeText}! Opening map view...`);
      } else if (data.error) {
        // Handle backend error responses
        setError(data.error);
      } else {
        setError('No restaurants found in your area. Please try a different location.');
      }

    } catch (err) {
      console.error('Error scanning nearby:', err);

      // Handle different types of errors
      if (err.code === err.PERMISSION_DENIED) {
        setError('Location access denied. Please enable location services to find nearby restaurants.');
      } else if (err.code === err.POSITION_UNAVAILABLE) {
        setError('Location information is unavailable. Please try again.');
      } else if (err.code === err.TIMEOUT) {
        setError('Location request timed out. Please try again.');
      } else if (err.message.includes('HTTP error')) {
        setError('Unable to connect to our servers. Please try again later.');
      } else {
        setError('Unable to get your location. Please check your settings and try again.');
      }
    } finally {
      setIsScanning(false);
    }
  };

  const handleCloseMap = () => {
    setShowMap(false);
    setRestaurants(null);
  };

  return (
    <div className="App">
      <div className="landing-container">
        <div className="content">
          <div className="logo-container">
            <Zap className="logo-icon" size={64} />
          </div>

          <h1 className="main-title">MacroMap</h1>

          <div className="description">
            <p className="description-text">
              Discover local restaurant meals tailored to your macros.
            </p>
            <p className="tap-text">
              Tap to scan your area.
            </p>
          </div>

          {error && (
            <div className="error-message">
              <AlertCircle size={20} />
              <span>{error}</span>
            </div>
          )}

          {/* Mock Mode Toggle */}
          <div className="mock-toggle">
            <label className="toggle-label">
              <input
                type="checkbox"
                checked={mockMode}
                onChange={(e) => setMockMode(e.target.checked)}
                className="toggle-checkbox"
              />
              <span className="toggle-text">
                {mockMode ? '🧪 Mock Mode (Free)' : '🌐 Live Mode (Uses Credits)'}
              </span>
            </label>
          </div>

          <Button
            className="scan-button"
            size="lg"
            onClick={handleScanNearby}
            disabled={isScanning}
          >
            {isScanning ? (
              <>
                <MapPin className="button-icon spinning" size={20} />
                Finding Location...
              </>
            ) : (
              <>
                <Search className="button-icon" size={20} />
                Scan Nearby
              </>
            )}
          </Button>
        </div>

        <footer className="footer">
          <p className="footer-text">© 2025 MacroMap. Find your fit.</p>
        </footer>
      </div>

      {/* Restaurant Map Overlay */}
      {showMap && restaurants && userLocation && (
        <RestaurantMap
          restaurants={restaurants}
          userLocation={userLocation}
          onClose={handleCloseMap}
        />
      )}
    </div>
  );
}

export default App;
