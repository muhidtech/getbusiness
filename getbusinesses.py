import time
import json
import urllib.parse
import threading
import argparse
import sys
import csv
from tkinter import (
    Tk, Entry, Button, Text, Scrollbar, Label,
    END, DISABLED, NORMAL, Frame, messagebox, filedialog, Toplevel
)
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

from extract_businesses import extract_businesses

# === DRIVER SETUP ===
def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--window-size=1920,1080")
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)

# === FLAGS ===
stop_flag = False
pause_flag = False

def run_extraction(query, max_results, text_box=None, log_func=None):
    global stop_flag, pause_flag
    stop_flag = False
    pause_flag = False
    encoded_query = urllib.parse.quote(query)
    search_url = f"https://www.google.com/maps/search/{encoded_query}"

    def log(msg):
        if text_box:
            text_box.config(state=NORMAL)
            text_box.insert(END, msg)
            text_box.see(END)
            text_box.config(state=DISABLED)
        elif log_func:
            log_func(msg)
        else:
            print(msg, end="")

    log(f"🔍 Starting extraction for: {query} (max {max_results} results)\n")

    driver = setup_driver()
    driver.get(search_url)

    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CLASS_NAME, "Nv2PK"))
        )
    except Exception as e:
        log(f"❌ Timed out: {e}\n")
        driver.quit()
        return []

    try:
        def live_callback(biz):
            while pause_flag:
                time.sleep(0.5)
            log(f"✅ {biz['name']}\n")

        results = extract_businesses(
            driver,
            max_results=max_results,
            live_callback=live_callback,
            stop_flag_func=lambda: stop_flag
        )

        if stop_flag:
            log("\n🛑 Extraction manually stopped.\n")
        else:
            log(f"\n🎉 Finished! Total: {len(results)} businesses found.\n")

    except Exception as e:
        log(f"❌ Error during extraction: {e}\n")
        results = []

    driver.quit()
    return results

def show_saved_json(text_box=None, file_path="businesses.json", log_func=None):
    def log(msg):
        if text_box:
            text_box.config(state=NORMAL)
            text_box.insert(END, msg)
            text_box.config(state=DISABLED)
        elif log_func:
            log_func(msg)
        else:
            print(msg, end="")

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        log("\n📂 Saved Businesses:\n\n")
        for i, biz in enumerate(data, start=1):
            name = biz.get("name", "N/A")
            phone = biz.get("phone", "N/A")
            address = biz.get("address", "N/A")
            social = biz.get("social_links", "N/A")
            website = biz.get("website", "N/A")
            log(f"{i}. 🏢 {name}\n")
            log(f"   📞 Phone: {phone}\n")
            log(f"   📍 Address: {address}\n")
            log(f"   🌐 Website: {website}\n")
            log(f"   🔗 Social: {social}\n\n")
    except Exception as e:
        log(f"⚠️ Could not read file: {e}\n")

def export_to_csv(json_file="businesses.json"):
    try:
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not data:
            messagebox.showinfo("Export", "No data to export.")
            return
        file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if not file_path:
            return
        with open(file_path, "w", newline="", encoding="utf-8") as csvfile:
            fieldnames = ["name", "address", "phone", "email", "website", "social_links"]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for biz in data:
                writer.writerow({
                    "name": biz.get("name", ""),
                    "address": biz.get("address", ""),
                    "phone": biz.get("phone", ""),
                    "email": biz.get("email", ""),
                    "website": biz.get("website", ""),
                    "social_links": str(biz.get("social_links", "")),
                })
        messagebox.showinfo("Export", f"Exported to {file_path}")
    except Exception as e:
        messagebox.showerror("Export Error", str(e))

def show_about():
    about = Toplevel()
    about.title("About")
    about.geometry("400x200")
    Label(about, text="Google Maps Business Scraper", font=("Arial", 14, "bold")).pack(pady=10)
    Label(about, text="By Muhidtech\n\nScrapes business info from Google Maps.\nSupports CLI and GUI.\n\n© 2025", justify="center").pack(pady=10)

