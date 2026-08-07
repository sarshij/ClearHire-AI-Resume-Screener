# Introduction to PostgreSQL (Postgres)

Welcome! Since you're completely new to this, we'll break it down into simple terms.

## What is PostgreSQL?
PostgreSQL (often just called "Postgres") is an **open-source Relational Database Management System (RDBMS)**. 
Think of it as a highly organized, digital filing cabinet where your application (the Resume Screener) saves all its data—like user accounts, uploaded resumes, analysis results, and scores.

### Key Concepts
1. **Database:** The overall container holding your data (in your case, one named `resume_screener`).
2. **Tables:** Inside the database, data is organized into tables (like spreadsheets). For example, a `users` table or a `resume_analyses` table.
3. **Rows & Columns:** 
   - **Columns** define the type of data (e.g., `filename`, `score`, `classification`).
   - **Rows** are the actual individual entries (e.g., one row = one specific resume you scanned).
4. **SQL (Structured Query Language):** The programming language used to talk to the database (e.g., `SELECT * FROM resume_analyses;`). 
5. **ORM (Object-Relational Mapper):** In your Python project, you are using a tool called **SQLAlchemy**. It allows your Python code to talk to Postgres using Python objects instead of writing raw SQL queries.

## Why did you get that error?
The error `ConnectionRefusedError: [WinError 1225]` happened because your Python app knocked on your computer's "door" (port 5432) looking for Postgres, but Postgres isn't installed or running, so no one answered.

## How to use it for your project
When you run your project, the Python code (FastAPI + SQLAlchemy) will automatically connect to Postgres, create the necessary tables, and save the data for you. You don't usually need to manually write SQL commands unless you are trying to inspect the data by hand.

If you ever want to look inside the database yourself, Postgres comes with a graphical tool called **pgAdmin**, which lets you see your tables and data visually.

## Installation Options

For your 6th-semester minor project, since PostgreSQL is required by your tech stack:
You will need to download and install the official PostgreSQL software. I have provided the exact commands to run in our chat. Once installed and the database is created, your project will run perfectly.
