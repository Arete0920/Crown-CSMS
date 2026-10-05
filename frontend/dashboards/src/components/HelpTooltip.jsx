import { useEffect, useId, useRef, useState } from 'react';
import { apiFetch } from '../lib/api';
import SolomonCharacter from './SolomonCharacter';
import './SolomonHelp.css';

/** On-demand governed help. No form values, records or free-text prompts are sent. */
export function HelpTooltip({ slug, context, label = 'Help from Solomon', pose = 'explain' }) {
  const id = useId();
  const dialog = useRef(null);
  const trigger = useRef(null);
  const request = useRef(null);
  const [open, setOpen] = useState(false);
  const [status, setStatus] = useState('idle');
  const [article, setArticle] = useState(null);
  const [introducing, setIntroducing] = useState(false);
  const introductionButton = useRef(null);
  const returnButton = useRef(null);

  useEffect(() => () => request.current?.abort(), []);

  function close() {
    request.current?.abort();
    dialog.current?.close();
    setOpen(false);
    setIntroducing(false);
    trigger.current?.focus();
  }

  async function load() {
    request.current?.abort();
    const controller = new AbortController();
    request.current = controller;
    setArticle(null);
    setStatus('loading');
    const path = slug
      ? `/api/v1/help/${encodeURIComponent(slug)}/`
      : `/api/v1/solomon/context/?${new URLSearchParams(context || {})}`;
    try {
      const response = await apiFetch(path, { signal: controller.signal, validateStatus: status => (status >= 200 && status < 300) || status === 404 });
      if (controller.signal.aborted) return;
      if (response.status === 404) { setStatus('empty'); return; }
      if (!response.ok) throw new Error('Help unavailable');
      const payload = await response.json();
      if (controller.signal.aborted) return;
      const content = slug ? payload : payload.primary_article;
      if (!content?.title || typeof content.content !== 'string') {
        setStatus('empty');
        return;
      }
      setArticle(content);
      setStatus('ready');
    } catch {
      if (!controller.signal.aborted) setStatus('error');
    }
  }

  function show() {
    dialog.current.showModal();
    setOpen(true);
    load();
  }

  return (
    <span className="solomon-help">
      <button ref={trigger} type="button" className="solomon-help-trigger"
        onClick={show} aria-label={label} aria-haspopup="dialog"
        aria-expanded={open} aria-controls={id}>
        <SolomonCharacter />
        <span>Solomon</span>
      </button>
      <dialog ref={dialog} id={id} className="solomon-help-panel"
        aria-labelledby={`${id}-title`} onCancel={close} onClose={() => setOpen(false)}>
        <header className="solomon-help-heading">
          <SolomonCharacter height={88} pose={introducing ? 'guide' : status === 'loading' ? 'review' : status === 'error' ? 'caution' : pose} />
          <div><small>Solomon · CROWN help</small>
            <h2 id={`${id}-title`}>{introducing ? 'Meet Solomon' : article?.title || 'How can I help?'}</h2>
          </div>
          <button type="button" className="solomon-help-close" onClick={close} aria-label="Close help">×</button>
        </header>
        {introducing ? (
          <div className="solomon-help-content">
            <p><strong>Hi, I’m Solomon—your guide to CROWN.</strong></p>
            <p>My name is inspired by the biblical King Solomon and his request for wisdom. I’m here to help you find your way and take the next step with confidence.</p>
            <ul>
              <li><strong>Find your way:</strong> get help navigating CROWN.</li>
              <li><strong>Get answers:</strong> read guidance about the page or task in front of you.</li>
              <li><strong>Take the next step:</strong> find directions for school workflows.</li>
            </ul>
            <p>Whenever you see me beside a help bubble, select me for guidance. Your school’s policies and decisions still guide the work.</p>
          </div>
        ) : (
          <div className="solomon-help-content" aria-live="polite" aria-busy={status === 'loading'}>
            {status === 'loading' && <p>Finding guidance…</p>}
            {status === 'empty' && <p>No published guidance is available for this topic yet. Contact your school administrator for help.</p>}
            {status === 'error' && <><p>Guidance could not be loaded. Please try again.</p><button type="button" onClick={load}>Try again</button></>}
            {status === 'ready' && <p className="solomon-help-article">{article.content}</p>}
          </div>
        )}
        <footer className="solomon-help-footer">
          {introducing ? (
            <button ref={returnButton} type="button" className="solomon-help-link" onClick={() => {
              setIntroducing(false);
              requestAnimationFrame(() => introductionButton.current?.focus());
            }}>Back to page help</button>
          ) : (
            <><span>Published CROWN guidance</span>
              <button ref={introductionButton} type="button" className="solomon-help-link" onClick={() => {
                setIntroducing(true);
                requestAnimationFrame(() => returnButton.current?.focus());
              }}>Meet Solomon</button>
            </>
          )}
        </footer>
      </dialog>
    </span>
  );
}
