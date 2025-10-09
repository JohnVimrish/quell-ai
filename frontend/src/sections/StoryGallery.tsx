const stories = [
  { file: "story-01.png", caption: "Every VIP caller rings through immediately, while others are greeted by the copilot." },
  { file: "story-02.png", caption: "Summaries and action items drop into your workspace without opening another app." },
  { file: "story-03.png", caption: "Quell respects your schedule—no unexpected after-hours disruptions." },
  { file: "story-04.png", caption: "Call transcripts arrive pre-tagged so your team can focus on decisions, not logistics." },
  { file: "story-05.png", caption: "Share wrap-ups instantly with stakeholders in a polished, branded format." },
];

function publicRefUrl(name: string) {
  // Vite serves files placed in frontend/public at the site root
  return `${import.meta.env.BASE_URL}reference_images/${name}`;
}

export default function StoryGallery() {
  return (
    <section className="section-padding storytelling-gallery">
      {stories.map(({ file, caption }) => {
        const fallback = new URL(`../assets/images/${file}`, import.meta.url).href;
        const primary = publicRefUrl(file);
        return (
          <article key={file} className="story-item">
            <img
              src={primary}
              onError={(e) => {
                const target = e.currentTarget as HTMLImageElement;
                if (target.src !== fallback) target.src = fallback;
              }}
              alt={caption}
              loading="lazy"
              decoding="async"
            />
            <div className="story-caption">
              <p>{caption}</p>
            </div>
          </article>
        );
      })}
    </section>
  );
}
