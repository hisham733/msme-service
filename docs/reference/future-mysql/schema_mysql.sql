CREATE DATABASE IF NOT EXISTS msme_newsbot DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE msme_newsbot;

-- Schema for the MSME newsbot. Prepared for switching the service off SQLite
-- and onto MySQL (config.DB_ENGINE=mysql + MYSQL_DSN). Not yet used.

CREATE TABLE IF NOT EXISTS runs (
    id VARCHAR(64) PRIMARY KEY,
    email_id VARCHAR(200),
    subject TEXT,
    status VARCHAR(20),
    created_at DATETIME,
    error TEXT,
    INDEX idx_runs_status (status),
    INDEX idx_runs_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS checklist (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    subject TEXT,
    threadId VARCHAR(200),
    date VARCHAR(100),
    folderId VARCHAR(200),
    folderUrl VARCHAR(500),
    articleFile VARCHAR(300),
    hasArticle VARCHAR(5),
    hasPic VARCHAR(5),
    hasLogo VARCHAR(5),
    hasLogoInArticle VARCHAR(5),
    hasImageInArticle VARCHAR(5),
    subjectMatch VARCHAR(5),
    subjectScore VARCHAR(10),
    readyToFilter VARCHAR(5),
    created_at DATETIME,
    INDEX idx_checklist_thread (threadId),
    INDEX idx_checklist_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
-- D32: one filter verdict per checklist row (latest shown; history retained)
CREATE TABLE IF NOT EXISTS filter_results (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    checklist_id BIGINT,
    run_id VARCHAR(64),
    threadId VARCHAR(200),
    status VARCHAR(20),
    outcome VARCHAR(30),
    weighted INT,
    gate VARCHAR(80),
    confidence DOUBLE,
    gates JSON,
    scores JSON,
    verdict JSON,
    model VARCHAR(80),
    error TEXT,
    created_at DATETIME,
    INDEX idx_filter_checklist (checklist_id),
    INDEX idx_filter_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
