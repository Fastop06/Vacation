/* =========================================================
   MY PERFECT VACATION · ZERMATT
   Навигация + переход с пролетающим самолётом
   ========================================================= */
(function () {
  'use strict';

  var stage    = document.getElementById('stage');
  var slides   = Array.prototype.slice.call(document.querySelectorAll('.slide'));
  var flyover  = document.getElementById('flyover');
  var curtain  = document.getElementById('curtain');
  var cloudField = document.getElementById('cloudField');
  var flights  = document.getElementById('flights');
  var plane    = document.getElementById('plane');

  var N = slides.length;
  var index = 0;
  var busy = false;
  var reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ---------- 1. ФОТОГРАФИИ ---------- */
  (function loadPhotos() {
    Array.prototype.forEach.call(document.querySelectorAll('.ph[data-img]'), function (el) {
      var img = new Image();
      img.alt = '';
      img.decoding = 'async';
      img.className = 'photo';
      img.src = 'images/' + el.dataset.img + '.jpg';
      img.addEventListener('load', function () { el.classList.add('has-photo'); });
      img.addEventListener('error', function () { img.remove(); });
      el.insertBefore(img, el.firstChild);
    });
  })();

  /* ---------- 2. ОБЛАКА И СЛЕД ---------- */
  function rnd(a, b) { return a + Math.random() * (b - a); }

  var COLS = 9, ROWS = 7;
  for (var c = 0; c < COLS; c++) {
    for (var r = 0; r < ROWS; r++) {
      var b = document.createElement('i');
      b.style.width  = rnd(26, 46) + 'vw';
      b.style.height = rnd(15, 27) + 'vh';
      b.style.left = (-8 + c * (176 / COLS) + rnd(-4, 4)) + 'vw';
      b.style.top  = (-26 + r * (152 / ROWS) + rnd(-3.5, 3.5)) + 'vh';
      b.style.opacity = rnd(0.6, 1);
      var roll = Math.random();
      if (roll > 0.74) b.className = 'shade';
      else if (roll > 0.6) b.className = 'pine';
      cloudField.appendChild(b);
    }
  }
  var core = document.createElement('i');
  core.style.cssText =
    'left:-12vw;top:-24vh;width:192vw;height:150vh;border-radius:6vw;filter:blur(1px);' +
    'background:radial-gradient(58% 58% at 50% 46%, rgba(255,255,255,.99) 0%, rgba(247,250,248,.96) 55%, rgba(233,240,236,.92) 100%)';
  cloudField.insertBefore(core, cloudField.firstChild);

  for (var i = 0; i < 22; i++) {
    var f = document.createElement('i');
    var sz = rnd(2, 5);
    f.style.width = f.style.height = sz + 'px';
    f.style.top = rnd(4, 96) + 'vh';
    flights.appendChild(f);
  }
  var flakes = Array.prototype.slice.call(flights.children);
  var seed = flakes.map(function () {
    return { dx: rnd(24, 110), dy: rnd(-22, 22), sp: rnd(.5, 1.5) };
  });

  /* ---------- 3. ВСПОМОГАТЕЛЬНОЕ ---------- */
  function sweep(u) { return u * 0.74 + (u * u * (3 - 2 * u)) * 0.26; }

  /* ---------- 4. МАСШТАБ ПОД ОКНО ---------- */
  function fitOne(slide) {
    var inner = slide.querySelector('.inner');
    if (!inner) return;
    inner.style.transform = '';
    var cs = getComputedStyle(slide);
    var availW = slide.clientWidth -
      parseFloat(cs.paddingLeft) - parseFloat(cs.paddingRight);
    var availH = slide.clientHeight -
      parseFloat(cs.paddingTop) - parseFloat(cs.paddingBottom);
    var k = Math.min(1, availW / Math.max(1, inner.scrollWidth),
                        availH / Math.max(1, inner.scrollHeight));
    k = Math.max(0.4, k);
    inner.style.transform = 'scale(' + k.toFixed(4) + ')';
  }
  function fitAll() { slides.forEach(fitOne); }

  /* ---------- 5. ПОКАЗ СЛАЙДА ---------- */
  function showSlide(i) {
    slides.forEach(function (s) { s.classList.remove('active', 'leaving'); });
    index = i;
    slides[index].classList.add('active');
    fitOne(slides[index]);
    if (history.replaceState) history.replaceState(null, '', '#' + (index + 1));
  }

  /* ---------- 6. САМОЛЁТ ---------- */
  var DURATION = 1240;
  var SWEEP = 172;

  function fly(dir, nextIndex) {
    if (busy) return;
    busy = true;
    flyover.classList.add('run');

    var swapped = false, t0 = null;

    function frame(ts) {
      if (t0 === null) t0 = ts;
      var t = Math.min(1, (ts - t0) / DURATION);
      var e = sweep(t);

      var cu = e < 0.5 ? -SWEEP * (1 - e * 2) : SWEEP * ((e - 0.5) * 2);
      curtain.style.transform = 'translate3d(' + cu.toFixed(2) + 'vw,0,0)';

      if (!swapped && e >= 0.5) { swapped = true; showSlide(nextIndex); }

      var px = -26 + 152 * e;
      var py = 36 + 20 * Math.sin(Math.PI * t * 1.05) - 12 * t;
      var rot = -3 - 11 * Math.sin(Math.PI * t) + Math.sin(t * 26) * 1.6;
      var sc = 0.88 + 0.4 * t;
      var op = t > 0.9 ? Math.max(0, (1 - t) / 0.1) : 1;

      plane.style.transform =
        'translate3d(' + px.toFixed(2) + 'vw,' + py.toFixed(2) + 'vh,0) rotate(' +
        rot.toFixed(2) + 'deg) scale(' + sc.toFixed(3) + ')';
      plane.style.opacity = op;

      var fade = Math.sin(Math.PI * Math.min(1, t * 1.08));
      for (var k = 0; k < flakes.length; k++) {
        var s = seed[k];
        flakes[k].style.transform =
          'translate3d(' + (px - s.dx + Math.sin(t * 9 + k) * 4).toFixed(2) + 'vw,' +
          (s.dy + (k / flakes.length) * 96 + Math.cos(t * 7 + k * .7) * 5 + t * 6 * s.sp).toFixed(2) + 'vh,0)';
        flakes[k].style.opacity = (fade * .5).toFixed(2);
      }

      if (t < 1) requestAnimationFrame(frame);
      else { flyover.classList.remove('run'); busy = false; }
    }
    requestAnimationFrame(frame);
  }

  /* ---------- 7. НАВИГАЦИЯ ---------- */
  function go(i) {
    if (i < 0 || i >= N || i === index) return;
    if (reduced) { showSlide(i); return; }
    fly(i > index ? 1 : -1, i);
  }
  function next() { if (index < N - 1) go(index + 1); }
  function prev() { if (index > 0) go(index - 1); }

  document.addEventListener('keydown', function (e) {
    if (e.metaKey || e.ctrlKey || e.altKey) return;
    switch (e.key) {
      case 'ArrowRight': case 'PageDown': case ' ': case 'Enter':
        e.preventDefault(); next(); break;
      case 'ArrowLeft': case 'PageUp': case 'Backspace':
        e.preventDefault(); prev(); break;
      case 'Home': e.preventDefault(); go(0); break;
      case 'End':  e.preventDefault(); go(N - 1); break;
    }
  });

  stage.addEventListener('click', function (e) { next(); });

  var lock = 0, acc = 0;
  window.addEventListener('wheel', function (e) {
    var now = Date.now();
    if (busy || now < lock) return;
    acc += e.deltaY;
    if (Math.abs(acc) > 42) { lock = now + 780; acc > 0 ? next() : prev(); acc = 0; }
  }, { passive: true });

  var tx = 0, ty = 0;
  window.addEventListener('touchstart', function (e) {
    tx = e.changedTouches[0].clientX; ty = e.changedTouches[0].clientY;
  }, { passive: true });
  window.addEventListener('touchend', function (e) {
    var dx = e.changedTouches[0].clientX - tx, dy = e.changedTouches[0].clientY - ty;
    if (Math.abs(dx) > 60 && Math.abs(dx) > Math.abs(dy)) dx < 0 ? next() : prev();
  }, { passive: true });

  /* ---------- 8. СТАРТ ---------- */
  var start = 0;
  var h = parseInt((location.hash || '').replace('#', ''), 10);
  if (h >= 1 && h <= N) start = h - 1;
  showSlide(start);
  fitAll();

  if (document.fonts && document.fonts.ready) document.fonts.ready.then(fitAll);
  window.addEventListener('load', function () { setTimeout(fitAll, 60); });

  var rz;
  window.addEventListener('resize', function () {
    clearTimeout(rz);
    rz = setTimeout(function () {
      fitAll();
      if (!busy) curtain.style.transform = 'translate3d(' + SWEEP + 'vw,0,0)';
    }, 140);
  });
})();
