// DroughtGuard Frontend JavaScript

let map;
let geojsonLayer;
let currentPredictions = {};

// Initialize map
function initMap() {
    map = L.map('map').setView([0.0236, 37.9062], 6);
    
    // Add OpenStreetMap tiles
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors'
    }).addTo(map);
    
    loadGeoJson();
}

// Load region names into dropdown
function loadRegions() {
    fetch('/api/regions')
        .then(response => response.json())
        .then(data => {
            console.log("✅ /api/regions response:", data);
            const select = document.getElementById('region-select');
            select.innerHTML = '<option value="">-- Select a region --</option>'; // clear existing

            if (data.regions && data.regions.length > 0) {
                data.regions.forEach(region => {
                    const option = document.createElement('option');
                    option.value = region;
                    option.textContent = region;
                    select.appendChild(option);
                });
            } else {
                console.warn('⚠️ No regions found in /api/regions');
            }
        })
        .catch(error => console.error('❌ Error loading regions:', error));
}


// Load GeoJSON data
function loadGeoJson() {
    fetch('/api/map-data')
        .then(response => response.json())
        .then(data => {
            if (data.features && data.features.length > 0) {
                addGeoJsonLayer(data);
            }
        })
        .catch(error => console.error('Error loading GeoJSON:', error));
}

// Add GeoJSON layer to map
function addGeoJsonLayer(geojsonData) {
    geojsonLayer = L.geoJSON(geojsonData, {
        style: getDefaultStyle,
        onEachFeature: onEachFeature
    }).addTo(map);

    // Zoom map to show all Kenya polygons
    map.fitBounds(geojsonLayer.getBounds());
}


// Default style for regions
const DEFAULT_FILL = '#28a745'; // green

function getDefaultStyle(feature) {
  const c = feature?.properties?.fillColor || DEFAULT_FILL;
  return {
    fillColor: c,
    weight: 2,
    opacity: 1,
    color: 'white',
    dashArray: '3',
    fillOpacity: 0.7
  };
}


// On each feature (for interactions)
function onEachFeature(feature, layer) {
    layer.bindPopup(feature.properties.name || 'Unknown Region');
    
    layer.on({
        mouseover: highlightFeature,
        mouseout: resetHighlight,
        click: selectRegion
    });
}

// Highlight feature on hover
function highlightFeature(e) {
  const layer = e.target;
  layer.setStyle({
    weight: 4,
    color: '#666',
    dashArray: '',
    // keep the current fillColor; only bump fillOpacity slightly
    fillOpacity: 0.8
  });
  if (!L.Browser.ie && !L.Browser.opera && !L.Browser.edge) layer.bringToFront();
}


// Reset highlight
function resetHighlight(e) {
   // geojsonLayer.resetStyle(e.target);
    e.target.setStyle(getDefaultStyle(e.target.feature));
}

// Select region
function selectRegion(e) {
    const region = e.target.feature.properties.name;
    document.getElementById('region-select').value = region;
}

// Handle predict button click
document.getElementById('predict-btn').addEventListener('click', function() {
    const region = document.getElementById('region-select').value;
    
    if (!region) {
        alert('Please select a region');
        return;
    }
    
    predictRisk(region);
});

// Predict risk for region
function predictRisk(region) {
    fetch('/api/predict', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ region: region })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert(data.error);
            return;
        }
        
        displayResults(data);
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error predicting risk');
    });
}

// Display results
function displayResults(data) {
    const resultsPanel = document.getElementById('results');
    currentPredictions = data.predictions;
    
    // Create forecast cards
    let forecastHtml = `
        <h3>Forecast for ${data.display_name}</h3>
        <div class="forecast-grid">
    `;
    
    // Add card for each horizon
    const horizonLabels = {
        1: 'Next Month',
        2: 'Two Months Ahead',
        3: 'Three Months Ahead'
    };
    
    for (const [horizon, pred] of Object.entries(data.predictions)) {
        const h = parseInt(horizon);
        forecastHtml += `
            <div class="forecast-card">
                <div class="card">
                    <div class="card-header">
                        <h5>${horizonLabels[h]}</h5>
                    </div>
                    <div class="card-body">
                        <div class="risk-indicator" style="background-color: ${pred.color}"></div>
                        <h3 class="text-center">${pred.category}</h3>
                        <div class="progress">
                            <div class="progress-bar" 
                                role="progressbar" 
                                style="width: ${pred.probability * 100}%; background-color: ${pred.color}"
                                aria-valuenow="${pred.probability * 100}" 
                                aria-valuemin="0" 
                                aria-valuemax="100">
                            </div>
                        </div>
                        <p class="text-center mt-2">${(pred.probability * 100).toFixed(1)}% Risk</p>
                    </div>
                </div>
            </div>
        `;
    }
    
    forecastHtml += '</div>';
    
    // Update panel content
    resultsPanel.innerHTML = forecastHtml;
    
    // Use the nearest-term prediction for map coloring
    if (data.predictions[1]) {
        updateMapRegion(data.region, data.predictions[1].color);
    }
    
    // Show AI Advisor section and fetch default explanation
    document.getElementById('ai-advisor-section').style.display = 'block';
    loadAIExplanation(data.region, 1, 'explain');
}

