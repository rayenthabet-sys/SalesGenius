import { SALESGENIUS_BASE_URL } from '../config';

/**
 * SalesGenius API wrapper
 * Calls the Gradio /run/predict endpoint on the SalesGenius backend.
 * All arguments map 1:1 to the Gradio /process_chat fn signature.
 */
export async function sendChatMessage({ message, history, companyName, sector, size, useSearch }) {
  const payload = {
    fn_index: 0,
    data: [
      message,
      history,
      companyName,
      sector,
      size,
      useSearch,
    ],
  };

  const res = await fetch(`${SALESGENIUS_BASE_URL}/run/predict`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`SalesGenius API error ${res.status}: ${text}`);
  }

  const json = await res.json();
  // Gradio returns { data: [msg, history, dna, profile_json, recs, trace] }
  const [, newHistory, dna, profileJson, recommendations, trace] = json.data;
  return { newHistory, dna, profileJson, recommendations, trace };
}
