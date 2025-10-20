// Reveal on scroll for elements with .reveal
(function () {
  const items = document.querySelectorAll('.reveal');
  if (!items.length) return;
  const io = new IntersectionObserver((entries) => {
    entries.forEach((e) => {
      if (e.isIntersecting) {
        e.target.classList.add('show');
        io.unobserve(e.target);
      }
    });
  }, { threshold: 0.12 });
  items.forEach((el) => io.observe(el));
})();

// Client-side filtering enhancements on index page
(function () {
  const form = document.querySelector('.search-form');
  if (!form) return;
  const qInput = form.querySelector('input[name="q"]');
  const catSelect = form.querySelector('select[name="category"]');
  const cards = Array.from(document.querySelectorAll('.grid .card'));

  function matches(card, q, cat) {
    const name = card.getAttribute('data-name') || '';
    const desc = card.getAttribute('data-desc') || '';
    const category = card.getAttribute('data-category') || '';
    const qok = !q || name.includes(q) || desc.includes(q) || category.includes(q);
    const cok = !cat || category === cat;
    return qok && cok;
  }

  function filter() {
    const q = (qInput?.value || '').trim().toLowerCase();
    const cat = (catSelect?.value || '').trim().toLowerCase();
    let visible = 0;
    cards.forEach((c) => {
      const show = matches(c, q, cat);
      c.style.display = show ? '' : 'none';
      if (show) visible++;
    });
    // Optionally, could show a "no results" message if none visible
  }

  qInput?.addEventListener('input', filter);
  catSelect?.addEventListener('change', filter);
})();

// Drag-and-drop image upload with preview on upload page
(function () {
  const dz = document.getElementById('dropzone');
  if (!dz) return;
  const input = document.getElementById('image-input');
  const preview = document.getElementById('image-preview');
  const instructions = dz.querySelector('.dz-instructions');

  function showPreview(file) {
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (e) => {
      preview.src = e.target.result;
      preview.style.display = 'block';
      if (instructions) instructions.style.display = 'none';
    };
    reader.readAsDataURL(file);
  }

  dz.addEventListener('click', () => input?.click());

  input?.addEventListener('change', (e) => {
    const file = e.target.files && e.target.files[0];
    showPreview(file);
  });

  ['dragenter', 'dragover'].forEach((ev) => {
    dz.addEventListener(ev, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dz.classList.add('dragover');
    });
  });
  ['dragleave', 'drop'].forEach((ev) => {
    dz.addEventListener(ev, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dz.classList.remove('dragover');
    });
  });
  dz.addEventListener('drop', (e) => {
    const dt = e.dataTransfer;
    if (!dt || !dt.files || !dt.files.length) return;
    const file = dt.files[0];
    // Assign to input so it submits with form
    const dataTransfer = new DataTransfer();
    dataTransfer.items.add(file);
    input.files = dataTransfer.files;
    showPreview(file);
  });
})();

// Modal Quick View for products on Buy page
(function () {
  const modal = document.getElementById('product-modal');
  if (!modal) return;
  const backdrop = modal.querySelector('.modal-backdrop');
  const closeBtn = modal.querySelector('.modal-close');
  const prevBtn = modal.querySelector('[data-prev]');
  const nextBtn = modal.querySelector('[data-next]');
  const mImg = document.getElementById('m-img');
  const mTitle = document.getElementById('m-title');
  const mCat = document.getElementById('m-category');
  const mPrice = document.getElementById('m-price');
  const mDesc = document.getElementById('m-desc');
  const mContact = document.getElementById('m-contact');
  const mView = document.getElementById('m-view');

  function openModal() { modal.setAttribute('aria-hidden', 'false'); document.body.style.overflow = 'hidden'; }
  function closeModal() { modal.setAttribute('aria-hidden', 'true'); document.body.style.overflow = ''; }

  [backdrop, closeBtn].forEach((el) => el && el.addEventListener('click', closeModal));
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closeModal();
    if (e.key === 'ArrowLeft') go(-1);
    if (e.key === 'ArrowRight') go(1);
  });

  // Delegate clicks on cards
  const grid = document.querySelector('.grid');
  if (!grid) return;
  const cards = Array.from(document.querySelectorAll('.grid .card[data-id]'));
  let currentIndex = -1;

  async function loadById(id) {
    const res = await fetch(`/api/product/${id}`);
    if (!res.ok) throw new Error('Failed to fetch product');
    const p = await res.json();
    mImg.src = p.image_url; mImg.alt = p.name;
    mTitle.textContent = p.name;
    mCat.textContent = p.category;
    mPrice.textContent = `₹ ${Number(p.price).toFixed(2)}`;
    mDesc.textContent = p.description;
    mContact.href = `mailto:${p.seller_email}`;
    if (p.status === 'sold') { mContact.setAttribute('aria-disabled', 'true'); mContact.style.pointerEvents = 'none'; mContact.style.opacity = '.6'; } else { mContact.removeAttribute('aria-disabled'); mContact.style.pointerEvents = ''; mContact.style.opacity = ''; }
    mView.href = `/product/${p.id}`;
  }

  function go(delta) {
    if (!cards.length) return;
    currentIndex = (currentIndex + delta + cards.length) % cards.length;
    const id = cards[currentIndex].getAttribute('data-id');
    loadById(id).catch(() => {});
  }

  prevBtn && prevBtn.addEventListener('click', () => go(-1));
  nextBtn && nextBtn.addEventListener('click', () => go(1));

  grid.addEventListener('click', async (e) => {
    const hit = e.target.closest('.card-hit');
    if (!hit) return;
    const card = hit.closest('.card');
    const id = card?.getAttribute('data-id');
    if (!id) return;
    e.preventDefault();
    try {
      // set current index for nav
      currentIndex = cards.findIndex((c) => c === card);
      await loadById(id);
      openModal();
    } catch (err) {
      console.error(err);
      // fallback: navigate to details
      window.location.href = hit.getAttribute('href');
    }
  });

  // Subtle parallax on image
  const media = document.querySelector('.modal-media');
  if (media) {
    media.addEventListener('mousemove', (e) => {
      const rect = media.getBoundingClientRect();
      const x = (e.clientX - rect.left) / rect.width - 0.5;
      const y = (e.clientY - rect.top) / rect.height - 0.5;
      mImg.style.transform = `scale(1.03) translate3d(${x * 8}px, ${y * 8}px, 0)`;
    });
    media.addEventListener('mouseleave', () => {
      mImg.style.transform = '';
    });
  }
})();