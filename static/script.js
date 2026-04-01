    document.getElementById('csv-input').addEventListener('change', function () {
      const file = this.files[0];
      if (!file) return;
      setStatus('Fichier selectionne : ' + file.name + '. Cliquez sur le bouton pour regenerer la carte.', 'ok');
    });

    function setStatus(msg, type) {
      const el = document.getElementById('csv-status');
      el.textContent = msg;
      el.className = type === 'error' ? 'csv-error' : 'csv-ok';
    }
