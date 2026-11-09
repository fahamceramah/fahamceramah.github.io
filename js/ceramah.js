/**
 * FahamCeramah - Dedicated Ceramah Reading Page Controller (Universal GitHub Pages & Local)
 */
document.addEventListener('DOMContentLoaded', async () => {
  const urlParams = new URLSearchParams(window.location.search);
  const videoId = urlParams.get('id') || 'sg2LSuC8ATQ'; // Default to Siri 1 if none provided

  // Elements
  const ceramahContent = document.getElementById('ceramah-content');
  const loadingState = document.getElementById('loading-state');
  const errorState = document.getElementById('error-state');

  // Load Saved Preferences (Theme & Font Scaling)
  const savedTheme = localStorage.getItem('fahamceramah_theme') || 'light';
  document.documentElement.setAttribute('data-theme', savedTheme);

  const savedScale = localStorage.getItem('fahamceramah_font_scale') || '1';
  document.documentElement.style.setProperty('--text-scale', savedScale);

  // Fetch Video Detail
  const res = await API.getVideoDetail(videoId);
  if (res.status === 'error' || !res.video) {
    if (loadingState) loadingState.style.display = 'none';
    if (errorState) errorState.style.display = 'block';
    return;
  }

  const v = res.video;
  document.title = `${v.short_title} (Siri ${v.series_no}) - FahamCeramah`;

  // Render Full Content
  renderCeramahPage(v);

  if (loadingState) loadingState.style.display = 'none';
  if (ceramahContent) ceramahContent.style.display = 'block';

  // Setup Bottom Actions
  setupBottomActions(v);
});

