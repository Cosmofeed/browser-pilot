// DOM Compression Engine for browser-pilot
// Extracts interactive + text elements, assigns indices, returns compact representation
// Runs inside Chrome via evaluate_script

(() => {
  const INTERACTIVE_TAGS = new Set(['A', 'BUTTON', 'INPUT', 'SELECT', 'TEXTAREA', 'DETAILS', 'SUMMARY']);
  const INTERACTIVE_ROLES = new Set(['button', 'link', 'menuitem', 'tab', 'checkbox', 'radio', 'switch', 'slider', 'spinbutton', 'combobox', 'listbox', 'option', 'searchbox', 'textbox', 'menu', 'menubar', 'tablist']);
  const TEXT_TAGS = new Set(['H1', 'H2', 'H3', 'H4', 'H5', 'H6', 'P', 'SPAN', 'LABEL', 'TD', 'TH', 'LI', 'CAPTION', 'FIGCAPTION']);
  const SKIP_TAGS = new Set(['SCRIPT', 'STYLE', 'NOSCRIPT', 'SVG', 'PATH', 'META', 'LINK', 'BR', 'HR']);

  function isVisible(el) {
    if (!el.offsetParent && el.tagName !== 'BODY' && el.tagName !== 'HTML') return false;
    const style = window.getComputedStyle(el);
    if (style.display === 'none' || style.visibility === 'hidden' || style.opacity === '0') return false;
    const rect = el.getBoundingClientRect();
    if (rect.width === 0 && rect.height === 0) return false;
    return true;
  }

  function isInteractive(el) {
    if (INTERACTIVE_TAGS.has(el.tagName)) return true;
    const role = el.getAttribute('role');
    if (role && INTERACTIVE_ROLES.has(role)) return true;
    if (el.getAttribute('onclick') || el.getAttribute('tabindex') !== null) return true;
    if (el.getAttribute('contenteditable') === 'true') return true;
    const cursor = window.getComputedStyle(el).cursor;
    if (cursor === 'pointer') return true;
    return false;
  }

  function getElementText(el) {
    // Get direct text, not children's text
    let text = '';
    for (const child of el.childNodes) {
      if (child.nodeType === Node.TEXT_NODE) {
        text += child.textContent.trim() + ' ';
      }
    }
    text = text.trim();
    if (!text) {
      // Fallback to aria-label, title, placeholder, alt
      text = el.getAttribute('aria-label') || el.getAttribute('title') ||
             el.getAttribute('placeholder') || el.getAttribute('alt') ||
             el.getAttribute('value') || '';
    }
    // For inputs, show current value
    if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') {
      const val = el.value;
      if (val) text = `value="${val}" ${text}`;
    }
    return text.trim().substring(0, 80);
  }

  function getElementDescriptor(el) {
    const tag = el.tagName.toLowerCase();
    const role = el.getAttribute('role');
    const type = el.getAttribute('type');
    const href = el.getAttribute('href');
    const id = el.getAttribute('id');
    const name = el.getAttribute('name');

    let parts = [];
    if (role) parts.push(role);
    else if (tag === 'input') parts.push(type || 'text');
    else parts.push(tag);

    const text = getElementText(el);
    if (text) parts.push(`"${text}"`);
    if (href && href.length < 80 && !href.startsWith('javascript:')) parts.push(`href=${href}`);
    if (id) parts.push(`id=${id}`);
    if (el.disabled) parts.push('[disabled]');
    if (el.checked) parts.push('[checked]');

    return parts.join(' ');
  }

  function getSelector(el) {
    if (el.id) return `#${CSS.escape(el.id)}`;

    // Try aria-label
    const ariaLabel = el.getAttribute('aria-label');
    if (ariaLabel) return `[aria-label="${CSS.escape(ariaLabel)}"]`;

    // Try role + text
    const role = el.getAttribute('role');
    if (role) {
      const text = getElementText(el);
      if (text) return `[role="${role}"]`;
    }

    // Build path
    const parts = [];
    let current = el;
    while (current && current !== document.body) {
      let selector = current.tagName.toLowerCase();
      if (current.id) {
        selector = `#${CSS.escape(current.id)}`;
        parts.unshift(selector);
        break;
      }
      const parent = current.parentElement;
      if (parent) {
        const siblings = [...parent.children].filter(c => c.tagName === current.tagName);
        if (siblings.length > 1) {
          const idx = siblings.indexOf(current) + 1;
          selector += `:nth-of-type(${idx})`;
        }
      }
      parts.unshift(selector);
      current = current.parentElement;
    }
    return parts.join(' > ');
  }

  // Walk the DOM
  const elements = [];
  let index = 0;
  const seen = new Set();

  function walk(node, depth) {
    if (depth > 15) return; // Max depth
    if (!node || !node.tagName) return;
    if (SKIP_TAGS.has(node.tagName)) return;
    if (seen.has(node)) return;
    seen.add(node);

    try {
      if (!isVisible(node)) return;
    } catch (e) {
      return;
    }

    const interactive = isInteractive(node);
    const isTextEl = TEXT_TAGS.has(node.tagName);
    const text = getElementText(node);

    if (interactive && text) {
      index++;
      elements.push({
        idx: index,
        type: 'interactive',
        desc: getElementDescriptor(node),
        selector: getSelector(node),
        tag: node.tagName.toLowerCase(),
        rect: node.getBoundingClientRect()
      });
    } else if (isTextEl && text && text.length > 1) {
      // Only include text elements with meaningful content
      elements.push({
        idx: null,
        type: 'text',
        desc: `${node.tagName.toLowerCase()}: "${text}"`,
        tag: node.tagName.toLowerCase()
      });
    } else if (node.tagName === 'TABLE') {
      // Extract table as structured text
      const rows = [];
      node.querySelectorAll('tr').forEach(tr => {
        const cells = [...tr.querySelectorAll('td, th')].map(c => c.innerText.trim().substring(0, 50));
        if (cells.length > 0 && cells.some(c => c.length > 0)) {
          rows.push(cells.join(' | '));
        }
      });
      if (rows.length > 0) {
        elements.push({
          idx: null,
          type: 'table',
          desc: `table (${rows.length} rows):\n${rows.slice(0, 20).join('\n')}`,
          tag: 'table'
        });
        return; // Don't walk into table children
      }
    }

    // Walk children
    for (const child of node.children) {
      walk(child, depth + 1);
    }
  }

  walk(document.body, 0);

  // Build output
  const lines = [];
  lines.push(`Page: ${document.title}`);
  lines.push(`URL: ${window.location.href}`);
  lines.push(`---`);

  for (const el of elements) {
    if (el.type === 'interactive') {
      lines.push(`[${el.idx}] ${el.desc}`);
    } else if (el.type === 'table') {
      lines.push(el.desc);
    } else {
      lines.push(`    ${el.desc}`);
    }
  }

  lines.push(`---`);
  lines.push(`${index} interactive elements found`);

  return {
    compressed: lines.join('\n'),
    elementCount: index,
    selectors: Object.fromEntries(
      elements
        .filter(e => e.type === 'interactive')
        .map(e => [e.idx, e.selector])
    )
  };
})()
