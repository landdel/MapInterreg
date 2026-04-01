    document.getElementById('csv-input').addEventListener('change', function () {
      const file = this.files[0];
      if (!file) return;
      const reader = new FileReader();
      reader.onload = function (e) { parseAndRender(e.target.result); };
      reader.readAsText(file, 'ISO-8859-1');
    });

    function parseAndRender(text) {
      const lines = text.split(/\r?\n/).filter(l => l.trim());
      if (lines.length < 2) { setStatus('Fichier vide ou invalide.', 'error'); return; }

      const headers = lines[0].split(';').map(h => h.trim().toLowerCase());
      const latIdx = headers.findIndex(h => h === 'latitude');
      const lonIdx = headers.findIndex(h => h === 'longitude');

      if (latIdx === -1 || lonIdx === -1) {
        setStatus('Colonnes Latitude/Longitude introuvables dans le CSV.', 'error');
        return;
      }

      const nameIdx = headers.indexOf('name');
      const catIdx  = headers.indexOf('category');
      const typeIdx = headers.indexOf('type');
      const urlIdx  = headers.indexOf('url');

      const points = [];
      let skipped = 0;

      for (let i = 1; i < lines.length; i++) {
        const cols = lines[i].split(';');
        const latRaw = (cols[latIdx] || '').trim().replace(',', '.');
        const lonRaw = (cols[lonIdx] || '').trim().replace(',', '.');
        const lat = parseFloat(latRaw);
        const lon = parseFloat(lonRaw);

        if (!latRaw || !lonRaw || isNaN(lat) || isNaN(lon)) { skipped++; continue; }

        points.push({
          lat, lon,
          name:     nameIdx >= 0 ? (cols[nameIdx] || '').trim() : '',
          category: catIdx  >= 0 ? (cols[catIdx]  || '').trim() : '',
          type:     typeIdx >= 0 ? (cols[typeIdx]  || '').trim() : '',
          url:      urlIdx  >= 0 ? (cols[urlIdx]   || '').trim() : '',
        });
      }

      let msg = points.length + ' point(s) affiche(s)';
      if (skipped > 0) msg += ' \u2014 ' + skipped + ' ligne(s) sans coordonnees ignoree(s)';
      setStatus(msg, 'ok');

      if (points.length > 0) renderMap(points);
    }

    let csvMap = null;

    function renderMap(points) {
      const el = document.getElementById('csv-map');
      el.style.display = 'block';
      if (csvMap) { csvMap.remove(); csvMap = null; }

      csvMap = L.map('csv-map');
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '\u00a9 OpenStreetMap contributors', maxZoom: 19
      }).addTo(csvMap);

      const bounds = [];
      points.forEach(function (p) {
        let html = '<strong>' + (p.name || '\u2014') + '</strong>';
        if (p.category) html += '<br>' + p.category;
        if (p.type)     html += ' \u00b7 ' + p.type;
        if (p.url)      html += '<br><a href="' + p.url + '" target="_blank" rel="noopener">Lien</a>';

        L.circleMarker([p.lat, p.lon], {
          radius: 7, color: '#0a6f6a', fillColor: '#0a6f6a', fillOpacity: 0.7, weight: 1.5
        }).bindPopup(html).addTo(csvMap);
        bounds.push([p.lat, p.lon]);
      });

      csvMap.fitBounds(bounds, { padding: [30, 30] });
    }

    function setStatus(msg, type) {
      const el = document.getElementById('csv-status');
      el.textContent = msg;
      el.className = type === 'error' ? 'csv-error' : 'csv-ok';
    }