// Explicit imports ensure stable URLs across dev/build
import story01 from "../assets/images/story-01.png";
import story02 from "../assets/images/story-02.png";
import story03 from "../assets/images/story-03.png";
import story04 from "../assets/images/story-04.png";
import story05 from "../assets/images/story-05.png";

const imageMap: Record<string, string> = {
  "story-01.png": story01,
  "story-02.png": story02,
  "story-03.png": story03,
  "story-04.png": story04,
  "story-05.png": story05,
};

const stories = [
  { file: "story-01.png", caption: "Every VIP caller rings through immediately, while others are greeted by the copilot." },
  { file: "story-02.png", caption: "Summaries and action items drop into your workspace without opening another app." },
  { file: "story-03.png", caption: "Quell respects your schedule—no unexpected after-hours disruptions." },
  { file: "story-04.png", caption: "Call transcripts arrive pre-tagged so your team can focus on decisions, not logistics." },
  { file: "story-05.png", caption: "Share wrap-ups instantly with stakeholders in a polished, branded format." },
];

export default function StoryGallery() {
  return (
    <section className="section-padding storytelling-gallery">
      {stories.map(({ file, caption }) => {
        const src = imageMap[file];
        return (
          <article key={file} className="story-item">
            <img
              src={src}
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
