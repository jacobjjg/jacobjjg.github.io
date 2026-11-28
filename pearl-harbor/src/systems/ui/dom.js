// Tiny DOM toolkit + icon set for the HUD.  No innerHTML with external text anywhere: names,
// captions and facts always go through textContent.

/**
 * el('div.ph-x.ph-y', { text, title, on: { click }, data: { k: v }, aria: { label }, attrs: { type } }, child, child, ...)
 */
export function el(spec, props, ...kids) {
  const parts = spec.split('.');
  const node = document.createElement(parts[0] || 'div');
  if (parts.length > 1) node.className = parts.slice(1).join(' ');
  if (props && (props.nodeType || typeof props === 'string' || Array.isArray(props))) { kids.unshift(props); props = null; }
  if (props) {
    if (props.text != null) node.textContent = props.text;
    if (props.title) node.title = props.title;
    if (props.id) node.id = props.id;
    if (props.on) for (const k in props.on) node.addEventListener(k, props.on[k]);
    if (props.data) for (const k in props.data) node.dataset[k] = props.data[k];
    if (props.aria) for (const k in props.aria) node.setAttribute(`aria-${k}`, props.aria[k]);
    if (props.attrs) for (const k in props.attrs) node.setAttribute(k, props.attrs[k]);
    if (props.style) for (const k in props.style) node.style.setProperty(k, props.style[k]);
  }
  for (const k of kids.flat()) {
    if (k == null || k === false) continue;
    node.appendChild(typeof k === 'string' ? document.createTextNode(k) : k);
  }
  return node;
}

/** Set textContent only when it changed (keeps per-frame DOM writes at zero when nothing moves). */
export function setText(node, text) {
  if (node._t !== text) { node._t = text; node.textContent = text; }
}
/** Toggle a class only when the boolean changed. */
export function setClass(node, name, on) {
  const key = `_c_${name}`;
  on = !!on;
  if (node[key] !== on) { node[key] = on; node.classList.toggle(name, on); }
}
/** Set an inline style property only when it changed. */
export function setStyle(node, prop, value) {
  const key = `_s_${prop}`;
  if (node[key] !== value) { node[key] = value; node.style[prop] = value; }
}
export function setAttr(node, name, value) {
  const key = `_a_${name}`;
  if (node[key] !== value) { node[key] = value; node.setAttribute(name, value); }
}

// ---- icons (24 px grid, 1.5 px strokes, currentColor) --------------------------------------
const S = 'fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"';
const ICONS = {
  play: '<path d="M8 5.5v13l10.5-6.5z" fill="currentColor" stroke="none"/>',
  pause: '<path d="M7.5 5.5h3v13h-3zM13.5 5.5h3v13h-3z" fill="currentColor" stroke="none"/>',
  captions: `<rect x="3" y="5.5" width="18" height="13" rx="2" ${S}/><path d="M10.2 10.6a2 2 0 1 0 0 2.8M16.2 10.6a2 2 0 1 0 0 2.8" ${S}/>`,
  voice: `<rect x="9.5" y="3.5" width="5" height="10" rx="2.5" ${S}/><path d="M6 11.5a6 6 0 0 0 12 0M12 17.5v3M9 20.5h6" ${S}/>`,
  sound: `<path d="M4 9.5h3l4.5-4v13l-4.5-4H4z" ${S}/><path d="M15 9a4.2 4.2 0 0 1 0 6M17.6 6.5a7.8 7.8 0 0 1 0 11" ${S}/>`,
  labels: `<path d="M3.5 12.5v-7a1 1 0 0 1 1-1h7l9 9-8 8z" ${S}/><circle cx="8" cy="9" r="1.4" ${S}/>`,
  map: `<path d="M3.5 6.5l5.5-2 6 2 5.5-2v13l-5.5 2-6-2-5.5 2zM9 4.5v13M15 6.5v13" ${S}/>`,
  fullscreen: `<path d="M4 9V4.5h4.5M20 9V4.5h-4.5M4 15v4.5h4.5M20 15v4.5h-4.5" ${S}/>`,
  compass: `<circle cx="12" cy="12" r="8.5" ${S}/><path d="M15.5 8.5l-2 5-5 2 2-5z" ${S}/>`,
  film: `<rect x="3.5" y="5" width="17" height="14" rx="1.5" ${S}/><path d="M7.5 5v14M16.5 5v14M3.5 9.5h4M3.5 14.5h4M16.5 9.5h4M16.5 14.5h4" ${S}/>`,
  help: `<circle cx="12" cy="12" r="8.5" ${S}/><path d="M9.6 9.6a2.5 2.5 0 1 1 3.6 2.2c-.8.5-1.2 1-1.2 2" ${S}/><circle cx="12" cy="16.6" r=".6" fill="currentColor" stroke="none"/>`,
  close: `<path d="M6 6l12 12M18 6L6 18" ${S}/>`,
  target: `<circle cx="12" cy="12" r="5.5" ${S}/><path d="M12 2.5v4M12 17.5v4M2.5 12h4M17.5 12h4" ${S}/>`,
  follow: `<path d="M3.5 12s3.2-6 8.5-6 8.5 6 8.5 6-3.2 6-8.5 6-8.5-6-8.5-6z" ${S}/><circle cx="12" cy="12" r="2.6" ${S}/>`,
  list: `<path d="M8.5 6.5h12M8.5 12h12M8.5 17.5h12" ${S}/><circle cx="4.5" cy="6.5" r=".9" fill="currentColor" stroke="none"/><circle cx="4.5" cy="12" r=".9" fill="currentColor" stroke="none"/><circle cx="4.5" cy="17.5" r=".9" fill="currentColor" stroke="none"/>`,
  plus: `<path d="M12 6v12M6 12h12" ${S}/>`,
  minus: `<path d="M6 12h12" ${S}/>`,
  chevron: `<path d="M9 6l6 6-6 6" ${S}/>`,
  search: `<circle cx="10.5" cy="10.5" r="5.5" ${S}/><path d="M15 15l5 5" ${S}/>`,
};

