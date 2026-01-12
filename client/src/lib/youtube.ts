export function extractVideoId(url: string) {
  try {
    const parsed = new URL(url);
    if (parsed.hostname.includes("youtu.be")) {
      return parsed.pathname.replace("/", "");
    }
    if (parsed.hostname.includes("youtube.com")) {
      const v = parsed.searchParams.get("v");
      if (v) return v;
      const match = parsed.pathname.match(/\/embed\/(.+)/);
      if (match) return match[1];
    }
  } catch (error) {
    return null;
  }
  return null;
}

export function isValidYoutubeUrl(url: string) {
  return Boolean(extractVideoId(url));
}

export function buildEmbedUrl(videoId: string) {
  return `https://www.youtube.com/embed/${videoId}`;
}

export async function fetchYoutubeOembed(url: string) {
  const response = await fetch(`https://www.youtube.com/oembed?url=${encodeURIComponent(url)}&format=json`);
  if (!response.ok) return null;
  return (await response.json()) as {
    title?: string;
    author_name?: string;
    thumbnail_url?: string;
  };
}