function renderCeramahPage(v) {
  const container = document.getElementById('ceramah-content');
  const durationMin = Math.round(v.duration_sec / 60);

  container.innerHTML = `
    <!-- Header & Metadata -->
    <header class="ceramah-header-meta">
      <nav class="ceramah-breadcrumb" aria-label="Breadcrumb">
        <a href="index.html">Utama</a>
        <span>›</span>
        <span>Bulughul Maram</span>
        <span>›</span>
        <span>Siri ${v.series_no}</span>
      </nav>

      <div class="meta-tags-row">
        <span class="siri-badge">Siri ${v.series_no}</span>
        <span class="meta-badge">${v.book_section}</span>
        <span class="meta-badge">Durasi: ~${durationMin} minit</span>
        <span class="meta-badge">Penceramah: ${v.speaker}</span>
      </div>

      <h1 id="ceramah-title">${v.title}</h1>
      <p style="color: var(--text-muted); font-size: var(--font-sm);">
        Kuliah asal dirakam di Masjid Alwi, Kangar, Perlis. Sumber YouTube:
        <a href="${v.youtube_url}" target="_blank" rel="noopener noreferrer">Tonton di YouTube ↗</a>
      </p>
    </header>

    <!-- Collapsible Video Player -->
    <section class="video-collapsible-bar" aria-label="Pemain Video Kuliah">
      <button type="button" class="video-toggle-btn" id="video-toggle-btn" aria-expanded="false" aria-controls="video-player-container">
        <span>▶ Tunjuk / Sembunyikan Rakaman Video YouTube</span>
        <span id="video-toggle-icon">▼</span>
      </button>
      <div class="video-frame-container" id="video-player-container">
        <iframe
          id="yt-iframe"
          src="https://www.youtube-nocookie.com/embed/${v.video_id}?enablejsapi=1"
          title="Rakaman Video Kuliah ${v.short_title}"
          allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
          allowfullscreen>
        </iframe>
      </div>
    </section>

    <!-- Scrollable Tab Bar -->
    <div class="tab-nav-wrapper" role="tablist" aria-label="Bahagian Kandungan Kuliah">
      <button class="tab-btn active" role="tab" aria-selected="true" data-tab="tab-pantas">Ringkasan Pantas</button>
      <button class="tab-btn" role="tab" aria-selected="false" data-tab="tab-penuh">Ringkasan Penuh</button>
      <button class="tab-btn" role="tab" aria-selected="false" data-tab="tab-topik">Topik & Cap Masa (${v.topics.length})</button>
      <button class="tab-btn" role="tab" aria-selected="false" data-tab="tab-dalil">Dalil & Hadis (${v.religious_references.length})</button>
      <button class="tab-btn" role="tab" aria-selected="false" data-tab="tab-glosari">Glosari Istilah (${v.terminology.length})</button>
    </div>

    <!-- TAB 1: Ringkasan Pantas -->
    <div id="tab-pantas" class="tab-pane active" role="tabpanel">
      <div class="content-box">
        <h2>Ringkasan Eksekutif (2 Minit Bacaan)</h2>
        <div style="font-size: var(--font-base); line-height: 1.7; margin-bottom: var(--space-lg);">
          ${v.summary.short.split('\n\n').map(p => `<p>${p}</p>`).join('')}
        </div>

        <h3 style="margin-top: var(--space-lg); border-top: 1px solid var(--border-subtle); padding-top: var(--space-md);">
          Pengajaran & Amalan Utama
        </h3>
        <ul class="takeaway-list">
          ${v.summary.key_takeaways.map(t => `<li class="takeaway-item">${t}</li>`).join('')}
        </ul>
      </div>
    </div>

    <!-- TAB 2: Ringkasan Penuh -->
    <div id="tab-penuh" class="tab-pane" role="tabpanel">
      <div class="content-box">
        <h2>Huraian Terperinci & Perbahasan Fiqh</h2>
        <div style="font-size: var(--font-base); line-height: 1.8;">
          ${v.summary.detailed.split('\n\n').map(p => `<p>${p}</p>`).join('')}
        </div>
      </div>
    </div>

    <!-- TAB 3: Topik & Cap Masa -->
    <div id="tab-topik" class="tab-pane" role="tabpanel">
      <div class="content-box">
        <h2>Navigasi Mengikut Topik & Cap Masa</h2>
        <p style="color: var(--text-muted); font-size: var(--font-sm); margin-bottom: var(--space-md);">
          Klik mana-mana cap masa untuk melompat terus ke bahagian perbincangan dalam pemain video.
        </p>

        <div class="topic-timeline">
          ${v.topics.map(t => `
            <article class="topic-card">
              <div class="topic-header">
                <button class="timestamp-badge" onclick="seekVideo('${t.timestamp}', ${t.start_time})" aria-label="Lompat ke minit ${t.timestamp}">
                  ⏱ ${t.timestamp}
                </button>
                <h3 style="font-size: var(--font-md); margin-bottom: 0;">${t.title}</h3>
              </div>
              <p style="color: var(--text-muted); font-size: var(--font-sm); margin-top: 4px;">${t.summary}</p>
              ${t.key_points && t.key_points.length > 0 ? `
                <ul style="padding-left: 20px; font-size: var(--font-xs); color: var(--text-soft); margin-top: 4px;">
                  ${t.key_points.map(kp => `<li>${kp}</li>`).join('')}
                </ul>
              ` : ''}
            </article>
          `).join('')}
        </div>
      </div>
    </div>

    <!-- TAB 4: Dalil & Rujukan Agama -->
    <div id="tab-dalil" class="tab-pane" role="tabpanel">
      <div class="content-box">
        <h2>Dalil Hadis & Rujukan Al-Quran</h2>
        <p style="color: var(--text-muted); font-size: var(--font-sm); margin-bottom: var(--space-lg);">
          Matan hadis lengkap berbaris berserta terjemahan, perawi sahabat, dan pengesahan darjat hadis.
        </p>

        ${v.religious_references.map((ref, idx) => `
          <article class="reference-card">
            <div class="ref-header">
              <h3 style="font-size: var(--font-md); color: var(--accent-primary); margin: 0;">
                ${ref.reference}
              </h3>
              <span class="ref-grade">${ref.grade || 'Sahih'}</span>
            </div>

            <p style="font-size: var(--font-xs); color: var(--text-soft); margin-bottom: var(--space-xs);">
              ${ref.narrator ? `<strong>Perawi:</strong> ${ref.narrator} | ` : ''}
              ${ref.source_book ? `<strong>Sumber:</strong> ${ref.source_book}` : ''}
            </p>

            ${ref.text_ar ? `
              <div class="arabic-text" aria-label="Teks Arab Hadis">${ref.text_ar}</div>
            ` : ''}

            ${ref.text_ms ? `
              <div style="font-size: var(--font-base); line-height: 1.6; margin-top: var(--space-sm);">
                <strong>Terjemahan:</strong> "${ref.text_ms}"
              </div>
            ` : ''}
          </article>
        `).join('')}
      </div>
    </div>

    <!-- TAB 5: Glosari Istilah -->
    <div id="tab-glosari" class="tab-pane" role="tabpanel">
      <div class="content-box">
        <h2>Glosari Istilah Agama & Dialek</h2>
        <div class="glosari-grid">
          ${v.terminology.map(term => `
            <div class="term-card">
              <span class="term-badge">${term.category}</span>
              <h3 style="font-size: var(--font-md); margin-bottom: 4px;">${term.term}</h3>
              <p style="color: var(--text-muted); font-size: var(--font-sm); margin-bottom: 0;">${term.explanation}</p>
            </div>
          `).join('')}
        </div>
      </div>
    </div>
  `;

  // Setup Tabs
  const tabBtns = container.querySelectorAll('.tab-btn');
  const tabPanes = container.querySelectorAll('.tab-pane');

  tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      tabBtns.forEach(b => {
        b.classList.remove('active');
        b.setAttribute('aria-selected', 'false');
      });
      tabPanes.forEach(p => p.classList.remove('active'));

      btn.classList.add('active');
      btn.setAttribute('aria-selected', 'true');
      const target = document.getElementById(btn.dataset.tab);
      if (target) target.classList.add('active');
    });
  });

  // Setup Video Player Collapsible
  const videoToggleBtn = document.getElementById('video-toggle-btn');
  const videoPlayerContainer = document.getElementById('video-player-container');
  const videoToggleIcon = document.getElementById('video-toggle-icon');

  if (videoToggleBtn && videoPlayerContainer) {
    videoToggleBtn.addEventListener('click', () => {
      const isOpen = videoPlayerContainer.classList.toggle('is-open');
      videoToggleBtn.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
      videoToggleIcon.textContent = isOpen ? '▲' : '▼';
    });
  }
}

