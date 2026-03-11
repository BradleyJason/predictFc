import { useEffect, useState } from 'react'

function gaugeColor(score) {
  if (score >= 70) return '#00ff88'
  if (score >= 50) return '#ffcc00'
  return '#ff5566'
}

/**
 * Animated horizontal confidence gauge (0–100).
 */
export default function ConfidenceGauge({ score }) {
  const [filled, setFilled] = useState(false)
  const [count, setCount] = useState(0)
  const color = gaugeColor(score)

  useEffect(() => {
    let intervalId
    const timerId = setTimeout(() => {
      setFilled(true)
      let current = 0
      const step = score / 60
      intervalId = setInterval(() => {
        current += step
        if (current >= score) {
          setCount(score)
          clearInterval(intervalId)
        } else {
          setCount(Math.floor(current))
        }
      }, 1000 / 60)
    }, 900)   // longer delay: appears after prediction bars

    return () => {
      clearTimeout(timerId)
      if (intervalId) clearInterval(intervalId)
    }
  }, [score])

  return (
    <div>
      {/* Label + big number */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '12px',
        }}
      >
        <div>
          <div
            style={{
              fontFamily: 'var(--font-ui)',
              fontSize: '11px',
              fontWeight: 500,
              letterSpacing: '0.12em',
              textTransform: 'uppercase',
              color: 'var(--text-muted)',
              marginBottom: '2px',
            }}
          >
            INDICE DE CONFIANCE
          </div>
          <div
            style={{
              fontFamily: 'var(--font-mono)',
              fontSize: '10px',
              color: 'var(--text-muted)',
              letterSpacing: '0.08em',
            }}
          >
            QUALITÉ DES DONNÉES · STABILITÉ · COHÉRENCE
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'baseline', gap: '2px' }}>
          <span
            style={{
              fontFamily: 'var(--font-mono)',
              fontSize: '42px',
              fontWeight: 700,
              color,
              textShadow: filled ? `0 0 24px ${color}55` : 'none',
              lineHeight: 1,
              transition: 'text-shadow 0.3s ease',
            }}
          >
            {count}
          </span>
          <span
            style={{
              fontFamily: 'var(--font-mono)',
              fontSize: '16px',
              fontWeight: 400,
              color: 'var(--text-muted)',
              lineHeight: 1,
              alignSelf: 'flex-end',
              marginBottom: '4px',
            }}
          >
            /100
          </span>
        </div>
      </div>

      {/* Gauge bar */}
      <div
        style={{
          height: '8px',
          background: 'var(--border)',
          borderRadius: '4px',
          overflow: 'hidden',
        }}
      >
        <div
          style={{
            height: '100%',
            width: filled ? `${score}%` : '0%',
            background: `linear-gradient(90deg, ${color}88, ${color})`,
            borderRadius: '4px',
            transition: 'width 1.5s cubic-bezier(0.4, 0, 0.2, 1)',
            boxShadow: `0 0 12px ${color}55`,
          }}
        />
      </div>

      {/* Tick marks */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          marginTop: '6px',
        }}
      >
        {[0, 25, 50, 75, 100].map((tick) => (
          <span
            key={tick}
            style={{
              fontFamily: 'var(--font-mono)',
              fontSize: '9px',
              color: 'var(--text-muted)',
              letterSpacing: '0.04em',
            }}
          >
            {tick}
          </span>
        ))}
      </div>
    </div>
  )
}
