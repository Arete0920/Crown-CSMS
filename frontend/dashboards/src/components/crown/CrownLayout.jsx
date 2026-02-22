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
        <nav style={{ marginTop: 24, display: 'flex', flexDirection: 'column', gap: 0 }}>
          {[
            { group: 'Operations' },
            { href: '/admin',                   label: 'Administration'       },
            { href: '/board',                   label: 'School Board'         },
            { href: '/finance',                 label: 'Finance'              },
            { href: '/office',                  label: 'Office / HR'          },
            { href: '/it',                      label: 'IT'                   },
            { href: '/facilities',              label: 'Facilities'           },
            { href: '/transportation',          label: 'Transportation'       },
            { href: '/communications-director', label: 'Communications'       },
            { href: '/pd',                      label: 'PD / Staff Dev'       },
            { group: 'Safety & Student Services' },
            { href: '/health',                  label: 'Health / Nurse'       },
            { href: '/counseling',              label: 'Counseling'           },
            { href: '/security',                label: 'Security'             },
            { href: '/food',                    label: 'Food Services'        },
            { group: 'Student Life' },
            { href: '/teacher',                 label: 'Teacher'              },
            { href: '/parent',                  label: 'Parent'               },
            { href: '/student',                 label: 'Student'              },
            { href: '/athletics',               label: 'Athletics'            },
            { href: '/fine-arts',               label: 'Fine Arts'            },
            { href: '/spiritual-life',          label: 'Spiritual Life'       },
            { group: 'Academics & Records' },
            { href: '/academic-support',        label: 'Academic Support'     },
            { href: '/library',                 label: 'Library'              },
            { href: '/registrar',               label: 'Registrar'            },
            { href: '/extended-care',           label: 'Extended Care'        },
            { group: 'Enrollment & Revenue' },
            { href: '/admissions',              label: 'Admissions'           },
            { href: '/financial-aid',           label: 'Financial Aid'        },
            { href: '/marketing',               label: 'Marketing'            },
            { href: '/advancement',             label: 'Advancement'          },
            { href: '/student-services',        label: 'Student Services'     },
            { href: '/billing',                 label: 'Billing'              },
            { group: 'System' },
            { href: '/integrity',               label: 'System Integrity'     },
          ].map((item, i) => {
            if (item.group) {
              return (
                <div key={`g-${i}`} style={{
                  fontSize: 9, fontWeight: 800, letterSpacing: 1.2,
                  textTransform: 'uppercase', color: 'rgba(255,255,255,0.35)',
                  padding: '10px 10px 2px', marginTop: 4,
                }}>
                  {item.group}
                </div>
              );
            }
            const active = window.location.pathname === item.href;
            return (
              <a
                key={item.href}
                href={item.href}
                style={{
                  display: 'block',
                  padding: '5px 10px',
                  borderRadius: 5,
                  fontSize: 13,
                  color: active ? '#fff' : 'rgba(255,255,255,0.72)',
                  background: active ? 'rgba(255,255,255,0.15)' : 'transparent',
                  fontWeight: active ? 700 : 400,
                  textDecoration: 'none',
                  transition: 'background 0.1s',
                }}
              >
                {item.label}
              </a>
            );
          })}
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
