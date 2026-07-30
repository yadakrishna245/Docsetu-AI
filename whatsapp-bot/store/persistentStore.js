const fs = require('fs');
const path = require('path');

const DATA_DIR = path.join(__dirname, 'data');

class PersistentStore {
  constructor(filename) {
    this._filePath = path.join(DATA_DIR, `${filename}.json`);
    this._data = {};
    this._saveTimeout = null;
    this._ensureDir();
    this._load();
  }

  get(key) {
    return this._data[key] !== undefined ? this._data[key] : null;
  }

  set(key, value) {
    this._data[key] = value;
    this._scheduleSave();
  }

  delete(key) {
    delete this._data[key];
    this._scheduleSave();
  }

  getAll() {
    return { ...this._data };
  }

  _load() {
    try {
      if (fs.existsSync(this._filePath)) {
        const raw = fs.readFileSync(this._filePath, 'utf-8');
        this._data = JSON.parse(raw);
      }
    } catch (error) {
      // JSON parse error or read error — reset to empty
      console.warn(`[PersistentStore] Failed to load ${this._filePath}, starting fresh:`, error.message);
      this._data = {};
    }
  }

  _save() {
    try {
      fs.writeFileSync(this._filePath, JSON.stringify(this._data, null, 2), 'utf-8');
    } catch (error) {
      console.error(`[PersistentStore] Failed to save ${this._filePath}:`, error.message);
    }
  }

  _scheduleSave() {
    if (this._saveTimeout) {
      clearTimeout(this._saveTimeout);
    }
    this._saveTimeout = setTimeout(() => {
      this._save();
      this._saveTimeout = null;
    }, 1000);
  }

  _ensureDir() {
    if (!fs.existsSync(DATA_DIR)) {
      fs.mkdirSync(DATA_DIR, { recursive: true });
    }
  }
}

module.exports = PersistentStore;
