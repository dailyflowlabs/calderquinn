/* ==========================================================================
   CALDER QUINN — OFFICIAL PLATFORM INTERACTIVE SCRIPTS
   Audio Player, Merch Checkout & The Hollow Fan Club
   ========================================================================== */

document.addEventListener('DOMContentLoaded', () => {
  // Navigation scroll effect
  const siteHeader = document.getElementById('siteHeader');
  window.addEventListener('scroll', () => {
    if (window.scrollY > 40) {
      siteHeader.classList.add('scrolled');
    } else {
      siteHeader.classList.remove('scrolled');
    }
  });

  // Mobile menu toggle
  const mobileToggle = document.getElementById('mobileToggle');
  const navMenu = document.getElementById('navMenu');
  if (mobileToggle && navMenu) {
    mobileToggle.addEventListener('click', () => {
      const isVisible = navMenu.style.display === 'flex';
      navMenu.style.display = isVisible ? 'none' : 'flex';
      navMenu.style.flexDirection = 'column';
      navMenu.style.position = 'absolute';
      navMenu.style.top = '80px';
      navMenu.style.left = '0';
      navMenu.style.width = '100%';
      navMenu.style.background = 'rgba(13, 14, 17, 0.98)';
      navMenu.style.padding = '24px';
      navMenu.style.boxShadow = '0 10px 30px rgba(0,0,0,0.8)';
    });
  }

  // Track data & audio engine
  let tracks = [];
  let currentTrackIndex = 0;
  const audio = new Audio();

  const playPauseBtn = document.getElementById('playPauseBtn');
  const playIcon = document.getElementById('playIcon');
  const pauseIcon = document.getElementById('pauseIcon');
  const prevBtn = document.getElementById('prevBtn');
  const nextBtn = document.getElementById('nextBtn');
  const progressBar = document.getElementById('progressBar');
  const progressFill = document.getElementById('progressFill');
  const currentTimeEl = document.getElementById('currentTime');
  const durationEl = document.getElementById('duration');
  const nowPlayingTitle = document.getElementById('nowPlayingTitle');
  const nowPlayingDesc = document.getElementById('nowPlayingDesc');
  const tracklistContainer = document.getElementById('tracklistContainer');

  // Mini Floating Player Elements
  const persistentMiniPlayer = document.getElementById('persistentMiniPlayer');
  const miniPlayerTitle = document.getElementById('miniPlayerTitle');
  const miniPlayerArtist = document.getElementById('miniPlayerArtist');
  const miniPlayerThumb = document.getElementById('miniPlayerThumb');
  const miniPlayBtn = document.getElementById('miniPlayBtn');
  const miniPlayIcon = document.getElementById('miniPlayIcon');
  const miniPauseIcon = document.getElementById('miniPauseIcon');
  const floatingTrackInfo = document.getElementById('floatingTrackInfo');

  function formatTime(seconds) {
    if (isNaN(seconds)) return '0:00';
    const m = Math.floor(seconds / 60);
    const s = Math.floor(seconds % 60);
    return `${m}:${s < 10 ? '0' : ''}${s}`;
  }

  function loadTrack(index) {
    if (!tracks.length) return;
    currentTrackIndex = (index + tracks.length) % tracks.length;
    const track = tracks[currentTrackIndex];
    audio.src = track.file;
    audio.load();

    if (nowPlayingTitle) nowPlayingTitle.textContent = track.title;
    if (nowPlayingDesc) nowPlayingDesc.textContent = track.description;

    if (miniPlayerTitle) miniPlayerTitle.textContent = track.title;
    if (miniPlayerArtist) miniPlayerArtist.textContent = 'Calder Quinn • ' + (track.vibe || 'Debut Album');

    document.querySelectorAll('.track-row').forEach((row, i) => {
      row.classList.toggle('active', i === currentTrackIndex);
    });
  }

  function togglePlay() {
    if (audio.paused) {
      audio.play().then(() => {
        updatePlayState(true);
      }).catch(err => {
        console.warn('Playback error:', err);
      });
    } else {
      audio.pause();
      updatePlayState(false);
    }
  }

  function updatePlayState(isPlaying) {
    if (playIcon && pauseIcon) {
      playIcon.style.display = isPlaying ? 'none' : 'block';
      pauseIcon.style.display = isPlaying ? 'block' : 'none';
    }
    if (miniPlayIcon && miniPauseIcon) {
      miniPlayIcon.style.display = isPlaying ? 'none' : 'block';
      miniPauseIcon.style.display = isPlaying ? 'block' : 'none';
    }
    if (miniPlayerThumb) {
      if (isPlaying) {
        miniPlayerThumb.classList.add('spinning');
      } else {
        miniPlayerThumb.classList.remove('spinning');
      }
    }
    if (persistentMiniPlayer) {
      if (isPlaying) {
        persistentMiniPlayer.classList.add('visible');
      }
    }
  }

  if (playPauseBtn) playPauseBtn.addEventListener('click', togglePlay);
  if (prevBtn) prevBtn.addEventListener('click', () => {
    loadTrack(currentTrackIndex - 1);
    audio.play();
    updatePlayState(true);
  });
  if (nextBtn) nextBtn.addEventListener('click', () => {
    loadTrack(currentTrackIndex + 1);
    audio.play();
    updatePlayState(true);
  });

  if (miniPlayBtn) {
    miniPlayBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      togglePlay();
    });
  }

  if (floatingTrackInfo) {
    floatingTrackInfo.addEventListener('click', () => {
      const musicSec = document.getElementById('music');
      if (musicSec) musicSec.scrollIntoView({ behavior: 'smooth' });
    });
  }

  // Time & Progress Updates
  audio.addEventListener('timeupdate', () => {
    if (audio.duration) {
      const pct = (audio.currentTime / audio.duration) * 100;
      if (progressFill) progressFill.style.width = `${pct}%`;
      if (currentTimeEl) currentTimeEl.textContent = formatTime(audio.currentTime);
      if (durationEl) durationEl.textContent = formatTime(audio.duration);
    }
  });

  audio.addEventListener('loadedmetadata', () => {
    if (durationEl) durationEl.textContent = formatTime(audio.duration);
  });

  audio.addEventListener('ended', () => {
    loadTrack(currentTrackIndex + 1);
    audio.play();
    updatePlayState(true);
  });

  if (progressBar) {
    progressBar.addEventListener('click', (e) => {
      const rect = progressBar.getBoundingClientRect();
      const clickPos = (e.clientX - rect.left) / rect.width;
      if (audio.duration) {
        audio.currentTime = clickPos * audio.duration;
      }
    });
  }

  // Fetch track list
  fetch('/data/tracks.json')
    .then(res => res.json())
    .then(data => {
      tracks = data;
      renderTracklist();
      loadTrack(0);
    })
    .catch(err => {
      console.error('Could not load tracks:', err);
    });

  function renderTracklist() {
    if (!tracklistContainer) return;
    tracklistContainer.innerHTML = '';
    tracks.forEach((t, idx) => {
      const row = document.createElement('div');
      row.className = `track-row ${idx === 0 ? 'active' : ''}`;
      const trackNum = (idx + 1) < 10 ? '0' + (idx + 1) : String(idx + 1);
      row.innerHTML = `
        <div class="track-info">
          <span class="track-index">${trackNum}</span>
          <div>
            <span class="track-name">${t.title}</span>
            <span class="track-vibe">${t.vibe}</span>
          </div>
        </div>
        <span class="track-duration">${t.duration}</span>
      `;
      row.addEventListener('click', () => {
        loadTrack(idx);
        audio.play();
        updatePlayState(true);
      });
      tracklistContainer.appendChild(row);
    });
  }

  // Hero CTA quick action
  const heroListenBtn = document.getElementById('heroListenBtn');
  if (heroListenBtn) {
    heroListenBtn.addEventListener('click', () => {
      const musicEl = document.getElementById('music');
      if (musicEl) musicEl.scrollIntoView({ behavior: 'smooth' });
      togglePlay();
    });
  }

  // ========================================================================
  // Custom Modal (Strictly Zero window.alert / window.confirm)
  // ========================================================================
  const modalBackdrop = document.getElementById('customModalBackdrop');
  const modalTitle = document.getElementById('modalTitle');
  const modalBody = document.getElementById('modalBody');
  const modalCloseBtn = document.getElementById('modalCloseBtn');

  window.showCustomDialog = function(title, message) {
    if (modalBackdrop && modalTitle && modalBody) {
      modalTitle.textContent = title;
      modalBody.innerHTML = `<p style="text-align: center; color: var(--text-secondary);">${message}</p>`;
      const actions = document.querySelector('.modal-actions');
      if (actions) {
        actions.innerHTML = '<button class="btn btn-primary" id="modalCloseBtn">Got it</button>';
        document.getElementById('modalCloseBtn').addEventListener('click', () => {
          modalBackdrop.classList.remove('active');
        });
      }
      modalBackdrop.classList.add('active');
    }
  };

  if (modalCloseBtn && modalBackdrop) {
    modalCloseBtn.addEventListener('click', () => {
      modalBackdrop.classList.remove('active');
    });
  }

  if (modalBackdrop) {
    modalBackdrop.addEventListener('click', (e) => {
      if (e.target === modalBackdrop) {
        modalBackdrop.classList.remove('active');
      }
    });
  }

  // ========================================================================
  // Merch Modal & Checkout
  // ========================================================================
  window.openMerchModal = function(productId) {
    fetch('/api/merch/products')
      .then(res => res.json())
      .then(products => {
        const product = products.find(p => p.id === productId || String(p.id) === String(productId));
        if (!product) {
          window.showCustomDialog('Provisioner Notice', 'Item details could not be loaded at this moment.');
          return;
        }

        const availableVariants = (product.variants && product.variants.length > 0)
          ? product.variants.filter(v => v.is_available !== false)
          : [];

        const variantOptions = availableVariants.map(v => `
          <option value="${v.id}">${v.title || 'Standard'} — $${(v.price / 100).toFixed(2)} USD</option>
        `).join('');

        const displayImg = product.images && product.images.length > 0
          ? (typeof product.images[0] === 'string' ? product.images[0] : (product.images[0]?.src || ''))
          : '';

        modalTitle.textContent = product.title;
        modalBody.innerHTML = `
          <div style="display: flex; flex-direction: column; gap: 1.25rem; text-align: left;">
            <div style="display: flex; gap: 1.25rem; align-items: center; flex-wrap: wrap;">
              <img src="${displayImg}" alt="${product.title}" style="width: 100px; height: 100px; border-radius: 8px; object-fit: cover; border: 1px solid var(--border-amber); background: #14161b;">
              <div style="flex: 1;">
                <p style="font-size: 0.9rem; color: var(--text-secondary); line-height: 1.4;">${product.description}</p>
              </div>
            </div>

            <div style="display: flex; flex-direction: column; gap: 0.5rem;">
              <label style="font-size: 0.8rem; font-weight: 700; color: var(--amber-primary); text-transform: uppercase; letter-spacing: 0.1em;">Select Option / Size:</label>
              <select id="merchVariantSelect" style="padding: 10px 14px; border-radius: 6px; background: var(--bg-surface); color: var(--text-primary); border: 1px solid var(--border-amber); font-size: 0.95rem; outline: none; width: 100%;">
                ${variantOptions}
              </select>
            </div>

            <p style="font-size: 0.8rem; color: var(--text-muted); text-align: center;">Hand-printed on demand and shipped with live tracking.</p>
          </div>
        `;

        const actions = document.querySelector('.modal-actions');
        if (actions) {
          actions.innerHTML = `
            <button class="btn btn-secondary" id="modalCancelBtn">Cancel</button>
            <button class="btn btn-primary" id="confirmOrderBtn">Proceed to Checkout</button>
          `;

          document.getElementById('modalCancelBtn').addEventListener('click', () => {
            modalBackdrop.classList.remove('active');
          });

          const confirmBtn = document.getElementById('confirmOrderBtn');
          confirmBtn.addEventListener('click', () => {
            const variantId = document.getElementById('merchVariantSelect').value;
            confirmBtn.disabled = true;
            confirmBtn.textContent = 'Opening Checkout...';

            fetch('/api/merch/checkout', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ productId: product.id, variantId: variantId, quantity: 1 })
            })
              .then(res => res.json())
              .then(data => {
                if (data.url) {
                  window.location.href = data.url;
                } else {
                  modalTitle.textContent = 'Store Notice';
                  modalBody.innerHTML = `<p style="text-align: center; color: var(--text-secondary);">${data.error || 'Checkout is momentarily unavailable.'}</p>`;
                  actions.innerHTML = `<button class="btn btn-primary" id="modalGotItBtn">Understood</button>`;
                  document.getElementById('modalGotItBtn').addEventListener('click', () => {
                    modalBackdrop.classList.remove('active');
                  });
                }
              })
              .catch(err => {
                confirmBtn.disabled = false;
                confirmBtn.textContent = 'Proceed to Checkout';
                console.error(err);
              });
          });
        }

        modalBackdrop.classList.add('active');
      })
      .catch(err => {
        console.error(err);
        window.showCustomDialog('Provisioner Notice', 'Unable to load merchandise at this time.');
      });
  };

  // ========================================================================
  // Fan Club Signup
  // ========================================================================
  const newsletterForm = document.getElementById('newsletterForm');
  if (newsletterForm) {
    newsletterForm.addEventListener('submit', (e) => {
      e.preventDefault();
      const emailInput = document.getElementById('newsletterEmail');
      const email = emailInput ? emailInput.value.trim() : '';
      if (!email) return;

      const submitBtn = document.getElementById('newsletterSubmitBtn');
      if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.textContent = 'Joining...';
      }

      fetch('/api/newsletter', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: email })
      })
        .then(res => res.json())
        .then(data => {
          if (emailInput) emailInput.value = '';
          if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.textContent = 'Join The Hollow';
          }
          window.showCustomDialog('The Hollow Club', data.message || "You're in. Keep the light on.");
        })
        .catch(err => {
          if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.textContent = 'Join The Hollow';
          }
          window.showCustomDialog('Notice', 'Unable to sign up right now. Please try again later.');
        });
    });
  }
});
