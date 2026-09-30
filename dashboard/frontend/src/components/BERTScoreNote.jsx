export default function BERTScoreNote() {
  return <p className="metric-note">
    BERTScore measures wording similarity, not factual correctness. A wrong name,
    date, or number can still score highly. See{' '}
    <a href="https://aclanthology.org/2025.acl-long.745/" target="_blank" rel="noopener noreferrer">
      The Mirage of Model Editing
    </a>; use Exact Match or LLM Judge to check the answer.
  </p>
}
