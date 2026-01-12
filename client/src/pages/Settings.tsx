import { useEffect, useState } from "react";
import { loadActivePresetId, loadPresets, saveActivePresetId, savePresets } from "../lib/store";
import { Preset } from "../lib/types";

const Settings = () => {
  const [presets, setPresets] = useState<Preset[]>([]);
  const [activePresetId, setActivePresetId] = useState<string | undefined>();
  const [name, setName] = useState("");
  const [watermark, setWatermark] = useState("");
  const [template, setTemplate] = useState("standard");

  useEffect(() => {
    const stored = loadPresets();
    setPresets(stored);
    setActivePresetId(loadActivePresetId() ?? stored[0]?.id);
  }, []);

  const addPreset = () => {
    if (!name.trim()) return;
    const newPreset: Preset = {
      id: crypto.randomUUID(),
      name: name.trim(),
      watermark: watermark.trim(),
      template: template.trim(),
    };
    const next = [newPreset, ...presets];
    setPresets(next);
    savePresets(next);
    if (!activePresetId) {
      setActivePresetId(newPreset.id);
      saveActivePresetId(newPreset.id);
    }
    setName("");
    setWatermark("");
    setTemplate("standard");
  };

  const handleActiveChange = (presetId: string) => {
    setActivePresetId(presetId);
    saveActivePresetId(presetId);
  };

  return (
    <section>
      <header className="page-header">
        <div>
          <h1>Settings</h1>
          <p>Manage your presets and branding options.</p>
        </div>
      </header>

      <div className="card">
        <h3>Create Preset</h3>
        <div className="form-grid">
          <label>
            Preset name
            <input value={name} onChange={(event) => setName(event.target.value)} />
          </label>
          <label>
            Watermark text
            <input value={watermark} onChange={(event) => setWatermark(event.target.value)} />
          </label>
          <label>
            Output template
            <input value={template} onChange={(event) => setTemplate(event.target.value)} />
          </label>
        </div>
        <button className="primary" onClick={addPreset}>
          Save preset
        </button>
      </div>

      <div className="card">
        <h3>Presets</h3>
        {presets.length === 0 ? (
          <p>No presets saved yet.</p>
        ) : (
          <div className="preset-list">
            {presets.map((preset) => (
              <label key={preset.id} className="preset-item">
                <input
                  type="radio"
                  checked={activePresetId === preset.id}
                  onChange={() => handleActiveChange(preset.id)}
                />
                <div>
                  <strong>{preset.name}</strong>
                  <p>Watermark: {preset.watermark || "None"}</p>
                  <p>Template: {preset.template}</p>
                </div>
              </label>
            ))}
          </div>
        )}
      </div>
    </section>
  );
};

export default Settings;
