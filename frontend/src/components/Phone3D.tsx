
import { useState, useRef } from "react";

export default function Phone3D() {
  const [isPlaying, setIsPlaying] = useState(false);
  const videoRef = useRef<HTMLVideoElement>(null);

  const handlePlayPause = () => {
    if (videoRef.current) {
      if (isPlaying) {
        videoRef.current.pause();
      } else {
        videoRef.current.play();
      }
      setIsPlaying(!isPlaying);
    }
  };

  return (
    <div className="phone-3d-container">
      <div className="phone-3d-screen">
        <video
          ref={videoRef}
          className="phone-3d-video"
          loop
          playsInline
          onPlay={() => setIsPlaying(true)}
          onPause={() => setIsPlaying(false)}
        >
          {/* Placeholder video - replace with actual video URL */}
          <source src="/assets/videos/demo-placeholder.mp4" type="video/mp4" />
          {/* Fallback to YouTube iframe if local video not available */}
        </video>
        
        {!isPlaying && (
          <div 
            className="video-play-overlay"
            onClick={handlePlayPause}
          >
            <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
              <path d="M8 5v14l11-7z"/>
            </svg>
          </div>
        )}
      </div>
    </div>
  );
}