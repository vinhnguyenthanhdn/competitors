// Run on https://www.getyourguide.com/da-nang-l939/ after clicking "Show more" N times
// (each click appends ~15-18 more cards; page passes Cloudflare after a few seconds' wait).
// via: cat getyourguide.js | agent-browser eval --stdin --json
(function(){
  const links = Array.from(document.querySelectorAll('a[href*="da-nang-l939"]'));
  const seen = {};
  const out = [];
  links.forEach(function(a){
    var h = a.getAttribute('href').split('?')[0];
    if (!/-t\d+/.test(h)) return;
    if (seen[h]) return;
    seen[h] = true;
    const img = a.querySelector('img');
    out.push({href: h, text: a.innerText, img: img ? img.src : null});
  });
  return JSON.stringify(out);
})()
