# Database and System Architecture Guide: Resume Screener

This document is a comprehensive guide to understanding how the database and your local system interact in your Resume Screener project. It is specifically designed to help you confidently present your project during your final defense without accidentally breaking anything.

## 1. The Basics: What is `localhost`?
- **Localhost** (`127.0.0.1`) simply means "this computer." 
- When your app runs on `http://localhost:8000`, it means your web server is running entirely on your machine. No one else on the internet can access it.
- Similarly, your PostgreSQL database is running on `localhost:5432`. Your Python app talks to your PostgreSQL database internally on your machine using this port.

## 2. Where is the Database Stored?
- You are using **PostgreSQL 17** (as seen in your pgAdmin screenshot).
- **pgAdmin 4** is just a *viewer* (a graphical user interface). It is NOT the database itself. It is a tool that lets you look inside PostgreSQL easily.
- The actual data is saved deep inside your Windows file system, typically in `C:\Program Files\PostgreSQL\17\data`. 
- **DO NOT** ever touch, move, or delete files in that `data` folder directly. Always use pgAdmin or your Python app to interact with the database.

## 3. How the App Connects to the Database
1. The app looks at the `.env` file in your project folder.
2. It finds the credentials: Username (`postgres`), Password (`postgres`), Port (`5432`), and Database Name (`resume_screener`).
3. Using a Python library called **SQLAlchemy**, the app connects to the database. SQLAlchemy acts as a translator, turning Python code into SQL queries.

## 4. Understanding Your Tables
If you expand the `resume_screener` database in pgAdmin (under `Schemas > public > Tables`), you will see three main tables:
1. **`users`**: Stores login credentials. Passwords are encrypted (hashed) using SHA-256 before saving. If you look at this table in pgAdmin, you will not see "password123"; you will see a long string of random characters.
2. **`job_descriptions`**: Stores the job descriptions uploaded by HR.
3. **`resume_analyses`**: Stores the results of every resume processed (match scores, AI plausibility, classification). 

## 5. Dos and Don'ts for Your Final Defense

### DOs: ✅
- **DO** use the `run.bat` file to start your project. It cleanly activates your environment and starts the server.
- **DO** keep pgAdmin open in the background if you want to show the examiners that data is actually being saved to a real database in real-time. (You can right-click a table in pgAdmin and select "View/Edit Data" to prove it works).
- **DO** remember the default demo accounts seeded in the database:
  - HR Admin: Username: `admin` | Password: `hr2026`
  - Applicant: Username: `applicant` | Password: `apply2026`

### DON'Ts: ❌
- **DON'T** delete or rename the `.env` file. Without it, the app will crash because it won't know how to log into PostgreSQL.
- **DON'T** stop the PostgreSQL service in Windows Services. If PostgreSQL isn't running in the background, the app will throw a "Connection Refused" error immediately on startup.
- **DON'T** manually edit rows in pgAdmin during the live demo unless specifically asked to. It's safer to let the Python app handle data insertion.
- **DON'T** panic if the very first request takes ~1 minute to load. Explain to the examiners that the system is *Pre-warming AI Models* (loading massive NLP and SBERT neural networks into RAM) so that all subsequent requests run instantly.

## 6. Clearing Up Potential Doubts
- **"Is the system secure?"**: Yes. Passwords are not saved as plain text. The system uses SHA-256 hashing.
- **"What happens if the app crashes?"**: If the app crashes, the data in PostgreSQL is safe. PostgreSQL saves everything to your hard drive permanently. When you restart the app via `run.bat`, all previous resumes and users will still be there.
- **"Do I need the internet?"**: The core app and database run entirely offline on your localhost. However, if your code uses external APIs (like Groq/OpenAI for LLM detection, or if it needs to download the spaCy model for the first time), you will need an internet connection.

## 7. Frequently Asked Questions (Live Demo)

- **"How do I actually view the saved data in pgAdmin?"**
  In your pgAdmin (like in your screenshot), you are right-clicking the `users` table. Instead of clicking "Refresh", go slightly up and click **View/Edit Data** -> **All Rows**. A new tab will open on the right side showing you exactly what is stored inside that table (like the usernames and hashed passwords).

- **"If a user registers, is the data saved permanently?"**
  **YES, 100% permanent.** PostgreSQL does not just save data in your temporary RAM; it writes it directly to your physical hard drive. 
  Even if you:
  - Close the `run.bat` terminal.
  - Turn off the localhost server.
  - Shut down your computer completely.
  - Unplug your laptop for a week.
  
  The next time you turn your computer back on and run `run.bat`, that user's data will **still be there**, and they will still be able to log in with the exact same credentials. The data stays there forever until you explicitly write an SQL command to DELETE it, or uninstall PostgreSQL entirely.

## 8. What Exactly Gets Saved? (Are Resumes Saved?)

It is very important to understand exactly what goes into the database and what doesn't. Your system is actually highly optimized for privacy:

1. **User Credentials (`users` table):**
   - Usernames and roles (Applicant vs HR).
   - Encrypted (hashed) passwords.

2. **Job Descriptions (`job_descriptions` table):**
   - The job title and the raw text of the job description uploaded by HR.

3. **Resume Analysis Results (`resume_analyses` table):**
   - The *filename* of the resume (e.g., `john_doe_resume.pdf`).
   - The AI Classification (e.g., "Authentic", "Suspicious").
   - The Match Scores (e.g., 85.5%).
   - A JSON summary containing the extracted skills, years of experience, and a text preview.

**Are the actual physical Resume files (PDFs/Word Docs) saved?**
**NO.** The actual physical files uploaded by applicants are **never saved** to PostgreSQL and they are **never saved** to your hard drive. 

Here is exactly what happens when a resume is uploaded:
1. The PDF is loaded into temporary RAM.
2. The AI reads the text out of it.
3. The AI scores the text and saves the *results* (the score and a summary) into PostgreSQL.
4. The actual PDF file is immediately thrown away and discarded from RAM.

This is a great point to bring up during your defense if they ask about data privacy or storage limits: your system is lightweight because it doesn't hoard heavy PDF files, it only stores the valuable extracted data!

You are fully set up. Follow these guidelines and your defense will go smoothly!
