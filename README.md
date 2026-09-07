# 🔎 Darus Search Engine

**Darus Search Engine** adalah MCP (Model Context Protocol) untuk membantu AI melakukan pencarian dan riset web secara cepat, multi-sumber, dan terstruktur.

Project ini merupakan modifikasi dari [RivalSearchMCP](https://github.com/damionrashford/RivalSearchMCP) dengan fokus utama pada **Ultra Speed**: eksekusi asynchronous/concurrent, connection reuse, caching, dan pengurangan bottleneck internal sambil tetap mempertahankan coverage sumber dan kemampuan tool.

## 🚀 Cocok Untuk Apa?

Darus Search Engine cocok untuk AI agent, chatbot, coding agent, research assistant, dan aplikasi yang membutuhkan akses ke data web tanpa harus membangun seluruh sistem search/crawling dari nol.

Contoh penggunaan:

- 🔎 Pencarian web multi-engine
- 📰 Riset berita dan informasi terbaru
- 💬 Pencarian komunitas/social web
- 🐙 Pencarian repository dan kode GitHub
- 🔬 Pencarian paper akademik dan dataset
- 🌐 Crawling / pemetaan website
- 📄 Membaca dan menganalisis halaman, dokumen, PDF, DOCX, dan gambar/OCR
- 🧠 Riset topik dan profiling entity dengan menggabungkan banyak sumber
- 🔍 Mengambil, menilai, dan membandingkan konten dari beberapa URL

## ⚡ Ultra Speed

Darus mempertahankan beberapa sumber pencarian dan menjalankannya secara concurrent sehingga satu provider yang lambat tidak perlu membuat provider lain berjalan secara serial.

Optimasi mencakup:

- Concurrent multi-source search
- HTTP connection pooling / reuse
- Cache untuk operasi yang mahal dan request berulang
- Concurrent content fetching dan crawling
- Fast default search tanpa otomatis membuka semua halaman hasil
- Per-source failure isolation agar kegagalan satu sumber tidak menghentikan sumber lain

> **Catatan:** Ultra Speed mengurangi bottleneck internal aplikasi. Latency dan rate limit dari provider eksternal seperti search engine, GitHub, Reddit, dan sumber web lainnya tetap berada di luar kontrol server.

## 🛠️ MCP Tools

Darus Search Engine menyediakan 9 tool utama:

1. `web_search` — DuckDuckGo, Bing, Yahoo, Mojeek, Wikipedia
2. `social_search` — Reddit, Hacker News, Dev.to, Product Hunt, Medium, Stack Overflow, Bluesky, Lobste.rs, Lemmy
3. `news_aggregation` — Google News, Bing News, The Guardian, GDELT, DuckDuckGo News
4. `github_search` — pencarian repository/kode GitHub
5. `map_website` — crawling dan pemetaan website
6. `content_operations` — retrieve, stream, analyze, extract, score, conflict checking, dan validasi konten
7. `research_topic` — riset topic atau entity lintas sumber
8. `scientific_research` — paper akademik dan dataset
9. `document_analysis` — PDF, DOCX, text, image, dan OCR

## 🔗 MCP Endpoint

Endpoint HTTP yang digunakan oleh deployment FastMCP:

```text
https://darus-search-engine.fastmcp.app/mcp
```

**Penting:** URL di atas adalah **target endpoint deployment** untuk project Darus Search Engine. Endpoint baru dapat digunakan setelah repository ini dideploy ke FastMCP/Horizon dengan slug `darus-search-engine`. Repository GitHub sendiri tidak otomatis membuat hostname `*.fastmcp.app` aktif.

Untuk self-host, konfigurasi aplikasi menggunakan HTTP MCP di port `3000` dengan path `/mcp/`.

## 📦 Open Source

Darus Search Engine dikembangkan dari source code RivalSearchMCP yang berlisensi MIT. Silakan lihat repository upstream dan pertahankan attribution/license yang berlaku saat mendistribusikan modifikasi.

Upstream: https://github.com/damionrashford/RivalSearchMCP

## ⚠️ Batasan

Darus dapat mengoptimalkan concurrency, caching, dan overhead internal, tetapi tidak dapat menghapus rate limit atau downtime yang diberlakukan oleh layanan eksternal. Menghapus timeout aplikasi juga berarti request upstream yang benar-benar hang dapat menunggu tanpa batas.
