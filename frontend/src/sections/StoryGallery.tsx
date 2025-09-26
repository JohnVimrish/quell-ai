const stories = [
  {
    file: "story-01.png",
    caption: "Every VIP caller rings through immediately, while others are greeted by the copilot.",
  },
  {
    file: "story-02.png",
    caption: "Summaries and action items drop into your workspace without opening another app.",
  },
  {
    file: "story-03.png",
    caption: "Quell respects your schedule—no unexpected after-hours disruptions.",
  },
];

export default function StoryGallery() {
  return (
    <section className="section-padding storytelling-gallery">
      {stories.map(({ file, caption }) => (
        <article key={file} className="story-item">
          <img src={new URL(`../assets/images/${file}`, import.meta.url).href} alt="Story" />
          <div className="story-caption">
            <p>{caption}</p>
          </div>
        </article>
      ))}
    </section>
  );
}
