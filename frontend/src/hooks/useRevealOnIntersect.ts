import { useEffect, useRef } from "react";
import usePrefersReducedMotion from "./usePrefersReducedMotion";

export type RevealOptions = {
  threshold?: number;
  rootMargin?: string;
  once?: boolean;
  onReveal?: () => void;
};

export default function useRevealOnIntersect<T extends HTMLElement>({
  threshold = 0.2,
  rootMargin = "0px",
  once = true,
  onReveal,
}: RevealOptions = {}) {
  const elementRef = useRef<T | null>(null);
  const prefersReducedMotion = usePrefersReducedMotion();

  useEffect(() => {
    const node = elementRef.current;
    if (!node) return;

    if (prefersReducedMotion) {
      node.classList.add("is-visible");
      onReveal?.();
      return;
    }

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-visible");
            onReveal?.();
            if (once) {
              observer.unobserve(entry.target);
            }
          }
        });
      },
      {
        threshold,
        rootMargin,
      },
    );

    observer.observe(node);

    return () => {
      observer.disconnect();
    };
  }, [prefersReducedMotion, threshold, rootMargin, once, onReveal]);

  return elementRef;
}
