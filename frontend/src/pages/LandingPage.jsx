import { useState } from 'react'
import { Link } from 'react-router-dom'
import landingVideo from '../assets/landing_page.mp4'

export default function LandingPage() {
  const [showDashboardLink, setShowDashboardLink] = useState(false)

  return (
    <main className="landing-page">
      <video
        className="landing-video"
        src={landingVideo}
        autoPlay
        muted
        playsInline
        onEnded={() => setShowDashboardLink(true)}
        onError={() => setShowDashboardLink(true)}
      />

      <div className={`landing-action ${showDashboardLink ? 'visible' : ''}`}>
        <Link to="/dashboard" className="landing-link">
          View Dashboard
        </Link>
      </div>
    </main>
  )
}