// Update map region color
function updateMapRegion(regionName, color) {
  console.log("🗺️ Trying to color region:", regionName);

  let found = false;

  geojsonLayer.eachLayer(function(layer) {
    // Normalize names (remove spaces, lowercase)
    const featureName = layer.feature.properties.name.trim().toLowerCase();
    const targetName = regionName.trim().toLowerCase();

    // Match exactly or allow "County" suffixes, e.g. "Uasin Gishu County"
    if (
      featureName === targetName ||
      featureName.includes(targetName) ||
      targetName.includes(featureName)
    ) {
      found = true;

      // Persist chosen color in properties
      layer.feature.properties.fillColor = color;
      layer.setStyle(getDefaultStyle(layer.feature));

      // Optionally zoom to that region
      map.fitBounds(layer.getBounds(), { maxZoom: 8 });
    }
  });

  if (!found) {
    console.warn("⚠️ Region not found in GeoJSON for:", regionName);
  }
}


// Load AI explanation
function loadAIExplanation(region, horizon, mode) {
    const endpoint = mode === 'brief' ? 'brief' : 'explain';
    const aiText = document.getElementById('ai-text');
    const aiCached = document.getElementById('ai-cached-badge');
    
    aiText.innerHTML = '<em>Loading AI explanation...</em>';
    aiCached.style.display = 'none';
    
    fetch(`/api/${endpoint}/${region}?h=${horizon}`)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                aiText.innerHTML = `<span style="color: red;">Error: ${data.error}</span>`;
                return;
            }
            
            // Show cached badge if applicable
            if (data.cached) {
                aiCached.style.display = 'block';
            }
            
            // Display explanation
            let html = `<p>${data.data.explanation}</p>`;
            
            // Add actions if in brief mode
            if (mode === 'brief' && data.data.actions && data.data.actions.length > 0) {
                html += '<p style="margin-top: 1rem;"><strong>Recommended Actions:</strong></p><ul>';
                data.data.actions.forEach(action => {
                    html += `<li>${action}</li>`;
                });
                html += '</ul>';
            }
            
            // Add disclaimers
            if (data.data.disclaimers) {
                html += `<p style="margin-top: 1rem; font-size: 0.85em; color: #6c757d;"><em>${data.data.disclaimers}</em></p>`;
            }
            
            aiText.innerHTML = html;
            
            // Update button active states
            if (mode === 'explain') {
                document.getElementById('btn-explain').classList.add('ai-btn-active');
                document.getElementById('btn-brief').classList.remove('ai-btn-active');
            } else {
                document.getElementById('btn-explain').classList.remove('ai-btn-active');
                document.getElementById('btn-brief').classList.add('ai-btn-active');
            }
        })
        .catch(error => {
            console.error('Error loading AI explanation:', error);
            aiText.innerHTML = '<span style="color: red;">Error loading AI explanation</span>';
        });
}

// Button handlers for AI Advisor
document.getElementById('btn-explain').addEventListener('click', function() {
    const region = document.getElementById('region-select').value;
    if (region) {
        loadAIExplanation(region, 1, 'explain');
    }
});

document.getElementById('btn-brief').addEventListener('click', function() {
    const region = document.getElementById('region-select').value;
    if (region) {
        loadAIExplanation(region, 1, 'brief');
    }
});

// Initialize when page loads
document.addEventListener('DOMContentLoaded', function() {
    initMap();
    loadRegions();
});
