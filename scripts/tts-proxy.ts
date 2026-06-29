// Darija TTS proxy — gives the live "read it to me" box on the page a real Jamal voice.
//
// Why this exists: a normal browser can't call Microsoft's edge-tts (Jamal) service directly
// (it blocks non-Edge browsers and there's no free CORS-enabled Darija API). This tiny relay
// runs server-side — where edge-tts works fine — and returns the MP3 with permissive CORS so
// the static page can play it. Nothing is stored; responses may be cached by the browser/CDN.
//
// Deploy (easiest → Val.town):
//   1. Go to val.town, New → HTTP val, paste this file.
//   2. Save. Copy the val's URL.
//   3. On the World Cup page, open Darija → the 🎙️ section → ⚙️ settings, paste the URL, save.
//
// Also works on Deno Deploy (wrap the handler in `Deno.serve(handler)`), or any Deno/Node host.

import { EdgeTTS } from "npm:edge-tts-universal";

const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type",
};

export default async function handler(req: Request): Promise<Response> {
  if (req.method === "OPTIONS") return new Response(null, { headers: CORS });
  if (req.method !== "POST") return new Response("POST a JSON { text, voice }", { status: 405, headers: CORS });
  try {
    const { text, voice } = await req.json();
    const clean = String(text || "").slice(0, 2000);            // cap length; nothing persisted
    if (!clean) return new Response("missing text", { status: 400, headers: CORS });
    const tts = new EdgeTTS(clean, voice || "ar-MA-JamalNeural");
    const result = await tts.synthesize();
    const bytes = await result.audio.arrayBuffer();
    return new Response(bytes, {
      headers: { ...CORS, "Content-Type": "audio/mpeg", "Cache-Control": "public, max-age=86400" },
    });
  } catch (e) {
    return new Response("tts error: " + (e && (e as Error).message || e), { status: 500, headers: CORS });
  }
}

// Uncomment for Deno Deploy / `deno run`:
// Deno.serve(handler);
