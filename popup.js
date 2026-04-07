const extractBtn = document.getElementById('extractBtn');
const downloadBtn = document.getElementById('downloadBtn');
const output = document.getElementById('output');
const statusEl = document.getElementById('status');

let lastResult = null;

function htmlToMarkdown(html) {
  const temp = document.createElement('div');
  temp.innerHTML = html;

  temp.querySelectorAll('script,style,noscript,svg').forEach((n) => n.remove());

  temp.querySelectorAll('h1,h2,h3,h4,h5,h6').forEach((h) => {
    const level = Number(h.tagName[1]);
    h.textContent = `${'#'.repeat(level)} ${h.textContent}`;
  });

  temp.querySelectorAll('a').forEach((a) => {
    const href = a.getAttribute('href') || '';
    a.textContent = href ? `[${a.textContent}](${href})` : a.textContent;
  });

  temp.querySelectorAll('li').forEach((li) => {
    li.textContent = `- ${li.textContent}`;
  });

  return temp.innerText.replace(/\n{3,}/g, '\n\n').trim();
}

function cleanText(html) {
  const temp = document.createElement('div');
  temp.innerHTML = html;
  temp.querySelectorAll('script,style,noscript,svg,footer,nav').forEach((n) => n.remove());
  return temp.innerText.replace(/\s+/g, ' ').trim();
}

extractBtn.addEventListener('click', async () => {
  statusEl.textContent = 'Extracting...';
  output.value = '';

  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab?.id) {
    statusEl.textContent = 'No active tab found.';
    return;
  }

  const [{ result }] = await chrome.scripting.executeScript({
    target: { tabId: tab.id },
    func: () => ({
      title: document.title,
      url: location.href,
      raw_html: document.documentElement.outerHTML,
    }),
  });

  const payload = {
    status: 'ok',
    method_used: 'chrome-active-tab-dom',
    title: result.title,
    url: result.url,
    raw_html: result.raw_html,
    clean_text: cleanText(result.raw_html),
    markdown: htmlToMarkdown(result.raw_html),
    extracted_at: new Date().toISOString(),
  };

  lastResult = payload;
  output.value = JSON.stringify(payload, null, 2);
  statusEl.textContent = 'Done.';
});

downloadBtn.addEventListener('click', async () => {
  if (!lastResult) {
    statusEl.textContent = 'Run extraction first.';
    return;
  }

  const blob = new Blob([JSON.stringify(lastResult, null, 2)], {
    type: 'application/json',
  });
  const url = URL.createObjectURL(blob);

  await chrome.downloads.download({
    url,
    filename: 'llm-dom-extract.json',
    saveAs: true,
  });

  statusEl.textContent = 'Downloaded JSON.';
});
