// =========================================================
// DroughtGuard Frontend Script (robust + queued updates)
// =========================================================

let map;
let geojsonLayer;
<<<<<<< Updated upstream
=======
let mapReady = false;                 // set true after GeoJSON added
let currentPredictions = {};
const pendingColorUpdates = [];       // queued until mapReady === true
>>>>>>> Stashed changes

// =========================================================
// UTIL: Logging helpers
// =========================================================
const log = {
  info:  (...args) => console.log("ℹ️",  ...args),
  ok:    (...args) => console.log("✅",  ...args),
  warn:  (...args) => console.warn("⚠️", ...args),
  err:   (...args) => console.error("❌", ...args),
};

// =========================================================
// MAP COLORING (defined first so callers can use it later)
// =========================================================
function updateRegionColor(regionName, color) {
  if (!mapReady || !geojsonLayer) {
    // Not ready yet, queue the request
    pendingColorUpdates.push({ regionName, color });
    log.warn("GeoJSON not ready — queued color update:", regionName, color);
    return;
  }

  const target = regionName.trim().toLowerCase();
  let found = false;

  geojsonLayer.eachLayer(layer => {
    const p = layer.feature?.properties || {};
    const geoName =
      (p.shapeName || p.COUNTY_NAM || p.ADM1_EN || p.name || "").toLowerCase();

    if (!geoName) return;

    // match 'Kajiado' ↔ 'Kajiado County'
    if (geoName.includes(target) || target.includes(geoName)) {
      found = true;
      layer.setStyle({
        fillColor: color,
        fillOpacity: 0.7,
        color: "#333",
        weight: 1,
      });
      map.fitBounds(layer.getBounds(), { maxZoom: 8 });
      layer.bringToFront();
      log.ok(`Region colored → ${p.name || p.ADM1_EN || geoName}: ${color}`);
    }
  });

  if (!found) log.warn("Region not found in GeoJSON for:", regionName);
}

function flushPendingColorUpdates() {
  if (!mapReady || !geojsonLayer) return;
  if (pendingColorUpdates.length === 0) return;

  log.info(`Applying ${pendingColorUpdates.length} queued color update(s)…`);
  while (pendingColorUpdates.length) {
    const { regionName, color } = pendingColorUpdates.shift();
    updateRegionColor(regionName, color);
  }
}

// =========================================================
// DASHBOARD RENDERING
// =========================================================
function displayResults(data) {
  const resultsPanel = document.getElementById("results");
  if (!resultsPanel) {
    log.err("#results panel not found in DOM");
    return;
  }

  currentPredictions = data.predictions || {};
  const regionName = data.display_name || data.region || "Unknown Region";

  let html = `
    <h3>Forecast for ${regionName}</h3>
    <div class="forecast-grid">
  `;

  const labels = {
    1: "Next Month",
    2: "Two Months Ahead",
    3: "Three Months Ahead",
  };

  for (const [key, pred] of Object.entries(currentPredictions)) {
    let h = key.includes("3") ? 3 : key.includes("2") ? 2 : 1;

    const label = labels[h] || key;
    const color = pred.color || "#999";
    const prob  = ((pred.probability || 0) * 100);
    const cat   = pred.category || "N/A";

    html += `
      <div class="forecast-card">
        <div class="card">
          <div class="card-header text-center">
            <h5 class="mb-0">${label}</h5>
          </div>
          <div class="card-body">
            <div class="risk-indicator" style="background-color:${color};"></div>
            <h3 class="text-center mb-3">${cat}</h3>
            <div class="progress">
              <div class="progress-bar"
                   role="progressbar"
                   style="width:${prob}%; background-color:${color};"
                   aria-valuenow="${prob.toFixed(1)}"
                   aria-valuemin="0"
                   aria-valuemax="100">
              </div>
            </div>
            <p class="text-center mt-2">${prob.toFixed(1)}% Risk</p>
          </div>
        </div>
      </div>
    `;
  }

  html += "</div>";
  resultsPanel.innerHTML = html;

  // Color map using nearest (1-month) prediction
  const nearest = currentPredictions["1_month"];
  if (nearest && nearest.color) {
    updateRegionColor(regionName, nearest.color);
  } else {
    log.warn("No 1_month prediction found for", regionName);
  }
}

// =========================================================
// PREDICTION FLOW
// =========================================================
function predictRisk(region) {
  fetch("/api/predict", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ region }),
  })
    .then(res => res.json())
    .then(data => {
      if (!data || !data.predictions) {
        log.err("Invalid /api/predict response:", data);
        alert("Prediction failed — no data returned.");
        return;
      }
      log.info("Predictions:", data.predictions);
      displayResults(data);

      // Color map using 1-month horizon (already done in displayResults),
      // but keep this for explicitness if you prefer:
      const p = data.predictions["1_month"];
      if (p && p.color) updateRegionColor(region, p.color);
    })
    .catch(err => {
      log.err("Prediction fetch error:", err);
      alert("Error contacting prediction service.");
    });
}

