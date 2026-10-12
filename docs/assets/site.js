// Progressive enhancement: every project, locale and category works without JS.
const list = document.querySelector('.project-list');
if (list) {
  const search = document.querySelector('#search');
  const clear = document.querySelector('.clear-search');
  const rows = [...list.querySelectorAll('.project')];
  document.querySelector('.search').hidden = false;
  function update() {
    const query = search.value.trim().toLocaleLowerCase();
    let count = 0;
    for (const row of rows) {
      row.hidden = !row.dataset.search.includes(query);
      if (!row.hidden) count++;
    }
    document.querySelector('.result-count').textContent = `${count} ${list.dataset.works}`;
    document.querySelector('.empty-state').hidden = count > 0;
    clear.hidden = !search.value;
  }
  search.addEventListener('input', update);
  clear.addEventListener('click', () => { search.value = ''; update(); search.focus(); });
}

const shots = [...document.querySelectorAll('.screenshot-link')];
const dialog = document.querySelector('.lightbox');
if (dialog && typeof dialog.showModal === 'function' && shots.length) {
  let current = 0;
  let gallery = [];
  let trigger;
  function show(index) {
    current = (index + gallery.length) % gallery.length;
    const shot = gallery[current];
    const image = dialog.querySelector('img');
    image.src = shot.href;
    image.alt = shot.dataset.caption;
    dialog.querySelector('.lightbox-caption').textContent = shot.dataset.caption;
    dialog.querySelector('.lightbox-count').textContent = `${current + 1} / ${gallery.length}`;
    dialog.querySelector('.previous-shot').hidden = gallery.length < 2;
    dialog.querySelector('.next-shot').hidden = gallery.length < 2;
  }
  shots.forEach((shot, index) => shot.addEventListener('click', event => {
    event.preventDefault();
    trigger = shot;
    gallery = shots.filter(item => item.dataset.gallery === shot.dataset.gallery);
    show(gallery.indexOf(shot));
    dialog.showModal();
  }));
  dialog.querySelector('.close-lightbox').addEventListener('click', () => dialog.close());
  dialog.querySelector('.previous-shot').addEventListener('click', () => show(current - 1));
  dialog.querySelector('.next-shot').addEventListener('click', () => show(current + 1));
  dialog.addEventListener('keydown', event => {
    if (event.key === 'ArrowLeft') { event.preventDefault(); show(current - 1); }
    if (event.key === 'ArrowRight') { event.preventDefault(); show(current + 1); }
  });
  dialog.addEventListener('click', event => { if (event.target === dialog) dialog.close(); });
  dialog.addEventListener('close', () => trigger?.focus());
}

// Failed remote captures remain explicit, rather than showing a broken image.
document.querySelectorAll('img').forEach(image => {
  function missing() {
    const fallback = document.createElement('div');
    fallback.className = 'missing-cover';
    const title = document.createElement('span');
    title.textContent = image.alt;
    const message = document.createElement('span');
    message.textContent = document.documentElement.lang === 'ja' ? '画像を読み込めませんでした' : 'Image could not be loaded';
    fallback.append(title, message);
    image.replaceWith(fallback);
  }
  // The dialog image has no src until a screenshot is opened.
  if (!image.closest('dialog')) {
    image.addEventListener('error', missing, { once: true });
    if (image.complete && image.getAttribute('src') && !image.naturalWidth) missing();
  }
});
