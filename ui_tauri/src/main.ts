import { listen } from "@tauri-apps/api/event";
import { invoke } from "@tauri-apps/api/tauri";

const form = document.getElementById("job-form") as HTMLFormElement | null;
const logView = document.getElementById("log") as HTMLPreElement | null;

if (form) {
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const data = new FormData(form);
    const payload = {
      file: (data.get("file") as string) ?? "",
      template: (data.get("template") as string) ?? "creator-pack",
      minutes: Number(data.get("minutes") ?? 10),
      smart: data.get("smart") === "on",
      highlights: data.get("highlights") === "on",
      brand: (data.get("brand") as string) || undefined,
    };

    if (!payload.file) {
      appendLog("Select a file before running.");
      return;
    }

    appendLog("Launching CreatorPack job...");
    try {
      await invoke("run_creatorpack", { args: payload });
    } catch (error) {
      appendLog(`Error: ${error}`);
    }
  });
}

function appendLog(message: string) {
  if (!logView) return;
  const timestamp = new Date().toISOString();
  logView.textContent = `${timestamp} ${message}
${logView.textContent ?? ""}`;
}

listen("job-log", (event) => {
  const payload = event.payload as { message?: string };
  if (payload?.message) {
    appendLog(payload.message);
  }
});