def launch_gui():
    global stop_flag, pause_flag
    root = Tk()
    root.title("Google Maps Business Scraper")
    root.geometry("900x750")
    root.configure(bg="#181818")

    label_style = {"bg": "#181818", "fg": "white", "font": ("Arial", 11)}
    entry_style = {"bg": "#232323", "fg": "white", "insertbackground": "white", "font": ("Arial", 11)}

    Label(root, text="Search Query:", **label_style).pack(pady=3)
    query_entry = Entry(root, width=70, **entry_style)
    query_entry.pack(pady=3)

    Label(root, text="Max Results:", **label_style).pack(pady=3)
    max_results_entry = Entry(root, width=10, **entry_style)
    max_results_entry.insert(0, "3")
    max_results_entry.pack(pady=3)

    text_area = Text(root, wrap="word", height=28, state=DISABLED, bg="#1a1a1a", fg="white", insertbackground="white", font=("Consolas", 11))
    text_area.pack(padx=10, pady=10, expand=True, fill="both")

    scrollbar = Scrollbar(root, command=text_area.yview)
    text_area.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side="right", fill="y")

    # ==== Button Frame ====
    button_frame = Frame(root, bg="#181818")
    button_frame.pack(pady=5)

    def start_scrape_thread():
        query = query_entry.get().strip()
        max_results_raw = max_results_entry.get().strip()
        if not query:
            text_area.config(state=NORMAL)
            text_area.insert(END, "⚠️ Please enter a search query.\n")
            text_area.config(state=DISABLED)
            return
        try:
            max_results = int(max_results_raw)
        except ValueError:
            text_area.config(state=NORMAL)
            text_area.insert(END, "⚠️ Max results must be a number.\n")
            text_area.config(state=DISABLED)
            return

        text_area.config(state=NORMAL)
        text_area.delete("1.0", END)
        text_area.config(state=DISABLED)

        thread = threading.Thread(target=run_extraction, args=(query, max_results, text_area))
        thread.start()

    def stop_scraping():
        global stop_flag
        stop_flag = True

    def toggle_pause():
        global pause_flag
        pause_flag = not pause_flag
        pause_button.config(text="Resume" if pause_flag else "Pause")

    def clear_output():
        text_area.config(state=NORMAL)
        text_area.delete("1.0", END)
        text_area.config(state=DISABLED)

    # ==== Buttons with improved visuals ====
    btn_opts = {"bg": "#2d2d2d", "fg": "white", "activebackground": "#444", "activeforeground": "#fff", "width": 14, "font": ("Arial", 10, "bold")}
    Button(button_frame, text="Start", command=start_scrape_thread, **btn_opts).grid(row=0, column=0, padx=5)
    Button(button_frame, text="Stop", command=stop_scraping, **btn_opts).grid(row=0, column=1, padx=5)
    pause_button = Button(button_frame, text="Pause", command=toggle_pause, **btn_opts)
    pause_button.grid(row=0, column=2, padx=5)
    Button(button_frame, text="Clear", command=clear_output, **btn_opts).grid(row=0, column=3, padx=5)
    Button(button_frame, text="Show Saved", command=lambda: show_saved_json(text_area), **btn_opts).grid(row=0, column=4, padx=5)
    Button(button_frame, text="Export to CSV", command=export_to_csv, **btn_opts).grid(row=0, column=5, padx=5)
    Button(button_frame, text="About", command=show_about, **btn_opts).grid(row=0, column=6, padx=5)

    root.mainloop()

def launch_cli():
    print("=== Google Maps Business Scraper CLI ===")
    print("Type 'help' for commands. Ctrl+C or 'exit' to quit.\n")
    while True:
        try:
            cmd = input("Command (search/show/clear/exit/help): ").strip().lower()
            if cmd in ("exit", "quit"):
                print("Bye!")
                break
            elif cmd == "help":
                print("Commands:\n  search - Start a new search\n  show - Show saved businesses\n  clear - Clear saved businesses\n  exit - Quit\n")
            elif cmd == "show":
                show_saved_json(log_func=lambda msg: print(msg, end=""))
            elif cmd == "clear":
                open("businesses.json", "w", encoding="utf-8").write("[]")
                print("Cleared saved businesses.\n")
            elif cmd == "search":
                query = input("Enter search query: ").strip()
                if not query:
                    print("Query cannot be empty.\n")
                    continue
                try:
                    max_results = int(input("Max results (default 10): ").strip() or "10")
                except ValueError:
                    print("Invalid number.\n")
                    continue
                run_extraction(query, max_results, log_func=lambda msg: print(msg, end=""))
            else:
                print("Unknown command. Type 'help' for options.\n")
        except KeyboardInterrupt:
            print("\nBye!")
            break

def main():
    parser = argparse.ArgumentParser(description="Google Maps Business Scraper")
    parser.add_argument("-t", "--type", choices=["gui", "cli"], default="gui", help="Interface type: gui or cli (default: gui)")
    args = parser.parse_args()

    if args.type == "cli":
        launch_cli()
    else:
        launch_gui()

if __name__ == "__main__":
    main()