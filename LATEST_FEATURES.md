## Production Architecture & Recent Feature Integrations

To transition the system from a local prototype to a secure, production-ready application, the following architectural upgrades and features were implemented:

### 1. Cloud Infrastructure & Deployment
*   **Docker Containerization:** Packaged the FastAPI backend, NLP models (SBERT/spaCy), and OCR dependencies (`tesseract-ocr`, `poppler-utils`) into a customized, lightweight Docker container (`python:3.10-slim`).
*   **Hugging Face Spaces Hosting:** Deployed the Dockerized application to Hugging Face Spaces for scalable, cloud-based inference and public accessibility.
*   **Custom Domain Routing:** Configured a Cloudflare Redirect Rule to seamlessly route traffic from a custom subdomain (`https://resume.sarshijkarn.com.np`) to the Hugging Face Space endpoint.

### 2. Database & Data Persistence
*   **Supabase PostgreSQL Migration:** Migrated from ephemeral local SQLite to a persistent, remote PostgreSQL instance hosted on Supabase.
*   **Connection Pooling Optimization:** Integrated Supabase's session-mode connection pooler (`asyncpg` compatible) to handle high-concurrency database connections efficiently.
*   **Bulk Scan Persistence:** Refactored background worker tasks to asynchronously persist bulk-processed resume screening results directly to the PostgreSQL database, enabling unified historical analysis.

### 3. Security & Cross-Origin Authentication
*   **Cross-Origin Cookie Policies:** Reconfigured Starlette's `SessionMiddleware` (`SameSite=None`, `Secure=True`) to support strict browser security policies when hosted inside Hugging Face iframe deployments.

### 4. HR Data Isolation (Multi-Tenancy)
*   **Database Schema Evolution:** Upgraded the `ResumeAnalysis` schema with session-bound `username` indexing to transition from single-user to multi-tenant architecture.
*   **Isolated Scan & History Sessions:** Both single-resume scanning and bulk batch-screening processes dynamically bind the generated data to the currently authenticated HR account. 
*   **Strict Access Control:** The Analytics Dashboard and History Views rigorously enforce row-level filtering. Deletion and viewing endpoints explicitly verify ownership, ensuring complete data privacy and preventing cross-tenant data leaks between different recruiters.

