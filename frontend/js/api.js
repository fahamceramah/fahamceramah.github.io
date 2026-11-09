/**
 * FahamCeramah - API Client
 */
const API = {
  async getVideos() {
    try {
      const res = await fetch('/api/videos');
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return await res.json();
    } catch (err) {
      console.error('Error fetching videos:', err);
      return { status: 'error', videos: [] };
    }
  },

  async getVideoDetail(videoId) {
    try {
      const res = await fetch(`/api/videos/${encodeURIComponent(videoId)}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return await res.json();
    } catch (err) {
      console.error(`Error fetching video ${videoId}:`, err);
      return { status: 'error', video: null };
    }
  },

  async searchVideos(query) {
    try {
      const res = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return await res.json();
    } catch (err) {
      console.error('Error searching videos:', err);
      return { status: 'error', results: [] };
    }
  },

  async getStats() {
    try {
      const res = await fetch('/api/stats');
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return await res.json();
    } catch (err) {
      console.error('Error fetching stats:', err);
      return null;
    }
  },

  async getGlossary() {
    try {
      const res = await fetch('/api/dictionaries/terms');
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return await res.json();
    } catch (err) {
      console.error('Error fetching glossary:', err);
      return { terms: [] };
    }
  }
};
