import React from "react";

/**
 * CrownLayout – app shell with sidebar + main content area.
 *
 * Props:
 *   title    – page heading (h2)
 *   subtitle – secondary line under heading (muted)
 *   right    – JSX slotted to the top-right of the page header
 *   children – page body
 */
export default function CrownLayout({ title, subtitle, right, children, mainClassName = "" }) {
  return (
    <div className="crown-app">
      <aside className="crown-sidebar">
        <h1>Crown</h1>
        <div className="crown-badge">Demo / Internal</div>
        <div
          style={{
            marginTop: 16,
            opacity: 0.9,
            fontSize: 12,
            lineHeight: 1.5,
          }}
        >
          Strong. Secure. School-ready.
        </div>
        <nav style={{ marginTop: 24, display: 'flex', flexDirection: 'column', gap: 2 }}>
          {[
            { href: '/admin',       label: 'Administration' },
            { href: '/board',       label: 'School Board'   },
            { href: '/finance',     label: 'Finance'        },
            { href: '/financial-aid', label: 'Financial Aid' },
            { href: '/admissions',  label: 'Admissions'    },
            { href: '/academics',   label: 'Academics'     },
            { href: '/billing',     label: 'Billing'       },
            { href: '/integrity',   label: 'System Integrity' },
          ].map(({ href, label }) => (
            <a
              key={href}
              href={href}
              style={{
                display: 'block',
                padding: '5px 10px',
                borderRadius: 5,
                fontSize: 13,
                color: window.location.pathname === href ? '#fff' : 'rgba(255,255,255,0.72)',
                background: window.location.pathname === href ? 'rgba(255,255,255,0.15)' : 'transparent',
                fontWeight: window.location.pathname === href ? 700 : 400,
                textDecoration: 'none',
                transition: 'background 0.1s',
              }}
            >
              {label}
            </a>
          ))}
        </nav>
      </aside>

      <main className={`crown-main ${mainClassName}`.trim()}>
        {(title || subtitle || right) && (
          <div className="crown-pagehead">
            <div>
              {title && <h2 className="crown-title">{title}</h2>}
              {subtitle && <p className="crown-subtitle">{subtitle}</p>}
            </div>
            {right && <div>{right}</div>}
          </div>
        )}
        {children}
      </main>
    </div>
  );
}
