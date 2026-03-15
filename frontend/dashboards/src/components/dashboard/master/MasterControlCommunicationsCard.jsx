import CommunicationsCard from '../CommunicationsCard.jsx';

export default function MasterControlCommunicationsCard() {
  const rows = [
    { title: 'School Success Update', detail: 'Weekly school summary drafted' },
    { title: 'Support Notice', detail: 'Billing FAQ communication prepared' },
    { title: 'Executive Memo', detail: 'Platform growth update ready to send' },
  ];

  return (
    <CommunicationsCard
      title="Support and Communications"
      rightLabel="Open Support"
      messages={rows}
    />
  );
}
