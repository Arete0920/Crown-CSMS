import PropTypes from 'prop-types';

const ICONS = {
  dashboard: ['M4 4h6v6H4z', 'M14 4h6v6h-6z', 'M4 14h6v6H4z', 'M14 14h6v6h-6z'],
  school: ['M3 10 12 4l9 6', 'M5 9v10h14V9', 'M9 19v-6h6v6', 'M3 20h18'],
  control: ['M4 6h16', 'M7 6v4', 'M4 12h16', 'M15 12v4', 'M4 18h16', 'M10 18v-4'],
  admissions: ['M7 3h10v4H7z', 'M5 5h14v16H5z', 'M8 11h8', 'M8 15h5'],
  academics: ['M3 7 12 3l9 4-9 4z', 'M6 9v6c3 2 9 2 12 0V9', 'M21 7v7'],
  studentLife: ['M12 21s-7-4.4-7-10a4 4 0 0 1 7-2 4 4 0 0 1 7 2c0 5.6-7 10-7 10Z'],
  attendance: ['M7 3v3', 'M17 3v3', 'M4 8h16', 'M5 5h14v16H5z', 'm8 14 2 2 4-5'],
  finance: ['M4 6h16v12H4z', 'M8 10h8', 'M8 14h3', 'M15 14h1'],
  communications: ['M4 5h16v11H8l-4 4z', 'M8 9h8', 'M8 12h5'],
  reports: ['M5 3h10l4 4v14H5z', 'M15 3v5h5', 'M8 12h8', 'M8 16h8'],
  settings: ['M12 15.5a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7Z', 'M19.4 15a1.7 1.7 0 0 0 .34 1.88l.06.06-2.12 2.12-.06-.06a1.7 1.7 0 0 0-1.88-.34 1.7 1.7 0 0 0-1 1.55V20h-3v-.09a1.7 1.7 0 0 0-1-1.55 1.7 1.7 0 0 0-1.88.34l-.06.06-2.12-2.12.06-.06A1.7 1.7 0 0 0 7.1 15a1.7 1.7 0 0 0-1.55-1H5v-3h.55a1.7 1.7 0 0 0 1.55-1 1.7 1.7 0 0 0-.34-1.88l-.06-.06L8.82 5.94l.06.06a1.7 1.7 0 0 0 1.88.34 1.7 1.7 0 0 0 1-1.55V4h3v.79a1.7 1.7 0 0 0 1 1.55 1.7 1.7 0 0 0 1.88-.34l.06-.06 2.12 2.12-.06.06A1.7 1.7 0 0 0 19.4 10a1.7 1.7 0 0 0 1.55 1H21v3h-.05a1.7 1.7 0 0 0-1.55 1Z'],
  chat: ['M5 5h14v10H9l-4 4z', 'M8 9h8', 'M8 12h5'],
  mail: ['M3 5h18v14H3z', 'm4 8 8 5 8-5'],
  calendar: ['M5 4h14v17H5z', 'M8 2v4', 'M16 2v4', 'M5 9h14', 'M9 13h2', 'M13 13h2', 'M9 17h2'],
  document: ['M6 3h8l4 4v14H6z', 'M14 3v5h5', 'M9 12h6', 'M9 16h6'],
  spreadsheet: ['M5 3h14v18H5z', 'M5 9h14', 'M5 15h14', 'M11 3v18'],
  cloud: ['M7 18h11a4 4 0 0 0 .3-7.99A6 6 0 0 0 6.7 8.5 4.8 4.8 0 0 0 7 18Z'],
  help: ['M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18Z', 'M9.8 9a2.4 2.4 0 1 1 3.2 2.26c-.8.36-1 .88-1 1.74', 'M12 17h.01'],
  updates: ['M18 8a6 6 0 1 0 1.2 6', 'M18 4v4h-4'],
  search: ['M11 19a8 8 0 1 0 0-16 8 8 0 0 0 0 16Z', 'm21 21-4.35-4.35'],
  user: ['M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8Z', 'M4 21a8 8 0 0 1 16 0'],
  shield: ['M12 22c5-2 8-6 8-12V5l-8-3-8 3v5c0 6 3 10 8 12Z', 'm9 12 2 2 4-5'],
};

export default function CrownIcon({ name, size = 20, className = '', title }) {
  const paths = ICONS[name] || ICONS.dashboard;
  const labelled = Boolean(title);

  return (
    <svg
      className={`crown-icon ${className}`.trim()}
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden={labelled ? undefined : true}
      role={labelled ? 'img' : undefined}
    >
      {labelled ? <title>{title}</title> : null}
      {paths.map((path) => <path key={path} d={path} />)}
    </svg>
  );
}

CrownIcon.propTypes = {
  name: PropTypes.string.isRequired,
  size: PropTypes.number,
  className: PropTypes.string,
  title: PropTypes.string,
};
