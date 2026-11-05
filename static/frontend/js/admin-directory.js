(() => {
  const search = document.querySelector('#record-search');
  if (!search) return;
  document.querySelector('#directory-filter').hidden = false;
  search.addEventListener('input', () => {
    const query = search.value.trim().toLocaleLowerCase();
    let results = 0;
    for (const group of document.querySelectorAll('.record-group')) {
      let matches = 0;
      for (const row of group.querySelectorAll('[data-record]')) {
        row.hidden = !(group.dataset.app + ' ' + row.dataset.record).toLocaleLowerCase().includes(query);
        if (!row.hidden) matches++;
      }
      group.hidden = matches === 0;
      results += matches;
    }
    document.querySelector('#directory-empty').hidden = results > 0;
  });
})();
