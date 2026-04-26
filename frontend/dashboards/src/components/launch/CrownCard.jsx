export default function CrownCard({ className = '', children }) {
  const classes = ['launch-card', className].filter(Boolean).join(' ');
  return <section className={classes}>{children}</section>;
}