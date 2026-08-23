# ClearHire - Latest Feature Updates (v1.1)

This document details the latest features, architectural upgrades, and deployment configurations implemented in the ClearHire (SBERT Resume Screener) project. These updates transition the application from a local development prototype to a secure, multi-tenant, cloud-hosted production environment.

## 1. HR User Isolation (Multi-Tenant Security)
To support multiple HR recruiters across different companies, the system now enforces strict data isolation based on authenticated sessions.

*   **Schema Migration:** Upgraded the `ResumeAnalysis` table in PostgreSQL to include an indexed `username` column.
*   **Session Binding:** Both single-resume scans and bulk batch-screening processes now automatically bind the generated analysis records to the currently logged-in HR user.
*   **Isolated Analytics:** The Analytics Dashboard and History View dynamically filter database queries (`WHERE username = session.username`), ensuring HR recruiters only see the candidates they have personally scanned.
*   **Access Control:** Deletion and detailed viewing endpoints explicitly verify ownership before executing database operations, preventing cross-tenant data leaks.

## 2. Bulk Scan Database Persistence
Previously, batch processing results were ephemeral. Bulk screening has been entirely refactored for persistent storage.

*   **Background Task Context Injection:** The `/api/predict_batch` endpoint now captures the session context before delegating to the background worker.
*   **Asynchronous Database Logging:** As the background task finishes screening each resume in a zip file, it asynchronously saves the full feature array (Semantic Similarity, Skill Overlap, XGBoost Classification, etc.) to the PostgreSQL database.
*   **Unified History:** Bulk-processed resumes now seamlessly populate the HR dashboard's history and export features alongside single-scan resumes.

## 3. Production Cloud Deployment
The application is now live on the internet, hosted via a combination of Hugging Face Spaces and Supabase.

*   **Docker Containerization:** Created a custom `Dockerfile` based on `python:3.10-slim`. Installed complex system dependencies (`tesseract-ocr`, `poppler-utils`, `libgl1`) required by the NLP and OCR pipelines.
*   **Supabase PostgreSQL Integration:** Transitioned from a local SQLite/PostgreSQL setup to a persistent cloud database on Supabase.
*   **AsyncPG Optimization:** Configured the database connection string to utilize Supabase's session-mode pooler (port 5432) for flawless compatibility with `asyncpg` and prepared statements.
*   **Cross-Origin Session Fixes:** Updated Starlette's `SessionMiddleware` to use `same_site="none"` and `https_only=True`. This resolves strict modern browser blocking policies when the app is served inside a Hugging Face Space iframe.
*   **Custom Domain Routing:** Configured a Cloudflare Redirect Rule to seamlessly route `https://resume.sarshijkarn.com.np/` to the Hugging Face Space, providing users with a clean, branded entry point.
*   **Branding:** Injected the custom ClearHire `favicon.ico` across all Jinja2 HTML templates for a polished production feel.