// Seek video to specific timestamp
window.seekVideo = function(timestampStr, seconds) {
  const container = document.getElementById('video-player-container');
  const iframe = document.getElementById('yt-iframe');
  const toggleBtn = document.getElementById('video-toggle-btn');
  const toggleIcon = document.getElementById('video-toggle-icon');

  if (container && !container.classList.contains('is-open')) {
    container.classList.add('is-open');
    if (toggleBtn) toggleBtn.setAttribute('aria-expanded', 'true');
    if (toggleIcon) toggleIcon.textContent = '▲';
  }

  // Calculate seconds from timestamp if not passed
  let sec = seconds;
  if (!sec && timestampStr) {
    const parts = timestampStr.split(':').map(Number);
    if (parts.length === 3) sec = parts[0] * 3600 + parts[1] * 60 + parts[2];
    else if (parts.length === 2) sec = parts[0] * 60 + parts[1];
  }

  if (iframe) {
    const baseUrl = iframe.src.split('?')[0];
    iframe.src = `${baseUrl}?start=${Math.floor(sec)}&autoplay=1`;
    container.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }
};

// Bottom Control Bar
function setupBottomActions(v) {
  // Font scale cycle: 0.9 -> 1.0 -> 1.15 -> 1.3
  const scales = ['0.9', '1', '1.15', '1.3'];
  const fontBtn = document.getElementById('btn-font-scale');
  if (fontBtn) {
    fontBtn.addEventListener('click', () => {
      let current = localStorage.getItem('fahamceramah_font_scale') || '1';
      let idx = scales.indexOf(current);
      let next = scales[(idx + 1) % scales.length];
      localStorage.setItem('fahamceramah_font_scale', next);
      document.documentElement.style.setProperty('--text-scale', next);
    });
  }

  // Theme cycle: light -> sepia -> dark
  const themes = ['light', 'sepia', 'dark'];
  const themeBtn = document.getElementById('btn-theme-toggle');
  if (themeBtn) {
    themeBtn.addEventListener('click', () => {
      let current = localStorage.getItem('fahamceramah_theme') || 'light';
      let idx = themes.indexOf(current);
      let next = themes[(idx + 1) % themes.length];
      localStorage.setItem('fahamceramah_theme', next);
      document.documentElement.setAttribute('data-theme', next);
    });
  }

  // Export Markdown (Client-side download, works serverlessly!)
  const exportBtn = document.getElementById('btn-export-md');
  if (exportBtn) {
    exportBtn.addEventListener('click', () => {
      downloadMarkdown(v);
    });
  }
}

