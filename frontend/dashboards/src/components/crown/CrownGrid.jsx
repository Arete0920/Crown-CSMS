import React from 'react';

/**
 * CrownGrid – 12-column grid wrapper.
 *
 * Usage:
 *   <CrownGrid>
 *     <Col span={3}><CrownMetricCard ... /></Col>
 *     <Col span={12}><CrownCard ...>content</CrownCard></Col>
 *   </CrownGrid>
 */
export function CrownGrid({ children }) {
  return <div className="crown-grid">{children}</div>;
}

/**
 * Col – grid column, span 3/4/6/8/12.
 */
export function Col({ span = 12, children }) {
  const cls =
    span === 3  ? 'crown-col-3' :
    span === 4  ? 'crown-col-4' :
    span === 6  ? 'crown-col-6' :
    span === 8  ? 'crown-col-8' :
                  'crown-col-12';
  return <div className={cls}>{children}</div>;
}
