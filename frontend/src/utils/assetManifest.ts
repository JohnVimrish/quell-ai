export type ViteManifestEntry = {
  file: string;
  css?: string[];
  isEntry?: boolean;
};

export type ViteManifest = Record<string, ViteManifestEntry>;







