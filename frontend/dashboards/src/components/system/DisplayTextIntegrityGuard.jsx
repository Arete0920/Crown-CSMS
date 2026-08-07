import { useEffect } from 'react';
import { normalizeDisplayText } from '../../utils/displayTextIntegrity.js';

const NORMALIZED_ATTRIBUTES = ['aria-label', 'title', 'placeholder', 'alt'];
const NORMALIZED_ATTRIBUTE_SELECTOR = NORMALIZED_ATTRIBUTES
  .map((attribute) => `[${attribute}]`)
  .join(',');

function normalizeTextNode(node) {
  if (!node || node.nodeType !== Node.TEXT_NODE) return;
  const current = node.nodeValue || '';
  const normalized = normalizeDisplayText(current);
  if (normalized !== current) node.nodeValue = normalized;
}

function normalizeElementAttributes(element) {
  if (!element || element.nodeType !== Node.ELEMENT_NODE) return;

  NORMALIZED_ATTRIBUTES.forEach((attribute) => {
    if (!element.hasAttribute(attribute)) return;
    const current = element.getAttribute(attribute) || '';
    const normalized = normalizeDisplayText(current);
    if (normalized !== current) element.setAttribute(attribute, normalized);
  });
}

function normalizeSubtree(root) {
  if (!root) return;

  if (root.nodeType === Node.TEXT_NODE) {
    normalizeTextNode(root);
    return;
  }

  if (root.nodeType === Node.ELEMENT_NODE) {
    normalizeElementAttributes(root);
  }

  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
  let node = walker.nextNode();
  while (node) {
    normalizeTextNode(node);
    node = walker.nextNode();
  }

  if (root.querySelectorAll) {
    root.querySelectorAll(NORMALIZED_ATTRIBUTE_SELECTOR)
      .forEach(normalizeElementAttributes);
  }
}

export default function DisplayTextIntegrityGuard() {
  useEffect(() => {
    const root = document.getElementById('root');
    if (!root) return undefined;

    normalizeSubtree(root);

    const observer = new MutationObserver((records) => {
      records.forEach((record) => {
        if (record.type === 'characterData') {
          normalizeTextNode(record.target);
          return;
        }

        if (record.type === 'attributes') {
          normalizeElementAttributes(record.target);
          return;
        }

        record.addedNodes.forEach(normalizeSubtree);
      });
    });

    observer.observe(root, {
      subtree: true,
      childList: true,
      characterData: true,
      attributes: true,
      attributeFilter: NORMALIZED_ATTRIBUTES,
    });

    return () => observer.disconnect();
  }, []);

  return null;
}
