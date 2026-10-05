import guide from '../assets/solomon/guide.webp';
import explain from '../assets/solomon/explain.webp';
import review from '../assets/solomon/review.webp';
import caution from '../assets/solomon/caution.webp';
import success from '../assets/solomon/success.webp';

const poses = { guide, explain, review, caution, success };

/** Decorative artwork: the surrounding control or heading supplies accessible text. */
export default function SolomonCharacter({ pose = 'guide', height = 48 }) {
  return <img src={poses[pose] || guide} alt="" width={Math.round(height * .52)} height={height} />;
}
