#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::process::Command;

use tauri::{Manager, WindowEvent};

fn main() {
    tauri::Builder::default()
        .setup(|app| {
            let main_window = app.get_window("main").expect("main window");
            main_window.listen("run-cli", move |event| {
                if let Some(payload) = event.payload() {
                    let args: Vec<String> = serde_json::from_str(payload).unwrap_or_default();
                    let _ = Command::new("creatorpack").args(args).spawn();
                }
            });
            Ok(())
        })
        .on_window_event(|event| {
            if let WindowEvent::CloseRequested { api, .. } = event.event() {
                api.prevent_close();
                event.window().hide().ok();
            }
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
