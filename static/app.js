/* ═══════════════════════════════════════════════════════
   AtifJobs — Frontend Logic
   ═══════════════════════════════════════════════════════ */

const API = '';     // same origin — backend is FastAPI

// ── State ──────────────────────────────────────────────
let allJobs        = [];
let displayedJobs  = [];
let activeCategory = 'All';
let savedJobs      = new Set(JSON.parse(localStorage.getItem('savedJobs') || '[]'));
let refreshTimer   = null;
let nextRefreshAt  = null;
const POLL_INTERVAL_MS = 5 * 60 * 1000;   // poll API every 5 min

// ── Init ───────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  loadJobs();
  loadStats();
  setInterval(() => { loadJobs(); loadStats(); }, POLL_INTERVAL_MS);
  startLiveTimer();
});

// ── API calls ──────────────────────────────────────────
async function loadJobs() {
  try {
    const sort     = document.getElementById('sortFilter')?.value  || 'match_score';
    const location = document.getElementById('locationFilter')?.value || '';
    const source   = document.getElementById('sourceFilter')?.value  || '';

    const params = new URLSearchParams({ sort, min_score: 25, limit: 300 });
    if (location) params.set('location', location);
    if (source)   params.set('source', source);
    if (activeCategory && activeCategory !== 'All') params.set('category', activeCategory);

    const resp = await fetch(`${API}/api/jobs?${params}`);
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);

    const data = await resp.json();
    allJobs = data.jobs || [];
    applyFilters();

    document.getElementById('errorState').style.display = 'none';
  } catch (err) {
    console.error('loadJobs error:', err);
    showError(err.message);
  }
}

async function loadStats() {
  try {
    const resp = await fetch(`${API}/api/stats`);
    const stats = await resp.json();

    document.getElementById('statTotal').textContent = stats.total ?? '—';
    document.getElementById('statHigh').textContent  = stats.high_match ?? '—';

    if (stats.last_updated) {
      const ago = timeAgo(new Date(stats.last_updated));
      document.getElementById('liveText').textContent = `Updated ${ago}`;
    }
  } catch (_) {}
}

async function manualRefresh() {
  const btn = document.getElementById('refreshBtn');
  btn.disabled = true;
  btn.classList.add('spinning');
  showToast('🔄 Fetching fresh jobs…');
  try {
    await fetch(`${API}/api/refresh`, { method: 'POST' });
    await new Promise(r => setTimeout(r, 1500));
    await loadJobs();
    await loadStats();
    showToast('✅ Jobs refreshed!');
  } catch (e) {
    showToast('❌ Refresh failed — check logs');
  } finally {
    btn.disabled = false;
    btn.classList.remove('spinning');
  }
}

// ── Filtering & Search ─────────────────────────────────
function applyFilters() {
  const query = (document.getElementById('searchInput')?.value || '').toLowerCase().trim();

  displayedJobs = allJobs.filter(job => {
    if (!query) return true;
    const searchable = [
      job.title, job.company, job.location,
      job.description, ...(job.tags || [])
    ].join(' ').toLowerCase();
    return searchable.includes(query);
  });

  renderJobs(displayedJobs);
  document.getElementById('resultsCount').textContent =
    `${displayedJobs.length} job${displayedJobs.length !== 1 ? 's' : ''} found`;
}

function setCategory(btn) {
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  btn.classList.add('active');
  activeCategory = btn.dataset.cat;
  loadJobs();
}

// ── Rendering ──────────────────────────────────────────
function renderJobs(jobs) {
  const grid = document.getElementById('jobsGrid');
  const empty = document.getElementById('emptyState');

  if (!jobs.length) {
    grid.innerHTML = '';
    empty.style.display = 'block';
    return;
  }

  empty.style.display = 'none';
  grid.innerHTML = jobs.map((job, i) => jobCardHTML(job, i)).join('');
}

function jobCardHTML(job, index) {
  const score     = job.match_score || 0;
  const scoreTier = score >= 70 ? 'high' : score >= 40 ? 'med' : 'low';
  const tags      = Array.isArray(job.tags) ? job.tags.slice(0, 5) : [];
  const isSaved   = savedJobs.has(job.id);
  const logo      = (job.company || 'J')[0].toUpperCase();
  const posted    = job.posted_at ? timeAgo(new Date(job.posted_at)) : '';
  const salary    = job.salary ? `💰 ${job.salary}` : '';
  const sourceClass = `source-${(job.source || 'adzuna').toLowerCase()}`;
  const delay     = Math.min(index * 0.04, 0.6);

  return `
  <div
    class="job-card"
    data-score-tier="${scoreTier}"
    data-id="${esc(job.id)}"
    style="animation-delay: ${delay}s"
    onclick="openModal('${esc(job.id)}')"
  >
    <div class="card-header">
      <div class="card-left">
        <div class="company-row">
          <div class="company-logo">${esc(logo)}</div>
          <span class="company-name">${esc(job.company)}</span>
        </div>
        <div class="job-title">${esc(job.title)}</div>
      </div>
      <div class="score-badge score-${scoreTier}">
        <span class="score-num">${score}%</span>
        <span class="score-label">match</span>
      </div>
    </div>

    <div class="card-meta">
      <span class="meta-chip"><span class="icon">📍</span>${esc(job.location || 'India')}</span>
      ${job.category ? `<span class="meta-dot"></span><span class="meta-chip">🏷️ ${esc(job.category)}</span>` : ''}
      ${salary       ? `<span class="meta-dot"></span><span class="meta-chip">${esc(salary)}</span>` : ''}
    </div>

    ${tags.length ? `
    <div class="card-tags">
      ${tags.map(t => `<span class="tag">${esc(t)}</span>`).join('')}
    </div>` : ''}

    <div class="card-footer">
      <span class="source-badge ${sourceClass}">${esc(job.source || 'Adzuna')}</span>
      ${posted ? `<span class="posted-time">${esc(posted)}</span>` : ''}
      <div class="card-actions">
        <button
          class="btn-save ${isSaved ? 'saved' : ''}"
          onclick="toggleSave(event, '${esc(job.id)}')"
          title="${isSaved ? 'Unsave' : 'Save'}"
        >${isSaved ? '★ Saved' : '☆ Save'}</button>
        <a
          class="btn-apply"
          href="${esc(job.url)}"
          target="_blank"
          rel="noopener"
          onclick="event.stopPropagation()"
        >Apply →</a>
      </div>
    </div>
  </div>`;
}

