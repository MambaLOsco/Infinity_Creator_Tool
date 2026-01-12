#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use anyhow::Context;
use serde::{Deserialize, Serialize};
use std::process::{Command, Stdio};
use std::sync::Mutex;
use tauri::{Manager, State};

#[derive(Default)]
struct JobState {
    running: Mutex<bool>,
}

#[derive(Deserialize)]
struct RunArgs {
    file: String,
    template: String,
    minutes: u32,
    smart: bool,
    highlights: bool,
    brand: Option<String>,
}

#[derive(Serialize)]
struct JobEvent {
    message: String,
}

#[tauri::command]
async fn run_creatorpack(state: State<'_, JobState>, window: tauri::Window, args: RunArgs) -> Result<(), String> {
    {
        let mut running = state.running.lock().unwrap();
        if *running {
            return Err("A job is already running".into());
        }
        *running = true;
    }

    let mut command = Command::new("creatorpack");
    command.arg("run");
    command.arg("--file");
    command.arg(&args.file);
    command.arg("--template");
    command.arg(&args.template);
    command.arg("--minutes");
    command.arg(args.minutes.to_string());
    if args.smart {
        command.arg("--smart");
    }
    if args.highlights {
        command.arg("--highlights");
    }
    if let Some(brand) = &args.brand {
        command.arg("--brand");
        command.arg(brand);
    }
    command.stdout(Stdio::piped());
    command.stderr(Stdio::piped());

    let mut child = command.spawn().map_err(|err| err.to_string())?;

    let stdout = child
        .stdout
        .take()
        .context("stdout not captured")
        .map_err(|err| err.to_string())?;

    let window_clone = window.clone();
    tauri::async_runtime::spawn(async move {
        use tokio::io::{AsyncBufReadExt, BufReader};
        let mut reader = BufReader::new(stdout).lines();
        while let Ok(Some(line)) = reader.next_line().await {
            let _ = window_clone.emit("job-log", JobEvent { message: line });
        }
    });

    let status = child.wait().map_err(|err| err.to_string())?;
    {
        let mut running = state.running.lock().unwrap();
        *running = false;
    }
    if status.success() {
        window.emit("job-log", JobEvent { message: "Job completed" }).map_err(|err| err.to_string())?;
        Ok(())
    } else {
        Err(format!("CreatorPack exited with status {status}"))
    }
}

fn main() {
    tauri::Builder::default()
        .manage(JobState::default())
        .invoke_handler(tauri::generate_handler![run_creatorpack])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
