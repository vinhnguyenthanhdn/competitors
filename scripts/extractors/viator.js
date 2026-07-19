// Run on https://www.viator.com/Da-Nang/d4680-ttd or /Da-Nang/d4680-ttd/<page> (77 pages exist, ~40-50 unique/page)
// via: cat viator.js | agent-browser eval --stdin --json
(function(){
  const links = Array.from(document.querySelectorAll('a[href*="/tours/"]'));
  const seen = {};
  const out = [];
  links.forEach(function(a){
    var h = a.getAttribute('href');
    if (!/-\d+P\d+/.test(h)) return;
    if (seen[h]) return;
    seen[h] = true;
    const img = a.querySelector('img');
    out.push({href: h, text: a.innerText, img: img ? (img.src || img.getAttribute('data-src')) : null});
  });
  return JSON.stringify(out);
})()
