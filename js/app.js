(function () {
  "use strict";

  var CABA_CENTER = [-34.5950, -58.4300];

  var TYPE_LABELS = {
    ru: { rent: "Аренда", sale: "Продажа", both: "Аренда/продажа" },
    en: { rent: "For rent", sale: "For sale", both: "For rent/sale" },
  };
  var TYPE_COLORS = { rent: "#3b7a5a", sale: "#b5693b", both: "#3a6ea5" };

  var STATUS_LABELS = {
    ru: {
      free: "Свободно",
      soon: "Скоро свободно",
      reserved: "Забронировано",
      rented: "Сдано",
      sold: "Продано",
    },
    en: {
      free: "Available",
      soon: "Available soon",
      reserved: "Reserved",
      rented: "Rented",
      sold: "Sold",
    },
  };

  var ROOMS_LABELS = {
    ru: {
      monoambiente: "Моноамбиенте",
      "1_amb": "1 комната",
      "2_amb": "2 комнаты",
      "3_amb": "3 комнаты",
      "4_amb": "4 комнаты",
    },
    en: {
      monoambiente: "Studio",
      "1_amb": "1 room",
      "2_amb": "2 rooms",
      "3_amb": "3 rooms",
      "4_amb": "4 rooms",
    },
  };

  var AMENITY_DEFS = [
    { key: "pool", label: { ru: "Бассейн", en: "Pool" } },
    { key: "gym", label: { ru: "Спортзал", en: "Gym" } },
    { key: "parrilla", label: { ru: "Парилья", en: "Grill (parrilla)" } },
    { key: "laundry", label: { ru: "Прачечная", en: "Laundry" } },
    { key: "washing_machine", label: { ru: "Стиральная машина", en: "Washing machine" } },
    { key: "dishwasher", label: { ru: "Посудомойка", en: "Dishwasher" } },
    { key: "pets", label: { ru: "Можно с животными", en: "Pets allowed" } },
  ];

  var STRINGS = {
    ru: {
      subtitle: "Карта объектов — Буэнос-Айрес",
      type: "Тип",
      district: "Район",
      allDistricts: "Все районы",
      subBarrio: "Подрайон",
      allSubBarrios: "Все подрайоны",
      showSubBarrios: "Показывать границы подрайонов",
      subBarrioLabel: "Подрайон:",
      informalNote: "неофициальная граница, низкая точность",
      price: "Цена, USD",
      amenities: "Удобства",
      reset: "Сбросить фильтры",
      shown: "Показано:",
      of: "из",
      footer: "@EstateArg в Telegram",
      term: "Срок:",
      availableFrom: "Доступно с:",
      approx: "Координаты приблизительные (по району)",
      tgLink: "Пост в Telegram →",
      sourceLink: "Источник →",
      expensas: "expensas",
      perMonth: "/мес",
      priceFrom: "от",
      priceTo: "до",
    },
    en: {
      subtitle: "Buenos Aires listings map",
      type: "Type",
      district: "Neighborhood",
      allDistricts: "All neighborhoods",
      subBarrio: "Sub-neighborhood",
      allSubBarrios: "All sub-neighborhoods",
      showSubBarrios: "Show sub-neighborhood boundaries",
      subBarrioLabel: "Sub-neighborhood:",
      informalNote: "informal boundary, low accuracy",
      price: "Price, USD",
      amenities: "Amenities",
      reset: "Reset filters",
      shown: "Showing:",
      of: "of",
      footer: "@EstateArg on Telegram",
      term: "Term:",
      availableFrom: "Available from:",
      approx: "Approximate coordinates (neighborhood-level)",
      tgLink: "Telegram post →",
      sourceLink: "Source →",
      expensas: "HOA fee",
      perMonth: "/mo",
      priceFrom: "min",
      priceTo: "max",
    },
  };

  // District name (as stored in the sheet) -> official barrio name in the
  // GeoJSON boundaries dataset. Compound / informal names map to the
  // official barrio they administratively belong to.
  var DISTRICT_TO_BARRIO = {
    "villa crespo": "Villa Crespo",
    "recoleta": "Recoleta",
    "barrio norte": "Recoleta",
    "palermo": "Palermo",
    "palermo hollywood": "Palermo",
    "palermo soho": "Palermo",
    "palermo viejo": "Palermo",
    "palermo chico": "Palermo",
    "palermo (botánico)": "Palermo",
    "las cañitas": "Palermo",
    "colegiales": "Colegiales",
    "belgrano": "Belgrano",
    "belgrano r": "Belgrano",
    "belgrano c": "Belgrano",
    "belgrano chico": "Belgrano",
    "bajo belgrano": "Belgrano",
    "saavedra": "Saavedra",
    "boedo": "Boedo",
  };

  function isEmptyValue(v) {
    if (v === null || v === undefined) return true;
    var s = String(v).trim().toLowerCase();
    return s === "" || s === "unknown" || s === "нет данных" || s === "n/a";
  }

  function primaryDistrictKey(district) {
    if (!district) return "";
    var d = district.toLowerCase();
    d = d.replace(/\([^)]*\)/g, "").trim();
    d = d.split("/")[0].trim();
    return d;
  }

  function barrioFor(district) {
    return DISTRICT_TO_BARRIO[primaryDistrictKey(district)] || null;
  }

  function formatUsd(amount, isRent, lang) {
    var n = Math.round(Number(amount)).toLocaleString("en-US");
    if (lang === "en") return "USD " + n + (isRent ? "/mo" : "");
    return "USD " + n + "$" + (isRent ? "/мес" : "");
  }

  function formatArs(amount) {
    var n = Math.round(Number(amount)).toLocaleString("ru-RU").replace(/,/g, " ");
    return "ARS " + n;
  }

  function priceLine(obj, lang) {
    if (isEmptyValue(obj.price)) return null;
    var isRent = obj.type === "rent" || obj.type === "both";
    var line = formatUsd(obj.price, isRent, lang);
    if (!isEmptyValue(obj.expensas_ars) && Number(obj.expensas_ars) > 0) {
      line += " + " + STRINGS[lang].expensas + " " + formatArs(obj.expensas_ars) + STRINGS[lang].perMonth;
    }
    return line;
  }

  function escapeHtml(s) {
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  // ruKey/enKey hold the source (Russian) and translated (English) field
  // names for the same piece of content, e.g. ("other_amenities", "other_amenities_en").
  function fieldFor(obj, ruKey, enKey, lang) {
    if (lang === "en") {
      if (obj[enKey] !== undefined) return obj[enKey]; // "" is a valid translated-to-empty value
    }
    return obj[ruKey];
  }

  function buildPopup(obj, lang) {
    var t = STRINGS[lang];
    var parts = [];
    parts.push('<div class="popup-card">');

    var badgeColor = TYPE_COLORS[obj.type] || "#888";
    parts.push(
      '<span class="popup-badge" style="background:' + badgeColor + '">' +
        escapeHtml(TYPE_LABELS[lang][obj.type] || obj.type) +
      "</span>"
    );
    if (!isEmptyValue(obj.status) && STATUS_LABELS[lang][obj.status]) {
      parts.push(
        '<span class="popup-badge" style="background:#767167;margin-left:4px">' +
          escapeHtml(STATUS_LABELS[lang][obj.status]) +
        "</span>"
      );
    }

    parts.push('<p class="popup-title">' + escapeHtml(obj.address || obj.district) + "</p>");
    parts.push('<p class="popup-row" style="color:#767167">' + escapeHtml(obj.district) + "</p>");
    if (obj.sub_barrio) {
      parts.push('<p class="popup-row" style="color:#8e44ad">' + t.subBarrioLabel + " " + escapeHtml(obj.sub_barrio) + "</p>");
    }

    var price = priceLine(obj, lang);
    if (price) parts.push('<p class="popup-price">' + escapeHtml(price) + "</p>");

    var details = [];
    if (!isEmptyValue(obj.rooms_type)) {
      details.push(ROOMS_LABELS[lang][obj.rooms_type] || obj.rooms_type);
    }
    if (!isEmptyValue(obj.area_m2)) details.push(obj.area_m2 + " м²");
    if (!isEmptyValue(obj.bathrooms)) details.push(obj.bathrooms + (lang === "en" ? " bath" : " ванн."));
    if (details.length) {
      parts.push('<p class="popup-row">' + escapeHtml(details.join(" · ")) + "</p>");
    }

    var contractTerm = fieldFor(obj, "contract_term", "contract_term_en", lang);
    if (!isEmptyValue(contractTerm)) {
      parts.push('<p class="popup-row">' + t.term + " " + escapeHtml(contractTerm) + "</p>");
    }
    if (!isEmptyValue(obj.available_from)) {
      parts.push('<p class="popup-row">' + t.availableFrom + " " + escapeHtml(obj.available_from) + "</p>");
    }

    var amenities = [];
    AMENITY_DEFS.forEach(function (a) {
      var v = obj[a.key];
      if (!isEmptyValue(v) && String(v).toLowerCase() !== "no") {
        amenities.push(a.label[lang]);
      }
    });
    var otherAmenities = fieldFor(obj, "other_amenities", "other_amenities_en", lang);
    if (!isEmptyValue(otherAmenities)) {
      amenities.push(otherAmenities);
    }
    if (amenities.length) {
      parts.push('<div class="popup-amenities">' +
        amenities.map(function (a) { return '<span class="popup-amenity">' + escapeHtml(a) + "</span>"; }).join("") +
      "</div>");
    }

    var description = fieldFor(obj, "description_ru", "description_en", lang);
    if (!isEmptyValue(description)) {
      parts.push('<p class="popup-row">' + escapeHtml(description) + "</p>");
    }

    if (!isEmptyValue(obj.tg_post_url)) {
      parts.push('<a class="popup-link" href="' + escapeHtml(obj.tg_post_url) + '" target="_blank" rel="noopener">' + t.tgLink + "</a>");
    } else if (!isEmptyValue(obj.source_url)) {
      parts.push('<a class="popup-link" href="' + escapeHtml(obj.source_url) + '" target="_blank" rel="noopener">' + t.sourceLink + "</a>");
    }

    if (obj.coords_approx) {
      parts.push('<p class="popup-approx">' + t.approx + "</p>");
    }

    parts.push("</div>");
    return parts.join("");
  }

  // ---- App state ----
  var state = {
    lang: "ru",
    objects: [],
    activeTypes: new Set(),
    district: "",
    subBarrio: "",
    priceMin: null,
    priceMax: null,
    activeAmenities: new Set(),
  };

  var typeChipEls = [];
  var amenityChipEls = [];

  var map, markersLayer, barriosLayer, barriosByName = {}, layersControl;
  var subbarriosLayer, subbarriosByName = {}, subbarriosVisible = false;
  var SUBBARRIO_HIGHLIGHT_STYLE = { color: "#8e44ad", weight: 3, fillColor: "#d8b6e8", fillOpacity: 0.25, opacity: 0.9 };
  var baseLayers = {};

  var BASE_LAYER_LABELS = {
    ru: { street: "Улицы (похоже на Google Maps)", light: "Светлая (минимализм)", osm: "OpenStreetMap (классика)" },
    en: { street: "Streets (like Google Maps)", light: "Light (minimal)", osm: "OpenStreetMap (classic)" },
  };

  var BARRIO_DEFAULT_STYLE = { color: "#b5693b", weight: 1, fillOpacity: 0.02, opacity: 0.35 };
  var BARRIO_HIGHLIGHT_STYLE = { color: "#e0a800", weight: 4, fillColor: "#ffe28a", fillOpacity: 0.35, opacity: 0.95 };

  function initMap() {
    map = L.map("map", { zoomControl: true }).setView(CABA_CENTER, 13);

    var esriAttribution = "Tiles © Esri — Esri, HERE, Garmin, FAO, NOAA, USGS, © OpenStreetMap contributors";

    baseLayers.street = L.tileLayer(
      "https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}",
      { maxZoom: 19, attribution: esriAttribution }
    );
    baseLayers.light = L.tileLayer(
      "https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}",
      { maxZoom: 16, attribution: esriAttribution }
    );
    baseLayers.osm = L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 19,
      attribution: "© OpenStreetMap contributors",
    });

    baseLayers.street.addTo(map);
    buildLayersControl();

    markersLayer = L.layerGroup().addTo(map);
  }

  function buildLayersControl() {
    if (layersControl) map.removeControl(layersControl);
    var labels = BASE_LAYER_LABELS[state.lang];
    var layersMap = {};
    layersMap[labels.street] = baseLayers.street;
    layersMap[labels.light] = baseLayers.light;
    layersMap[labels.osm] = baseLayers.osm;
    layersControl = L.control.layers(layersMap, null, { collapsed: true }).addTo(map);
  }

  function addBarrios(geojson) {
    barriosLayer = L.geoJSON(geojson, {
      style: function () {
        return BARRIO_DEFAULT_STYLE;
      },
      onEachFeature: function (feature, layer) {
        layer.bindTooltip(feature.properties.nombre, { sticky: true });
        barriosByName[feature.properties.nombre] = layer;
      },
    }).addTo(map);
    barriosLayer.bringToBack();
  }

  // True only when districtKey IS the whole official barrio (e.g. "palermo",
  // "belgrano") rather than one of its informal sub-neighborhoods (e.g.
  // "palermo soho", "belgrano r", "barrio norte") — the city's open-data
  // boundaries only cover whole barrios, not these colloquial subdivisions.
  function isWholeBarrioKey(districtKey) {
    var barrioName = DISTRICT_TO_BARRIO[districtKey];
    return !!barrioName && barrioName.toLowerCase() === districtKey;
  }

  function subbarrioStyle(feature) {
    var base = feature.properties.boundary_type === "official_aph_hull"
      ? { color: "#1a7a3c", dashArray: null }
      : { color: "#8e44ad", dashArray: "6 4" };
    return { color: base.color, weight: 2, fillOpacity: 0.06, opacity: 0.6, dashArray: base.dashArray };
  }

  function addSubbarrios(geojson) {
    subbarriosLayer = L.geoJSON(geojson, {
      style: subbarrioStyle,
      onEachFeature: function (feature, layer) {
        var p = feature.properties;
        var label = p.name + (p.boundary_type === "informal" ? " — " + STRINGS[state.lang].informalNote : "");
        layer.bindTooltip(label, { sticky: true });
        subbarriosByName[p.name] = layer;
      },
    });
    // Hidden by default (toggle controls visibility); not added to map yet.
  }

  function setSubbarriosVisible(visible) {
    subbarriosVisible = visible;
    if (!subbarriosLayer) return;
    if (visible) {
      if (!map.hasLayer(subbarriosLayer)) subbarriosLayer.addTo(map);
      // Re-apply the highlight (if any) now that the layer is actually drawn.
      subbarriosLayer.eachLayer(function (layer) {
        layer.setStyle(
          layer.feature.properties.name === state.subBarrio
            ? SUBBARRIO_HIGHLIGHT_STYLE
            : subbarrioStyle(layer.feature)
        );
      });
    } else if (map.hasLayer(subbarriosLayer)) {
      map.removeLayer(subbarriosLayer);
    }
  }

  // Selecting a sub-barrio always filters markers and zooms the map to its
  // extent (getBounds() works on a Leaflet layer whether or not it is on
  // the map). It never changes layer visibility itself — the checkbox is
  // the single source of truth for whether any boundary is drawn.
  function highlightSubbarrio(name) {
    if (!subbarriosLayer) return;
    subbarriosLayer.eachLayer(function (layer) {
      layer.setStyle(subbarrioStyle(layer.feature));
    });
    if (!name) return;
    var layer = subbarriosByName[name];
    if (!layer) return;
    if (subbarriosVisible) {
      layer.setStyle(SUBBARRIO_HIGHLIGHT_STYLE);
      layer.bringToFront();
    }
    map.fitBounds(layer.getBounds(), { padding: [40, 40] });
  }

  function highlightDistrict(districtKey) {
    barriosLayer.eachLayer(function (layer) {
      layer.setStyle(BARRIO_DEFAULT_STYLE);
    });
    if (!districtKey) return;

    if (isWholeBarrioKey(districtKey)) {
      var barrioName = DISTRICT_TO_BARRIO[districtKey];
      var layer = barriosByName[barrioName];
      if (layer) {
        layer.setStyle(BARRIO_HIGHLIGHT_STYLE);
        layer.bringToFront();
        map.fitBounds(layer.getBounds(), { padding: [40, 40] });
        return;
      }
    }

    // Sub-neighborhood with no official boundary of its own: zoom to its
    // actual listings instead of highlighting the whole parent barrio.
    var points = state.objects
      .filter(function (o) { return primaryDistrictKey(o.district) === districtKey && o.lat !== null && o.lng !== null; })
      .map(function (o) { return [o.lat, o.lng]; });
    if (points.length) {
      map.fitBounds(L.latLngBounds(points), { padding: [60, 60], maxZoom: 16 });
    }
  }

  function matchesFilters(obj) {
    if (state.activeTypes.size > 0) {
      // Objects listed as "both" (rent or sale) show up under either filter.
      var matchesType = state.activeTypes.has(obj.type) || (obj.type === "both" && (state.activeTypes.has("rent") || state.activeTypes.has("sale")));
      if (!matchesType) return false;
    }
    if (state.district && primaryDistrictKey(obj.district) !== state.district) return false;
    if (state.subBarrio && obj.sub_barrio !== state.subBarrio) return false;
    if (state.priceMin !== null && Number(obj.price) < state.priceMin) return false;
    if (state.priceMax !== null && Number(obj.price) > state.priceMax) return false;
    if (state.activeAmenities.size > 0) {
      for (var key of state.activeAmenities) {
        var v = obj[key];
        if (isEmptyValue(v) || String(v).toLowerCase() === "no") return false;
      }
    }
    return true;
  }

  function render() {
    markersLayer.clearLayers();
    var shown = 0;
    state.objects.forEach(function (obj) {
      if (obj.lat === null || obj.lng === null) return;
      if (!matchesFilters(obj)) return;
      shown++;
      var color = TYPE_COLORS[obj.type] || "#888";
      var marker = L.circleMarker([obj.lat, obj.lng], {
        radius: 8,
        fillColor: color,
        fillOpacity: obj.coords_approx ? 0.45 : 0.9,
        color: "#fff",
        weight: 2,
      });
      marker.bindPopup(buildPopup(obj, state.lang), { maxWidth: 300 });
      marker.addTo(markersLayer);
    });
    document.getElementById("results-count").textContent = shown;
  }

  function buildTypeChips() {
    var container = document.getElementById("filter-type");
    var types = ["rent", "sale"];
    types.forEach(function (t) {
      var chip = document.createElement("div");
      chip.className = "chip";
      chip.textContent = TYPE_LABELS[state.lang][t];
      chip.dataset.type = t;
      chip.addEventListener("click", function () {
        if (state.activeTypes.has(t)) {
          state.activeTypes.delete(t);
          chip.classList.remove("active");
        } else {
          state.activeTypes.add(t);
          chip.classList.add("active");
        }
        render();
      });
      container.appendChild(chip);
      typeChipEls.push({ el: chip, type: t });
    });
  }

  function buildAmenityChips() {
    var container = document.getElementById("filter-amenities");
    AMENITY_DEFS.forEach(function (a) {
      var chip = document.createElement("div");
      chip.className = "chip";
      chip.textContent = a.label[state.lang];
      chip.addEventListener("click", function () {
        if (state.activeAmenities.has(a.key)) {
          state.activeAmenities.delete(a.key);
          chip.classList.remove("active");
        } else {
          state.activeAmenities.add(a.key);
          chip.classList.add("active");
        }
        render();
      });
      container.appendChild(chip);
      amenityChipEls.push({ el: chip, def: a });
    });
  }

  function buildDistrictSelect(objects) {
    var select = document.getElementById("filter-district");
    var seen = {};
    var options = [];
    objects.forEach(function (o) {
      var key = primaryDistrictKey(o.district);
      if (key && !seen[key]) {
        seen[key] = true;
        options.push(key);
      }
    });
    options.sort();
    options.forEach(function (key) {
      var opt = document.createElement("option");
      opt.value = key;
      opt.textContent = key
        .split(" ")
        .map(function (word) { return word.charAt(0).toUpperCase() + word.slice(1); })
        .join(" ");
      select.appendChild(opt);
    });
    select.addEventListener("change", function () {
      state.district = select.value;
      highlightDistrict(state.district);
      render();
    });
  }

  function buildSubbarrioSelect(subbarrioFeatures) {
    var select = document.getElementById("filter-subbarrio");
    var byParent = {};
    subbarrioFeatures.forEach(function (f) {
      var parent = f.properties.parent_barrio;
      (byParent[parent] = byParent[parent] || []).push(f.properties.name);
    });
    Object.keys(byParent).sort().forEach(function (parent) {
      var group = document.createElement("optgroup");
      group.label = parent;
      byParent[parent].sort().forEach(function (name) {
        var opt = document.createElement("option");
        opt.value = name;
        opt.textContent = name;
        group.appendChild(opt);
      });
      select.appendChild(group);
    });
    select.addEventListener("change", function () {
      state.subBarrio = select.value;
      highlightSubbarrio(state.subBarrio);
      render();
    });
  }

  function bindSubbarrioToggle() {
    document.getElementById("toggle-subbarrios").addEventListener("change", function (e) {
      setSubbarriosVisible(e.target.checked);
    });
  }

  function applyStaticText() {
    var t = STRINGS[state.lang];
    document.documentElement.lang = state.lang;
    document.getElementById("label-subtitle").textContent = t.subtitle;
    document.getElementById("label-type").textContent = t.type;
    document.getElementById("label-district").textContent = t.district;
    document.getElementById("option-all-districts").textContent = t.allDistricts;
    document.getElementById("label-subbarrio").textContent = t.subBarrio;
    document.getElementById("option-all-subbarrios").textContent = t.allSubBarrios;
    document.getElementById("label-subbarrios-toggle").textContent = t.showSubBarrios;
    document.getElementById("label-price").textContent = t.price;
    document.getElementById("label-amenities").textContent = t.amenities;
    document.getElementById("reset-filters").textContent = t.reset;
    document.getElementById("label-shown").textContent = t.shown;
    document.getElementById("label-of").textContent = t.of;
    document.getElementById("footer-link").textContent = t.footer;
    document.getElementById("price-min").placeholder = t.priceFrom;
    document.getElementById("price-max").placeholder = t.priceTo;

    typeChipEls.forEach(function (c) { c.el.textContent = TYPE_LABELS[state.lang][c.type]; });
    amenityChipEls.forEach(function (c) { c.el.textContent = c.def.label[state.lang]; });
    buildLayersControl();
  }

  function bindLangSwitch() {
    var buttons = document.querySelectorAll("#lang-switch .lang-btn");
    buttons.forEach(function (btn) {
      btn.addEventListener("click", function () {
        var lang = btn.dataset.lang;
        if (lang === state.lang) return;
        state.lang = lang;
        buttons.forEach(function (b) { b.classList.toggle("active", b === btn); });
        applyStaticText();
        render();
      });
    });
  }

  function bindPriceInputs() {
    var min = document.getElementById("price-min");
    var max = document.getElementById("price-max");
    min.addEventListener("input", function () {
      state.priceMin = min.value ? Number(min.value) : null;
      render();
    });
    max.addEventListener("input", function () {
      state.priceMax = max.value ? Number(max.value) : null;
      render();
    });
  }

  function bindReset() {
    document.getElementById("reset-filters").addEventListener("click", function () {
      state.activeTypes.clear();
      state.district = "";
      state.subBarrio = "";
      state.priceMin = null;
      state.priceMax = null;
      state.activeAmenities.clear();
      document.querySelectorAll(".chip.active").forEach(function (c) { c.classList.remove("active"); });
      document.getElementById("filter-district").value = "";
      document.getElementById("filter-subbarrio").value = "";
      document.getElementById("price-min").value = "";
      document.getElementById("price-max").value = "";
      highlightDistrict("");
      highlightSubbarrio("");
      map.setView(CABA_CENTER, 13);
      render();
    });
  }

  function loadJson(url) {
    return fetch(url, { cache: "no-cache" }).then(function (r) {
      if (!r.ok) throw new Error("Failed to load " + url + ": " + r.status);
      return r.json();
    });
  }

  function init() {
    initMap();
    Promise.all([loadJson("data/objects.json"), loadJson("data/barrios.geojson"), loadJson("data/subbarrios.geojson")])
      .then(function (results) {
        var objects = results[0];
        var barrios = results[1];
        var subbarrios = results[2];
        state.objects = objects;
        addBarrios(barrios);
        addSubbarrios(subbarrios);
        buildTypeChips();
        buildAmenityChips();
        buildDistrictSelect(objects);
        buildSubbarrioSelect(subbarrios.features);
        bindSubbarrioToggle();
        bindPriceInputs();
        bindReset();
        bindLangSwitch();
        applyStaticText();
        document.getElementById("total-count").textContent = objects.length;
        render();
      })
      .catch(function (err) {
        console.error(err);
        alert("Не удалось загрузить данные карты: " + err.message);
      });
  }

  document.addEventListener("DOMContentLoaded", init);
})();
