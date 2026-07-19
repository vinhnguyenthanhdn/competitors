// Run on https://www.toursbylocals.com/tours/vietnam/da-nang (and ?page=2 — only 2 pages exist, 117 tours total)
// via: cat toursbylocals.js | agent-browser eval --stdin --json
(function(){
  const anchors = Array.from(document.querySelectorAll('a[href*="tour-details"]'));
  const seen = {};
  const out = [];
  anchors.forEach(function(a){
    const href = a.getAttribute('href').split('?')[0];
    if (seen[href]) return;
    seen[href] = true;
    const img = a.querySelector('img');
    out.push({ href: href, text: a.innerText, img: img ? img.src : null });
  });
  return JSON.stringify(out);
})()
