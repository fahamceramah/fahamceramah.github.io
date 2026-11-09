/**
 * FahamCeramah - Universal API Client (Supports both GitHub Pages static hosting & local FastAPI)
 */
const API = {
  _cachedVideos: null,

  async getVideos() {
    // 1. Try static data (GitHub Pages)
    try {
      const res = await fetch('data/videos.json');
      if (res.ok) {
        const videos = await res.json();
        this._cachedVideos = videos;
        return { status: 'success', videos };
      }
    } catch (e) {}

    // 2. Fallback to dynamic backend
    try {
      const res = await fetch('/api/videos');
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      this._cachedVideos = data.videos || [];
      return data;
    } catch (err) {
      console.error('Error fetching videos:', err);
      return { status: 'error', videos: [] };
    }
  },

  async getVideoDetail(videoId) {
    // 1. Try static summary file (GitHub Pages)
    try {
      const res = await fetch(`data/summaries/${encodeURIComponent(videoId)}.json`);
      if (res.ok) {
        const video = await res.json();
        return { status: 'success', video };
      }
    } catch (e) {}

    // 2. Fallback to dynamic backend
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
    const q = query.toLowerCase().trim();
    if (!q) return { status: 'success', results: [] };

    if (!this._cachedVideos) {
      await this.getVideos();
    }

    if (this._cachedVideos) {
      const matched = this._cachedVideos.filter(v => {
        const titleMatch = (v.title || '').toLowerCase().includes(q) || (v.short_title || '').toLowerCase().includes(q);
        const summaryMatch = (v.summary_short || '').toLowerCase().includes(q);
        const takeawayMatch = (v.key_takeaways || []).some(t => t.toLowerCase().includes(q));
        return titleMatch || summaryMatch || takeawayMatch;
      });
      return { status: 'success', results: matched };
    }

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
      const res = await fetch('data/stats.json');
      if (res.ok) return await res.json();
    } catch (e) {}

    try {
      const res = await fetch('/api/stats');
      if (res.ok) return await res.json();
    } catch (err) {}

    return null;
  }
};
