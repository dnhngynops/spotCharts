import styles from './SummaryCards.module.css'

interface Card {
  label: string
  value: string | number | undefined
}

interface Props {
  cards: Card[]
  isLoading: boolean
}

export default function SummaryCards({ cards, isLoading }: Props) {
  return (
    <div className={styles.grid}>
      {cards.map(({ label, value }) => (
        <div key={label} className={styles.card}>
          <div className={styles.value}>
            {isLoading ? <span className={styles.skeleton} /> : value ?? '—'}
          </div>
          <div className={styles.label}>{label}</div>
        </div>
      ))}
    </div>
  )
}
