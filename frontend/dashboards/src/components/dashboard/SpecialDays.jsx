import CrownCard from '../crown/CrownCard.jsx';

export default function SpecialDays() {
  return (
    <CrownCard title="Birthdays and Special Days">
      <ul style={{ margin: 0, paddingLeft: 16, color: 'var(--crown-muted)', fontSize: 13, lineHeight: 1.9 }}>
        <li>Emily Carter - Grade 6</li>
        <li>Mr Johnson - Teacher</li>
        <li>Faculty Anniversary - 5 Years</li>
      </ul>
    </CrownCard>
  );
}