/** <span class="ph-ico"> holding an inline SVG (static markup from the table above only). */
export function icon(name) {
  const span = document.createElement('span');
  span.className = 'ph-ico';
  span.setAttribute('aria-hidden', 'true');
  span.innerHTML = `<svg viewBox="0 0 24 24" focusable="false">${ICONS[name] || ''}</svg>`;
  return span;
}
export function setIcon(span, name) {
  if (span._icon === name) return;
  span._icon = name;
  span.innerHTML = `<svg viewBox="0 0 24 24" focusable="false">${ICONS[name] || ''}</svg>`;
}

/** An icon button: button.ph-btn[.extra] with a tooltip + aria-label, optional visible text. */
export function button(cls, iconName, label, onClick, text) {
  const b = el(`button.ph-btn${cls ? '.' + cls.split(' ').join('.') : ''}`, { attrs: { type: 'button' }, aria: { label }, title: label });
  if (iconName) { b._ico = icon(iconName); b.appendChild(b._ico); }
  if (text) b.appendChild(el('span.ph-btn-text', { text }));
  if (onClick) b.addEventListener('click', (e) => { e.stopPropagation(); onClick(e); });
  return b;
}

/** A toggle button bound to a boolean getter; call .sync() (cheap) to refresh aria-pressed. */
export function toggle(cls, iconName, label, get, set) {
  const b = button(`ph-toggle ${cls || ''}`.trim(), iconName, label, () => { set(!get()); b.sync(); });
  b.sync = () => { const v = !!get(); if (b._v !== v) { b._v = v; b.setAttribute('aria-pressed', v ? 'true' : 'false'); } };
  b.sync();
  return b;
}

const pad = (n) => String(n).padStart(2, '0');
/** 83.4 -> '1:23', 3723 -> '1:02:03' (documentary time). */
export function fmtRun(sec) {
  const s = Math.max(0, Math.floor(sec));
  const h = Math.floor(s / 3600), m = Math.floor((s % 3600) / 60), ss = s % 60;
  return h ? `${h}:${pad(m)}:${pad(ss)}` : `${m}:${pad(ss)}`;
}

/** 'commandingOfficer' / 'commanding_officer' -> 'Commanding officer'. */
export function prettify(key) {
  const s = String(key).replace(/[_-]+/g, ' ').replace(/([a-z0-9])([A-Z])/g, '$1 $2').trim().toLowerCase();
  return s.charAt(0).toUpperCase() + s.slice(1);
}

export function isTypingTarget(t) {
  return !!t && (t.tagName === 'INPUT' || t.tagName === 'TEXTAREA' || t.tagName === 'SELECT' || t.isContentEditable);
}
