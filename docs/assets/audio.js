(() => {
  const script = document.currentScript;
  const root = new URL('../', script.src);
  const link = Array.from(document.querySelectorAll('a[href]')).find(a =>
    /(?:^|\/)narration\/\d{4}-\d{2}-\d{2}-(?:0600|1200|2200)\.txt$/.test(a.getAttribute('href')));
  if (!link) return;
  const issue = link.getAttribute('href').match(/(\d{4}-\d{2}-\d{2}-\d{4})\.txt$/)[1];
  const section = document.createElement('section');
  section.className = 'audio-player';
  section.setAttribute('aria-label', 'この号の音声');
  const heading = document.createElement('h2');
  heading.textContent = '音声で聴く';
  const status = document.createElement('p');
  status.textContent = '音声は準備中です。';
  status.setAttribute('role', 'status');
  section.append(heading, status);
  link.closest('p').after(section);
  let attempts = 0;
  async function update() {
    attempts++;
    try {
      const response = await fetch(new URL(`audio/${issue}.json`, root), {cache: 'no-store'});
      if (response.ok) {
        const state = await response.json();
        if (state.issue_id !== issue) return;
        if (state.status === 'skipped') {
          status.textContent = 'この号は音声なしでお届けします。';
          return;
        }
        if (state.status === 'ready' && state.file === `${issue}.mp3`) {
          const url = new URL(`audio/${state.file}`, root);
          const check = await fetch(url, {method: 'HEAD', cache: 'no-store'});
          if (check.ok) {
            status.remove();
            const player = document.createElement('audio');
            player.controls = true;
            player.preload = 'none';
            player.src = url.href;
            player.setAttribute('aria-label', `${issue}号の音声`);
            player.style.width = '100%';
            const download = document.createElement('a');
            download.href = url.href;
            download.download = state.file;
            download.textContent = 'MP3をダウンロード';
            const paragraph = document.createElement('p');
            paragraph.append(download);
            section.append(player, paragraph);
            return;
          }
        }
      }
    } catch (_) { /* Articles remain readable while audio is unavailable. */ }
    if (attempts < 30) window.setTimeout(update, 10000);
    else status.textContent = '音声の準備状況を確認できませんでした。しばらくしてからページを開き直してください。';
  }
  update();
})();
