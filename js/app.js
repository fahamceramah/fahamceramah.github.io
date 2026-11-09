/**
 * FahamCeramah - Home Page Controller
 */
document.addEventListener('DOMContentLoaded', async () => {
  const videoGrid = document.getElementById('video-grid');
  const searchInput = document.getElementById('search-input');
  const totalVideosEl = document.getElementById('stat-total-videos');
  const totalHoursEl = document.getElementById('stat-total-hours');
  const totalHadithEl = document.getElementById('stat-total-hadith');

  // Load Theme Preference
  const savedTheme = localStorage.getItem('fahamceramah_theme') || 'light';
  document.documentElement.setAttribute('data-theme', savedTheme);

  // Load Stats
  const stats = await API.getStats();
  if (stats) {
    if (totalVideosEl) totalVideosEl.textContent = `${stats.total_videos} Kuliah`;
    if (totalHoursEl) totalHoursEl.textContent = `~${stats.total_duration_hours} Jam`;
    if (totalHadithEl) totalHadithEl.textContent = `${stats.total_hadith_references} Hadis & Dalil`;
  }

  // Load Videos
  let allVideos = [];
  async function loadVideos() {
    videoGrid.innerHTML = `
      <div style="grid-column: 1/-1; text-align: center; padding: 48px; color: var(--text-muted);">
        <p>Sedang memuatkan senarai ceramah...</p>
      </div>
    `;

    const data = await API.getVideos();
    allVideos = data.videos || [];
    renderVideos(allVideos);
  }

  function renderVideos(videos) {
    if (!videos || videos.length === 0) {
      videoGrid.innerHTML = `
        <div style="grid-column: 1/-1; text-align: center; padding: 48px; color: var(--text-muted);">
          <p>Tiada ceramah dijumpai.</p>
        </div>
      `;
      return;
    }

    videoGrid.innerHTML = videos.map(v => {
      const durationMin = Math.round(v.duration_sec / 60);
      const excerpt = v.summary_short ? v.summary_short.slice(0, 160) + '...' : 'Ringkasan komprehensif kuliah pengajian Bulughul Maram.';
      return `
        <a href="ceramah.html?id=${encodeURIComponent(v.video_id)}" class="ceramah-card" aria-label="Buka ringkasan siri ${v.series_no}: ${v.short_title}">
          <div class="card-badge-row">
            <span class="siri-badge">Siri ${v.series_no}</span>
            <span class="duration-tag">${durationMin} minit</span>
          </div>
          <h3 class="card-title">${v.short_title}</h3>
          <p class="card-excerpt">${excerpt}</p>
          <div class="card-footer">
            <span>${v.book_section}</span>
            <span class="card-action-btn">Baca Ringkasan →</span>
          </div>
        </a>
      `;
    }).join('');
  }

  // Search Interaction (Debounced)
  let searchTimer;
  if (searchInput) {
    searchInput.addEventListener('input', (e) => {
      clearTimeout(searchTimer);
      const q = e.target.value.trim();
      if (!q) {
        renderVideos(allVideos);
        return;
      }

      searchTimer = setTimeout(async () => {
        if (q.length >= 2) {
          const res = await API.searchVideos(q);
          const matchedIds = new Set((res.results || []).map(r => r.video_id));
          const filtered = allVideos.filter(v => matchedIds.has(v.video_id) || v.title.toLowerCase().includes(q.toLowerCase()) || v.short_title.toLowerCase().includes(q.toLowerCase()));
          renderVideos(filtered);
        }
      }, 200);
    });
  }

  await loadVideos();
});
