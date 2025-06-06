# 🚀 getbusiness

**Google Maps Business Scraper**  
_By [Muhidtech](https://github.com/muhidtech)_

---

## 🌟 Overview

**getbusiness** is a powerful, user-friendly tool for extracting business information from Google Maps.  
It supports both a beautiful GUI and a fast, interactive CLI, making it perfect for researchers, marketers, and anyone who needs structured business data at scale.

- **Extracts:** Name, Address, Phone, Email, Website, Social Media Links
- **Interfaces:** Tkinter GUI & Command-Line (CLI)
- **Exports:** JSON & CSV
- **Easy to Use:** No coding required for basic use!

---

## ✨ Features

- **Dual Interface:**  
  - 🖥️ **GUI:** Modern, dark-themed, intuitive controls  
  - 💻 **CLI:** Interactive, scriptable, and fast
- **Smart Extraction:**  
  - Finds official websites, emails, phone numbers, and social links (Facebook, Instagram, Twitter/X, LinkedIn, YouTube, TikTok)
- **Live Progress:**  
  - See results as they are found (in both GUI and CLI)
- **Export:**  
  - Save results as JSON or CSV for easy use in Excel or other tools
- **Pause/Resume/Stop:**  
  - Full control over scraping sessions
- **Open Source:**  
  - MIT License, easy to extend

---

## 🛠️ Installation

1. **Clone the repo:**
    ```sh
    git clone https://github.com/muhidtech/getbusiness.git
    cd getbusiness
    ```

2. **Install dependencies:**
    ```sh
    pip install -r requirements.txt
    ```
    _If you don't have a `requirements.txt`, install manually:_
    ```sh
    pip install selenium webdriver-manager beautifulsoup4 google-api-python-client
    ```

3. **(Optional) Set up your Google Custom Search API key**  
   Edit `extract_businesses.py` and set your own `api_key` and `cse_id` for best results.

---

## 🚦 Usage

### 🖥️ GUI Mode (Recommended)

```sh
python getbusinesses.py
```

- Enter your search query (e.g., `restaurants in Accra`)
- Set the maximum number of results
- Click **Start**
- Use **Pause**, **Resume**, **Stop**, **Show Saved**, **Export to CSV**, and **About** as needed

### 💻 CLI Mode

```sh
python getbusinesses.py -t cli
```

**Commands:**
- `search` — Start a new search (prompts for query and max results)
- `show` — Display saved businesses
- `clear` — Clear saved businesses
- `exit` — Quit the CLI
- `help` — Show all commands

---

## 📦 Output

- **JSON:** All results are saved to `businesses.json`
- **CSV:** Export via GUI button or manually

**Sample JSON entry:**
```json
{
  "name": "Example Business",
  "address": "123 Main St, Accra",
  "phone": "+233 20 123 4567",
  "email": "info@example.com",
  "website": "https://example.com",
  "social_links": {
    "facebook": "https://facebook.com/example",
    "instagram": "https://instagram.com/example"
  }
}
```

---

## 🧠 How It Works

- Uses Selenium to automate Google Maps search and extract business cards
- Parses business details with BeautifulSoup
- Uses Google Custom Search API to find official social media links
- Cleans and deduplicates data before saving

---

## ⚡ Tips & Best Practices

- For best results, use specific queries (e.g., `cafes in Kumasi`)
- Increase "Max Results" for larger datasets, but note that Google Maps may limit results
- Use your own Google Custom Search API key for higher accuracy and quota

---

## 🐞 Troubleshooting

- **Missing modules?**  
  Install with `pip install -r requirements.txt`
- **Chrome not found?**  
  Make sure Google Chrome is installed and up to date
- **API errors?**  
  Set your own Google API key and CSE ID in `extract_businesses.py`

---

## 🤝 Contributing

Pull requests are welcome!  
Open an issue for feature requests or bug reports.

---

## 📄 License

MIT License

---

## 🙏 Credits

- [Selenium](https://www.selenium.dev/)
- [webdriver-manager](https://github.com/SergeyPirogov/webdriver_manager)
- [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/)
- [Google API Python Client](https://github.com/googleapis/google-api-python-client)

---

## ⭐ Motivation

> **"Data is the new oil."**  
> getbusiness empowers you to collect business data quickly and ethically, helping you make smarter decisions, build better products, and connect with the world.

---

**Made with ❤️ by [Muhidtech](https://github.com/muhidtech)**