// =========================================================
// MAP SETUP
// =========================================================
function initMap() {
  map = L.map("map").setView([0.0236, 37.9062], 6);

  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: "© OpenStreetMap contributors",
  }).addTo(map);

  loadGeoJson();
}

function loadGeoJson() {
  fetch("/api/map-data")
    .then(res => res.json())
    .then(data => {
      if (!data?.features?.length) {
        log.err("Invalid GeoJSON from /api/map-data");
        return;
      }
      addGeoJsonLayer(data);
    })
    .catch(err => log.err("GeoJSON load error:", err));
}

function addGeoJsonLayer(geojsonData) {
  geojsonLayer = L.geoJSON(geojsonData, {
    style: getDefaultStyle,
    onEachFeature: onEachFeature,
  }).addTo(map);

  map.fitBounds(geojsonLayer.getBounds());
  mapReady = true;
  log.ok("GeoJSON layer loaded.");

  // Apply any queued region color updates
  flushPendingColorUpdates();
}

const DEFAULT_FILL = "#28a745";

function getDefaultStyle(feature) {
  const c = feature?.properties?.fillColor || DEFAULT_FILL;
  return {
    fillColor: c,
    weight: 1,
    opacity: 1,
    color: "#fff",
    dashArray: "3",
    fillOpacity: 0.7,
  };
}

function onEachFeature(feature, layer) {
  layer.bindPopup(feature.properties.name || "Unknown Region");

  layer.on({
    mouseover: highlightFeature,
    mouseout: resetHighlight,
    click: selectRegion,
  });
}

function highlightFeature(e) {
  const layer = e.target;
  layer.setStyle({
    weight: 2,
    color: "#000",
    dashArray: "",
    fillOpacity: 0.9,
  });
  layer.bringToFront();
}

function resetHighlight(e) {
<<<<<<< Updated upstream
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
        updateMapRegion(region, data.risk_category.color);
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error predicting risk');
    });
}

// Display results
function displayResults(data) {
    const resultsPanel = document.getElementById('results');
    
    resultsPanel.innerHTML = `
        <h3>Prediction Results</h3>
        <p><strong>Region:</strong> ${data.region}</p>
        <p><strong>Risk Level:</strong> 
            <span class="risk-badge" style="background-color: ${data.risk_category.color}">
                ${data.risk_category.label}
            </span>
        </p>
        <p><strong>Risk Probability:</strong> ${(data.probability * 100).toFixed(1)}%</p>
        <p><strong>NDVI Anomaly:</strong> ${data.features.ndvi_anomaly.toFixed(2)}</p>
        <p><strong>Rainfall Anomaly:</strong> ${data.features.rainfall_anomaly.toFixed(2)}</p>
        <p><strong>Food Price Inflation:</strong> ${data.features.food_price_inflation.toFixed(2)}</p>
    `;
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
=======
  const layer = e.target;
  layer.setStyle({
    weight: 1,
    color: "#333",
    fillOpacity: 0.7,
>>>>>>> Stashed changes
  });
}

function selectRegion(e) {
  const region = e.target.feature.properties.name;
  const select = document.getElementById("region-select");
  if (select) select.value = region;
}

// =========================================================
// REGIONS DROPDOWN
// =========================================================
function loadRegions() {
  fetch("/api/regions")
    .then(res => res.json())
    .then(data => {
      const select = document.getElementById("region-select");
      if (!select) return;

      select.innerHTML = '<option value="">-- Select a region --</option>';

      if (data?.regions?.length) {
        // ✅ Remove duplicates and sort alphabetically
        const uniqueRegions = [...new Set(data.regions)].sort((a, b) =>
          a.localeCompare(b)
        );

        uniqueRegions.forEach(region => {
          const opt = document.createElement("option");
          opt.value = region;
          opt.textContent = region;
          select.appendChild(opt);
        });
        new TomSelect("#region-select", {
            create: false,
            sortField: {
                field: "text",
                direction: "asc"
            },
            maxOptions: 10,
            placeholder: "Search for a region...",
            });
      } else {
        log.warn("No regions returned by /api/regions");
      }
    })
    .catch(err => log.err("Regions load error:", err));
}
// =========================================================
// BOOTSTRAP
// =========================================================
document.addEventListener("DOMContentLoaded", () => {
  // Ensure Leaflet loaded
  if (typeof L === "undefined") {
    log.err("Leaflet (L) is undefined — check leaflet.js include order.");
    return;
  }

  initMap();
  loadRegions();

  const btn = document.getElementById("predict-btn");
  if (btn) {
    btn.addEventListener("click", () => {
      const region = document.getElementById("region-select")?.value || "";
      if (!region) {
        alert("Please select a region");
        return;
      }
      predictRisk(region);
    });
  } else {
    log.warn("#predict-btn not found in DOM");
  }
});
