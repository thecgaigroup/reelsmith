/* Reelsmith runtime for HyperFrames templates. Deterministic: no Math.random, no Date, no callbacks.
   Everything hangs off one paused GSAP timeline registered as window.__timelines.main. */
(function () {
  const D = JSON.parse(document.getElementById("rs-data").textContent);
  const V = (window.__hyperframes && window.__hyperframes.getVariables) ? (window.__hyperframes.getVariables() || {}) : {};
  const root = document.documentElement;
  // --variables overrides: color_primary etc. and any [data-var] text slot
  ["bg", "fg", "primary", "secondary", "accent", "muted", "surface"].forEach(k => {
    if (V["color_" + k]) root.style.setProperty("--" + k, V["color_" + k]);
  });
  document.querySelectorAll("[data-var]").forEach(el => {
    const v = V[el.dataset.var];
    if (v !== undefined && v !== null && v !== "") el.textContent = v;
  });
  let seed = D.seed || 7;
  const rand = () => { seed = (seed * 1664525 + 1013904223) % 4294967296; return seed / 4294967296; };
  const tl = gsap.timeline({ paused: true });
  const EASE = D.ease || "power3.out";
  const ENTER = {
    rise:   [{ y: "5vmin", opacity: 0 }, { y: 0, opacity: 1 }],
    fall:   [{ y: "-5vmin", opacity: 0 }, { y: 0, opacity: 1 }],
    pop:    [{ scale: 0.55, opacity: 0 }, { scale: 1, opacity: 1, ease: "back.out(1.9)" }],
    slam:   [{ scale: 1.9, opacity: 0 }, { scale: 1, opacity: 1, ease: "power4.out" }],
    left:   [{ x: "-9vmin", opacity: 0 }, { x: 0, opacity: 1 }],
    right:  [{ x: "9vmin", opacity: 0 }, { x: 0, opacity: 1 }],
    blur:   [{ filter: "blur(18px)", opacity: 0, scale: 1.08 }, { filter: "blur(0px)", opacity: 1, scale: 1 }],
    mask:   [{ clipPath: "inset(0% 100% 0% 0%)", opacity: 1 }, { clipPath: "inset(0% 0% 0% 0%)", opacity: 1 }],
    maskup: [{ clipPath: "inset(100% 0% 0% 0%)", yPercent: 30, opacity: 1 }, { clipPath: "inset(0% 0% 0% 0%)", yPercent: 0, opacity: 1 }],
    fade:   [{ opacity: 0 }, { opacity: 1 }],
  };
  function has(sel) { return document.querySelector(sel) !== null; }
  function enter(sel, t, kind, o) {
    if (!has(sel)) return;
    const k = ENTER[kind || "rise"];
    tl.fromTo(sel, Object.assign({}, k[0]), Object.assign({ duration: 0.55, ease: EASE }, k[1], o || {}), t);
  }
  function exit(sel, t, kind, o) {
    if (!has(sel)) return;
    const to = { up: { y: "-4vmin", opacity: 0 }, scale: { scale: 1.08, opacity: 0 }, shrink: { scale: 0.9, opacity: 0 },
                 left: { x: "-10vmin", opacity: 0 }, blur: { filter: "blur(14px)", opacity: 0 } }[kind] || { opacity: 0 };
    tl.to(sel, Object.assign({ duration: 0.3, ease: "power2.in" }, to, o || {}), t);
  }
  // continuous micro-motion so no frame is ever frozen ("nothing fully stops")
  function drift(sel, t, d, o) {
    if (!has(sel)) return;
    o = o || {};
    tl.fromTo(sel, { scale: o.from || 1, x: 0, y: 0 }, { scale: o.to || 1.045, x: o.x || 0, y: o.y || 0, duration: d, ease: "none" }, t);
  }
  function kenburns(sel, t, d, i) {
    if (!has(sel)) return;
    const s = i % 2 ? 1 : -1;
    tl.fromTo(sel, { scale: 1.16, xPercent: -3 * s, yPercent: 1.5 }, { scale: 1.02, xPercent: 3 * s, yPercent: -1.5, duration: d, ease: "none" }, t);
  }
  // slot-machine counter: digits are vertical strips moved with transforms (seek-safe, no onUpdate)
  function roll(sel, t, d, stagger) {
    document.querySelectorAll(sel + " .rs-strip").forEach((el, i, all) => {
      const target = parseInt(el.dataset.to, 10), spins = parseInt(el.dataset.spins || "1", 10);
      const steps = spins * 10 + target;
      tl.fromTo(el, { yPercent: 0 }, { yPercent: -100 * steps / (steps + 1), duration: d, ease: "power3.out" },
        t + (stagger || 0.06) * (all.length - 1 - i));
    });
  }
  // a brand-coloured bar crosses every cut: something always moves through the boundary
  function wipe(t, o) {
    if (!has("#rs-wipe")) return;
    o = o || {};
    const d = o.d || 0.55;
    tl.fromTo("#rs-wipe", { xPercent: -130, opacity: 1 }, { xPercent: 130, opacity: 1, duration: d, ease: "power2.inOut" }, t - d / 2);
  }
  // Background motion. In loop mode (D.loop) every tween is a yoyo so the last frame equals the first.
  function bgDrift(total) {
    const L = !!D.loop, d = L ? total / 2 : total, rep = L ? { repeat: 1, yoyo: true } : {};
    tl.fromTo("#rs-bg", { backgroundPosition: "0% 40%" }, Object.assign({ backgroundPosition: "100% 60%", duration: d, ease: L ? "sine.inOut" : "none" }, rep), 0);
    document.querySelectorAll(".rs-blob").forEach((el, i) => {
      const a = (rand() - 0.5) * 30, b = (rand() - 0.5) * 30;
      tl.fromTo(el, { xPercent: 0, yPercent: 0, scale: 1 }, Object.assign({ xPercent: a, yPercent: b, scale: 1.0 + rand() * 0.35, duration: d, ease: "sine.inOut" }, rep), 0);
    });
    if (has("#rs-grid")) tl.fromTo("#rs-grid", { backgroundPosition: "0px 0px" }, Object.assign({ backgroundPosition: "0px " + (d * 18) + "px", duration: d, ease: L ? "sine.inOut" : "none" }, rep), 0);
  }
  // Camera move on a screenshot/recording: keys = [{t, zoom, x, y}] with x/y focus 0..1 (borrowed idea: eased camera keyframes)
  function camera(sel, t0, keys) {
    if (!has(sel) || !keys || !keys.length) return;
    const el = document.querySelector(sel);
    const cl = (v, m) => Math.max(-m, Math.min(m, v));
    const xf = k => { const z = k.zoom || 1, m = (z - 1) / 2;
      return { scale: z, xPercent: 100 * cl((0.5 - (k.x === undefined ? 0.5 : k.x)) * z, m),
               yPercent: 100 * cl((0.5 - (k.y === undefined ? 0.5 : k.y)) * z, m) }; };
    tl.set(el, xf(keys[0]), t0);
    for (let i = 1; i < keys.length; i++) {
      tl.to(el, Object.assign({ duration: Math.max(0.2, keys[i].t - keys[i - 1].t), ease: "power2.inOut" }, xf(keys[i])), t0 + keys[i - 1].t);
    }
  }
  function finish() {
    window.__timelines = window.__timelines || {};
    window.__timelines["main"] = tl;
    tl.seek(0);
  }
  window.RS = { D, V, tl, rand, enter, exit, drift, kenburns, roll, wipe, bgDrift, finish, has, camera };
})();