function downloadMarkdown(v) {
  let md = `# ${v.title}\n`;
  md += `**Siri:** ${v.series_no} | **Penceramah:** ${v.speaker}\n`;
  md += `**Kitab:** ${v.series_name} - ${v.book_section}\n`;
  md += `**Pautan YouTube:** ${v.youtube_url}\n`;
  md += `**Tarikh Kuliah:** ${v.date_recorded} | **Durasi:** ${Math.round(v.duration_sec / 60)} minit\n\n---\n\n`;

  md += `## 1. Ringkasan Pantas\n${v.summary.short}\n\n### Pengajaran & Amalan Utama\n`;
  (v.summary.key_takeaways || []).forEach(pt => {
    md += `- ${pt}\n`;
  });

  md += `\n---\n\n## 2. Huraian Terperinci\n${v.summary.detailed}\n\n---\n\n`;

  md += `## 3. Dalil & Rujukan Agama\n`;
  (v.religious_references || []).forEach(ref => {
    md += `### ${ref.reference} (${ref.grade || 'Sahih'})\n`;
    if (ref.narrator) md += `**Perawi:** ${ref.narrator} | **Sumber:** ${ref.source_book || ''}\n\n`;
    if (ref.text_ar) md += `> **Matan Arab:**\n> ${ref.text_ar}\n\n`;
    if (ref.text_ms) md += `**Terjemahan:** "${ref.text_ms}"\n\n`;
  });

  md += `\n---\n\n## 4. Topik Perbincangan & Cap Masa\n| Masa | Topik | Huraian Ringkas |\n|---|---|---|\n`;
  (v.topics || []).forEach(t => {
    md += `| ${t.timestamp} | ${t.title} | ${t.summary} |\n`;
  });

  md += `\n---\n\n## 5. Glosari Istilah\n`;
  (v.terminology || []).forEach(term => {
    md += `- **${term.term}** *(${term.category})*: ${term.explanation}\n`;
  });

  md += `\n---\n\n## Penafian & Penghargaan\nSemua rakaman video kuliah asal yang diringkaskan di sini adalah hasil usaha gigih dan dedikasi berterusan pihak **PROmediaTAJDID**, **Pejabat Mufti Negeri Perlis**, dan seluruh barisan pasukan penerbitan yang bertungkus-lumus merakam serta menyiarkan kuliah pengajian ini. FahamCeramah hanya menyediakan ringkasan bertulis semata-mata untuk memudahkan capaian ilmu, rujukan, serta manfaat mereka yang memerlukan.\n`;

  const blob = new Blob([md], { type: 'text/markdown;charset=utf-8' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = `ceramah-siri-${v.series_no}-${v.video_id}.md`;
  a.click();
  URL.revokeObjectURL(a.href);
}
