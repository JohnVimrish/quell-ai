declare module "flipbook-viewer" {
  export interface FlipbookPageAsset {
    img: HTMLImageElement;
    num: number;
    width: number;
    height: number;
  }

  export interface FlipbookBook {
    numPages: () => number;
    getPage: (
      pageNumber: number,
      cb: (err?: unknown, page?: FlipbookPageAsset) => void,
    ) => void;
  }

  export interface FlipbookViewerInstance {
    page_count: number;
    zoom: (zoom?: number) => void;
    flip_forward: () => void;
    flip_back: () => void;
    on: (event: string, handler: (...args: unknown[]) => void) => void;
    off?: (event: string, handler: (...args: unknown[]) => void) => void;
  }

  export interface FlipbookViewerOptions {
    backgroundColor?: string;
    boxBorder?: number;
    width?: number;
    height?: number;
    margin?: number;
    marginTop?: number;
    marginLeft?: number;
    popup?: boolean;
    singlepage?: boolean;
  }

  export function init(
    book: FlipbookBook,
    container: string | Element,
    opts: FlipbookViewerOptions,
    cb: (err?: unknown, viewer?: FlipbookViewerInstance) => void,
  ): void;

  export function init(
    book: FlipbookBook,
    container: string | Element,
    cb: (err?: unknown, viewer?: FlipbookViewerInstance) => void,
  ): void;
}