// ── Save / Bookmark ─────────────────────────────────────
function toggleSave(event, jobId) {
  event.stopPropagation();
  const wasSaved = savedJobs.has(jobId);
  if (wasSaved) { savedJobs.delete(jobId); } else { savedJobs.add(jobId); }
  localStorage.setItem('savedJobs', JSON.stringify([...savedJobs]));

  // Update button UI
  const card = document.querySelector(`[data-id="${jobId}"]`);
  if (card) {
    const btn = card.querySelector('.btn-save');
    btn.classList.toggle('saved', !wasSaved);
    btn.textContent = !wasSaved ? '★ Saved' : '☆ Save';
  }

  // Async server-side save (best-effort)
  fetch(`${API}/api/jobs/${encodeURIComponent(jobId)}/save?saved=${!wasSaved}`, { method: 'POST' }).catch(() => {});
  showToast(!wasSaved ? '★ Job saved!' : 'Removed from saved');
}

// ── Modal ───────────────────────────────────────────────
function openModal(jobId) {
  const job = allJobs.find(j => j.id === jobId);
  if (!job) return;

  const score     = job.match_score || 0;
  const scoreTier = score >= 70 ? 'high' : score >= 40 ? 'med' : 'low';
  const tags      = Array.isArray(job.tags) ? job.tags : [];
  const desc      = job.description
    ? job.description.replace(/<[^>]*>/g, '').trim()
    : 'No description available.';

  document.getElementById('modalContent').innerHTML = `
    <div class="score-badge score-${scoreTier}" style="margin-bottom:16px; display:inline-flex">
      <span class="score-num">${score}%</span>
      <span class="score-label">match</span>
    </div>
    <div class="modal-job-title">${esc(job.title)}</div>
    <div class="modal-company">
      🏢 ${esc(job.company)}
      ${job.location ? ` &nbsp;·&nbsp; 📍 ${esc(job.location)}` : ''}
      ${job.salary   ? ` &nbsp;·&nbsp; 💰 ${esc(job.salary)}`  : ''}
    </div>

    ${tags.length ? `
    <div class="modal-section">
      <div class="modal-section-label">Matched Skills</div>
      <div class="card-tags">${tags.map(t => `<span class="tag">${esc(t)}</span>`).join('')}</div>
    </div>` : ''}

    <div class="modal-section">
      <div class="modal-section-label">Description</div>
      <div class="modal-desc">${esc(desc)}</div>
    </div>

    <a class="modal-apply-btn" href="${esc(job.url)}" target="_blank" rel="noopener">
      Apply Now →
    </a>
  `;

  document.getElementById('modalOverlay').classList.add('open');
  document.body.style.overflow = 'hidden';
}

function closeModal() {
  document.getElementById('modalOverlay').classList.remove('open');
  document.body.style.overflow = '';
}

document.addEventListener('keydown', e => { if (e.key === 'Escape') closeModal(); });

// ── Error state ────────────────────────────────────────
function showError(msg) {
  const grid = document.getElementById('jobsGrid');
  if (allJobs.length === 0) {
    grid.innerHTML = '';
    document.getElementById('errorState').style.display = 'block';
    document.getElementById('errorMsg').textContent = msg || 'Unknown error';
  }
}

// ── Toast ──────────────────────────────────────────────
let toastTimer = null;
function showToast(msg) {
  const el = document.getElementById('toast');
  el.textContent = msg;
  el.classList.add('show');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => el.classList.remove('show'), 2800);
}

// ── Live timer ─────────────────────────────────────────
function startLiveTimer() {
  setInterval(async () => {
    await loadStats();
  }, 60000);
}

// ── Utilities ──────────────────────────────────────────
function esc(str) {
  return String(str ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function timeAgo(date) {
  if (!(date instanceof Date) || isNaN(date)) return '';
  const diff = Math.floor((Date.now() - date.getTime()) / 1000);
  if (diff < 60)     return `${diff}s ago`;
  if (diff < 3600)   return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400)  return `${Math.floor(diff / 3600)}h ago`;
  return `${Math.floor(diff / 86400)}d ago`;
}
