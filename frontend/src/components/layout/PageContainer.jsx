export default function PageContainer({ children, className = '' }) {
  return <section className={`page-shell ${className}`.trim()}>{children}</section>
}
