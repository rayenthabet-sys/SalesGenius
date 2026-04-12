import { PLOTSENSE_BASE_URL } from '../config';

/**
 * PlotSense API wrapper
 * Calls the Gradio /run/predict endpoint on the PlotSense backend.
 * Accepts a File object (from <input type="file">).
 */
export async function analyzeCSV(file) {
  // Gradio expects multipart for file uploads — use the /upload + /predict pattern
  const uploadForm = new FormData();
  uploadForm.append('files', file);

  // 1. Upload the file to Gradio's /upload endpoint
  const uploadRes = await fetch(`${PLOTSENSE_BASE_URL}/upload`, {
    method: 'POST',
    body: uploadForm,
  });

  if (!uploadRes.ok) {
    const text = await uploadRes.text();
    throw new Error(`PlotSense upload error ${uploadRes.status}: ${text}`);
  }

  const uploadJson = await uploadRes.json();
  const filePath = uploadJson[0]; // Gradio returns an array of uploaded paths

  // 2. Predict using the uploaded file path
  const predictRes = await fetch(`${PLOTSENSE_BASE_URL}/run/predict`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      fn_index: 0,
      data: [{ name: file.name, data: null, is_file: true, orig_name: file.name, tmp_path: filePath }],
    }),
  });

  if (!predictRes.ok) {
    const text = await predictRes.text();
    throw new Error(`PlotSense predict error ${predictRes.status}: ${text}`);
  }

  const json = await predictRes.json();
  // Returns [dataset_info, plot_fig, recommendations_text, ai_insights]
  const [datasetInfo, plotFig, recommendationsText, aiInsights] = json.data;
  return { datasetInfo, plotFig, recommendationsText, aiInsights };
}
