import { useEffect, useState } from 'react'

/**
 * Returns a neon color based on probability (0–1).
 * ≥65% → electric green, ≥45% → cyan, ≥30% → amber, <30% → red
 */
function probaColor(value) {
  if (value >= 0.65) return '#00ff88'
  if (value >= 0.45) return '#00ccff'
  if (value >= 0.30) return '#ffcc00'
  return '#ff5566'
}

/**
 * Animated probability bar with counter.
 *
 * @param {string}  label    - Row label (e.g. "DOMICILE")
 * @param {number}  value    - Probability 0–1
 * @param {number}  delay    - Animation delay in ms
 * @param {number}  barHeight - Bar height in px (default 4)
 */
export default function PredictionBar({ label, value, delay = 0, barHeight = 4 }) {
  const [filled, setFilled] = useState(false)
  const [count, setCount] = useState(0)
  const pct = Math.round((value ?? 0) * 100)
  const color = probaColor(value ?? 0)

  useEffect(() => {
    let intervalId
    const timerId = setTimeout(() => {
      setFilled(true)
      let current = 0
      const step = pct / 60          // 60 frames over ~1s
      intervalId = setInterval(() => {
        current += step
        if (current >= pct) {
          setCount(pct)
          clearInterval(intervalId)
        } else {
          setCount(Math.floor(current))
        }
      }, 1000 / 60)
    }, delay)

    return () => {
      clearTimeout(timerId)
      if (intervalId) clearInterval(intervalId)
    }
  }, [pct, delay])

  return (
    <div style={{ marginBottom: '14px' }}>
      {/* Label + value */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'baseline',
          marginBottom: '6px',
        }}
      >
        <span
          style={{
            fontFamily: 'var(--font-ui)',
            fontSize: '11px',
            fontWeight: 500,
            letterSpacing: '0.1em',
            textTransform: 'uppercase',
            color: 'var(--text-secondary)',
          }}
        >
          {label}
        </span>
        <span
          style={{
            fontFamily: 'var(--font-mono)',
            fontSize: '17px',
            fontWeight: 700,
            color,
            textShadow: filled ? `0 0 12px ${color}55` : 'none',
            minWidth: '46px',
            textAlign: 'right',
            transition: 'text-shadow 0.3s ease',
          }}
        >
          {count}%
        </span>
      </div>

      {/* Bar track */}
      <div
        style={{
          height: `${barHeight}px`,
          background: 'var(--border)',
          borderRadius: `${barHeight}px`,
          overflow: 'hidden',
          position: 'relative',
        }}
      >
        <div
          style={{
            height: '100%',
            width: filled ? `${pct}%` : '0%',
            background: color,
            borderRadius: `${barHeight}px`,
            transition: `width 1s cubic-bezier(0.4, 0, 0.2, 1)`,
            boxShadow: `0 0 8px ${color}66`,
          }}
        />
      </div>
    </div>
  )
}
