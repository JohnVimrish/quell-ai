export default function FloatingOrbs() {
  return (
    <>
      <style>
        {`
          .floating-orb {
            position: fixed;
            border-radius: 50%;
            pointer-events: none;
            z-index: 0;
            filter: blur(60px);
            opacity: 0.3;
            animation: orb-float 25s ease-in-out infinite;
          }

          .orb-1 {
            width: 400px;
            height: 400px;
            background: radial-gradient(circle, var(--color-orange-400), var(--color-orange-600));
            top: 15%;
            right: 10%;
            animation-delay: 0s;
          }

          .orb-2 {
            width: 350px;
            height: 350px;
            background: radial-gradient(circle, var(--color-green-400), var(--color-green-600));
            bottom: 20%;
            left: 15%;
            animation-delay: -8s;
          }

          .orb-3 {
            width: 300px;
            height: 300px;
            background: radial-gradient(circle, var(--color-orange-300), var(--color-green-400));
            top: 50%;
            left: 50%;
            animation-delay: -15s;
          }

          @keyframes orb-float {
            0%, 100% {
              transform: translate(0, 0) scale(1);
            }
            25% {
              transform: translate(50px, -50px) scale(1.1);
            }
            50% {
              transform: translate(-30px, 30px) scale(0.9);
            }
            75% {
              transform: translate(40px, -20px) scale(1.05);
            }
          }

          @media (prefers-reduced-motion: reduce) {
            .floating-orb {
              animation: none;
            }
          }
        `}
      </style>
      <div className="floating-orb orb-1" aria-hidden="true" />
      <div className="floating-orb orb-2" aria-hidden="true" />
      <div className="floating-orb orb-3" aria-hidden="true" />
    </>
  );
}

