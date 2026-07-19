// Run on https://www.airbnb.com/s/<City>/experiences?place_id=...&kg_or_tags[]=Tag:XXXX (base page, per-category-tag,
// or per-city variants — each view hard-caps at ~20 rendered cards, so union many views to grow coverage).
// via: cat airbnb.js | agent-browser eval --stdin --json
(function(){
  const titles = Array.from(document.querySelectorAll('[data-testid="listing-card-title"]'));
  const seen = {};
  const out = [];
  titles.forEach(function(t){
    const id = t.id.replace('title_','');
    if (seen[id]) return;
    seen[id] = true;
    let el = t;
    for (let i=0;i<4;i++){ el = el.parentElement; }
    const imgEl = el.querySelector('picture source, img');
    let img = null;
    if (imgEl) {
      const raw = imgEl.getAttribute('srcset') || imgEl.getAttribute('src') || '';
      img = raw.split(',')[0].trim().split(' ')[0];
    }
    out.push({id: id, title: t.textContent, text: el.innerText, img: img});
  });
  return JSON.stringify(out);
})()
